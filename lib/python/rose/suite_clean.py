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
from rose.config import ConfigLoader, ConfigNode
from rose.env import env_var_process
from rose.fs_util import FileSystemEvent
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.reporter import Event, Reporter, ReporterContext
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor, StillRunningError
import shlex
import sys
import traceback

class SuiteRunCleaner(object):

    """Logic to remove items created by the previous runs of suites."""

    def __init__(self, event_handler=None, host_selector=None,
                 suite_engine_proc=None):
        if event_handler is None:
            event_handler = Reporter()
        self.event_handler = event_handler
        if host_selector is None:
            host_selector = HostSelector(
                    event_handler=event_handler)
        self.host_selector = host_selector
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                    event_handler=event_handler)
        self.suite_engine_proc = suite_engine_proc

    def clean(self, suite_name):
        """Remove items created by the previous run of a suite.

        Change to user's $HOME for safety.

        """
        os.chdir(os.path.expanduser('~'))
        engine = self.suite_engine_proc

        # Ensure suite is not still running
        suite_dir_rel = engine.get_suite_dir_rel(suite_name)
        if not os.path.isdir(suite_dir_rel):
            return
        hostnames = ["localhost"]
        host_file_path = engine.get_suite_dir_rel(
                suite_name, "log", "rose-suite-run.host")
        if os.access(host_file_path, os.F_OK | os.R_OK):
            for line in open(host_file_path):
                hostnames.append(line.strip())
        conf = ResourceLocator.default().get_conf()
        hostnames = self.host_selector.expand(
              ["localhost"] +
              conf.get_value(["rose-suite-run", "hosts"], "").split() +
              conf.get_value(["rose-suite-run", "scan-hosts"], "").split())[0]
        hostnames = list(set(hostnames))
        hosts_str = conf.get_value(["rose-suite-run", "scan-hosts"])
        hosts = []
        for h in hostnames:
            if h not in hosts:
                hosts.append(h)
        reason = engine.is_suite_running(None, suite_name, hosts)
        if reason:
            raise StillRunningError(suite_name, reason)

        # Clean
        locs_file_path = engine.get_suite_dir(
                suite_name, "log", "rose-suite-run.locs")
        locs_conf = ConfigNode().set(["localhost"], {})
        if os.access(locs_file_path, os.F_OK | os.R_OK):
            locs_conf = ConfigLoader()(locs_file_path, locs_conf)
        for auth, node in locs_conf.value.items():
            locs = []
            for key in ["share", "work", ""]:
                conf_key = "root-dir"
                if key:
                    conf_key = "root-dir-" + key
                item_root = node.get_value([conf_key])
                if item_root:
                    loc_rel = engine.get_suite_dir_rel(suite_name)
                    if key:
                        loc_rel = os.path.join(loc_rel, key)
                    locs.append(os.path.join(item_root, loc_rel))
            if auth == "localhost":
                locs.append(engine.get_suite_dir(suite_name))
                for loc in locs:
                    loc = os.path.abspath(env_var_process(loc))
                    engine.fs_util.delete(loc)
            else:
                locs.append(engine.get_suite_dir_rel(suite_name))
                command = engine.popen.get_cmd(
                        "ssh", auth, "bash", "--login", "-c")
                rm_command = "rm -rf " + engine.popen.list_to_shell_str(locs)
                command += ["'" + rm_command + "'"]
                engine.popen(*command)
                for loc in locs:
                    ev = FileSystemEvent(FileSystemEvent.DELETE,
                                         auth + ":" + loc)
                    engine.handle_event(ev)

    __call__ = clean


def main():
    """Implement the "rose suite-clean" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("non_interactive")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    cleaner = SuiteRunCleaner(event_handler=report)
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
            cleaner.clean(arg)
        except Exception as e:
            report(e)
            if opts.debug_mode:
                traceback.print_exc(e)
        else:
            n_done += 1
    sys.exit(len(args) - n_done) # Return 0 if everything done


if __name__ == "__main__":
    main()
