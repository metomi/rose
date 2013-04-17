# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
"""Implement the "rose suite-clean" command."""

import os
from rose.opt_parse import RoseOptionParser
from rose.reporter import Event, Reporter, ReporterContext
from rose.suite_engine_proc import SuiteEngineProcessor
import sys
import traceback


def main():
    """Implement the "rose suite-clean" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("non_interactive")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=report)
    if not args:
        args = [os.path.basename(os.getcwd())]
    os.chdir(os.path.expanduser('~'))
    n_done = 0
    for arg in args:
        if not opts.non_interactive:
            try:
                answer = raw_input("Clean %s? y/n (default n) " % arg)
            except EOFError:
                sys.exit(1)
            if answer not in ["Y", "y"]:
                continue
        try:
            suite_engine_proc.clean(arg)
        except Exception as e:
            if opts.debug_mode:
                traceback.print_exc(e)
            else:
                report(e)
        else:
            n_done += 1
    sys.exit(len(args) - n_done) # Return 0 if everything done


if __name__ == "__main__":
    main()
