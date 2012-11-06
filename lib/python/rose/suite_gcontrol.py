# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
"""Launch suite engine's control GUI from the correct suite host."""

import os
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import sys


class SuiteRunningOnMultipleHostsEvent(Event):
    """A warning raised if a suite is running on multiple hosts."""

    TYPE = Event.TYPE_ERR

    def __str__(self):
        suite_name, hosts = self.args
        return "%s is running on multiple hosts: %s" % (suite_name,
                                                        ", ".join(hosts))


class SuiteControlGUILauncher(object):

    """Launch suite engine's control GUI from the correct suite host."""

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

    def launch(self, suite_name, host=None, *args):
        """Launch suite engine's control GUI."""
        if not host:
            # Try pinging for a running suite
            conf = ResourceLocator.default().get_conf()
            node = conf.get(["rose-suite-run", "hosts"], no_ignore=True)
            if node is not None:
                hosts = self.suite_engine_proc.ping(
                        suite_name,
                        self.host_selector.expand(node.value.split())[0])
                if hosts:
                    host = hosts[0]
                    if len(hosts) > 1:
                        self.handle_event(SuiteRunningOnMultipleHostsEvent(
                                suite_name, hosts))
        return self.suite_engine_proc.launch_gcontrol(suite_name, host, *args)

    __call__ = launch


def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("host")
    opts, args = opt_parser.parse_args()
    event_handler = Reporter(opts.verbosity - opts.quietness)
    if args:
        suite_name = args.pop()
    else:
        suite_name = os.path.basename(os.getcwd())
    launcher = SuiteControlGUILauncher(event_handler=event_handler)
    if opts.debug_mode:
        launcher(suite_name, opts.host, *args)
    else:
        try:
            launcher(suite_name, opts.host, *args)
        except Exception as e:
            event_handler(e)
            sys.exit(1)
        

if __name__ == "__main__":
    main()
