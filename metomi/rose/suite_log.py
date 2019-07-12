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
"""Implement "rose suite-log" CLI."""

import os
import pwd
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Event, Reporter
from metomi.rose.suite_engine_proc import SuiteEngineProcessor
from metomi.rose.suite_control import get_suite_name
import sys
from time import sleep
import traceback


class RoseBushStartEvent(Event):

    """Event raised on "rose bush start"."""

    def __str__(self):
        return ("""Rose bush started:\n%s""" % self.args[0] +
                """Run "rose bush stop" when no longer required.""")


def main():
    """Implement "rose suite-log" CLI."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("archive_mode", "force_mode", "name",
                              "non_interactive", "prune_remote_mode",
                              "update_mode", "user", "view_mode")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)

    try:
        suite_log_view(opts, args, report)
    except Exception as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(1)


def suite_log_view(opts, args, event_handler=None):
    """Implement "rose suite-log" CLI functionality."""
    suite_engine_proc = SuiteEngineProcessor.get_processor(
        event_handler=event_handler)
    opts.update_mode = (
        opts.update_mode or opts.archive_mode or opts.force_mode)
    if opts.force_mode:
        args = ["*"]
    if not opts.name:
        opts.name = get_suite_name(event_handler)
        if not opts.update_mode and not opts.user:
            opts.user = pwd.getpwuid(os.stat(".").st_uid).pw_name
    if opts.archive_mode:
        suite_engine_proc.job_logs_archive(opts.name, args)
    elif opts.update_mode:
        suite_engine_proc.job_logs_pull_remote(
            opts.name, args, opts.prune_remote_mode, opts.force_mode)
    if opts.view_mode or not opts.update_mode:
        n_tries_left = 1
        is_rose_bush_started = False
        url = suite_engine_proc.get_suite_log_url(opts.user, opts.name)
        if url.startswith("file://"):
            if (opts.non_interactive or
                    input(
                        "Start rose bush? [y/n] (default=n) ") == "y"):
                suite_engine_proc.popen.run_bg(
                    "rose", "bush", "start", preexec_fn=os.setpgrp)
                is_rose_bush_started = True
                n_tries_left = 5  # Give the server a chance to start
        while n_tries_left:
            n_tries_left -= 1
            if n_tries_left:
                url = suite_engine_proc.get_suite_log_url(opts.user, opts.name)
                if url.startswith("file://"):
                    sleep(1)
                    continue
            suite_engine_proc.launch_suite_log_browser(opts.user, opts.name)
            break
        if is_rose_bush_started:
            status = suite_engine_proc.popen("rose", "bush")[0]
            event_handler(RoseBushStartEvent(status))
    return


if __name__ == "__main__":
    main()
