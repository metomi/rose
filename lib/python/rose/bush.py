# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
"""Web service for browsing users' Rose suite logs via an HTTP interface."""

import cherrypy
from fnmatch import fnmatch
from glob import glob
import jinja2
import math
import mimetypes
import os
import re
import pwd
import shlex
import simplejson
import rose.config
from rose.host_select import HostSelector
from rose.resource import ResourceLocator
from rose.bush_dao import RoseBushDAO
import tarfile
from tempfile import NamedTemporaryFile
from time import gmtime, strftime
import traceback
import urllib.request, urllib.parse, urllib.error

cherrypy.config.update({'environment': 'production'})

class RoseBushService(object):

    """Rose Bush Service."""

    NS = "rose"
    UTIL = "bush"
    TITLE = "Rose Bush"

    CYCLES_PER_PAGE = 100
    JOBS_PER_PAGE = 15
    JOBS_PER_PAGE_MAX = 300
    MIME_TEXT_PLAIN = "text/plain"
    REC_URL = re.compile(r"((https?):\/\/[^\s\(\)&\[\]\{\}]+)")
    SEARCH_MODE_REGEX = "REGEX"
    SEARCH_MODE_TEXT = "TEXT"
    SUITES_PER_PAGE = 100
    VIEW_SIZE_MAX = 10 * 1024 * 1024  # 10MB

    def __init__(self, *args, **kwargs):
        cherrypy.log("bush.init()")
        self.exposed = True
        self.bush_dao = RoseBushDAO()
        rose_conf = ResourceLocator.default().get_conf()
        self.logo = rose_conf.get_value(["rose-bush", "logo"])
        self.title = rose_conf.get_value(["rose-bush", "title"], self.TITLE)
        self.host_name = rose_conf.get_value(["rose-bush", "host"])
        if self.host_name is None:
            self.host_name = HostSelector().get_local_host()
            if self.host_name and "." in self.host_name:
                self.host_name = self.host_name.split(".", 1)[0]
        self.rose_version = ResourceLocator.default().get_version()
        template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(
            ResourceLocator.default().get_util_home(
                "lib", "html", "template", "rose-bush")))
        template_env.filters['urlise'] = self.url2hyperlink
        self.template_env = template_env

    @classmethod
    def url2hyperlink(cls, text):
        """Turn http or https link into a hyperlink."""
        cherrypy.log("bush.url2hyperlink()")
        return cls.REC_URL.sub(r'<a href="\g<1>">\g<1></a>', text)

    @cherrypy.expose
    def index(self, form=None):
        """Display a page to input user ID and suite ID."""
        cherrypy.log("bush.index()")
        data = {
            "logo": self.logo,
            "title": self.title,
            "host": self.host_name,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
        }
        if form == "json":
            return simplejson.dumps(data)
        try:
            return self.template_env.get_template("index.html").render(**data)
        except jinja2.TemplateError:
            traceback.print_exc()

    @cherrypy.expose
    def broadcast_states(self, user, suite, form=None):
        """List current broadcasts of a running or completed suite."""
        cherrypy.log("bush.broadcast_states()")
        data = {
            "logo": self.logo,
            "title": self.title,
            "host": self.host_name,
            "user": user,
            "suite": suite,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
            "method": "broadcast_states",
            "states": {},
            "time": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
        }
        data["states"].update(
            self.bush_dao.get_suite_state_summary(user, suite))
        data["states"]["last_activity_time"] = (
            self.get_last_activity_time(user, suite))
        data.update(self._get_suite_logs_info(user, suite))
        data["broadcast_states"] = (
            self.bush_dao.get_suite_broadcast_states(user, suite))
        if form == "json":
            return simplejson.dumps(data)
        try:
            return self.template_env.get_template(
                "broadcast-states.html").render(**data)
        except jinja2.TemplateError:
            traceback.print_exc()
        return simplejson.dumps(data)

    @cherrypy.expose
    def broadcast_events(self, user, suite, form=None):
        """List broadcasts history of a running or completed suite."""
        cherrypy.log("bush.broadcast_events()")
        data = {
            "logo": self.logo,
            "title": self.title,
            "host": self.host_name,
            "user": user,
            "suite": suite,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
            "method": "broadcast_events",
            "states": {},
            "time": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
        }
        data["states"].update(
            self.bush_dao.get_suite_state_summary(user, suite))
        data.update(self._get_suite_logs_info(user, suite))
        data["broadcast_events"] = (
            self.bush_dao.get_suite_broadcast_events(user, suite))
        if form == "json":
            return simplejson.dumps(data)
        try:
            return self.template_env.get_template(
                "broadcast-events.html").render(**data)
        except jinja2.TemplateError:
            traceback.print_exc()
        return simplejson.dumps(data)

    @cherrypy.expose
    def cycles(
            self, user, suite, page=1, order=None, per_page=None,
            no_fuzzy_time="0", form=None):
        """List cycles of a running or completed suite."""
        cherrypy.log("bush.cycles()")
        conf = ResourceLocator.default().get_conf()
        per_page_default = int(conf.get_value(
            ["rose-bush", "cycles-per-page"], self.CYCLES_PER_PAGE))
        if not isinstance(per_page, int):
            if per_page:
                per_page = int(per_page)
            else:
                per_page = per_page_default
        if page and per_page:
            page = int(page)
        else:
            page = 1
        data = {
            "logo": self.logo,
            "title": self.title,
            "host": self.host_name,
            "user": user,
            "suite": suite,
            "is_option_on": (
                order is not None and order != "time_desc" or
                per_page is not None and per_page != per_page_default
            ),
            "order": order,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
            "method": "cycles",
            "no_fuzzy_time": no_fuzzy_time,
            "states": {},
            "per_page": per_page,
            "per_page_default": per_page_default,
            "page": page,
            "task_status_groups": self.bush_dao.TASK_STATUS_GROUPS,
        }
        data["entries"], data["of_n_entries"] = (
            self.bush_dao.get_suite_cycles_summary(
                user, suite, order, per_page, (page - 1) * per_page))
        if per_page:
            data["n_pages"] = math.ceil(data["of_n_entries"] / per_page)
            if data["of_n_entries"] % per_page != 0:
                data["n_pages"] += 1
        else:
            data["n_pages"] = 1
        data.update(self._get_suite_logs_info(user, suite))
        data["states"].update(
            self.bush_dao.get_suite_state_summary(user, suite))
        data["states"]["last_activity_time"] = (
            self.get_last_activity_time(user, suite))
        data["time"] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        try:
            return self.template_env.get_template("cycles.html").render(**data)
        except jinja2.TemplateError:
            traceback.print_exc()
        return simplejson.dumps(data)

    @cherrypy.expose
    def taskjobs(
            self, user, suite, page=1, cycles=None, tasks=None,
            task_status=None, job_status=None,
            order=None, per_page=None, no_fuzzy_time="0", form=None):
        """List task jobs.

        user -- A string containing a valid user ID
        suite -- A string containing a valid suite ID
        page -- The page number to display
        cycles -- Display only task jobs matching these cycles. A value in the
                  list can be a cycle, the string "before|after CYCLE", or a
                  glob to match cycles.
        tasks -- Display only jobs for task names matching a list of names.
                 The list should be specified as a string which will be
                 shlex.split by this method. Values can be a valid task name or
                 a glob like pattern for matching valid task names.
        task_status -- Select by task statuses.
        job_status -- Select by job status. See RoseBushDAO.JOB_STATUS_COMBOS
                      for detail.
        order -- Order search in a predetermined way. A valid value is one of
            "time_desc", "time_asc",
            "cycle_desc_name_desc", "cycle_desc_name_asc",
            "cycle_asc_name_desc", "cycle_asc_name_asc",
            "name_asc_cycle_asc", "name_desc_cycle_asc",
            "name_asc_cycle_desc", "name_desc_cycle_desc",
            "time_submit_desc", "time_submit_asc",
            "time_run_desc", "time_run_asc",
            "time_run_exit_desc", "time_run_exit_asc",
            "duration_queue_desc", "duration_queue_asc",
            "duration_run_desc", "duration_run_asc",
            "duration_queue_run_desc", "duration_queue_run_asc"
        per_page -- Number of entries to display per page (defualt=32)
        no_fuzzy_time -- Don't display fuzzy time if this is True.
        form -- Specify return format. If None, display HTML page. If "json",
                return a JSON data structure.

        """
        cherrypy.log("bush.taskjobs()")
        conf = ResourceLocator.default().get_conf()
        per_page_default = int(conf.get_value(
            ["rose-bush", "jobs-per-page"], self.JOBS_PER_PAGE))
        per_page_max = int(conf.get_value(
            ["rose-bush", "jobs-per-page-max"], self.JOBS_PER_PAGE_MAX))
        if not isinstance(per_page, int):
            if per_page:
                per_page = int(per_page)
            else:
                per_page = per_page_default
        is_option_on = (
            cycles or
            tasks or
            task_status or
            job_status or
            order is not None and order != "time_desc" or
            per_page != per_page_default
        )
        if page and per_page:
            page = int(page)
        else:
            page = 1
        task_statuses = (
            [[item, ""] for item in self.bush_dao.TASK_STATUSES])
        if task_status:
            if not isinstance(task_status, list):
                task_status = [task_status]
        for item in task_statuses:
            if not task_status or item[0] in task_status:
                item[1] = "1"
        all_task_statuses = all([status[1] == "1" for status in task_statuses])
        if all_task_statuses:
            task_status = []
        data = {
            "cycles": cycles,
            "host": self.host_name,
            "is_option_on": is_option_on,
            "logo": self.logo,
            "method": "taskjobs",
            "no_fuzzy_time": no_fuzzy_time,
            "all_task_statuses": all_task_statuses,
            "task_statuses": task_statuses,
            "job_status": job_status,
            "order": order,
            "page": page,
            "per_page": per_page,
            "per_page_default": per_page_default,
            "per_page_max": per_page_max,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
            "states": {},
            "suite": suite,
            "tasks": tasks,
            "task_status_groups": self.bush_dao.TASK_STATUS_GROUPS,
            "title": self.title,
            "user": user,
        }
        if cycles:
            cycles = shlex.split(str(cycles))
        if tasks:
            tasks = shlex.split(str(tasks))
        data.update(self._get_suite_logs_info(user, suite))
        data["states"].update(
            self.bush_dao.get_suite_state_summary(user, suite))
        data["states"]["last_activity_time"] = (
            self.get_last_activity_time(user, suite))
        entries, of_n_entries = self.bush_dao.get_suite_job_entries(
            user, suite, cycles, tasks, task_status, job_status, order,
            per_page, (page - 1) * per_page)
        data["entries"] = entries
        data["of_n_entries"] = of_n_entries
        if per_page:
            data["n_pages"] = math.ceil(of_n_entries / per_page)
            if of_n_entries % per_page != 0:
                data["n_pages"] += 1
        else:
            data["n_pages"] = 1
        data["time"] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        try:
            return self.template_env.get_template("taskjobs.html").render(
                **data)
        except jinja2.TemplateError:
            traceback.print_exc()

    @cherrypy.expose
    def jobs(self, user, suite, page=1, cycles=None, tasks=None,
             no_status=None, order=None, per_page=None, no_fuzzy_time="0",
             form=None):
        """(Deprecated) Redirect to self.taskjobs.

        Convert "no_status" to "task_status" argument of self.taskjobs.
        """
        cherrypy.log("bush.jobs()")
        task_status = None
        if no_status:
            task_status = []
            if not isinstance(no_status, list):
                no_status = [no_status]
            for key, values in list(self.bush_dao.TASK_STATUS_GROUPS.items()):
                if key not in no_status:
                    task_status += values
        return self.taskjobs(
            user, suite, page, cycles, tasks, task_status,
            None, order, per_page, no_fuzzy_time, form)

    @cherrypy.expose
    def suites(self, user, names=None, page=1, order=None, per_page=None,
               no_fuzzy_time="0", form=None):
        """List (installed) suites of a user.

        user -- A string containing a valid user ID
        form -- Specify return format. If None, display HTML page. If "json",
                return a JSON data structure.

        """
        cherrypy.log("bush.suites()")
        user_suite_dir_root = self._get_user_suite_dir_root(user)
        conf = ResourceLocator.default().get_conf()
        per_page_default = int(conf.get_value(
            ["rose-bush", "suites-per-page"], self.SUITES_PER_PAGE))
        if not isinstance(per_page, int):
            if per_page:
                per_page = int(per_page)
            else:
                per_page = per_page_default
        if page and per_page:
            page = int(page)
        else:
            page = 1
        data = {
            "logo": self.logo,
            "title": self.title,
            "host": self.host_name,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
            "method": "suites",
            "no_fuzzy_time": no_fuzzy_time,
            "user": user,
            "is_option_on": (
                names and shlex.split(str(names)) != ["*"] or
                order is not None and order != "time_desc" or
                per_page is not None and per_page != per_page_default
            ),
            "names": names,
            "page": page,
            "order": order,
            "per_page": per_page,
            "per_page_default": per_page_default,
            "entries": [],
        }
        name_globs = ["*"]
        if names:
            name_globs = shlex.split(str(names))
        # Get entries
        sub_names = [
            ".service", "log", "share", "work", self.bush_dao.SUITE_CONF]
        for dirpath, dnames, fnames in os.walk(
                user_suite_dir_root, followlinks=True):
            if dirpath != user_suite_dir_root and (
                    any(name in dnames or name in fnames
                        for name in sub_names)):
                dnames[:] = []
            else:
                continue
            item = os.path.relpath(dirpath, user_suite_dir_root)
            if not any(fnmatch(item, glob_) for glob_ in name_globs):
                continue
            try:
                data["entries"].append({
                    "name": item,
                    "info": {},
                    "last_activity_time": (
                        self.get_last_activity_time(user, item))})
            except OSError:
                continue

        try:
            if order == "name_asc":
                data["entries"].sort(key=lambda entry: entry["name"])
            elif order == "name_desc":
                data["entries"].sort(key=lambda entry: entry["name"],
                    reverse=True)
            elif order == "time_asc":
                data["entries"].sort(key=lambda x: x["name"], reverse=True)
                data["entries"].sort(key=lambda x: x.get("last_activity_time"),
                    reverse=True)
            else:  # order == "time_desc"
                data["entries"].sort(key=lambda x: x["name"])
                data["entries"].sort(key=lambda x: x.get("last_activity_time"))
        except TypeError:
            # Empty entries create a NoneType vs str comparison
            pass

        data["of_n_entries"] = len(data["entries"])
        if per_page:
            data["n_pages"] = math.ceil(data["of_n_entries"] / per_page)
            if data["of_n_entries"] % per_page != 0:
                data["n_pages"] += 1
            offset = (page - 1) * per_page
            data["entries"] = data["entries"][offset:offset + per_page]
        else:
            data["n_pages"] = 1
        # Get suite info for each entry
        for entry in data["entries"]:
            user_suite_dir = os.path.join(user_suite_dir_root, entry["name"])
            rose_suite_info = os.path.join(user_suite_dir, "rose-suite.info")
            try:
                info_root = rose.config.load(rose_suite_info)
                for key, node in list(info_root.value.items()):
                    if (node.is_ignored() or
                            not isinstance(node.value, str)):
                        continue
                    entry["info"][key] = node.value
            except (IOError, rose.config.ConfigSyntaxError):
                pass
        data["time"] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        template = self.template_env.get_template("suites.html")
        return template.render(**data)

    def get_file(self, user, suite, path, path_in_tar=None, mode=None):
        """Returns file information / content or a cherrypy response."""
        cherrypy.log("bush.get_file()")
        f_name = self._get_user_suite_dir(user, suite, path)
        conf = ResourceLocator.default().get_conf()
        view_size_max = int(conf.get_value(
            ["rose-bush", "view-size-max"], self.VIEW_SIZE_MAX))
        if path_in_tar:
            tar_f = tarfile.open(f_name, "r:gz")
            try:
                tar_info = tar_f.getmember(path_in_tar)
            except KeyError:
                cherrypy.log.error("Unable to find " + path_in_tar +
                        "in tar file")
                raise cherrypy.HTTPError(404)
            f_size = tar_info.size
            handle = tar_f.extractfile(path_in_tar)
            if handle.read(2) == "#!":
                mime = self.MIME_TEXT_PLAIN
            else:
                mime = mimetypes.guess_type(
                    urllib.request.pathname2url(path_in_tar))[0]
            handle.seek(0)
            if (mode == "download" or
                    f_size > view_size_max or
                    mime and
                    (not mime.startswith("text/") or mime.endswith("html"))):
                temp_f = NamedTemporaryFile()
                f_bsize = os.fstatvfs(temp_f.fileno()).f_bsize
                while True:
                    bytes_ = handle.read(f_bsize)
                    if not bytes_:
                        break
                    temp_f.write(bytes_)
                cherrypy.response.headers["Content-Type"] = mime
                try:
                    return cherrypy.lib.static.serve_file(temp_f.name, mime)
                finally:
                    temp_f.close()
            text = handle.read()
        else:
            f_size = os.stat(f_name).st_size
            if open(f_name).read(2) == "#!":
                mime = self.MIME_TEXT_PLAIN
            else:
                mime = mimetypes.guess_type(urllib.request.pathname2url(f_name))[0]
            if not mime:
                mime = self.MIME_TEXT_PLAIN
            if (mode == "download" or
                    f_size > view_size_max or
                    mime and
                    (not mime.startswith("text/") or mime.endswith("html"))):
                cherrypy.response.headers["Content-Type"] = mime
                return cherrypy.lib.static.serve_file(f_name, mime)
            text = open(f_name).read()
        try:
            if mode in [None, "text"]:
                text = jinja2.escape(text)
            lines = [str(line) for line in text.splitlines()]
        except UnicodeDecodeError:
            if path_in_tar:
                handle.seek(0)
                # file closed by cherrypy
                return cherrypy.lib.static.serve_fileobj(
                    handle, self.MIME_TEXT_PLAIN)
            else:
                return cherrypy.lib.static.serve_file(
                    f_name, self.MIME_TEXT_PLAIN)
        else:
            if path_in_tar:
                handle.close()
        name = path
        if path_in_tar:
            name = "log/" + path_in_tar
        job_entry = None
        if name.startswith("log/job"):
            names = self.bush_dao.parse_job_log_rel_path(name)
            if len(names) == 4:
                cycle, task, submit_num, _ = names
                entries = self.bush_dao.get_suite_job_entries(
                    user, suite, [cycle], [task],
                    None, None, None, None, None)[0]
                for entry in entries:
                    if entry["submit_num"] == int(submit_num):
                        job_entry = entry
                        break
        if fnmatch(os.path.basename(path), "rose*.conf"):
            file_content = "rose-conf"
        else:
            file_content = self.bush_dao.is_conf(path)

        return lines, job_entry, file_content, f_name

    def get_last_activity_time(self, user, suite):
        """Returns last activity time for a suite based on database stat"""
        cherrypy.log("bush.get_last_activity_time()")
        for name in [os.path.join("log", "db"), "cylc-suite.db"]:
            fname = os.path.join(self._get_user_suite_dir(user, suite), name)
            try:
                return strftime(
                    "%Y-%m-%dT%H:%M:%SZ", gmtime(os.stat(fname).st_mtime))
            except OSError as e:
                cherrypy.log.error("bush.get_last_activity_time().error: "
                        + str(e))
                continue

    @cherrypy.expose
    def viewsearch(self, user, suite, path=None, path_in_tar=None, mode=None,
                   search_string=None, search_mode=None):
        """Search a text log file."""
        cherrypy.log("bush.viewsearch()")
        # get file or serve raw data
        file_output = self.get_file(
            user, suite, path, path_in_tar=path_in_tar, mode=mode)
        if isinstance(file_output, tuple):
            lines, _, file_content, _ = self.get_file(
                user, suite, path, path_in_tar=path_in_tar, mode=mode)
        else:
            return file_output

        template = self.template_env.get_template("view-search.html")

        if search_string:
            results = []
            line_numbers = []

            # perform search
            for i, line in enumerate(lines):
                if search_mode is None or search_mode == self.SEARCH_MODE_TEXT:
                    match = line.find(search_string)
                    if match == -1:
                        continue
                    start = match
                    end = start + len(search_string)
                elif search_mode == self.SEARCH_MODE_REGEX:
                    match = re.search(search_string, line)
                    if not match:
                        continue
                    start, end = match.span()
                else:
                    # ERROR: un-reccognised search_mode
                    break
                # if line matches search string include in results
                results.append([line[:start], line[start:end],
                                line[end:]])
                if mode in [None, "text"]:
                    line_numbers.append(i + 1)  # line numbers start from 1
            lines = results
        else:
            # no search is being performed, client is requesting the whole
            # page
            if mode in [None, "text"]:
                line_numbers = list(range(1, len(lines) + 1))
            else:
                line_numbers = []
            lines = [[line] for line in lines]

        return template.render(
            lines=lines,
            line_numbers=line_numbers,
            file_content=file_content
        )

    @cherrypy.expose
    def view(self, user, suite, path, path_in_tar=None, mode=None,
             no_fuzzy_time="0"):
        """View a text log file."""
        cherrypy.log("bush.view()")
        # get file or serve raw data
        file_output = self.get_file(
            user, suite, path, path_in_tar=path_in_tar, mode=mode)
        if isinstance(file_output, tuple):
            lines, job_entry, file_content, f_name = self.get_file(
                user, suite, path, path_in_tar=path_in_tar, mode=mode)
        else:
            return file_output

        template = self.template_env.get_template("view.html")

        data = {}
        data.update(self._get_suite_logs_info(user, suite))
        return template.render(
            rose_version=self.rose_version,
            script=cherrypy.request.script_name,
            method="view",
            time=strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
            logo=self.logo,
            title=self.title,
            host=self.host_name,
            user=user,
            suite=suite,
            path=path,
            path_in_tar=path_in_tar,
            f_name=f_name,
            mode=mode,
            no_fuzzy_time=no_fuzzy_time,
            file_content=file_content,
            lines=lines,
            entry=job_entry,
            task_status_groups=self.bush_dao.TASK_STATUS_GROUPS,
            **data)

    def _get_suite_logs_info(self, user, suite):
        """Return a dict with suite logs and Rosie suite info."""
        cherrypy.log("bush._get_suite_logs_info()")
        data = {"info": {}, "files": {}}
        user_suite_dir = self._get_user_suite_dir(user, suite)

        # rose-suite.info
        info_name = os.path.join(user_suite_dir, "rose-suite.info")
        if os.path.isfile(info_name):
            try:
                info_root = rose.config.load(info_name)
                for key, node in list(info_root.value.items()):
                    if node.is_ignored() or not isinstance(node.value, str):
                        continue
                    data["info"][key] = node.value
            except rose.config.ConfigSyntaxError:
                pass

        # rose-suite-run.conf, rose-suite-run.log, rose-suite-run.version
        data["files"]["rose"] = {}
        for key in ["conf", "log", "version"]:
            f_name = os.path.join(user_suite_dir, "log/rose-suite-run." + key)
            if os.path.isfile(f_name):
                stat = os.stat(f_name)
                data["files"]["rose"]["log/rose-suite-run." + key] = {
                    "path": "log/rose-suite-run." + key,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size}

        # Other recognised formats
        for key in ["html", "txt", "version"]:
            for f_name in glob(os.path.join(user_suite_dir, "log/*." + key)):
                if os.path.basename(f_name).startswith("rose-"):
                    continue
                name = os.path.join("log", os.path.basename(f_name))
                stat = os.stat(f_name)
                data["files"]["rose"]["other:" + name] = {
                    "path": name,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size}

        k, logs_info = self.bush_dao.get_suite_logs_info(user, suite)
        data["files"][k] = logs_info

        return data

    @classmethod
    def _check_dir_access(cls, path):
        """Check directory is accessible.

        Raise 404 if path does not exist, or 403 if path not accessible.

        Return path on success.

        """
        cherrypy.log("bush._check_dir_access()")
        if not os.path.exists(path):
            cherrypy.log.error(
                    "bush._check_dir_access: Path does not exist: " + path)
            raise cherrypy.HTTPError(404)
        if not os.access(path, os.R_OK):
            cherrypy.log.error(
                    "bush._check_dir_access: Path is not accessible: " + path)

            raise cherrypy.HTTPError(403)
        return path

    @staticmethod
    def _get_user_home(user):
        """Return, the path for a user cylc suite."""
        cherrypy.log("bush._get_user_home()")
        try:
            return pwd.getpwnam(user).pw_dir
        except KeyError:
            raise cherrypy.HTTPError(404)

    def _get_user_suite_dir_root(self, user):
        """Return /cylc-run/ for a cylc suite."""
        cherrypy.log("bush._get_user_suite_dir_root()")
        return self._check_dir_access(os.path.join(
            self._get_user_home(user),
            self.bush_dao.SUITE_DIR_REL_ROOT))

    def _get_user_suite_dir(self, user, suite, *paths):
        """Return, /cylc-run/suite/... for a cylc suite."""
        cherrypy.log("bush._get_user_suite_dir()")
        result = self._check_dir_access(os.path.join(
            self._get_user_home(user),
            self.bush_dao.SUITE_DIR_REL_ROOT,
            suite,
            *paths))
        return result


if __name__ == "__main__":
    from rose.ws import ws_cli
    ws_cli(RoseBushService)
else:
    from rose.ws import wsgi_app
    application = wsgi_app(RoseBushService)
