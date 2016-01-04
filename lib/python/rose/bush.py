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
"""Web service for browsing users' Rose suite logs via an HTTP interface."""

import cherrypy
from fnmatch import fnmatch
from glob import glob
import jinja2
import mimetypes
import os
import pwd
import shlex
import simplejson
import socket
import rose.config
from rose.host_select import HostSelector
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import tarfile
from tempfile import NamedTemporaryFile
from time import gmtime, strftime
import traceback
import urllib


MIME_TEXT_PLAIN = "text/plain"


class RoseBushService(object):

    """Serves the index page."""

    NS = "rose"
    UTIL = "bush"
    TITLE = "Rose Bush"
    CYCLES_PER_PAGE = 100
    JOBS_PER_PAGE = 15
    JOBS_PER_PAGE_MAX = 300
    SUITES_PER_PAGE = 100
    VIEW_SIZE_MAX = 10 * 1024 * 1024  # 10MB

    def __init__(self, *args, **kwargs):
        self.exposed = True
        self.suite_engine_proc = SuiteEngineProcessor.get_processor()
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
        self.template_env = template_env

    @cherrypy.expose
    def index(self, form=None):
        """Display a page to input user ID and suite ID."""
        # TODO: some way to allow autocomplete of user field?
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
        except Exception as exc:
            traceback.print_exc(exc)

    @cherrypy.expose
    def broadcast_states(self, user, suite, form=None):
        """List current broadcasts of a running or completed suite."""
        user_suite_dir = self._get_user_suite_dir(user, suite)
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
            "time": strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime()),
        }
        data["states"].update(
            self.suite_engine_proc.get_suite_state_summary(user, suite))
        data.update(self._get_suite_logs_info(user, suite))
        data["broadcast_states"] = (
            self.suite_engine_proc.get_suite_broadcast_states(user, suite))
        if form == "json":
            return simplejson.dumps(data)
        try:
            template = self.template_env.get_template("broadcast-states.html")
            return template.render(**data)
        except Exception as exc:
            traceback.print_exc(exc)
        return simplejson.dumps(data)

    @cherrypy.expose
    def broadcast_events(self, user, suite, form=None):
        """List broadcasts history of a running or completed suite."""
        user_suite_dir = self._get_user_suite_dir(user, suite)
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
            "time": strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime())
        }
        data["states"].update(
            self.suite_engine_proc.get_suite_state_summary(user, suite))
        data.update(self._get_suite_logs_info(user, suite))
        data["broadcast_events"] = (
            self.suite_engine_proc.get_suite_broadcast_events(user, suite))
        if form == "json":
            return simplejson.dumps(data)
        try:
            template = self.template_env.get_template("broadcast-events.html")
            return template.render(**data)
        except Exception as exc:
            traceback.print_exc(exc)
        return simplejson.dumps(data)

    @cherrypy.expose
    def cycles(
            self, user, suite, page=1, order=None, per_page=None, form=None):
        """List cycles of a running or completed suite."""
        user_suite_dir = self._get_user_suite_dir(user, suite)
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
            "states": {},
            "per_page": per_page,
            "per_page_default": per_page_default,
            "page": page,
        }
        data["entries"], data["of_n_entries"] = (
            self.suite_engine_proc.get_suite_cycles_summary(
                user, suite, order, per_page, (page - 1) * per_page))
        if per_page:
            data["n_pages"] = data["of_n_entries"] / per_page
            if data["of_n_entries"] % per_page != 0:
                data["n_pages"] += 1
        else:
            data["n_pages"] = 1
        data.update(self._get_suite_logs_info(user, suite))
        data["states"].update(
            self.suite_engine_proc.get_suite_state_summary(user, suite))
        data["time"] = strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        try:
            template = self.template_env.get_template("cycles.html")
            return template.render(**data)
        except Exception as exc:
            traceback.print_exc(exc)
        return simplejson.dumps(data)

    @cherrypy.expose
    def jobs(self, user, suite, page=1, cycles=None, tasks=None,
             no_status=None, order=None, per_page=None, form=None):
        """List jobs of a running or completed suite.

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
        no_status -- Do not display jobs of tasks matching these statuses.
                     The values in the list should be "active", "success" or
                     "fail".
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
        form -- Specify return format. If None, display HTML page. If "json",
                return a JSON data structure.

        """
        user_suite_dir = self._get_user_suite_dir(user, suite)
        conf = ResourceLocator.default().get_conf()
        per_page_default = int(conf.get_value(
            ["rose-bush", "jobs-per-page"], self.JOBS_PER_PAGE))
        per_page_max = int(conf.get_value(
            ["rose-bush", "jobs-per-page-max"], self.JOBS_PER_PAGE_MAX))
        is_option_on = (
            cycles or
            tasks or
            no_status is not None or
            order is not None and order != "time_desc" or
            per_page is not None and per_page != per_page_default
        )
        if not isinstance(per_page, int):
            if per_page:
                per_page = int(per_page)
            else:
                per_page = per_page_default
        if page and per_page:
            page = int(page)
        else:
            page = 1
        no_statuses = no_status
        if no_status and not isinstance(no_status, list):
            no_statuses = [no_status]
        data = {
            "logo": self.logo,
            "title": self.title,
            "host": self.host_name,
            "user": user,
            "suite": suite,
            "cycles": cycles,
            "is_option_on": is_option_on,
            "tasks": tasks,
            "no_statuses": no_statuses,
            "order": order,
            "per_page": per_page,
            "per_page_default": per_page_default,
            "per_page_max": per_page_max,
            "page": page,
            "rose_version": self.rose_version,
            "script": cherrypy.request.script_name,
            "method": "jobs",
            "states": {},
        }
        # TODO: add paths to other suite files
        if cycles:
            cycles = shlex.split(str(cycles))
        if tasks:
            tasks = shlex.split(str(tasks))
        data.update(self._get_suite_logs_info(user, suite))
        data["states"].update(
            self.suite_engine_proc.get_suite_state_summary(user, suite))
        entries, of_n_entries = self.suite_engine_proc.get_suite_job_events(
            user, suite, cycles, tasks, no_statuses, order, per_page,
            (page - 1) * per_page)
        data["entries"] = entries
        data["of_n_entries"] = of_n_entries
        if per_page:
            data["n_pages"] = of_n_entries / per_page
            if of_n_entries % per_page != 0:
                data["n_pages"] += 1
        else:
            data["n_pages"] = 1
        data["time"] = strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        try:
            template = self.template_env.get_template("jobs.html")
            return template.render(**data)
        except Exception as exc:
            traceback.print_exc(exc)

    @cherrypy.expose
    def list(self, user, suite, page=1, cycles=None, tasks=None,
             no_status=None, order=None, per_page=None, form=None):
        return self.jobs(user, suite, page, cycles, tasks, no_status, order,
                         per_page, form)

    @cherrypy.expose
    def suites(self, user, names=None, page=1, order=None, per_page=None,
               form=None):
        """List (installed) suites of a user.

        user -- A string containing a valid user ID
        form -- Specify return format. If None, display HTML page. If "json",
                return a JSON data structure.

        """
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
        try:
            items = os.listdir(user_suite_dir_root)
        except OSError:
            items = []
        for item in items:
            if not any([fnmatch(item, glob_) for glob_ in name_globs]):
                continue
            user_suite_dir = os.path.join(user_suite_dir_root, item)
            suite_conf = os.path.join(
                user_suite_dir, self.suite_engine_proc.SUITE_CONF)
            job_logs_db = os.path.join(
                user_suite_dir, self.suite_engine_proc.JOB_LOGS_DB)
            if (not os.path.exists(job_logs_db) and
                    not os.path.exists(suite_conf)):
                continue
            suite_db = os.path.join(
                user_suite_dir, self.suite_engine_proc.SUITE_DB)
            try:
                last_activity_time = strftime(
                    "%Y-%m-%dT%H:%M:%S+0000",
                    gmtime(os.stat(suite_db).st_mtime))
            except OSError:
                last_activity_time = None
            data["entries"].append({
                "name": item,
                "info": {},
                "last_activity_time": last_activity_time})

        if order == "name_asc":
            data["entries"].sort(key=lambda entry: entry["name"])
        elif order == "name_desc":
            data["entries"].sort(key=lambda entry: entry["name"], reverse=True)
        elif order == "time_asc":
            data["entries"].sort(self._sort_summary_entries, reverse=True)
        else:  # order == "time_desc"
            data["entries"].sort(self._sort_summary_entries)
        data["of_n_entries"] = len(data["entries"])
        if per_page:
            data["n_pages"] = data["of_n_entries"] / per_page
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
                for key, node in info_root.value.items():
                    if (node.is_ignored() or
                            not isinstance(node.value, str)):
                        continue
                    entry["info"][key] = node.value
            except (IOError, rose.config.ConfigSyntaxError):
                pass
        data["time"] = strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        template = self.template_env.get_template("suites.html")
        return template.render(**data)

    @cherrypy.expose
    def summary(self, user, form=None):
        return self.suites(user, form)

    @cherrypy.expose
    def view(self, user, suite, path, path_in_tar=None, mode=None):
        """View a text log file."""
        f_name = self._get_user_suite_dir(user, suite, path)
        conf = ResourceLocator.default().get_conf()
        view_size_max = int(conf.get_value(
            ["rose-bush", "view-size-max"], self.VIEW_SIZE_MAX))
        if path_in_tar:
            tar_f = tarfile.open(f_name, 'r:gz')
            try:
                tar_info = tar_f.getmember(path_in_tar)
            except KeyError:
                raise cherrypy.HTTPError(404)
            f_size = tar_info.size
            f = tar_f.extractfile(path_in_tar)
            if f.read(2) == "#!":
                mime = MIME_TEXT_PLAIN
            else:
                mime = mimetypes.guess_type(
                    urllib.pathname2url(path_in_tar))[0]
            f.seek(0)
            if (mode == "download" or
                    f_size > view_size_max or
                    mime and
                    (not mime.startswith("text/") or mime.endswith("html"))):
                t = NamedTemporaryFile()
                f_bsize = os.fstatvfs(t.fileno()).f_bsize
                while True:
                    bytes = f.read(f_bsize)
                    if not bytes:
                        break
                    t.write(bytes)
                cherrypy.response.headers["Content-Type"] = mime
                try:
                    return cherrypy.lib.static.serve_file(t.name, mime)
                finally:
                    t.close()
            s = f.read()
            f.close()
        else:
            f_size = os.stat(f_name).st_size
            if open(f_name).read(2) == "#!":
                mime = MIME_TEXT_PLAIN
            else:
                mime = mimetypes.guess_type(urllib.pathname2url(f_name))[0]
            if (mode == "download" or
                    f_size > view_size_max or
                    mime and
                    (not mime.startswith("text/") or mime.endswith("html"))):
                cherrypy.response.headers["Content-Type"] = mime
                return cherrypy.lib.static.serve_file(f_name, mime)
            s = open(f_name).read()
        if mode == "text":
            s = jinja2.escape(s)
        try:
            lines = [unicode(line) for line in s.splitlines()]
        except UnicodeDecodeError:
            return cherrypy.lib.static.serve_file(f_name, MIME_TEXT_PLAIN)
        name = path
        if path_in_tar:
            name = path_in_tar
        job_entry = None
        if name.startswith("log/job/"):
            names = self.suite_engine_proc.parse_job_log_rel_path(name)
            if len(names) == 4:
                cycle, task, submit_num, ext = names
                entries = self.suite_engine_proc.get_suite_job_events(
                    user, suite, [cycle], [task], None, None, None, None)[0]
                for entry in entries:
                    if entry["submit_num"] == int(submit_num):
                        job_entry = entry
                        break
        if fnmatch(os.path.basename(path), "rose*.conf"):
            file_content = "rose-conf"
        else:
            file_content = self.suite_engine_proc.is_conf(path)
        template = self.template_env.get_template("view.html")
        data = {}
        data.update(self._get_suite_logs_info(user, suite))
        return template.render(
            rose_version=self.rose_version,
            script=cherrypy.request.script_name,
            method="view",
            time=strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime()),
            logo=self.logo,
            title=self.title,
            host=self.host_name,
            user=user,
            suite=suite,
            path=path,
            path_in_tar=path_in_tar,
            f_name=f_name,
            mode=mode,
            file_content=file_content,
            lines=lines,
            entry=job_entry,
            **data)

    def _get_suite_logs_info(self, user, suite):
        data = {"info": {}, "files": {}}
        user_suite_dir = self._get_user_suite_dir(user, suite)

        # rose-suite.info
        info_name = os.path.join(user_suite_dir, "rose-suite.info")
        if os.path.isfile(info_name):
            try:
                info_root = rose.config.load(info_name)
                for key, node in info_root.value.items():
                    if node.is_ignored() or not isinstance(node.value, str):
                        continue
                    data["info"][key] = node.value
            except rose.config.ConfigSyntaxError as err:
                pass

        # rose-suite-run.conf, rose-suite-run.log, rose-suite-run.version
        data["files"]["rose"] = {}
        for key in ["conf", "log", "version"]:
            f_name = os.path.join(user_suite_dir, "log/rose-suite-run." + key)
            if os.path.isfile(f_name):
                s = os.stat(f_name)
                data["files"]["rose"]["log/rose-suite-run." + key] = {
                    "path": "log/rose-suite-run." + key,
                    "mtime": s.st_mtime,
                    "size": s.st_size}

        # Other version files
        for f_name in glob(os.path.join(user_suite_dir, "log/*.version")):
            if os.path.basename(f_name).startswith("rose-"):
                continue
            name = os.path.join("log", os.path.basename(f_name))
            s = os.stat(f_name)
            data["files"]["rose"]["other:" + name] = {
                "path": name,
                "mtime": s.st_mtime,
                "size": s.st_size}

        k, logs_info = self.suite_engine_proc.get_suite_logs_info(user, suite)
        data["files"][k] = logs_info

        return data

    @classmethod
    def _check_dir_access(cls, path):
        """Check directory is accessible.

        Raise 404 if path does not exist, or 403 if path not accessible.

        Return path on success.

        """
        if not os.path.exists(path):
            raise cherrypy.HTTPError(404)
        if not os.access(path, os.R_OK):
            raise cherrypy.HTTPError(403)
        return path

    def _get_user_home(self, user):
        """Return, e.g. ~/cylc-run/ for a cylc suite.

        N.B. os.path.expanduser does not fail if ~user is invalid.

        """
        try:
            return pwd.getpwnam(user).pw_dir
        except KeyError:
            raise cherrypy.HTTPError(404)

    def _get_user_suite_dir_root(self, user):
        """Return, e.g. ~user/cylc-run/ for a cylc suite."""
        return self._check_dir_access(os.path.join(
            self._get_user_home(user),
            self.suite_engine_proc.SUITE_DIR_REL_ROOT))

    def _get_user_suite_dir(self, user, suite, *paths):
        """Return, e.g. ~user/cylc-run/suite/... for a cylc suite."""
        return self._check_dir_access(os.path.join(
            self._get_user_home(user),
            self.suite_engine_proc.SUITE_DIR_REL_ROOT,
            suite,
            *paths))

    def _sort_summary_entries(self, a, b):
        return (cmp(b.get("last_activity_time"),
                    a.get("last_activity_time")) or
                cmp(a["name"], b["name"]))


if __name__ == "__main__":
    from rose.ws import ws_cli
    ws_cli(RoseBushService)
else:
    from rose.ws import wsgi_app
    application = wsgi_app(RoseBushService)
