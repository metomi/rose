# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
#-----------------------------------------------------------------------------
"""Web server frontend for a database, using a JSON API.

Classes:
    Root - represents the root web page.
    PrefixRoot - represents the interface page for a given prefix.

Functions:
    main - setup the server.

"""

import cherrypy
import jinja2
import os
import simplejson
from rose.env import env_var_process
from rose.resource import ResourceLocator
import rosie.db
from rosie.suite_id import SuiteId


class Root(object):

    """Serves the index page."""

    def __init__(self, template_env, db_url_map):
        self.exposed = True
        self.template_env = template_env
        self.db_url_map = db_url_map
        if not self.db_url_map:
            self.db_url_map = {}
        for key, db_url in self.db_url_map.items():
            setattr(self, key, PrefixRoot(self.template_env, key, db_url))

    @cherrypy.expose
    def index(self, *_):
        """Provide the root index page."""
        template = self.template_env.get_template("index.html")
        return template.render(web_prefix=cherrypy.request.script_name,
                               keys=sorted(self.db_url_map.keys()))


class PrefixRoot(object):

    """Serves the index page of the database of a given prefix."""

    HELLO = "Hello %s\n"

    def __init__(self, template_env, prefix, db_url):
        self.exposed = True
        self.template_env = template_env
        self.prefix = prefix
        source_option = "prefix-web." + self.prefix
        source_url_node = ResourceLocator.default().get_conf().get(
                                          ["rosie-id", source_option])
        self.source_url = ""
        if source_url_node is not None:
            self.source_url = source_url_node.value
        self.dao = rosie.db.DAO(db_url)

    @cherrypy.expose
    def index(self, *_):
        """Provide the index page."""
        return self._render()

    @cherrypy.expose
    def hello(self, format=None):
        """Say Hello on success."""
        if cherrypy.request.login:
            data = self.HELLO % cherrypy.request.login
        else:
            data = self.HELLO % "user"
        if format == "json":
            return simplejson.dumps(data)
        return data

    @cherrypy.expose
    def query(self, q, all_revs=0, format=None):
        """Search database for rows with data matching the query string."""
        all_revs = int(all_revs)
        filters = []
        if not isinstance(q, list):
            q = [q]
        filters = [_query_parse_string(q_str) for q_str in q]
        data = self.dao.query(filters, all_revs)
        if format == "json":
            return simplejson.dumps(data)
        return self._render(all_revs, data, filters=filters)

    @cherrypy.expose
    def search(self, s, all_revs=0, format=None):
        """Search database for rows with data matching the query string."""
        all_revs = int(all_revs)
        data = self.dao.search(s, all_revs)
        if format == "json":
            return simplejson.dumps(data)
        return self._render(all_revs, data, s=s)

    @cherrypy.expose
    def get_known_keys(self, format=None):
        """Return the names of the common fields."""
        if format == "json":
            return simplejson.dumps(self.dao.get_known_keys())

    @cherrypy.expose
    def get_query_operators(self, format=None):
        """Return the allowed query operators."""
        if format == "json":
            return simplejson.dumps(self.dao.get_query_operators())

    @cherrypy.expose
    def get_optional_keys(self, format=None):
        """Return the names of the optional fields."""
        if format == "json":
            return simplejson.dumps(self.dao.get_optional_keys())

    def _render(self, all_revs=0, data=None, filters=None, s=None):
        """Render return data with a template."""
        if data:
            for item in data:
                suite_id = SuiteId.from_idx_branch_revision(
                    item["idx"], item["branch"], item["revision"])
                item["href"] = suite_id.to_web()
        template = self.template_env.get_template("prefix-index.html")
        return template.render(
                        web_prefix=cherrypy.request.script_name,
                        prefix=self.prefix,
                        prefix_source_url=self.source_url,
                        known_keys=self.dao.get_known_keys(),
                        query_operators=self.dao.get_query_operators(),
                        all_revs=all_revs,
                        filters=filters,
                        s=s,
                        data=data)


def _query_parse_string(q_str):
    """Split a query filter string into component parts."""
    conjunction, tail = q_str.split(" ", 1)
    if conjunction == "or" or conjunction == "and":
        q_str = tail
    else:
        conjunction = "and"
    filt = [conjunction]
    if all(s == "(" for s in q_str.split(" ", 1)[0]):
        start_group, q_str = q_str.split(" ", 1)
        filt.append(start_group)
    key, operator, value = q_str.split(" ", 2)
    filt.extend([key, operator])
    last_groups = value.rsplit(" ", 1)
    if (len(last_groups) > 1 and last_groups[1] and
        all([s == ")" for s in last_groups[1]])):
        filt.extend(last_groups)
    else:
        filt.extend([value])
    return filt


def _handle_error():
    """Handle an error occurring during a request in cherrypy."""
    cherrypy.response.status = 500
    print cherrypy._cperror.format_exc()


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
    for key, value in [("ROSE_NS", "rosa"), ("ROSE_UTIL", "ws")]:
        if os.getenv(key) is None:
            os.environ[key] = value

    # CherryPy quick server configuration
    rose_conf = ResourceLocator.default().get_conf()
    if is_main and rose_conf.get_value(["rosie-ws", "log-dir"]) is not None:
        log_dir_value = rose_conf.get_value(["rosie-ws", "log-dir"])
        log_dir = env_var_process(os.path.expanduser(log_dir_value))
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, "server.log")
        log_error_file = os.path.join(log_dir, "server.err.log")
        cherrypy.config["log.error_file"] = log_error_file
        cherrypy.config["log.access_file"] = log_file
        cherrypy.config["request.error_response"] = _handle_error
    cherrypy.config["log.screen"] = False
    # Configuration for dynamic pages
    db_url_map = {}
    for key, node in rose_conf.get(["rosie-db"]).value.items():
        if key.startswith("db.") and key[3:]:
            db_url_map[key[3:]] = node.value
    res_loc = ResourceLocator.default()
    html_lib = res_loc.get_util_home("lib", "html")
    icon_path = res_loc.locate("images/rosie-icon-trim.png")
    tmpl_loader = jinja2.FileSystemLoader(os.path.join(html_lib, "rosie-ws"))
    root = Root(jinja2.Environment(loader=tmpl_loader), db_url_map)

    # Configuration for static pages
    config = {"/etc": {
                    "tools.staticdir.dir": os.path.join(html_lib, "external"),
                    "tools.staticdir.on": True},
              "/favicon.ico": {
                    "tools.staticfile.on": True,
                    "tools.staticfile.filename": icon_path}}
    if is_main:
        port = int(rose_conf.get_value(["rosie-ws", "port"], 8080))
        config.update({"global": {"server.socket_host": "0.0.0.0",
                                  "server.socket_port": port}})

    # Start server or return WSGI application
    if is_main:
        return cherrypy.quickstart(root, "/", config=config)
    else:
        return cherrypy.Application(root, script_name=None, config=config)


if __name__ == "__main__":
    # Quick server
    start(is_main=True)
else:
    # WSGI server
    application = start()
