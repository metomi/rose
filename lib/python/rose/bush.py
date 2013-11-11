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
"""Web service for browsing users' Rose suite logs via an HTTP interface."""

import cherrypy
from glob import glob
import jinja2
import mimetypes
import os
import pwd
import shlex
import simplejson
import signal
import socket
import sys
import rose.config
from rose.opt_parse import RoseOptionParser
from rose.reporter import Reporter
from rose.suite_engine_proc import SuiteEngineProcessor
import tarfile
from tempfile import NamedTemporaryFile
from time import gmtime, strftime
import traceback
import urllib


UTIL = "bush"
ROSE_UTIL = "rose-bush"
LOG_ROOT = os.path.expanduser("~/.metomi/" + ROSE_UTIL)
LOG_STATUS = LOG_ROOT + ".status"


class Root(object):

    """Serves the index page."""

    PER_PAGE = 15
    PER_PAGE_MAX = 300
    VIEW_SIZE_MAX = 10 * 1024 * 1024 # 10MB

    def __init__(self, template_env):
        self.exposed = True
        self.suite_engine_proc = SuiteEngineProcessor.get_processor()
        self.template_env = template_env
        self.host_name = socket.gethostname()
        if self.host_name and "." in self.host_name:
            self.host_name = self.host_name.split(".", 1)[0]

    @cherrypy.expose
    def index(self):
        """Display a page to input user ID and suite ID."""
        # TODO: some way to allow autocomplete of user field?
        try:
            template = self.template_env.get_template("index.html")
            return template.render(host=self.host_name,
                                   script=cherrypy.request.script_name)
        except Exception as e:
            traceback.print_exc(e)

    @cherrypy.expose
    def list(self, user, suite, page=1, cycles=None, tasks=None,
             no_status=None, order=None, per_page=PER_PAGE, form=None):
        """List tasks of a running or completed suite.

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
                 "time_desc", "time_asc","cycle_desc_name_desc",
                 "cycle_desc_name_asc", "cycle_asc_name_desc",
                 "cycle_asc_name_asc", "name_asc_cycle_asc",
                 "name_desc_cycle_asc", "name_asc_cycle_desc",
                 "name_desc_cycle_desc".
        per_page -- Number of entries to display per page (defualt=32)
        form -- Specify return format. If None, display HTML page. If "json",
                return a JSON data structure.

        """
        user_suite_dir = self._get_user_suite_dir(user, suite)
        if not os.path.isdir(user_suite_dir):
            raise cherrypy.HTTPError(400)
        if not isinstance(per_page, int):
            if per_page:
                per_page = int(per_page)
            else:
                per_page = self.PER_PAGE
        if page and per_page:
            page = int(page)
        else:
            page = 1
        no_statuses = no_status
        if no_status and not isinstance(no_status, list):
            no_statuses = [no_status]
        data = {
            "host": self.host_name,
            "user": user,
            "suite": suite,
            "cycles": cycles,
            "tasks": tasks,
            "no_statuses": no_statuses,
            "order": order,
            "per_page": per_page,
            "per_page_default": self.PER_PAGE,
            "per_page_max": self.PER_PAGE_MAX,
            "page": page,
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
        data["offset"] = (page - 1) * per_page
        entries, of_n_entries = self.suite_engine_proc.get_suite_job_events(
                                    user, suite,
                                    cycles, tasks, no_statuses, order,
                                    per_page, data["offset"])
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
            template = self.template_env.get_template("list.html")
            return template.render(script=cherrypy.request.script_name, **data)
        except Exception as e:
            traceback.print_exc(e)

    @cherrypy.expose
    def summary(self, user, form=None):
        """Summarise a user's installed suites.

        user -- A string containing a valid user ID
        form -- Specify return format. If None, display HTML page. If "json",
                return a JSON data structure.

        """
        user_suite_dir_root = self._get_user_suite_dir_root(user)
        data = {"host": self.host_name, "user": user, "entries": []}
        if os.path.isdir(user_suite_dir_root):
            for name in os.listdir(user_suite_dir_root):
                entry = {"name": name, "states": {}}
                data["entries"].append(entry)
                entry.update(self._get_suite_logs_info(user, name))
                s = self.suite_engine_proc.get_suite_state_summary(user, name)
                entry["states"].update(s)
            data["entries"].sort(self._sort_summary_entries)
        data["time"] = strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime())
        if form == "json":
            return simplejson.dumps(data)
        template = self.template_env.get_template("summary.html")
        return template.render(script=cherrypy.request.script_name, **data)

    @cherrypy.expose
    def view(self, user, suite, path, path_in_tar=None, mode=None):
        """View a text log file."""
        f_name = self._get_user_suite_dir(user, suite, path)
        if not os.access(f_name, os.F_OK | os.R_OK):
            raise cherrypy.HTTPError(404)
        if path_in_tar:
            tar_f = tarfile.open(f_name, 'r:gz')
            try:
                tar_info = tar_f.getmember(path_in_tar)
            except KeyError:
                raise cherrypy.HTTPError(404)
            f_size = tar_info.size
            f = tar_f.extractfile(path_in_tar)
            if f.read(2) == "#!":
                mime = "text/plain"
            else:
                mime = mimetypes.guess_type(
                            urllib.pathname2url(path_in_tar))[0]
            f.seek(0)
            if (mode == "download" or
                f_size > self.VIEW_SIZE_MAX or
                mime and (not mime.startswith("text/") or
                mime.endswith("html"))):
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
                mime = "text/plain"
            else:
                mime = mimetypes.guess_type(urllib.pathname2url(f_name))[0]
            if (mode == "download" or
                f_size > self.VIEW_SIZE_MAX or
                mime and (not mime.startswith("text/") or
                mime.endswith("html"))):
                cherrypy.response.headers["Content-Type"] = mime
                return cherrypy.lib.static.serve_file(f_name, mime)
            s = open(f_name).read()
        if mode == "text":
            s = jinja2.escape(s)
        lines = s.splitlines()
        template = self.template_env.get_template("view.html")
        return template.render(
                script=cherrypy.request.script_name,
                time=strftime("%Y-%m-%dT%H:%M:%S+0000", gmtime()),
                host=self.host_name,
                user=user,
                suite=suite,
                path=path,
                path_in_tar=path_in_tar,
                mode=mode,
                lines=lines)

    def _get_suite_logs_info(self, user, suite):
        data = {"info": {}, "files": {}}
        user_suite_dir = self._get_user_suite_dir(user, suite)

        # rose-suite.info
        info_name = os.path.join(user_suite_dir, "rose-suite.info")
        if os.path.isfile(info_name):
            info_root = rose.config.load(info_name)
            for key, node in info_root.value.items():
                if node.is_ignored() or not isinstance(node.value, str):
                    continue
                data["info"][key] = node.value

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

    def _get_user_home(self, user):
        try:
            return pwd.getpwnam(user).pw_dir
        except KeyError:
            raise cherrypy.HTTPError(404)

    def _get_user_suite_dir_root(self, user):
        return os.path.join(
                    self._get_user_home(user),
                    self.suite_engine_proc.SUITE_DIR_REL_ROOT)

    def _get_user_suite_dir(self, user, suite, *paths):
        return os.path.join(
                    self._get_user_home(user),
                    self.suite_engine_proc.SUITE_DIR_REL_ROOT,
                    suite,
                    *paths)

    def _sort_summary_entries(self, a, b):
        return (cmp(b["states"].get("last_activity_time"),
                    a["states"].get("last_activity_time")) or
                cmp(a["name"], b["name"]))


