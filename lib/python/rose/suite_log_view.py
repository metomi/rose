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

import errno
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
from rose.suite_control import get_suite_name, SuiteNotFoundError
import shutil
import sys
from time import time, sleep
import webbrowser

class LockEvent(Event):
    """An warning raised when the generator aborts due to a lock file."""

    KIND = Event.KIND_ERR
    LEVEL = Event.V

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
    LOCK = "." + NS + ".lock"

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

    def generate(self, suite_name, task_ids=None, full_mode=False,
                 log_archive_threshold=None):
        """Generate the log view for a suite.

        suite_name -- The name of the suite.
        task_ids -- If specified, a list of relevant task IDs. If None or list
                    is empty, all tasks are relevant.
        full_mode -- A boolean to indicate whether a full update is required.
        log_archive_threshold -- Switch on job log archiving by specifying a
                                 cycle time threshold. All job logs at this
                                 cycle time or older will be archived. Implies
                                 full_mode.

        """
        # Update the log JSON dumps
        suite_log_dir = self.suite_engine_proc.get_suite_dir(suite_name, "log")
        cwd = os.getcwd()
        if suite_log_dir is not None:
            self.fs_util.chdir(suite_log_dir)
        try:
            lock = os.path.join(os.getcwd(), self.LOCK)
            try:
                os.mkdir(lock)
            except OSError:
                self.handle_event(LockEvent(lock))
                return
            finally:
                if task_ids:
                    for task_id in task_ids:
                        self.fs_util.touch(os.path.join(lock, task_id))
                elif full_mode or log_archive_threshold:
                    self.fs_util.touch(os.path.join(lock, "." + self.NS))
            while os.path.isdir(lock):
                try:
                    self._generate(suite_name, full_mode, log_archive_threshold)
                finally:
                    # FIXME: but what if a lock is left behind?
                    try:
                        os.rmdir(lock)
                    except OSError as e:
                        if e.errno != errno.ENOTEMPTY:
                            raise e
        finally:
            try:
                self.fs_util.chdir(cwd)
            except OSError:
                pass

    __call__ = generate

    def _generate(self, suite_name, full_mode=False,
                  log_archive_threshold=None):

        # Copy presentation files into the log directory
        html_lib_source = os.path.join(os.getenv("ROSE_HOME"), "lib", "html")
        html_lib_dest = "html-lib"
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

        # Remove view data files, where necessary
        archived_cycles = []
        if full_mode:
            for p in glob(self.NS + "*.json"):
                self.fs_util.delete(p)
        elif log_archive_threshold:
            for p in glob(self.NS + "-*.json"):
                cycle = p[len(self.NS) + 1:-len(".json")]
                arch = self.suite_engine_proc.get_cycle_log_archive_name(cycle)
                if cycle <= log_archive_threshold and not os.path.exists(arch):
                    archived_cycles.append(cycle)
                    self.fs_util.delete(p)
            self.suite_engine_proc.archive_job_logs(suite_name,
                                                    log_archive_threshold)
        # (Re-)Create view data file
        main_data_dump_path = self.NS + ".json"
        main_data = {"suite": suite_name,
                     "suite_info": {},
                     "cycle_times_current": [],
                     "cycle_times_archived": [],
                     "updated_at": None}
        if os.access(main_data_dump_path, os.F_OK | os.R_OK):
            main_data.update(json.load(open(main_data_dump_path)))
        else:
            suite_info_file_name = self.suite_engine_proc.get_suite_dir(
                    suite_name, "rose-suite.info")
            if os.access(suite_info_file_name, os.F_OK | os.R_OK):
                info_conf = ConfigLoader()(suite_info_file_name)
                for key, node in info_conf.value.items():
                    if not node.state:
                        main_data["suite_info"][key] = node.value
        suite_db_file = self.suite_engine_proc.get_suite_db_file(suite_name)
        if os.path.exists(suite_db_file):
            names = os.listdir(self.LOCK)
            has_done_nothing = True
            data = {}
            while names or has_done_nothing:
                task_ids = []
                for name in names:
                    if name != "." + self.NS:
                        task_ids.append(name)
                    self.fs_util.delete(os.path.join(self.LOCK, name))
                if task_ids or (full_mode and has_done_nothing):
                    self.suite_engine_proc.update_job_log(suite_name, task_ids)
                new_data = self.suite_engine_proc.get_suite_events(
                        suite_name,
                        task_ids=task_ids,
                        cycles=archived_cycles)
                for cycle, new_datum in new_data.items():
                    cycle_f_name = self.NS + "-" + cycle + ".json"
                    if cycle in data:
                        data[cycle]["tasks"].update(new_datum["tasks"])
                    elif os.access(cycle_f_name, os.F_OK | os.R_OK):
                        data[cycle] = json.load(open(cycle_f_name))
                        data[cycle]["tasks"].update(new_datum["tasks"])
                    else:
                        data[cycle] = new_datum
                names = os.listdir(self.LOCK)
                archived_cycles = []
                has_done_nothing = False
            for cycle, datum in data.items():
                cycle_f_name = self.NS + "-" + cycle + ".json"
                json.dump(datum, open(cycle_f_name, "wb"), indent=0)
                self.handle_event(FileSystemEvent("update", cycle_f_name))
        for name in glob(self.NS + "-*.json"):
            cycle = name[len(self.NS) + 1 : -len(".json")]
            p = self.suite_engine_proc.get_cycle_log_archive_name(cycle)
            if os.path.exists(p):
                add_key = "cycle_times_archived"
                del_key = "cycle_times_current"
            else:
                del_key = "cycle_times_archived"
                add_key = "cycle_times_current"
            if cycle not in main_data[add_key]:
                main_data[add_key].append(cycle)
            while cycle in main_data[del_key]:
                main_data[del_key].remove(cycle)
        for key in ["cycle_times_current", "cycle_times_archived"]:
            main_data[key].sort()
            main_data[key].reverse()
        main_data["updated_at"] = time()
        json.dump(main_data, open(main_data_dump_path, "wb"), indent=0)
        self.handle_event(FileSystemEvent("update", self.NS + ".json"))
        return

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
                              "name", "web_browser_mode")
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
    if opts.name:
        suite_name = opts.name
    else:
        suite_name = os.path.basename(os.getcwd())
        try:
            suite_name = get_suite_name(report)
        except SuiteNotFoundError as e:
            report(e)
            sys.exit(1)
    if args or opts.full_mode or opts.log_archive_threshold:
        gen(suite_name, args, opts.full_mode, opts.log_archive_threshold)
    if opts.web_browser_mode:
        return gen.view_suite_log_url(suite_name)
    else:
        return

if __name__ == "__main__":
    main()
