# Copyright (C) British Crown (Met Office) & Contributors.
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
    GetHandler - overrides HTTP GET method to return known fields and operators
    HelloHandler - overrides HTTP GET method to write a hello message
    SearchHandler - overrides HTTP GET method to serve a database search
    QueryHandler - overrides HTTP GET method to serve a database query

"""

from glob import glob
import json
import logging
import os
from pathlib import Path
import pwd
import signal
from time import sleep

import jinja2
import pkg_resources
from tornado.ioloop import IOLoop, PeriodicCallback
import tornado.log
import tornado.web
import tornado.wsgi

from metomi.isodatetime.data import get_timepoint_from_seconds_since_unix_epoch
from metomi.rose import __version__ as ROSE_VERSION
from metomi.rose.host_select import HostSelector
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.resource import ResourceLocator
import metomi.rosie.db
from metomi.rosie.suite_id import SuiteId

LOG_ROOT_TMPL = os.path.join(
    "~", ".metomi", "%(ns)s-%(util)s-%(host)s-%(port)s"
)
DEFAULT_PORT = 8080
INTERVAL_CHECK_FOR_STOP_CMD = 1  # in units of seconds


class RosieDiscoServiceApplication(tornado.web.Application):

    """Basic Tornado application defining the web service."""

    NAMESPACE = "rosie"
    UTIL = "disco"
    TITLE = "Rosie Suites Discovery"

    def __init__(self, service_root_mode=False, *args, **kwargs):
        self.stopping = False
        self.service_root_mode = service_root_mode

        self.props = {}
        rose_conf = ResourceLocator.default().get_conf()
        self.props["title"] = rose_conf.get_value(
            ["rosie-disco", "title"], self.TITLE
        )
        self.props["host_name"] = rose_conf.get_value(["rosie-disco", "host"])
        if self.props["host_name"] is None:
            self.props["host_name"] = HostSelector().get_local_host()
            if self.props["host_name"] and "." in self.props["host_name"]:
                self.props["host_name"] = self.props["host_name"].split(
                    ".", 1
                )[0]
        self.props["rose_version"] = ROSE_VERSION

        # Get location of HTML files from package
        rosie_lib = os.path.join(
            pkg_resources.resource_filename('metomi.rosie', 'lib'),
            "html",
            "template",
            "rosie-disco",
        )

        # Autoescape markup to prevent code injection from user inputs.
        self.props["template_env"] = jinja2.Environment(
            autoescape=jinja2.select_autoescape(
                enabled_extensions=("html", "xml"), default_for_string=True
            ),
            loader=jinja2.FileSystemLoader(rosie_lib),
        )

        db_url_map = {}
        for key, node in rose_conf.get(["rosie-db"]).value.items():
            if key.startswith("db.") and key[3:]:
                db_url_map[key[3:]] = node.value
        self.db_url_map = db_url_map

        # Specify the root URL for the handlers and template.
        ROOT = "%s-%s" % (self.NAMESPACE, self.UTIL)
        service_root = r"/?"
        if self.service_root_mode:
            service_root = service_root.replace("?", ROOT + r"/?")

        # Set-up the Tornado application request-handling structure.
        prefix_handlers = []
        class_args = {"props": self.props}
        root_class_args = dict(class_args)  # mutable so copy for safety
        root_class_args.update({"db_url_map": self.db_url_map})
        root_handler = (service_root, RosieDiscoServiceRoot, root_class_args)
        for key, db_url in self.db_url_map.items():
            prefix_class_args = dict(class_args)  # mutable so copy for safety
            prefix_class_args.update(
                {
                    "prefix": key,
                    "db_url": db_url,
                    "service_root": service_root,
                }
            )
            handler = (
                service_root + key + r"/?",
                RosieDiscoService,
                prefix_class_args,
            )
            get_handler = (
                service_root + key + r"/get_(.+)",
                GetHandler,
                prefix_class_args,
            )
            hello_handler = (
                service_root + key + r"/hello/?",
                HelloHandler,
                prefix_class_args,
            )
            search_handler = (
                service_root + key + r"/search",
                SearchHandler,
                prefix_class_args,
            )
            query_handler = (
                service_root + key + r"/query",
                QueryHandler,
                prefix_class_args,
            )
            prefix_handlers.extend(
                [
                    handler,
                    get_handler,
                    hello_handler,
                    search_handler,
                    query_handler,
                ]
            )

        handlers = [root_handler] + prefix_handlers
        settings = dict(
            autoreload=True,
            static_path=str(
                Path(metomi.rosie.__file__).parent / 'lib/html/static'
            ),
        )
        super(RosieDiscoServiceApplication, self).__init__(
            handlers, **settings
        )

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
            # Log that the stop was clean (as opposed to a kill of the process)
            tornado.log.gen_log.info("Stopped application and server cleanly")


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
        self.write(
            tmpl.render(
                title=self.props["title"],
                host=self.props["host_name"],
                rose_version=self.props["rose_version"],
                script="/static",
                keys=sorted(self.db_url_map.keys()),
            )
        )


class RosieDiscoService(tornado.web.RequestHandler):

    """Serves a page for the database of a given prefix."""

    def initialize(self, props, prefix, db_url, service_root):
        self.props = props
        self.prefix = prefix
        source_option = "prefix-web." + self.prefix
        source_url_node = (
            ResourceLocator.default()
            .get_conf()
            .get(["rosie-id", source_option])
        )
        self.source_url = ""
        if source_url_node is not None:
            self.source_url = source_url_node.value
        self.dao = metomi.rosie.db.DAO(db_url)
        self.service_root = service_root[:-1]  # remove the '?' regex aspect

    # Decorator to ensure there is a trailing slash since buttons for keys
    # otherwise go to wrong URLs for "/rosie/key" (e.g. -> "rosie/query?...").
    @tornado.web.addslash
    def get(self, *args):
        """Provide the index page."""
        try:
            self._render()
        except (KeyError, AttributeError, jinja2.exceptions.TemplateError):
            import traceback

            traceback.print_exc()
        except metomi.rosie.db.RosieDatabaseConnectError as exc:
            raise tornado.web.HTTPError(404, str(exc))

    def _render(self, all_revs=0, data=None, filters=None, s=None):
        """Render return data with a template."""
        if data:
            for item in data:
                suite_id = SuiteId.from_idx_branch_revision(
                    item["idx"], item["branch"], item["revision"]
                )
                item["href"] = suite_id.to_web()
                item["date"] = str(
                    get_timepoint_from_seconds_since_unix_epoch(item["date"])
                )
        tmpl = self.props["template_env"].get_template("prefix-index.html")
        self.write(
            tmpl.render(
                title=self.props["title"],
                host=self.props["host_name"],
                rose_version=self.props["rose_version"],
                script="/static",
                service_root=self.service_root,
                prefix=self.prefix,
                prefix_source_url=self.source_url,
                known_keys=self.dao.get_known_keys(),
                query_operators=self.dao.get_query_operators(),
                all_revs=all_revs,
                filters=filters,
                s=s,
                data=data,
            )
        )


class GetHandler(RosieDiscoService):

    """Write out basic data for the names of standard fields or operators."""

    QUERY_KEYS = [
        "known_keys",  # Return the names of the common fields.
        "query_operators",  # Return the allowed query operators.
        "optional_keys",  # Return the names of the optional fields.
    ]

    def get(self, *args):
        """Return data for basic API points of query keys without values."""
        format_arg = self.get_query_argument("format", default=None)
        if args[0] and format_arg == "json":
            for query in self.QUERY_KEYS:
                if args[0].startswith(query):
                    # No need to catch AttributeError as all QUERY_KEYS valid.
                    self.write(json.dumps(getattr(self.dao, "get_" + query)()))


class HelloHandler(RosieDiscoService):

    """Writes a 'Hello' message to the current logged-in user, else 'user'."""

    HELLO = "Hello %s\n"

    def get(self, *args):
        """Say Hello on success."""
        format_arg = self.get_query_argument("format", default=None)
        data = self.HELLO % pwd.getpwuid(os.getuid()).pw_name
        if format_arg == "json":
            self.write(json.dumps(data))
        else:
            self.write(data)


class SearchHandler(RosieDiscoService):

    """Serves a search of the database on the page of a given prefix."""

    def get(self, *args):
        """Search database for rows with data matching the search string."""
        s_arg = self.get_query_argument("s", default=None)
        all_revs = self.get_query_argument("all_revs", default=0)
        format_arg = self.get_query_argument("format", default=None)

        if s_arg:
            data = self.dao.search(s_arg, all_revs)
        else:  # Blank search: provide no rather than all output (else slow)
            data = None
        if format_arg == "json":
            self.write(json.dumps(data))
        else:
            self._render(all_revs, data, s=s_arg)


class QueryHandler(RosieDiscoService):

    """Serves a query of the database on the page of a given prefix."""

    def get(self, *args):
        """Search database for rows with data matching the query string."""
        q_args = self.get_query_arguments("q")  # empty list if none given
        all_revs = self.get_query_argument("all_revs", default=0)
        format_arg = self.get_query_argument("format", default=None)

        filters = []
        if not isinstance(q_args, list):
            q_args = [q_args]
        filters = [self._query_parse_string(q_str) for q_str in q_args]
        while None in filters:  # remove invalid i.e. blank query filters
            filters.remove(None)
        if filters:
            data = self.dao.query(filters, all_revs)
        else:  # in case of a fully blank query
            data = None
        if format_arg == "json":
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
        try:
            key, operator, value = q_str.split(" ", 2)
        except ValueError:  # blank query i.e. no value provided
            return None
        filt.extend([key, operator])
        last_groups = value.rsplit(" ", 1)
        if (
            len(last_groups) > 1
            and last_groups[1]
            and all([s == ")" for s in last_groups[1]])
        ):
            filt.extend(last_groups)
        else:
            filt.extend([value])
        return filt


def _log_app_base(
    application, host, port, logger_type, file_ext, level_threshold=None
):
    """Log to file some information from an application and/or its server."""
    log = logging.getLogger(logger_type)
    log.propagate = False
    if level_threshold:  # else defaults to logging.WARNING
        log.setLevel(level_threshold)

    log_root = os.path.expanduser(
        LOG_ROOT_TMPL
        % {
            "ns": application.NAMESPACE,
            "util": application.UTIL,
            "host": host,
            "port": port,
        }
    )
    log_channel = logging.FileHandler(log_root + file_ext)
    # Use Tornado's log formatter to add datetime stamps & handle encoding:
    log_channel.setFormatter(tornado.log.LogFormatter(color=False))
    log.addHandler(log_channel)
    return log_channel


def _log_server_status(application, host, port):
    """Log a brief status, including process ID, for an application server."""
    log_root = os.path.expanduser(
        LOG_ROOT_TMPL
        % {
            "ns": application.NAMESPACE,
            "util": application.UTIL,
            "host": host,
            "port": port,
        }
    )
    log_status = log_root + ".status"
    os.makedirs(os.path.dirname(log_root), exist_ok=True)
    with open(log_status, "w") as handle:
        handle.write("host=%s\n" % host)
        handle.write("port=%d\n" % port)
        handle.write("pid=%d\n" % int(application.get_app_pid()))
    return log_status


def _get_server_status(application, host, port):
    """Return a dictionary containing a brief application server status."""
    ret = {}
    log_root_glob = os.path.expanduser(
        LOG_ROOT_TMPL
        % {
            "ns": application.NAMESPACE,
            "util": application.UTIL,
            "host": "*",
            "port": "*",
        }
    )
    for filename in glob(log_root_glob + ".status"):
        try:
            for line in open(filename):
                key, value = line.strip().split("=", 1)
                ret[key] = value
            break
        except (IOError, ValueError):
            pass
    return ret


def parse_cli(*args, **kwargs):
    """Parse command line, start/stop ad-hoc server.

    Return a CLI instruction tuple for a valid command instruction, else False:
        ("start", Boolean, port):
            start server on 'port', [2]==True indicating non_interactive mode.
        ("stop", Boolean):
            stop server, [2]==True indicating service_root_mode.
        None:
            bare command, requesting to print server status
    """
    opt_parser = RoseOptionParser(
        description='''
Start/stop ad-hoc Rosie suite discovery web service server.

For `rosie disco start`, if `PORT` is not specified, use port 8080.

Examples:
    rosie disco start [PORT] # start ad-hoc web service server (on PORT)
    rosie disco stop         # stop ad-hoc web service server
    rosie disco stop -y      # stop ad-hoc web service server w/o prompting
    rosie disco              # print status of ad-hoc web service server
        ''',
    )
    opt_parser.add_my_options("non_interactive", "service_root_mode")
    opts, args = opt_parser.parse_args()

    arg = None
    if args:
        arg = args[0]

    if arg == "start":
        port = DEFAULT_PORT
        if args[1:]:
            try:
                port = int(args[1])
            except ValueError:
                print("Invalid port specified. Using the default port.")
        return ("start", opts.service_root_mode, port)
    elif arg == "stop":
        return ("stop", opts.non_interactive)
    elif arg:  # unrecognised (invalid) argument, to ignore
        return False  # False to distinguish from None for no arguments given


def main():
    port = DEFAULT_PORT
    instruction = False

    cli_input = parse_cli()
    if cli_input is False:  # invalid arguments
        print(" Command argument unrecognised.")
    elif cli_input is None:  # no arguments: bare command
        instruction = "status"
    else:  # valid argument, either 'start' or 'stop'
        instruction, cli_opt = cli_input[:2]
        if len(cli_input) == 3:
            port = cli_input[2]

    if instruction == "start" and cli_opt:
        app = RosieDiscoServiceApplication(service_root_mode=True)
    else:
        app = RosieDiscoServiceApplication()
    app_info = app, app.props["host_name"], port

    # User-friendly message to be written to STDOUT:
    user_msg_end = " the server providing the Rosie Disco web application"
    # Detailed message to be written to log file:
    log_msg_end = " server running application %s on host %s and port %s" % (
        app_info
    )

    if instruction == "start":
        app.listen(port)
        signal.signal(signal.SIGINT, app.sigint_handler)

        # This runs a callback every INTERVAL_CHECK_FOR_STOP_CMD s, needed to
        # later stop the server cleanly via command on demand, as once start()
        # is called on an IOLoop it blocks; stop() cannot be called directly.
        PeriodicCallback(
            app.stop_application, INTERVAL_CHECK_FOR_STOP_CMD * 1000
        ).start()

        # Set-up logging and message outputs
        _log_server_status(*app_info)
        _log_app_base(*app_info, "tornado.access", ".access", logging.INFO)
        _log_app_base(*app_info, "tornado.general", ".general", logging.DEBUG)
        _log_app_base(*app_info, "tornado.application", ".error")

        tornado.log.gen_log.info("Started" + log_msg_end)
        # Call to print before IOLoop start() else it prints only on loop stop.
        print("Started" + user_msg_end)
        append_url_root = ""
        if app.service_root_mode:
            append_url_root = "%s-%s/" % (app.NAMESPACE, app.UTIL)
        # Also print the URL for quick access; 'http://' added so that the URL
        # is hyperlinked in the terminal stdout, but it is not required.
        print(
            "Application root page available at http://%s:%s/%s"
            % (app.props["host_name"], port, append_url_root)
        )

        IOLoop.current().start()
    elif instruction == "status":
        status_info = _get_server_status(*app_info)
        if status_info:
            # Use JSON: 1) easily-parsable & 2) can "pretty print" via indent.
            print(json.dumps(status_info, indent=4))
        else:
            print("No such server running.")
    elif (
        instruction == "stop"
        and (cli_opt or input("Stop server? y/n (default=n)") == "y")
        and (_get_server_status(*app_info).get("pid"))
    ):
        stop_server = True
        try:
            os.killpg(
                int(_get_server_status(*app_info).get("pid")), signal.SIGINT
            )
        except ProcessLookupError:  # process already stopped, e.g. by Ctrl-C
            print(
                "Failed to stop%s; no such server or process to stop."
                % (user_msg_end)
            )
            stop_server = False
        if stop_server:
            # Must wait for next callback, so server will not stop immediately;
            # wait one callback interval so server has definitely stopped...
            sleep(INTERVAL_CHECK_FOR_STOP_CMD)
            IOLoop.current().close()  # ... then close event loop to clean up.

            # Log via stop_application callback (logging module is blocking):
            print("Stopped" + user_msg_end)
            # Close all logging handlers to release log files:
            logging.shutdown()
