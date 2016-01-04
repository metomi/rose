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
"""Implement "rose suite-restart-only"."""

import os
import sys
import traceback

from rose.config import ConfigLoader, ConfigSyntaxError
from rose.config_processor import ConfigProcessorsManager
from rose.config_tree import ConfigTree
from rose.fs_util import FileSystemUtil
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Reporter
from rose.resource import ResourceLocator
from rose.suite_control import get_suite_name, SuiteNotFoundError
from rose.suite_engine_proc import SuiteEngineProcessor
from rose.suite_run import SuiteHostSelectEvent


class SuiteRestarter(object):

    """Wrap "cylc restart"."""

    def __init__(self, event_handler=None):
        self.event_handler = event_handler
        self.popen = RosePopener(self.event_handler)
        self.fs_util = FileSystemUtil(self.event_handler)
        self.config_pm = ConfigProcessorsManager(
            self.event_handler, self.popen, self.fs_util)
        self.host_selector = HostSelector(self.event_handler, self.popen)
        self.suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=self.event_handler,
            popen=self.popen,
            fs_util=self.fs_util)

    def handle_event(self, *args, **kwargs):
        """Handle event."""
        if callable(self.event_handler):
            self.event_handler(*args, **kwargs)

    def restart(
            self, suite_name=None, host=None, gcontrol_mode=None, args=None):
        """Restart a "cylc" suite."""
        # Check suite engine specific compatibility
        self.suite_engine_proc.check_global_conf_compat()

        if not suite_name:
            suite_name = get_suite_name(self.event_handler)

        suite_dir = self.suite_engine_proc.get_suite_dir(suite_name)
        if not os.path.exists(suite_dir):
            raise SuiteNotFoundError(suite_dir)

        # Ensure suite is not running
        hosts = []
        if host:
            hosts.append(host)
        self.suite_engine_proc.check_suite_not_running(suite_name, hosts)

        # Determine suite host to restart suite
        if host:
            hosts = [host]
        else:
            hosts = []
            val = ResourceLocator.default().get_conf().get_value(
                ["rose-suite-run", "hosts"], "localhost")
            known_hosts = self.host_selector.expand(val.split())[0]
            for known_host in known_hosts:
                if known_host not in hosts:
                    hosts.append(known_host)

        if hosts == ["localhost"]:
            host = hosts[0]
        else:
            host = self.host_selector(hosts)[0][0]
        self.handle_event(SuiteHostSelectEvent(suite_name, "restart", host))

        # Suite host environment
        run_conf_file_name = self.suite_engine_proc.get_suite_dir(
            suite_name, "log", "rose-suite-run.conf")
        try:
            run_conf = ConfigLoader().load(run_conf_file_name)
        except (ConfigSyntaxError, IOError):
            environ = None
        else:
            run_conf_tree = ConfigTree()
            run_conf_tree.node = run_conf
            environ = self.config_pm(run_conf_tree, "env")

        # Restart the suite
        self.suite_engine_proc.run(suite_name, host, environ, "restart", args)

        # Write suite host name to host file
        host_file_name = self.suite_engine_proc.get_suite_dir(
            suite_name, "log", "rose-suite-run.host")
        open(host_file_name, "w").write(host + "\n")

        # Launch the monitoring tool
        # Note: maybe use os.ttyname(sys.stdout.fileno())?
        if os.getenv("DISPLAY") and host and gcontrol_mode:
            self.suite_engine_proc.gcontrol(suite_name, host)

        return


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("gcontrol_mode", "host", "name")
    opts, args = opt_parser.parse_args(sys.argv[1:])
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_restarter = SuiteRestarter(event_handler)
    try:
        sys.exit(suite_restarter.restart(
            suite_name=opts.name,
            host=opts.host,
            gcontrol_mode=opts.gcontrol_mode,
            args=args))
    except Exception as exc:
        event_handler(exc)
        if opts.debug_mode:
            traceback.print_exc(exc)
        if isinstance(exc, RosePopenError):
            sys.exit(exc.rc)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
