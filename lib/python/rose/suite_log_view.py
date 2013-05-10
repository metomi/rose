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

from glob import glob
import json
import os
from rose.config import ConfigLoader
from rose.fs_util import FileSystemUtil, FileSystemEvent
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import shutil
import sys
from time import time, sleep
import webbrowser

class LockEvent(Event):
    """An warning raised when the generator aborts due to a lock file."""

    TYPE = Event.TYPE_ERR

    def __str__(self):
        return str(self.args[0]) + ": lock exists, abort"


# TODO: should this be moved to rose.external?
class WebBrowserEvent(Event):
    """An event raised when a web browser is launched."""

    LEVEL = Event.V

    def __init__(self, *args):
        Event.__init__(self, *args)
        self.browser, self.url = args

    def __str__(self):
        return "%s %s" % self.args


class SuiteLogViewGenerator(object):
    """Generate the log view for a suite."""

    NS = "rose-suite-log-view"
    MAX_ATTEMPTS = 5

    def __init__(self, event_handler=None, fs_util=None, popen=None,
                 suite_engine_proc=None):
        self.event_handler = event_handler
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler=event_handler)
        self.fs_util = fs_util
        if popen is None:
            popen = RosePopener(event_handler=event_handler)
        self.popen = popen
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                    event_handler=event_handler)
        self.suite_engine_proc = suite_engine_proc

    def get_suite_log_url(self, suite_name):
        """Return the log view URL of the suite.

        Return None if the URL does not exist.

        """
        return self.suite_engine_proc.get_suite_log_url(suite_name)

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def _chdir(self, method, suite_name, *args, **kwargs):
        """Ensure that current working directory is preserved."""
        suite_log_dir = self.suite_engine_proc.get_suite_dir(suite_name, "log")
        cwd = os.getcwd()
        if suite_log_dir is not None:
            self.fs_util.chdir(suite_log_dir)
        
        lock = os.path.join(os.getcwd(), "." + self.NS + ".lock")
        
        attempts = 0
        
        while attempts < self.MAX_ATTEMPTS:
            try:
                os.mkdir(lock)
                break
            except OSError:
                attempts += 1
                if attempts < self.MAX_ATTEMPTS:
                    sleep(1)
        if attempts == self.MAX_ATTEMPTS:
            self.handle_event(LockEvent(lock))
            return
        try:
            return method(suite_name, *args, **kwargs)
        finally:
            os.rmdir(lock)
            try:
                self.fs_util.chdir(cwd)
            except OSError:
                pass

    def generate(self, suite_name, full_mode=False,
                 log_archive_threshold=None):
        """Generate the log view for a suite.

        suite_name -- The name of the suite.
        full_mode -- A boolean to indicate whether a full update is required.
        log_archive_threshold -- Switch on job log archiving by specifying a
                                 cycle time threshold. All job logs at this
                                 cycle time or older will be archived. Implies
                                 full_mode.

        """
        return self._chdir(self._generate, suite_name, full_mode,
                           log_archive_threshold)

    __call__ = generate

    def _generate(self, suite_name, full_mode=False,
                  log_archive_threshold=None):
        # Copy presentation files into the log directory
        html_lib_source = os.path.join(os.getenv("ROSE_HOME"), "lib", "html")
        html_lib_dest = "html-lib"
        if log_archive_threshold:
            full_mode = True
        if full_mode:
            self.fs_util.delete(html_lib_dest)
        if not os.path.isdir(html_lib_dest):
            external_html_lib_source = os.path.join(html_lib_source,
                                                    "external")
            shutil.copytree(external_html_lib_source, html_lib_dest)
            self.handle_event(FileSystemEvent(FileSystemEvent.INSTALL,
                                              html_lib_dest,
                                              external_html_lib_source))
        this_html_lib_source = os.path.join(html_lib_source, self.NS)
        for name in os.listdir(this_html_lib_source):
            if name.startswith("."):
                continue
            if full_mode or not os.path.isfile(name):
                source = os.path.join(this_html_lib_source, name)
                shutil.copy2(source, ".")
                self.handle_event(FileSystemEvent(FileSystemEvent.INSTALL,
                                                  name, source))
                os.utime(name, None)
        # (Re-)Create view data file
        suite_info = {}
        suite_info_file_name = self.suite_engine_proc.get_suite_dir(
                suite_name, "rose-suite.info")
        if os.access(suite_info_file_name, os.F_OK | os.R_OK):
            info_conf = ConfigLoader()(suite_info_file_name)
            for key, node in info_conf.value.items():
                if not node.state:
                    suite_info[key] = node.value
        main_data = {"suite": suite_name,
                     "suite_info": suite_info,
                     "cycle_times": [],
                     "updated_at": time()}
        suite_db_file = self.suite_engine_proc.get_suite_db_file(suite_name)
        if os.path.exists(suite_db_file):
            prev_mtime = None
            if not full_mode and os.access(self.NS + ".json",
                                           os.F_OK | os.R_OK):
                prev_mtime = os.stat(self.NS + ".json").st_mtime
            this_mtime = os.stat(suite_db_file).st_mtime
            while prev_mtime is None or prev_mtime < this_mtime:
                cycles = self.suite_engine_proc.get_suite_events(
                        suite_name, log_archive_threshold)
                for cycle_time, data in cycles.items():
                    if cycle_time not in main_data["cycle_times"]:
                        main_data["cycle_times"].append(cycle_time)
                    f = open(self.NS + "-" + cycle_time + ".json", "wb")
                    json.dump(data, f, indent=0)
                    f.close()
                main_data["updated_at"] = time()
                prev_mtime = this_mtime
                this_mtime = os.stat(suite_db_file).st_mtime
        if not main_data["cycle_times"]:
            for name in glob(self.NS + "-*.json"):
                key = name[len(self.NS) + 1 : -len(".json")]
                if key != "latest":
                    main_data["cycle_times"].append(key)
        if main_data["cycle_times"]:
            main_data["cycle_times"].sort()
            main_data["cycle_times"].reverse()
            self.fs_util.symlink(
                    self.NS + "-" + main_data["cycle_times"][0] + ".json",
                    self.NS + "-latest.json")
        f = open(self.NS + ".json", "wb")
        json.dump(main_data, f, indent=0)
        f.close()
        self.handle_event(FileSystemEvent("update", self.NS + ".json"))
        return

    def update_job_log(self, suite_name, task_ids=None):
        """Update the log(s) of tasks in suite_name.

        If "task_ids" is None, update the logs for all tasks.

        """
        return self._chdir(self._update_job_log, suite_name, task_ids)

    def _update_job_log(self, suite_name, task_ids=None):
        return self.suite_engine_proc.update_job_log(suite_name, task_ids)

    def view_suite_log_url(self, suite_name):
        """Launch web browser to view suite log.

        Return URL of suite log on success, None otherwise.

        """
        if not os.getenv("DISPLAY"):
            return
        url = self.suite_engine_proc.get_suite_log_url(suite_name)
        if not url:
            return
        w = webbrowser.get()
        w.open(url, new=True, autoraise=True)
        self.handle_event(WebBrowserEvent(w.name, url))
        return url


def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("full_mode", "log_archive_threshold",
                              "web_browser_mode")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)

    if opts.debug_mode:
        suite_log_view(opts, args, report)
    else:
        try:
            suite_log_view(opts, args, report)
        except Exception as e:
            report(e)
            sys.exit(1)


def suite_log_view(opts, args, report=None):
    gen = SuiteLogViewGenerator(event_handler=report)
    if args:
        suite_name = args.pop(0)
    else:
        suite_name = os.path.basename(os.getcwd())
    if not opts.full_mode and args:
        gen.update_job_log(suite_name, tasks=args)
    gen(suite_name, opts.full_mode, opts.log_archive_threshold)
    if opts.web_browser_mode:
        return gen.view_suite_log_url(suite_name)
    else:
        return

if __name__ == "__main__":
    main()
