# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------
"""Provide a common environment for a task in a cycling suite."""

from rose.env import EnvExportEvent
from rose.opt_parse import RoseOptionParser
from rose.reporter import Reporter
from rose.suite_engine_proc import SuiteEngineProcessor
import sys


def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("cycle", "cycle_offsets",
                              "prefix_delim", "suffix_delim")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness - 1)
    suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=report)
    kwargs = {}
    for k, v in vars(opts).items():
        kwargs[k] = v
    if opts.debug_mode:
        task_props = suite_engine_proc.get_task_props(*args, **kwargs)
    else:
        try:
            task_props = suite_engine_proc.get_task_props(*args, **kwargs)
        except Exception as e:
            report(e)
            sys.exit(1)
    for k, v in task_props:
        report(str(EnvExportEvent(k, v)) + "\n", level=0)


if __name__ == "__main__":
    main()
