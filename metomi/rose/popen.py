# Copyright (C) British Crown (Met Office) & Contributors.
# This file is part of Rose, a framework for meteorological suites.
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
# -----------------------------------------------------------------------------
"""Wraps Python's subprocess.Popen."""

import asyncio
import os
import re
import select
import shlex
from subprocess import PIPE, Popen
import sys
from typing import Iterable, List

from metomi.rose.reporter import Event
from metomi.rose.resource import ResourceLocator


class WorkflowFileNotFoundError(Exception):

    """Error: Workflow file not found.

    Expected error for fcm_make remote where the flow.cylc is
    not included in the file installation.
    """

    def __str__(self):
        return "No workflow file found."


class RosePopenError(Exception):

    """An error raised when a shell command call fails."""

    def __init__(self, command, ret_code, stdout, stderr, stdin=None):
        self.command = command
        self.ret_code = ret_code
        self.stdout = stdout
        self.stderr = stderr
        self.stdin = stdin
        Exception.__init__(self, command, ret_code, stdout, stderr)

    def __str__(self):
        cmd_str = str(RosePopenEvent(self.command, self.stdin))
        tail = ""
        if self.stderr:
            tail = ", stderr=\n%s" % self.stderr
        return "%s # return-code=%d%s" % (cmd_str, self.ret_code, tail)


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
            ret = RosePopener.shlex_join(self.command)

        try:
            # real file or real stream
            self.stdin.fileno()
            # ask select if it is readable (real files can hang)
            readable = bool(select.select([self.stdin], [], [], 0.0)[0])
        except (AttributeError, IOError, ValueError):
            # file like
            readable = True

        if self.stdin:
            if isinstance(self.stdin, str):
                # string
                stdin = self.stdin
            elif isinstance(self.stdin, bytes):
                # byte string
                stdin = self.stdin.decode()
            elif readable:
                # file like
                try:
                    pos = self.stdin.tell()
                    stdin = self.stdin.read()
                    self.stdin.seek(pos)
                    if not isinstance(stdin, str):
                        stdin = stdin.decode()
                except Exception:
                    # purposefully vague for safety (catch any exception)
                    stdin = ''
            else:
                stdin = ''

            if stdin:
                ret += f" <<'__STDIN__'\n{stdin}\n__STDIN__"

        return ret


