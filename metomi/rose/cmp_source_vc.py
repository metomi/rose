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
"""Tool to determine whether source of an installed suite has changed."""

from difflib import unified_diff
import os
from io import StringIO
import sys
import traceback

from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Reporter
from metomi.rose.run_source_vc import write_source_vc_info
from metomi.rose.suite_engine_proc import SuiteEngineProcessor


class SuiteVCComparator(object):
    """Tool to determine whether source of an installed suite has changed."""

    def __init__(self, event_handler=None):
        self.event_handler = event_handler
        self.popen = RosePopener(self.event_handler)
        self.suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=self.event_handler, popen=self.popen)

    def cmp_source_vc_info(self, suite_name):
        """Compare source VC with installed "log/rose-suite-run.version".

        Return (list): Result in unified diff format or None if irrelevant.

        Args:
            suite_name (str): suite name.
        """
        rund = self.suite_engine_proc.get_suite_dir(suite_name)
        old_info_file_name = self.suite_engine_proc.get_suite_dir(
            suite_name, 'log', 'rose-suite-run.version')
        try:
            old_info = open(old_info_file_name).read().splitlines()
        except IOError:  # Cannot find/read version file
            return None
        else:
            if len(old_info) <= 1:  # No VC information
                return None
        handle = StringIO()
        write_source_vc_info(old_info[0], handle, self.popen)
        new_info = handle.getvalue().splitlines()
        return unified_diff(
            old_info, new_info,
            "installed @ %s" % rund, "latest @ %s" % old_info[0])

    def handle_event(self, *args, **kwargs):
        """Handle event."""
        if callable(self.event_handler):
            self.event_handler(*args, **kwargs)


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options('name')
    opts, args = opt_parser.parse_args(sys.argv[1:])
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_vc_cmp = SuiteVCComparator(event_handler)
    suite_name = opts.name
    if not suite_name and args:
        suite_name = args[0]
    if not suite_name:
        suite_name = os.getenv(suite_vc_cmp.suite_engine_proc.SUITE_NAME_ENV)
    if not suite_name:
        opt_parser.print_usage(sys.stderr)
        sys.exit(2)
    try:
        lines = suite_vc_cmp.cmp_source_vc_info(suite_name=suite_name)
    except Exception as exc:
        event_handler(exc)
        traceback.print_exc()
        sys.exit(2)
    else:
        if lines is None:
            event_handler(
                '%s: rose-suite-run.version: VC info not found' % (
                    suite_name),
                kind=Reporter.KIND_ERR, level=Reporter.FAIL)
            sys.exit(2)
        lines = list(line for line in lines)
        for line in lines:
            event_handler('%s\n' % line, prefix='')
        if lines:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
