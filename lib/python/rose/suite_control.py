# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
"""Launch suite engine's control commands from the correct suite host."""

import os
import rose.config
from rose.fs_util import FileSystemUtil
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Event, Reporter
from rose.suite_engine_proc import SuiteEngineProcessor
from rose.suite_scan import SuiteScanner
import sys


YES = "y"
PROMPT = "Really %s %s at %s? [" + YES + " or n (default)] "


class SuiteControl(object):
    """Launch suite engine's control commands from the correct suite host."""

    def __init__(self, event_handler=None, popen=None, suite_engine_proc=None,
                 host_selector=None):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                event_handler=event_handler, popen=popen)
        self.suite_engine_proc = suite_engine_proc
        if host_selector is None:
            host_selector = HostSelector(event_handler, popen)
        self.host_selector = host_selector

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler if it is callable."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def gcontrol(self, suite_name, host=None, confirm=None, stderr=None,
                 stdout=None, *args):
        """Launch suite engine's control GUI.

        suite_name: name of the suite.
        host: a host where the suite is running.
        args: extra arguments for the suite engine's gcontrol command.

        N.B. "confirm", "stderr" and "stdout" are not used. They are included
        so that this method can have the same interface as the "shutdown"
        method.

        """
        engine_version = self._get_engine_version(suite_name)
        for host in self._get_hosts(suite_name, host):
            self.suite_engine_proc.gcontrol(
                suite_name, host, engine_version, args)

    def shutdown(self, suite_name, host=None, confirm=None, stderr=None,
                 stdout=None, *args):
        """Shutdown the suite.

        suite_name: the name of the suite.
        host: a host where the suite is running.
        confirm: If specified, must be a callable with the interface
                  b = confirm("shutdown", suite_name, host). This method will
                  only issue the shutdown command to suite_name at host if b is
                  True.
        stderr: A file handle for stderr, if relevant for suite engine.
        stdout: A file handle for stdout, if relevant for suite engine.
        args: extra arguments for the suite engine's shutdown command.

        """
        engine_version = self._get_engine_version(suite_name)
        for host in self._get_hosts(suite_name, host):
            if confirm is None or confirm("shutdown", suite_name, host):
                self.suite_engine_proc.shutdown(
                    suite_name, host, engine_version, args, stderr, stdout)

    def _get_hosts(self, suite_name, host):
        if host:
            hosts = [host]
        else:
            hosts = self.suite_engine_proc.ping(suite_name)
            if not hosts:
                # Try the "rose-suite.host" file in the suite log directory
                log = self.suite_engine_proc.get_suite_dir(suite_name, "log")
                try:
                    host_file = os.path.join(log, "rose-suite-run.host")
                    hosts = [open(host_file).read().strip()]
                except IOError:
                    pass
            if not hosts:
                hosts = ["localhost"]
        return hosts

    def _get_engine_version(self, suite_name):
        conf_path = self.suite_engine_proc.get_suite_dir(
            suite_name, "log", "rose-suite-run.conf")
        if os.access(conf_path, os.F_OK | os.R_OK):
            conf = rose.config.load(conf_path)
            key = self.suite_engine_proc.get_version_env_name()
            return conf.get_value(["env", key])


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
    return raw_input(PROMPT % (action, suite_name, host)).strip() in [YES]


def main():
    """Implement "rose suite-gcontrol" and "rose suite-shutdown"."""
    argv = sys.argv[1:]
    method_name = argv.pop(0)
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("all", "host", "name", "non_interactive")
    opts, args = opt_parser.parse_args(argv)
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_control = SuiteControl(event_handler=event_handler)
    method = getattr(suite_control, method_name)
    confirm = None
    suite_names = []
    if not opts.non_interactive:
        confirm = prompt
    if opts.all:
        suite_scanner = SuiteScanner(event_handler=event_handler)
        results, exceptions = suite_scanner.scan()
        suite_names = [result.name for result in results]
    else:
        if opts.name:
            suite_names.append(opts.name)
        else:
            try:
                suite_name = get_suite_name(event_handler)
                suite_names.append(suite_name)
            except SuiteNotFoundError as e:
                event_handler(e)
                sys.exit(1)

    if opts.debug_mode:
        for sname in suite_names:
            method(sname, opts.host, confirm, sys.stderr, sys.stdout, *args)
    else:
        for sname in suite_names:
            try:
                method(sname, opts.host, confirm, sys.stderr, sys.stdout,
                       *args)
            except Exception as e:
                event_handler(e)
                sys.exit(1)


if __name__ == "__main__":
    main()
