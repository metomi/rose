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
"""Rosie discovery service.

Classes:
    RosieDiscoServiceRoot - discovery service root web page.
    RosieDiscoService - discovery service for a given prefix.

"""

import cherrypy
from isodatetime.data import get_timepoint_from_seconds_since_unix_epoch
import jinja2
import simplejson
from rose.host_select import HostSelector
from rose.resource import ResourceLocator
import rosie.db
from rosie.suite_id import SuiteId


class RosieDiscoServiceRoot(object):

    """Serves the Rosie discovery service index page."""

    NS = "rosie"
    UTIL = "disco"
    TITLE = "Rosie Suites Discovery"

    def __init__(self, *args, **kwargs):
        self.exposed = True
        self.props = {}
        rose_conf = ResourceLocator.default().get_conf()
        self.props["title"] = rose_conf.get_value(
            ["rosie-disco", "title"], self.TITLE)
        self.props["host_name"] = rose_conf.get_value(["rosie-disco", "host"])
        if self.props["host_name"] is None:
            self.props["host_name"] = HostSelector().get_local_host()
            if self.props["host_name"] and "." in self.props["host_name"]:
                self.props["host_name"] = (
                    self.props["host_name"].split(".", 1)[0])
        self.props["rose_version"] = ResourceLocator.default().get_version()
        self.props["template_env"] = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                ResourceLocator.default().get_util_home(
                    "lib", "html", "template", "rosie-disco")))
        db_url_map = {}
        for key, node in rose_conf.get(["rosie-db"]).value.items():
            if key.startswith("db.") and key[3:]:
                db_url_map[key[3:]] = node.value
        self.db_url_map = db_url_map
        if not self.db_url_map:
            self.db_url_map = {}
        for key, db_url in self.db_url_map.items():
            setattr(self, key, RosieDiscoService(self.props, key, db_url))

    @cherrypy.expose
    def index(self, *_):
        """Provide the root index page."""
        tmpl = self.props["template_env"].get_template("index.html")
        return tmpl.render(
            title=self.props["title"],
            host=self.props["host_name"],
            rose_version=self.props["rose_version"],
            script=cherrypy.request.script_name,
            keys=sorted(self.db_url_map.keys()))


class RosieDiscoService(object):

    """Serves the index page of the database of a given prefix."""

    HELLO = "Hello %s\n"

    def __init__(self, props, prefix, db_url):
        self.exposed = True
        self.props = props
        self.prefix = prefix
        source_option = "prefix-web." + self.prefix
        source_url_node = ResourceLocator.default().get_conf().get(
            ["rosie-id", source_option])
        self.source_url = ""
        if source_url_node is not None:
            self.source_url = source_url_node.value
        self.dao = rosie.db.DAO(db_url)

    def __call__(self):
        """Dummy."""
        pass

    @cherrypy.expose
    def index(self, *_):
        """Provide the index page."""
        try:
            return self._render()
        except:
            import traceback
            traceback.print_exc()

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
                item["date"] = str(get_timepoint_from_seconds_since_unix_epoch(
                    item["date"]))
        tmpl = self.props["template_env"].get_template("prefix-index.html")
        return tmpl.render(
            title=self.props["title"],
            host=self.props["host_name"],
            rose_version=self.props["rose_version"],
            script=cherrypy.request.script_name,
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


if __name__ == "__main__":
    from rose.ws import ws_cli
    ws_cli(RosieDiscoServiceRoot)
else:
    from rose.ws import wsgi_app
    application = wsgi_app(RosieDiscoServiceRoot)
