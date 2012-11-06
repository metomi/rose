# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
# 
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------
"""Wraps Python's subprocess.Popen."""

import os
import re
from rose.reporter import Event
from rose.resource import ResourceLocator
import shlex
from subprocess import Popen, PIPE
import sys


class RosePopenError(Exception):

    """An error raised when a shell command call fails."""

    def __init__(self, command, rc, stdout, stderr, stdin=None):
        self.command = command
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr
        self.stdin = stdin
        Exception.__init__(self, command, rc, stdout, stderr)

    def __str__(self):
        cmd_str = str(RosePopenEvent(self.command, self.stdin))
        tail = ""
        if self.stderr:
            tail = ", stderr=\n%s" % self.stderr
        return "%s # rc=%d%s" % (cmd_str, self.rc, tail)


class RosePopenEvent(Event):

    """An event raised before a shell command call."""

    LEVEL = Event.VV

    def __init__(self, command, stdin):
        self.command = command
        self.stdin = stdin
        Event.__init__(self, command, stdin)

    def __str__(self):
        command = self.command
        if len(command) == 1:
            command = command[0]
        if isinstance(command, str):
            ret = command
        else:
            ret = RosePopener.list_to_shell_str(self.command)
        if isinstance(self.stdin, str):
            ret += " <<'__STDIN__'\n" + self.stdin + "\n'__STDIN__'"
        elif isinstance(self.stdin, file):
            try:
                # FIXME: Is this safe?
                pos = self.stdin.tell()
                ret += " <<'__STDIN__'\n" + self.stdin.read() + "\n'__STDIN__'"
                self.stdin.seek(pos)
            except IOError:
                pass
        return ret


class RosePopener(object):

    """Wrap Python's subprocess.Popen."""

    CMDS = {"editor": ["vi"],
            "fs_browser": ["nautilus"],
            "geditor": ["gedit"],
            "rsync": ["rsync", "-a", "--exclude=.*", "--timeout=1800",
                      "--rsh=ssh -oBatchMode=yes"],
            "ssh": ["ssh", "-oBatchMode=yes"],
            "terminal": ["xterm"]}

    ENVS_OF_CMDS = {"editor": ["VISUAL", "EDITOR"],
                    "geditor": ["VISUAL", "EDITOR"]}

    @classmethod
    def list_to_shell_str(cls, args):
        if not args:
            return ""
        return " ".join([re.sub(r"([\"'\s])", r"\\\1", arg) for arg in args])

    def __init__(self, event_handler=None):
        self.event_handler = event_handler
        self.cmds = {}

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def get_cmd(self, key, *args):
        """Return default options and arguments of a known command as a list.

        If a setting [external] <key> is defined in the site/user
        configuration, use the setting.

        Otherwise, if RosePopener.ENVS_OF_CMDS[key] exists, it looks for each
        environment variable in the list in RosePopener.ENVS_OF_CMDS[key] in
        order. If the environment variable is defined and is not a null string,
        use the value of the environment variable.

        Otherwise, return RosePopener.CMDS[key]

        key: must be a key of RosePopener.CMDS
        args: if specified, will be added to the returned list

        """
        if not self.cmds.has_key(key):
            root_node = ResourceLocator.default().get_conf()
            node = root_node.get(["external", key], no_ignore=True)
            if node is not None:
                self.cmds[key] = shlex.split(node.value)
        if not self.cmds.has_key(key):
            for name in self.ENVS_OF_CMDS.get(key, []):
                if os.getenv(name): # not None, not null str
                    self.cmds[key] = shlex.split(os.getenv(name))
                    break
        if not self.cmds.has_key(key):
            self.cmds[key] = self.CMDS[key]
        return self.cmds[key] + list(args)

    def run(self, *args, **kwargs):
        """Provide a Rose-friendly interface to subprocess.Popen.

        Return rc, out, err.

        If kwargs["stdin"] is a str, communicate it to the command via a pipe.

        """
        p = self.run_bg(*args, **kwargs)
        stdin = None
        if isinstance(kwargs.get("stdin"), str):
            stdin = kwargs.get("stdin")
        stdout, stderr = p.communicate(stdin)
        return p.wait(), stdout, stderr

    def run_bg(self, *args, **kwargs):
        """Provide a Rose-friendly interface to subprocess.Popen.

        Return a subprocess.Popen object.

        If kwargs["stdin"] is a str, turn it into subprocess.PIPE.
        However, it cannot communicate stdin to the Popen object,
        because the Popen.communicate() method implies a wait().

        """
        for key in ["stdout", "stderr"]:
            if kwargs.get(key) is None:
                kwargs[key] = PIPE
        stdin = kwargs.get("stdin")
        if isinstance(stdin, str):
            kwargs["stdin"] = PIPE
        self.handle_event(RosePopenEvent(args, stdin))
        sys.stdout.flush()
        try:
            if kwargs.get("shell"):
                p = Popen(args[0], **kwargs)
            else:
                p = Popen(args, **kwargs)
        except OSError as e:
            raise RosePopenError(args, 1, "", str(e))
        return p

    def run_ok(self, *args, **kwargs):
        """Same as RosePopener.run, but raise RosePopenError if rc != 1.

        Return out, err.

        """
        stdin = kwargs.get("stdin")
        rc, stdout, stderr = self.run(*args, **kwargs)
        if rc:
            raise RosePopenError(args, rc, stdout, stderr, kwargs.get("stdin"))
        return stdout, stderr

    __call__ = run_ok
