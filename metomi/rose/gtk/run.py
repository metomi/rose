# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
"""Miscellaneous gtk mini-applications."""

import multiprocessing
from subprocess import check_output

from metomi.rose.gtk.dialog import (
    DialogProcess,
    run_dialog,
    DIALOG_TYPE_WARNING,
)
from metomi.rose.opt_parse import RoseOptionParser

# from metomi.rose.suite_engine_procs.cylc import CylcProcessor
# from metomi.rose.suite_run import SuiteRunner
from metomi.rose.reporter import Reporter, ReporterContextQueue


def run_suite(*args):
    """Run "rose suite-run [args]" with a GTK dialog."""
    # Set up reporter
    queue = multiprocessing.Manager().Queue()
    verbosity = Reporter.VV
    out_ctx = ReporterContextQueue(Reporter.KIND_OUT, verbosity, queue=queue)
    err_ctx = ReporterContextQueue(Reporter.KIND_ERR, verbosity, queue=queue)
    event_handler = Reporter(
        contexts={"stdout": out_ctx, "stderr": err_ctx}, raise_on_exc=True
    )

    # Parse arguments
    suite_runner = SuiteRunner(event_handler=event_handler)

    # Don't use rose-suite run if Cylc Version is 8.*:
    if suite_runner.suite_engine_proc.get_version()[0] == "8":
        run_dialog(
            DIALOG_TYPE_WARNING,
            "`rose suite-run` does not work with Cylc 8 workflows: "
            "Use `cylc install`.",
            "Cylc Version == 8",
        )
        return None

    prog = "rose suite-run"
    description = prog
    if args:
        description += " " + suite_runner.popen.list_to_shell_str(args)
    opt_parse = RoseOptionParser(prog=prog)
    opt_parse.add_my_options(*suite_runner.OPTIONS)
    opts, args = opt_parse.parse_args(list(args))

    # Invoke the command with a GTK dialog
    dialog_process = DialogProcess(
        [suite_runner, opts, args],
        description=description,
        modal=False,
        event_queue=queue,
    )
    return dialog_process.run()
