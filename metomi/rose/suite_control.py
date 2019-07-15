# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
#
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
"""Launch suite engine's control commands."""

import os
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Reporter
from metomi.rose.suite_engine_proc import SuiteEngineProcessor
import sys


YES = "y"
PROMPT = "Really %s %s? [" + YES + " or n (default)] "


class SuiteControl(object):
    """Launch suite engine's control commands from the correct suite host."""

    def __init__(self, event_handler=None):
        self.event_handler = event_handler
        self.suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=event_handler)

    def shutdown(self, suite_name, confirm=None, stderr=None,
                 stdout=None, *args):
        """Shutdown the suite.

        suite_name: the name of the suite.
        confirm: If specified, must be a callable with the interface
                  b = confirm("shutdown", suite_name, host). This method will
                  only issue the shutdown command to suite_name at host if b is
                  True.
        stderr: A file handle for stderr, if relevant for suite engine.
        stdout: A file handle for stdout, if relevant for suite engine.
        args: extra arguments for the suite engine's shutdown command.

        """
        if confirm is None or confirm("shutdown", suite_name):
            self.suite_engine_proc.shutdown(suite_name, args, stderr, stdout)


class SuiteNotFoundError(Exception):

    """An exception raised when a suite can't be found at or below cwd."""
    def __str__(self):
        return ("%s - no suite found for this path." % self.args[0])


def get_suite_name(event_handler=None):
    """Find the top level of a suite directory structure"""
    fs_util = FileSystemUtil(event_handler)
    conf_dir = os.getcwd()
    while True:
        if os.path.basename(conf_dir) != "rose-stem":
            for tail in [
                    "rose-suite.conf",
                    "log/rose-suite-run.conf",
                    "rose-stem/rose-suite.conf"]:
                conf = os.path.join(conf_dir, tail)
                if os.path.exists(conf):
                    return os.path.basename(conf_dir)
        up_dir = fs_util.dirname(conf_dir)
        if up_dir == conf_dir:
            raise SuiteNotFoundError(os.getcwd())
        conf_dir = up_dir


def prompt(action, suite_name, host):
    """Prompt user to confirm action for suite_name at host."""
    if not host:
        host = "localhost"
    return input(PROMPT % (action, suite_name, host)).strip() in [YES]


def main():
    """Implement "rose suite-shutdown"."""
    argv = sys.argv[1:]
    method_name = argv.pop(0)
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("name", "non_interactive")
    opts, args = opt_parser.parse_args(argv)
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_control = SuiteControl(event_handler=event_handler)
    method = getattr(suite_control, method_name)
    confirm = None
    suite_names = []
    if not opts.non_interactive:
        confirm = prompt
    else:
        if opts.name:
            suite_names.append(opts.name)
        else:
            try:
                suite_name = get_suite_name(event_handler)
                suite_names.append(suite_name)
            except SuiteNotFoundError as exc:
                event_handler(exc)
                sys.exit(1)

    if opts.debug_mode:
        for sname in suite_names:
            method(sname, confirm, sys.stderr, sys.stdout, *args)
    else:
        for sname in suite_names:
            try:
                method(sname, confirm, sys.stderr, sys.stdout, *args)
            except Exception as exc:
                event_handler(exc)
                sys.exit(1)


if __name__ == "__main__":
    main()
