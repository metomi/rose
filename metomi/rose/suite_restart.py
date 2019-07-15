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
"""Implement "rose suite-restart-only"."""

import os
import sys
import traceback

from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Reporter
from metomi.rose.suite_control import get_suite_name, SuiteNotFoundError
from metomi.rose.suite_engine_proc import SuiteEngineProcessor


class SuiteRestarter(object):

    """Wrap "cylc restart"."""

    def __init__(self, event_handler=None):
        self.event_handler = event_handler
        self.suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=self.event_handler)

    def handle_event(self, *args, **kwargs):
        """Handle event."""
        if callable(self.event_handler):
            self.event_handler(*args, **kwargs)

    def restart(self, suite_name=None, host=None, args=None):
        """Restart a "cylc" suite."""
        # Check suite engine specific compatibility
        self.suite_engine_proc.check_global_conf_compat()

        if not suite_name:
            suite_name = get_suite_name(self.event_handler)

        suite_dir = self.suite_engine_proc.get_suite_dir(suite_name)
        if not os.path.exists(suite_dir):
            raise SuiteNotFoundError(suite_dir)

        # Ensure suite is not running
        self.suite_engine_proc.check_suite_not_running(suite_name)

        # Restart the suite
        self.suite_engine_proc.run(suite_name, host, "restart", args)

        return


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("host", "name")
    opts, args = opt_parser.parse_args(sys.argv[1:])
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_restarter = SuiteRestarter(event_handler)
    try:
        sys.exit(suite_restarter.restart(
            suite_name=opts.name,
            host=opts.host,
            args=args))
    except Exception as exc:
        event_handler(exc)
        if opts.debug_mode:
            traceback.print_exc()
        if isinstance(exc, RosePopenError):
            sys.exit(exc.ret_code)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