class RosePopener:

    """Wrap Python's subprocess.Popen."""

    CMDS = {
        "diff_tool": ["diff", "-u"],
        "editor": ["vi"],
        "fs_browser": ["nautilus"],
        "gdiff_tool": ["gvimdiff"],
        "geditor": ["gedit"],
        "image_viewer": ["eog", "--new-instance"],
        "rsync": [
            "rsync",
            "-a",
            "--exclude=.*",
            "--timeout=1800",
            "--rsh=ssh -oBatchMode=yes -oConnectTimeout=10",
        ],
        "ssh": ["ssh", "-oBatchMode=yes", "-oConnectTimeout=10"],
        "terminal": ["xterm"],
    }
    ENVS_OF_CMDS = {"editor": ["VISUAL", "EDITOR"]}

    @staticmethod
    def shlex_join(args: Iterable[str]) -> str:
        """Convert a list of strings into a shell command, safely quoting
        when the strings contain whitespace and special chars.

        Basically a back-port of shlex.join(), needed for py 3.7.

        Examples:
        >>> RosePopener.shlex_join([])
        ''
        >>> RosePopener.shlex_join(["echo", "-n", "Multiple words"])
        "echo -n 'Multiple words'"
        >>> RosePopener.shlex_join(["ls", "my_dir;foiled_injection"])
        "ls 'my_dir;foiled_injection'"
        >>> RosePopener.shlex_join(["what", "about", "globs*"])
        "what about 'globs*'"
        """
        return " ".join(shlex.quote(arg) for arg in args)

    @staticmethod
    def list_to_shell_str(args: Iterable[str]) -> str:
        """Convert a list of strings into a shell command, escaping whitespace
        and quotes, but otherwise allowing special chars so user defined
        commands can run without sanitisation.

        Examples:
        >>> RosePopener.list_to_shell_str([])
        ''
        >>> _ = RosePopener.list_to_shell_str(["it's"])
        >>> print(_)
        it\\'s
        >>> _
        "it\\\\'s"
        >>> RosePopener.list_to_shell_str(["echo", "-n", "Multiple words"])
        'echo -n Multiple\\\\ words'
        >>> RosePopener.list_to_shell_str(["ls", "my_dir;allow_this"])
        'ls my_dir;allow_this'
        >>> RosePopener.list_to_shell_str(["what", "about", "globs*"])
        'what about globs*'
        """
        return " ".join(re.sub(r"([\"'\s])", r"\\\1", arg) for arg in args)

    def __init__(self, event_handler=None):
        self.event_handler = event_handler
        self.cmds = {}

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def get_cmd(self, key: str, *args: str) -> List[str]:
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
        if key not in self.cmds:
            root_node = ResourceLocator.default().get_conf()
            node = root_node.get(["external", key], no_ignore=True)
            if node is not None:
                self.cmds[key] = shlex.split(node.value)
        if key not in self.cmds:
            for name in self.ENVS_OF_CMDS.get(key, []):
                env_var = os.getenv(name)
                if env_var:  # not None, not null str
                    self.cmds[key] = shlex.split(env_var)
                    break
        if key not in self.cmds:
            self.cmds[key] = self.CMDS[key]
        return self.cmds[key] + list(args)

    def run(self, *args, **kwargs):
        """Provide a Rose-friendly interface to subprocess.Popen.

        Return ret_code, out, err.

        If kwargs["stdin"] is a str, communicate it to the command via a pipe.

        """
        proc = self.run_bg(*args, **kwargs)
        stdin = None
        if isinstance(kwargs.get("stdin"), str):
            stdin = kwargs.get("stdin")
        stdout, stderr = proc.communicate(stdin)
        retcode = proc.wait()

        return retcode, stdout, stderr

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
        elif stdin is None:
            kwargs["stdin"] = open(os.devnull)
        self.handle_event(RosePopenEvent(args, stdin))
        sys.stdout.flush()
        try:
            if kwargs.get("shell"):
                proc = Popen(args[0], text=True, **kwargs)
            else:
                proc = Popen(args, text=True, **kwargs)
        except OSError as exc:
            if exc.filename is None and args:
                exc.filename = args[0]
            raise RosePopenError(args, 1, "", str(exc))
        return proc

    def run_nohup_gui(self, cmd):
        """Launch+detach a GUI command with nohup.

        Launch the GUI command with `nohup bash -c 'exec ...'` redirecting
        standard input and outputs from and to `/dev/null`, and setting it to
        become a process group leader. Equivalent to a double fork.

        Arguments:
            cmd (str): command string of the GUI.

        Return (subprocess.Popen):
            Return the process object for the "nohup" command.
            Return None if no DISPLAY is set.
        """
        if 'DISPLAY' not in os.environ:
            return
        return self.run_bg(
            r'nohup',
            r'bash',
            r'-c',
            r'exec ' + cmd + r' <"/dev/null" >"/dev/null" 2>&1',
            preexec_fn=os.setpgrp,
            stdin=open(os.devnull),
            stdout=open(os.devnull, "wb"),
            stderr=open(os.devnull, "wb"),
        )

    def run_ok(self, *args, **kwargs):
        """Same as RosePopener.run, but raise RosePopenError if ret_code != 1.

        Return out, err.

        """
        ret_code, stdout, stderr = self.run(*args, **kwargs)
        if ret_code:
            raise RosePopenError(
                args, ret_code, stdout, stderr, kwargs.get("stdin")
            )
        return stdout, stderr

    def run_simple(self, *args, **kwargs):
        """Similar to RosePopener.run_ok, but event handle stdout and stderr.

        kwargs["stderr_level"] -- set event level of stderr
        kwargs["stdout_level"] -- set event level of stdout

        Return None.

        """
        stderr_level = kwargs.pop("stderr_level", None)
        stdout_level = kwargs.pop("stdout_level", None)
        ret_code, stdout, stderr = self.run(*args, **kwargs)
        if stdout:
            self.handle_event(stdout, level=stdout_level)
        if ret_code:
            raise RosePopenError(
                args, ret_code, stdout, stderr, kwargs.get("stdin")
            )
        if stderr:
            self.handle_event(stderr, level=stderr_level)

    @staticmethod
    def which(name):
        """Search an executable file name in PATH, and return its full path.

        If name is an absolute path and is an executable file, return name.
        If name is not found in PATH, return None.

        """
        if os.path.isabs(name) and os.access(name, os.F_OK | os.X_OK):
            return name
        for dir_ in os.getenv("PATH").split(os.pathsep):
            file_name = os.path.join(dir_, name)
            if os.access(file_name, os.F_OK | os.X_OK):
                return file_name

    async def run_bg_async(self, *args, **kwargs):
        """Provide a Rose-friendly interface to subprocess.Popen.

        Return a subprocess.Popen object.

        If kwargs["stdin"] is a str, turn it into subprocess.PIPE.
        However, it cannot communicate stdin to the Popen object,
        because the Popen.communicate() method implies a wait().

        """
        for key in ["stdout", "stderr"]:
            if kwargs.get(key) is None:
                kwargs[key] = asyncio.subprocess.PIPE
        stdin = kwargs.get("stdin")
        if isinstance(stdin, str):
            kwargs["stdin"] = asyncio.subprocess.PIPE
        elif stdin is None:
            kwargs["stdin"] = open(os.devnull)
        self.handle_event(RosePopenEvent(args, stdin))
        sys.stdout.flush()
        try:
            if kwargs.get("shell"):
                proc = Popen(args[0], **kwargs)
            else:
                command = ' '.join(map(shlex.quote, args))
                proc = await asyncio.create_subprocess_shell(command, **kwargs)
        except OSError as exc:
            if exc.filename is None and args:
                exc.filename = args[0]
            raise RosePopenError(args, 1, "", str(exc))
        return proc

    async def run_async(self, *args, **kwargs):
        """Provide a Rose-friendly interface to subprocess.Popen.

        Return ret_code, out, err.

        If kwargs["stdin"] is a str, communicate it to the command via a pipe.

        """
        proc = await self.run_bg_async(*args, **kwargs)
        stdin = None
        if isinstance(kwargs.get("stdin"), str):
            stdin = kwargs.get("stdin")
        stdout, stderr = await proc.communicate(stdin)
        await proc.wait()
        return proc.returncode, stdout, stderr

    async def run_ok_async(self, *args, **kwargs):
        ret_code, stdout, stderr = await self.run_async(*args, **kwargs)
        if ret_code:
            if stderr:
                stderr = stderr.decode()
            else:
                stderr = ''
            raise RosePopenError(
                args, ret_code, stdout, stderr, kwargs.get("stdin")
            )
        return stdout, stderr

    __call__ = run_ok
