# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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

Base classes:
    RosieDiscoServiceApplication - collection of request handlers defining the
        discovery service web application.
    RosieDiscoServiceRoot - discovery service root web page request handler.
    RosieDiscoService - discovery service request handler for a given prefix.

Sub-classes, for handling API points by inheriting from RosieDiscoService:
    HelloHandler - overrides HTTP GET method to write a hello message
    SearchHandler - overrides HTTP GET method to serve a database search
    QueryHandler - overrides HTTP GET method to serve a database query

"""

from glob import glob
import jinja2
import json
import os
import pwd
import signal
import socket
from time import sleep
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import define, options, parse_command_line
import tornado.web

from isodatetime.data import get_timepoint_from_seconds_since_unix_epoch
from rose.resource import ResourceLocator
import rosie.db
from rosie.suite_id import SuiteId


LOG_ROOT_TMPL = "~/.metomi/%(ns)s-%(util)s-%(host)s-%(port)s"
DEFAULT_PORT = 8080
INTERVAL_CHECK_FOR_STOP_CMD = 5  # in units of seconds


class RosieDiscoServiceApplication(tornado.web.Application):

    """Basic Tornado application defining the web service."""

    NAMESPACE = "rosie"
    UTIL = "disco"
    TITLE = "Rosie Suites Discovery"

    def __init__(self, *args, **kwargs):
        self.stopping = False

        self.props = {}
        rose_conf = ResourceLocator.default().get_conf()
        self.props["title"] = rose_conf.get_value(
            ["rosie-disco", "title"], self.TITLE)
        self.props["host_name"] = rose_conf.get_value(["rosie-disco", "host"])
        if self.props["host_name"] is None:
            self.props["host_name"] = socket.gethostname()
            if self.props["host_name"] and "." in self.props["host_name"]:
                self.props["host_name"] = (
                    self.props["host_name"].split(".", 1)[0])
        self.props["rose_version"] = ResourceLocator.default().get_version()
        # Autoescape markup to prevent code injection from user inputs.
        self.props["template_env"] = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                ResourceLocator.default().get_util_home(
                    "lib", "html", "template", "rosie-disco")),
            autoescape=jinja2.select_autoescape(
                enabled_extensions=('html', 'xml'), default_for_string=True))

        db_url_map = {}
        for key, node in list(rose_conf.get(["rosie-db"]).value.items()):
            if key.startswith("db.") and key[3:]:
                db_url_map[key[3:]] = node.value
        self.db_url_map = db_url_map

        # Set-up the Tornado application request-handling structure.
        service_root = r"/" + self.NAMESPACE + r"/?"
        prefix_handlers = []
        class_args = {"props": self.props}

        root_class_args = dict(class_args)  # mutable so copy for safety
        root_class_args.update({"db_url_map": self.db_url_map})
        root_handler = (service_root, RosieDiscoServiceRoot,
                        root_class_args)
        for key, db_url in list(self.db_url_map.items()):
            prefix_class_args = dict(class_args)  # mutable so copy for safety
            prefix_class_args.update({
                "prefix": key,
                "db_url": db_url,
                "root_service_url": self.NAMESPACE,
            })
            handler = (service_root + key + r"/?$", RosieDiscoService,
                       prefix_class_args)
            hello_handler = (service_root + key + r"/hello/?$",
                             HelloHandler, prefix_class_args)
            search_handler = (service_root + key + r"/search(.*)",
                              SearchHandler, prefix_class_args)
            query_handler = (service_root + key + r"/query(.*)",
                             QueryHandler, prefix_class_args)
            prefix_handlers.extend(
                [handler, hello_handler, search_handler, query_handler])

        handlers = [root_handler] + prefix_handlers
        settings = dict(
            debug=True,
            autoreload=True,
            static_path=ResourceLocator.default().get_util_home(
                "lib", "html", "static"),
        )
        super(
            RosieDiscoServiceApplication, self).__init__(handlers, **settings)

    @staticmethod
    def get_app_pid():
        """Return process ID of the application on the current server."""
        return os.getpid()

    def sigint_handler(self, signum, frame):
        """Catch SIGINT signal allowing server stop by stop_application()."""
        self.stopping = True

    def stop_application(self):
        """Stop main event loop and server if 'stopping' flag is True."""
        if self.stopping:
            IOLoop.current().stop()


class RosieDiscoServiceRoot(tornado.web.RequestHandler):

    """Serves the Rosie discovery service index page."""

    def initialize(self, props, db_url_map, *args, **kwargs):
        self.props = props
        self.db_url_map = db_url_map

    # Decorator to ensure there is a trailing slash since buttons for keys
    # otherwise go to wrong URLs for "/rosie" (-> "/key/" not "/rosie/key/").
    @tornado.web.addslash
    def get(self):
        """Provide the root index page."""
        tmpl = self.props["template_env"].get_template("index.html")
        self.write(tmpl.render(
            title=self.props["title"],
            host=self.props["host_name"],
            rose_version=self.props["rose_version"],
            script="/static",
            keys=sorted(self.db_url_map.keys()))
        )


class RosieDiscoService(tornado.web.RequestHandler):

    """Serves the index page of the database of a given prefix."""

    def initialize(self, props, prefix, db_url, root_service_url):
        self.props = props
        self.prefix = prefix
        source_option = "prefix-web." + self.prefix
        source_url_node = ResourceLocator.default().get_conf().get(
            ["rosie-id", source_option])
        self.source_url = ""
        if source_url_node is not None:
            self.source_url = source_url_node.value
        self.dao = rosie.db.DAO(db_url)
        self.root_service_url = root_service_url

    # Decorator to ensure there is a trailing slash since buttons for keys
    # otherwise go to wrong URLs for "/rosie/key" (e.g. -> "rosie/query?...").
    @tornado.web.addslash
    def get(self, *_):
        """Provide the index page."""
        try:
            self._render()
        except (KeyError, AttributeError, jinja2.exceptions.TemplateError):
            import traceback
            traceback.print_exc()
        except rosie.db.RosieDatabaseConnectError as exc:
            raise tornado.web.HTTPError(404, str(exc))

    def get_known_keys(self, format=None):
        """Return the names of the common fields."""
        if self.get_query_argument("format", default=None) == "json":
            self.write(json.dumps(self.dao.get_known_keys()))

    def get_query_operators(self, format=None):
        """Return the allowed query operators."""
        if self.get_query_argument("format", default=None) == "json":
            self.write(json.dumps(self.dao.get_query_operators()))

    def get_optional_keys(self, format=None):
        """Return the names of the optional fields."""
        if self.get_query_argument("format", default=None) == "json":
            self.write(json.dumps(self.dao.get_optional_keys()))

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
        self.write(tmpl.render(
            title=self.props["title"],
            host=self.props["host_name"],
            rose_version=self.props["rose_version"],
            script="/static",
            root_service_url=self.root_service_url,
            prefix=self.prefix,
            prefix_source_url=self.source_url,
            known_keys=self.dao.get_known_keys(),
            query_operators=self.dao.get_query_operators(),
            all_revs=all_revs,
            filters=filters,
            s=s,
            data=data)
        )


class HelloHandler(RosieDiscoService):

    """Writes a 'Hello' message to the current logged-in user, else 'user'."""

    HELLO = "Hello %s\n"

    def get(self):
        """Say Hello on success."""
        data = self.HELLO % pwd.getpwuid(os.getuid()).pw_name
        if self.get_query_argument("format", default=None) == "json":
            self.write(json.dumps(data))
        else:
            self.write(data)


class SearchHandler(RosieDiscoService):

    """Serves a search of the database on the page of a given prefix."""

    def get(self, _, all_revs=0):
        """Search database for rows with data matching the search string."""
        all_revs = int(all_revs)
        # None default produces a blank search i.e. returns all suites in DB.
        s_arg = self.get_query_argument("s", default=None)
        data = self.dao.search(s_arg, all_revs)
        if self.get_query_argument("format", default=None) == "json":
            self.write(json.dumps(data))
        else:
            self._render(all_revs, data, s=s_arg)


class QueryHandler(RosieDiscoService):

    """Serves a query of the database on the page of a given prefix."""

    def get(self, _, all_revs=0):
        """Search database for rows with data matching the query string."""
        all_revs = int(all_revs)
        q_args = self.get_query_arguments("q")
        filters = []
        if not isinstance(q_args, list):
            q_args = [q_args]
        filters = [self._query_parse_string(q_str) for q_str in q_args]
        data = self.dao.query(filters, all_revs)
        if self.get_query_argument("format", default=None) == "json":
            self.write(json.dumps(data))
        else:
            self._render(all_revs, data, filters=filters)

    @staticmethod
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


def _log_server_status(application, host, port):
    """ Log a brief status, including process ID, for an application server."""
    log_root = os.path.expanduser(LOG_ROOT_TMPL % {
        "ns": application.NAMESPACE,
        "util": application.UTIL,
        "host": host,
        "port": port})
    log_status = log_root + ".status"
    if not os.path.isdir(os.path.dirname(log_root)):
        os.makedirs(os.path.dirname(log_root))
    with open(log_status, "w") as handle:
        handle.write("host=%s\n" % host)
        handle.write("port=%d\n" % port)
        handle.write("pid=%d\n" % int(application.get_app_pid()))
    return log_status


def _get_server_status(application, host, port):
    """Return a dictionary containing a brief application server status."""
    ret = {}
    log_root_glob = os.path.expanduser(LOG_ROOT_TMPL % {
        "ns": application.NAMESPACE,
        "util": application.UTIL,
        "host": "*",
        "port": "*"})
    for filename in glob(log_root_glob):
        try:
            for line in open(filename):
                key, value = line.strip().split("=", 1)
                ret[key] = value
            break
        except (IOError, ValueError):
            pass
    return ret


def main():
    arg_msg_comp = "ad-hoc web service server"
    # No value req for Boolean options e.g. --start equivalent to --start=True.
    define("start", type=bool, default=False,
           help="start %s (on specified port, else on port %s)" % (
               arg_msg_comp, DEFAULT_PORT))
    define("port", type=int, default=DEFAULT_PORT, help="port to listen on")
    define("stop", type=bool, default=False, help="stop %s" % arg_msg_comp)
    define("non-interactive", type=bool, default=False,
           help="to stop %s w/o prompting" % arg_msg_comp)
    parse_command_line()

    info_msg_end = " the server providing the Rosie Disco web application"
    status = None
    app = RosieDiscoServiceApplication()
    if options.start:
        app.listen(options.port)
        signal.signal(signal.SIGINT, app.sigint_handler)

        # This runs a callback every INTERVAL_CHECK_FOR_STOP_CMD s, needed to
        # later stop the server cleanly via command on demand, as once start()
        # is called on an IOLoop it blocks; stop() cannot be called directly.
        PeriodicCallback(
            app.stop_application, INTERVAL_CHECK_FOR_STOP_CMD * 1000).start()

        # Before the actual IOLoop start() else it prints only on stop of loop.
        print("Started" + info_msg_end)

        status = _log_server_status(app, app.props["host_name"], options.port)
        IOLoop.current().start()
    elif options.stop and (options.non_interactive or
                           input("Stop server? y/n (default=n)") == "y") and (
        _get_server_status(
            app, app.props["host_name"], options.port).get("pid")):
        os.killpg(int(_get_server_status(
            app, app.props["host_name"], options.port).get("pid")),
            signal.SIGINT)
        # Must wait for next callback, so server will not stop immediately.
        print("Stopping" + info_msg_end + " within the next %s seconds" %
              INTERVAL_CHECK_FOR_STOP_CMD)

        # Wait one callback interval so server has definitely been stopped...
        sleep(INTERVAL_CHECK_FOR_STOP_CMD)
        IOLoop.current().close()  # ... then close event loop to clean up.

        if status:
            os.unlink(status)
        print("Stopped" + info_msg_end)
    elif options.stop:
        print("Failed to stop%s; no such server or process to stop." % (
              info_msg_end))


if __name__ == "__main__":  # Run on an ad-hoc server in a test environment.
    main()
else:  # Run as a WSGI application in a system service environment.
    wsgi_app = tornado.wsgi.WSGIAdapter(app)
    server = wsgiref.simple_server.make_server('', DEFAULT_PORT, wsgi_app)
    server.serve_forever()