def _handle_error():
    # Handle an error occurring during a request in cherrypy.
    cherrypy.response.status = 500
    print cherrypy._cperror.format_exc()

def main():
    """Start quick server."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("non_interactive")
    opts, args = opt_parser.parse_args()
    arg = None
    if sys.argv[1:]:
        arg = sys.argv[1]
    if arg == "start":
        start(is_main=True)
    else:
        report = Reporter(opts.verbosity - opts.quietness)
        status = rose_bush_quick_server_status()
        level = Reporter.DEFAULT
        if arg != "stop":
           level = 0
        for k, v in sorted(status.items()):
            report("%s=%s" % (k, v), level=level)
        if (arg == "stop" and status.get("pid") and
            (opts.non_interactive or
             raw_input("Stop server? y/n (default=n)") == "y")):
            os.kill(int(status["pid"]), signal.SIGTERM)
            # TODO: should check whether it is killed or not


def start(is_main=False):
    """Create the server.

    If is_main, invoke cherrypy.quickstart.
    Otherwise, return a cherrypy.Application instance.

    """
    # Environment variables (not normally defined in WSGI mode)
    if os.getenv("ROSE_HOME") is None:
        path = os.path.abspath(__file__)
        while os.path.dirname(path) != path: # not root
            if os.path.basename(path) == "lib":
                os.environ["ROSE_HOME"] = os.path.dirname(path)
                break
            path = os.path.dirname(path)
    for k, v in [("ROSE_NS", "rose"), ("ROSE_UTIL", "bush")]:
        if os.getenv(k) is None:
            os.environ[k] = v

    # Configuration for HTML library
    rose_home = os.getenv("ROSE_HOME")
    html_lib = os.path.join(rose_home, "lib/html")
    icon_path = os.path.join(rose_home, "etc/images/rose-icon-trim.png")
    css_path = os.path.join(html_lib, ROSE_UTIL, "rose-bush.css")
    js_path = os.path.join(html_lib, ROSE_UTIL, "rose-bush.js")
    config = {"/etc": {
                    "tools.staticdir.dir": os.path.join(html_lib, "external"),
                    "tools.staticdir.on": True},
              "/favicon.ico": {
                    "tools.staticfile.filename": icon_path,
                    "tools.staticfile.on": True},
              "/rose-bush.css": {
                    "tools.staticfile.filename": css_path,
                    "tools.staticfile.on": True},
              "/rose-bush.js": {
                    "tools.staticfile.filename": js_path,
                    "tools.staticfile.on": True}}
    tmpl_loader = jinja2.FileSystemLoader(os.path.join(html_lib, ROSE_UTIL))
    root = Root(jinja2.Environment(loader=tmpl_loader))

    # Start server or return WSGI application
    cherrypy.config["tools.encode.on"] = True
    cherrypy.config["tools.encode.encoding"] = "utf-8"
    if is_main:
        # Quick server
        if not os.path.isdir(os.path.dirname(LOG_ROOT)):
            os.makedirs(os.path.dirname(LOG_ROOT))
        cherrypy.config["log.access_file"] = LOG_ROOT + "-access.log"
        open(cherrypy.config["log.access_file"], "w").close()
        cherrypy.config["log.error_file"] = LOG_ROOT + "-error.log"
        open(cherrypy.config["log.error_file"], "w").close()
        cherrypy.config["request.error_response"] = _handle_error
        config["global"] = {"server.socket_host": "0.0.0.0"}
        f = open(LOG_STATUS, "w")
        f.write("host=%s\n" % cherrypy.server.socket_host)
        f.write("port=%d\n" % cherrypy.server.socket_port)
        f.write("pid=%d\n" % os.getpid())
        f.close()
        try:
            return cherrypy.quickstart(root, "/", config=config)
        finally:
            os.unlink(LOG_STATUS)
    else:
        # WSGI server
        return cherrypy.Application(root, script_name=None, config=config)


def rose_bush_quick_server_status():
    ret = {}
    try:
        for line in open(LOG_STATUS):
            k, v = line.strip().split("=", 1)
            ret[k] = v
    except:
        pass
    return ret


if __name__ == "__main__":
    main()
else:
    # WSGI server
    application = start()
