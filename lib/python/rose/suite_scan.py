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
"""Scan for running suites in suite hosts."""

from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import sys


class SuiteScanner(object):

    """Scan for running suites in suite hosts."""

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

    def scan(self, *hosts):
        """Scan for running suites (in hosts).

        Return (suite_scan_results, exceptions) where suite_scan_results is a
        list of rose.suite_engine_proc.SuiteScanResult instances and exceptions
        is a list of exceptions resulting from any failed scans

        """
        conf = ResourceLocator.default().get_conf()
        if not hosts:
            hosts = self.host_selector.expand(
                ["localhost"] +
                conf.get_value(["rose-suite-run", "hosts"], "").split() +
                conf.get_value(["rose-suite-run", "scan-hosts"], "").split()
            )[0]
        timeout = conf.get_value(["rose-suite-scan", "timeout"])
        if timeout:
            timeout = int(timeout)
        return self.suite_engine_proc.scan(set(hosts), timeout=timeout)

    __call__ = scan


def main():
    opt_parser = RoseOptionParser()
    opts, args = opt_parser.parse_args()
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_scanner = SuiteScanner(event_handler=event_handler)
    results, exceptions = SuiteScanner(event_handler=event_handler)(*args)
    ret = 1
    if results:
        ret = 0
        for result in results:
            suite_scanner.handle_event(result)
    if exceptions:
        ret = 2
        for exception in exceptions:
            event_handler(exception)
    sys.exit(ret)


if __name__ == "__main__":
    main()
