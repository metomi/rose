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

import json
import os
from rose.fs_util import FileSystemUtil
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter
from rose.suite_engine_proc import SuiteEngineProcessor
import shutil
import sys
import webbrowser

class LockEvent(Event):
    """An warning raised when the generator aborts due to a lock file."""

    TYPE = Event.TYPE_ERR

    def __str__(self):
        return str(self.args[0]) + ": lock exists, abort"


# TODO: should this be moved to rose.fs_util?
class FileInstallEvent(Event):
    """An event raised when files are installed."""

    LEVEL = Event.V

    def __init__(self, target, source):
        self.target = target
        self.source = source
        Event.__init__(self, target, source)

    def __str__(self):
        return "install: %s <= %s" % (self.target, self.source)


# TODO: should this be moved to rose.fs_util?
class FileUpdateEvent(Event):
    """An event raised when the content of a file is updated."""

    LEVEL = Event.V

    def __str__(self):
        return str(self.args[0]) + ": updated"


# TODO: should this be moved to rose.external?
class WebBrowserEvent(Event):
    """An event raised when a web browser is launched."""

    LEVEL = Event.V

    def __str__(self):
        return "%s %s" % self.args


class SuiteLogViewGenerator(object):
    """Generate the log view for a suite."""

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
        try:
            return method(suite_name, *args, **kwargs)
        finally:
            try:
                self.fs_util.chdir(cwd)
            except OSError:
                pass

    def generate(self, suite_name):
        """Generate the log view for a suite."""
        return self._chdir(self._generate, suite_name)

    __call__ = generate

    def _generate(self, suite_name):
        if not os.path.exists(self.suite_engine_proc.SUITE_LOG):
            return
        ns = "rose-suite-log-view"
        lock = os.path.join(os.getcwd(), "." + ns + ".lock")
        try:
            os.mkdir(lock)
        except OSError:
            self.handle_event(LockEvent(lock))
            return
        try:
            # Copy presentation files into the log directory
            html_lib_source = os.path.join(os.getenv("ROSE_HOME"), "lib",
                                           "html")
            html_lib_dest = "html-lib"
            if not os.path.isdir(html_lib_dest):
                external_html_lib_source = os.path.join(html_lib_source,
                                                        "external")
                shutil.copytree(external_html_lib_source, html_lib_dest,
                                ignore=shutil.ignore_patterns(".svn"))
                ev = FileInstallEvent(html_lib_dest, external_html_lib_source)
                self.handle_event(ev)
            this_html_lib_source = os.path.join(html_lib_source, ns)
            for name in os.listdir(this_html_lib_source):
                if not name.startswith(".") and not os.path.isfile(name):
                    source = os.path.join(this_html_lib_source, name)
                    shutil.copy2(source, ".")
                    self.handle_event(FileInstallEvent(name, source))
            # Parse the suite log
            suite_log_file = self.suite_engine_proc.SUITE_LOG
            suite_log_file_size_prev = None
            suite_log_file_size = os.stat(suite_log_file).st_size
            while suite_log_file_size != suite_log_file_size_prev:
                data = self.suite_engine_proc.process_suite_log()
                f = open("JOB.json", "w")
                json.dump(data, f, indent=0)
                f.close()
                self.handle_event(FileUpdateEvent("JOB.json"))
                suite_log_file_size_prev = suite_log_file_size
                suite_log_file_size = os.stat(suite_log_file).st_size
        finally:
            os.rmdir(lock)

    def update_task_log(self, suite_name, task_names=None):
        """Update the log(s) of tasks in suite_name.

        If "task_names" is None, update the logs for all tasks.

        """
        return self._chdir(self._update_task_log, suite_name, task_names)

    def _update_task_log(self, suite_name, task_names=None):
        users_and_hosts_and_tasks = []
        if task_names:
            for task_name in task_names:
                task_name_0 = task_name.split("%", 1)[0]
                user_and_host = self.suite_engine_proc.get_task_auth(
                        suite_name, task_name_0)
                if user_and_host is None:
                    continue
                user, host = user_and_host
                users_and_hosts_and_tasks.append((user, host, task_name))
        else:
            users_and_hosts = self.suite_engine_proc.get_tasks_auths(suite_name)
            for user, host in users_and_hosts:
                users_and_hosts_and_tasks.append((user, host, ""))

        log_dir_rel = self.suite_engine_proc.get_task_log_dir_rel(suite_name)
        log_dir = os.path.join(os.path.expanduser("~"), log_dir_rel)
        for user, host, task in users_and_hosts_and_tasks:
            r_log_dir = "%s@%s:%s/%s*" % (user, host, log_dir_rel, task)
            cmd = self.popen.get_cmd("rsync", r_log_dir, log_dir)
            try:
                out, err = self.popen(*cmd)
            except RosePopenError as e:
                self.handle_event(e, level=Reporter.WARN)


def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("full_mode", "web_browser_mode")
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
    if opts.full_mode:
        gen.update_task_log(suite_name)
    elif args:
        gen.update_task_log(suite_name, tasks=args)
    gen(suite_name)
    if os.getenv("DISPLAY") and opts.web_browser_mode:
        w = webbrowser.get()
        url = gen.suite_engine_proc.get_suite_log_url(suite_name)
        gen.handle_event(WebBrowserEvent(w.name, url))
        w.open_new_tab(url)


if __name__ == "__main__":
    main()
