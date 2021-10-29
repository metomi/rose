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
"""Create database files for Rosie web service."""

import os
import sys

import sqlalchemy as al

from metomi.rose.config import ConfigError
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Event, Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rosie.db import (
    LATEST_TABLE_NAME,
    MAIN_TABLE_NAME,
    META_TABLE_NAME,
    OPTIONAL_TABLE_NAME,
)
from metomi.rosie.svn_hook import InfoFileError
from metomi.rosie.svn_post_commit import RosieSvnPostCommitHook


class RosieDatabaseCreateEvent(Event):

    """Event raised when a Rosie database is created."""

    def __str__(self):
        return "%s: DB created." % (self.args[0])


class RosieDatabaseCreateSkipEvent(Event):

    """Event raised when a Rosie database creation is skipped."""

    KIND = Event.KIND_ERR

    def __str__(self):
        return "%s: DB already exists, skip." % (self.args[0])


class RosieDatabaseLoadEvent(Event):

    """Event raised when a Rosie database has loaded with I of N revisions.

    Args:
        repos_path (str)
        revision (int) - Ith revision
        youngest (int) - Nth revision
    """

    LEVEL = Event.V

    def __str__(self):
        return "%s: DB loaded, r%d of %d." % self.args


class RosieDatabaseLoadSkipEvent(Event):

    """Event raised when a Rosie database load is skipped.

    Args:
        repos_path (str)
        message (str)
    """

    KIND = Event.KIND_ERR

    def __str__(self):
        return "%s: DB not loaded: %s" % self.args


class RosieDatabaseInitiator:

    """Initiate a database file from the repository information."""

    LEN_DB_STRING = 1024
    LEN_STATUS = 2
    SQLITE_PREFIX = "sqlite:///"

    def __init__(self, event_handler=None, popen=None, fs_util=None):
        if event_handler is None:
            event_handler = self._dummy
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        self.fs_util = fs_util
        self.post_commit_hook = RosieSvnPostCommitHook(
            event_handler=event_handler, popen=popen
        )

    def _dummy(self, *args, **kwargs):
        """Does nothing."""
        pass

    def create_and_load(self, db_url, repos_path):
        """Create web service database and load content from repository."""
        try:
            self.create(db_url)
        except al.exc.OperationalError:
            pass
        else:
            self.load(repos_path)

    __call__ = create_and_load

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def create(self, db_url):
        """Create database tables."""
        if db_url.startswith(self.SQLITE_PREFIX):
            db_url_dir = os.path.dirname(db_url[len(self.SQLITE_PREFIX) :])
            self.fs_util.makedirs(db_url_dir)
        try:
            engine = al.create_engine(db_url)
            metadata = al.MetaData()
            db_string = al.String(self.LEN_DB_STRING)
            tables = []
            tables.append(
                al.Table(
                    LATEST_TABLE_NAME,
                    metadata,
                    al.Column(
                        "idx", db_string, nullable=False, primary_key=True
                    ),
                    al.Column(
                        "branch", db_string, nullable=False, primary_key=True
                    ),
                    al.Column(
                        "revision",
                        al.Integer,
                        nullable=False,
                        primary_key=True,
                    ),
                )
            )
            tables.append(
                al.Table(
                    MAIN_TABLE_NAME,
                    metadata,
                    al.Column(
                        "idx", db_string, nullable=False, primary_key=True
                    ),
                    al.Column(
                        "branch", db_string, nullable=False, primary_key=True
                    ),
                    al.Column(
                        "revision",
                        al.Integer,
                        nullable=False,
                        primary_key=True,
                    ),
                    al.Column("owner", db_string, nullable=False),
                    al.Column("project", db_string, nullable=False),
                    al.Column("title", db_string, nullable=False),
                    al.Column("author", db_string, nullable=False),
                    al.Column("date", al.Integer, nullable=False),
                    al.Column(
                        "status", al.String(self.LEN_STATUS), nullable=False
                    ),
                    al.Column("from_idx", db_string),
                )
            )
            tables.append(
                al.Table(
                    OPTIONAL_TABLE_NAME,
                    metadata,
                    al.Column(
                        "idx", db_string, nullable=False, primary_key=True
                    ),
                    al.Column(
                        "branch", db_string, nullable=False, primary_key=True
                    ),
                    al.Column(
                        "revision",
                        al.Integer,
                        nullable=False,
                        primary_key=True,
                    ),
                    al.Column(
                        "name", db_string, nullable=False, primary_key=True
                    ),
                    al.Column("value", db_string),
                )
            )
            tables.append(
                al.Table(
                    META_TABLE_NAME,
                    metadata,
                    al.Column(
                        "name", db_string, primary_key=True, nullable=False
                    ),
                    al.Column("value", db_string),
                )
            )
            for table in tables:
                table.create(engine)
            engine.connect()
            self.handle_event(RosieDatabaseCreateEvent(db_url))
        except al.exc.OperationalError as exc:
            self.handle_event(RosieDatabaseCreateSkipEvent(db_url))
            raise exc

    def load(self, repos_path):
        """Load database contents from a repository."""
        if not repos_path or not os.path.exists(repos_path):
            message = "Path not found"
            self.handle_event(RosieDatabaseLoadSkipEvent(repos_path, message))
            return
        repos_path = os.path.abspath(repos_path)
        youngest = int(self.popen("svnlook", "youngest", repos_path)[0])
        revision = 1
        while revision <= youngest:
            if sys.stdout.isatty():
                sys.stdout.write(
                    f"\r{Reporter.PREFIX_INFO}... loading revision {revision} "
                    f"of {youngest}"
                )
                sys.stdout.flush()
            try:
                self.post_commit_hook.run(
                    repos_path, str(revision), no_notification=True
                )
            except (ConfigError, InfoFileError, al.exc.DatabaseError) as err:
                if sys.stdout.isatty():
                    sys.stdout.write("\r")
                    sys.stdout.flush()
                err_msg = f"Exception occurred: {type(err).__name__} - {err}"
                message = (
                    f"Could not load revision {revision} of {youngest} as "
                    f"the post-commit hook failed:\n{err_msg}\n"
                )
                event = RosieDatabaseLoadSkipEvent(repos_path, message)
            else:
                event = RosieDatabaseLoadEvent(repos_path, revision, youngest)
            if revision == youngest:
                # Check if any new revisions have been added.
                youngest = self.popen("svnlook", "youngest", repos_path)[0]
                youngest = int(youngest)
            if revision == youngest:
                event.level = event.DEFAULT
            if sys.stdout.isatty():
                sys.stdout.write("\r")
            self.handle_event(event)
            revision += 1
        return revision


def main():
    """rosa db-create."""
    db_conf = ResourceLocator.default().get_conf().get(["rosie-db"])
    if db_conf is not None:
        opts = RoseOptionParser().parse_args()[0]
        reporter = Reporter(opts.verbosity - opts.quietness)
        init = RosieDatabaseInitiator(event_handler=reporter)
        conf = ResourceLocator.default().get_conf()
        for key in db_conf.value:
            if key.startswith("db."):
                prefix = key.replace("db.", "", 1)
                db_url = conf.get_value(["rosie-db", "db." + prefix])
                repos_path = conf.get_value(["rosie-db", "repos." + prefix])
                init(db_url, repos_path)


if __name__ == "__main__":
    main()
