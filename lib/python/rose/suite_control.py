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
"""Launch suite engine's control commands from the correct suite host."""

import os
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import sys


YES = "y"
PROMPT = "Really %s %s at %s? [" + YES + "/n] "


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

    def gcontrol(self, suite_name, host=None, callback=None, *args):
        """Launch suite engine's control GUI.

        suite_name: name of the suite.
        host: a host where the suite is running.
        args: extra arguments for the suite engine's gcontrol command.

        N.B. "callback" is not used. It is included so that this method can
        have the same interface as the "shutdown" method.

        """
        for host in self._get_hosts(suite_name, host):
            self.suite_engine_proc.gcontrol(suite_name, host, args)

    def shutdown(self, suite_name, host=None, callback=None, *args):
        """Shutdown the suite.

        suite_name: the name of the suite.
        host: a host where the suite is running.
        callback: If specified, must be a callable with the interface
                  b = callback("shutdown", suite_name, host). This method will
                  only issue the shutdown command to suite_name at host if b is
                  True.
        args: extra arguments for the suite engine's gcontrol command.

        """
        for host in self._get_hosts(suite_name, host):
            if callback is None or callback("shutdown", suite_name, host):
                self.suite_engine_proc.shutdown(suite_name, host, args)

    def _get_hosts(self, suite_name, host):
        if host:
            hosts = [host]
        else:
            conf = ResourceLocator.default().get_conf()
            node = conf.get(["rose-suite-run", "hosts"], no_ignore=True)
            host = None
            if node is not None:
                hosts = self.suite_engine_proc.ping(
                        suite_name,
                        self.host_selector.expand(node.value.split())[0])
            if not hosts:
                hosts = [None]
        return hosts


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
    opt_parser.add_my_options("host", "non_interactive")
    opts, args = opt_parser.parse_args(argv)
    event_handler = Reporter(opts.verbosity - opts.quietness)
    suite_control = SuiteControl(event_handler=event_handler)
    method = getattr(suite_control, method_name)
    callback = None
    if not opts.non_interactive:
        callback = prompt
    if args:
        suite_name = args.pop()
    else:
        suite_name = os.path.basename(os.getcwd())
    if opts.debug_mode:
        method(suite_name, opts.host, callback, *args)
    else:
        try:
            method(suite_name, opts.host, callback, *args)
        except Exception as e:
            event_handler(e)
            sys.exit(1)
        

if __name__ == "__main__":
    main()
