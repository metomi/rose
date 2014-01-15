# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
"""Module containing classes for data retrieval.

Classes:
    DAO - data access object.

Functions:
    create - initialises a new database.

"""

import os

import sqlalchemy as al

import rose.config
from rose.fs_util import FileSystemUtil
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Reporter, Event
from rose.resource import ResourceLocator
import rosie.suite_id


LATEST_TABLE_NAME = "latest"
MAIN_TABLE_NAME = "main"
META_TABLE_NAME = "meta"
OPTIONAL_TABLE_NAME = "optional"


def _col_by_key(table, key):
    for c in table.c:
        if c.key == key:
            return c


def _col_keys(table):
    return [c.key for c in table.c]


class DAO(object):

    """Retrieves data from the suite database.

    It stores the results of the request in the attribute "results"
    (self.results). This is always a list.

    """

    QUERY_OP_ALIASES = {"eq": "__eq__", "ge": "__ge__", "gt": "__gt__",
                        "le": "__le__", "lt": "__lt__", "ne": "__ne__"}

    QUERY_OPERATORS = ["eq", "ge", "gt", "le", "lt", "ne",
                       "contains", "endswith", "ilike", "like",
                       "match", "startswith"]
    TEXT_ST_DELETED = "D "

    def __init__(self, db_url):
        self.db_url = db_url

    def _connect(self):
        self.db_engine = al.create_engine(self.db_url)
        self.db_connection = self.db_engine.connect()
        self.db_metadata = al.MetaData(self.db_engine)
        self.results = None
        self.tables = {}
        for n in [LATEST_TABLE_NAME, MAIN_TABLE_NAME, META_TABLE_NAME,
                  OPTIONAL_TABLE_NAME]:
            self.tables[n] = al.Table(n, self.db_metadata, autoload=True)

    def _execute(self, query):
        """Execute the query and store the database results."""
        rows = self.db_connection.execute(query)
        self.results = [list(row) for row in rows]
        return self.results

    def _get_join_and_columns(self):
        """Create a join of the latest information.

        Return the joined tables object and columns.

        """
        latest_table = self.tables[LATEST_TABLE_NAME]
        main_table = self.tables[MAIN_TABLE_NAME]
        optional_table = self.tables[OPTIONAL_TABLE_NAME]
        joined_column_keys = [c.key for c in main_table.c]
        joined_column_keys += ["name", "value"]
        joined_columns = list(main_table.c) + [
            optional_table.c.name, optional_table.c.value]
        expr = al.sql.select(joined_columns)
        join_main_clause = latest_table.c.idx == main_table.c.idx
        join_main_clause &= latest_table.c.branch == main_table.c.branch
        join_main_clause &= latest_table.c.revision == main_table.c.revision
        from_obj = latest_table.join(main_table,
                                     onclause=join_main_clause)
        join_optional_clause = main_table.c.idx == optional_table.c.idx
        join_optional_clause &= main_table.c.branch == optional_table.c.branch
        join_optional_clause &= (
            main_table.c.revision == optional_table.c.revision)
        from_obj = from_obj.outerjoin(optional_table,
                                      onclause=join_optional_clause)
        return_cols = []
        for key in joined_column_keys:
            for col in from_obj.c:
                if col.key == key:
                    return_cols.append(col)
                    break
        return from_obj, return_cols

    def _get_hist_join_and_columns(self):
        """Create a join for information across all revisions.

        Return the joined tables object and columns.

        """
        main_table = self.tables["main"]
        optional_table = self.tables["optional"]
        joined_column_keys = [c.key for c in main_table.c]
        joined_column_keys += ["name", "value"]
        joined_columns = list(main_table.c) + [
            optional_table.c.name, optional_table.c.value]
        expr = al.sql.select(joined_columns)
        join_optional_clause = main_table.c.idx == optional_table.c.idx
        join_optional_clause &= main_table.c.branch == optional_table.c.branch
        join_optional_clause &= (
            main_table.c.revision == optional_table.c.revision)
        from_obj = main_table.outerjoin(optional_table,
                                        onclause=join_optional_clause)
        return_cols = []
        for key in joined_column_keys:
            for col in from_obj.c:
                if col.key == key:
                    return_cols.append(col)
                    break
        return from_obj, return_cols

    def get_common_keys(self, *args):
        """Return the names of the main and changeset table fields."""
        self._connect()
        self.results = _col_keys(self.tables["main"])
        return self.results

    def get_known_keys(self):
        """Return all known field names."""
        common_keys = self.get_common_keys()
        meta_table = self.tables[META_TABLE_NAME]
        self._connect()
        where = (meta_table.c.name == "known_keys")
        select = al.sql.select([meta_table.c.value],
                               whereclause=where)
        self.results = [r[0] for r in self._execute(select)]  # De-proxy.
        if any(self.results):
            self.results = self.results[0].split()  # shlex.split garbles it.
        self.results = common_keys + self.results
        self.results.sort()
        return self.results

    def get_optional_keys(self, *args):
        """Return the names of the optional fields."""
        self._connect()
        select = al.sql.select([self.tables["optional"].c.name])
        self._execute(select.distinct())
        self.results = [r.pop() for r in self.results]
        self.results.sort()
        return self.results

    def get_query_operators(self, *args):
        """Return the query operators."""
        return self.QUERY_OPERATORS

    def query(self, filters, all_revs=False):
        """Return the results of a series of filters on both tables.

        filters is a list of tuples, each tuple containing:
        joining operator string: 'and' or 'or',
        (optional) start bracket(s): '(', '((', etc,
        column name string: e.g. 'idx' or 'description',
        column operator name string: e.g. 'contains' or 'between',
        column operator argument string: e.g. 'UM' or '200'
        (optional) close bracket(s): ')', '))', etc
        The first joining operator string is superfluous.

        For example:
        [('and', 'idx', 'startswith', 'aba'),
         ('or', 'description', 'eq', 'shiny')]
        will return all suites that have an idx that starts with 'aba'
        and also all suites that have the property 'description' set
        to the value 'shiny'.

        [('and', 'idx', 'startswith', 'aba'),
         ('and', '(' , 'description', 'eq', 'shiny'),
         ('or', 'description', 'eq', 'happy', ')')]
        will return all suites that have an idx that starts with 'aba'
        and the property 'description' set to 'shiny' or 'happy'.

        The logic for joining in the tuples together is based on the
        order in which they are given - e.g. [A, B, C] -> (A & B) & C
        This will be overridden by any bracketed groups.

        If all_revs is True, matching deleted suites and old revisions
        of suites will be returned.
        If all_revs is False, they won't be.

        """
        self._connect()
        if all_revs:
            from_obj, cols = self._get_hist_join_and_columns()
        else:
            from_obj, cols = self._get_join_and_columns()
        where = self.parse_filters_to_expr(filters, from_obj)
        statement = al.sql.select(cols, whereclause=where, from_obj=from_obj)
        statement = statement.distinct()
        values_list = self._execute(statement)
        return_maps = self._rows_to_maps(values_list, cols)
        return return_maps

    def parse_filters_to_expr(self, filters, from_obj=None):
        """Construct an SQL expression from a list of string-tuples."""
        self._connect()
        if from_obj is None:
            from_obj, cols = self._get_join_and_columns()
        item_list = []
        current_expr = []
        for filter_tuple in filters:
            for i, entry in enumerate(filter_tuple):
                if ((entry in ["and", "or"] and i == 0) or
                    entry and (
                     all([e == "(" for e in entry]) or
                     all([e == ")" for e in entry]))):
                    if current_expr:
                        item_list.append(current_expr)
                        current_expr = []
                    if entry in ["and", "or"]:
                        item_list.append(entry)
                    else:
                        item_list.extend(entry)
                else:
                    current_expr.append(entry)
        if current_expr:
            item_list.append(current_expr)
        if item_list and item_list[0] in ["and", "or"]:
            item_list.pop(0)
        for i, item in enumerate(item_list):
            if isinstance(item, list):
                item_list[i] = self._get_sql_expr(item, from_obj)
        return self._get_compound_sql_expr(item_list)

    def _get_compound_sql_expr(self, items):
        """Construct a complex logical expression containing "(", and, etc."""
        levels = [[[]]]
        level = 0
        for i, item in enumerate(items):
            if item == "(":
                level += 1
                if level > len(levels) - 1:
                    levels.append([])
                levels[level].append([])
            for i in range(level + 1):
                levels[i][-1].append(item)
            if item == ")":
                level -= 1
        for i in range(len(levels) - 1, -1, -1):
            for items in levels[i]:
                no_bracket_items = [c for c in items if c != "(" and c != ")"]
                expr = self._get_expr_join(no_bracket_items)
                if i == 0:
                    return expr
                if i > 0:
                    substituted = False
                    # Substitute expr for items in lower levels.
                    for j in range(i - 1, -1, -1):
                        for down_items in levels[j]:
                            ind = -1
                            for k in range(down_items.count(items[1])):
                                ind = down_items.index(items[1], ind + 1) - 1
                                if down_items[ind: ind + len(items)] == items:
                                    del down_items[ind: ind + len(items)]
                                    down_items.insert(ind, expr)
                                    substituted = True
                                    break
                            if substituted:
                                break
        return False

    def _get_sql_expr(self, expr_tuple, from_obj):
        optional_name_col = _col_by_key(from_obj, "name")
        optional_value_col = _col_by_key(from_obj, "value")
        column, operator, value = expr_tuple
        if operator not in self.QUERY_OPERATORS:
            return False
        if operator in self.QUERY_OP_ALIASES:
            operator = self.QUERY_OP_ALIASES[operator]
        for col in from_obj.columns:
            if col.key == column:
                if isinstance(col.type, al.types.INTEGER):
                    try:
                        value = float(value)
                    except (TypeError, ValueError):
                        pass
                expr = getattr(col, operator)(value)
                break
        else:
            expr1 = optional_name_col == column
            expr2 = getattr(optional_value_col, operator)(value)
            expr = expr1 & expr2
        return expr

    def _get_expr_join(self, expr_items):
        """Return an operator-precedence left-to-right logical join."""
        items = list(expr_items)
        while "and" in items:
            i = items.index("and")
            expr = al.and_(items[i - 1], items[i + 1])
            del items[i - 1: i + 2]
            items.insert(i - 1, expr)
        while "or" in items:
            i = items.index("or")
            expr = al.or_(items[i - 1], items[i + 1])
            del items[i - 1: i + 2]
            items.insert(i - 1, expr)
        return items.pop()

    def search(self, s, all_revs=False):
        """Search database for rows with values matching the words in "s".

        If all_revs is True, matching deleted suites and old revisions
        of suites will be returned.
        If all_revs is False, they won't be.

        """
        self._connect()
        if all_revs:
            from_obj, cols = self._get_hist_join_and_columns()
        else:
            from_obj, cols = self._get_join_and_columns()
        where = None
        optional_value_col = _col_by_key(from_obj, "value")
        if not isinstance(s, list):
            s = s.split()
        where = None
        for word in s:
            expr = None
            for column in from_obj.c:
                if expr is None:
                    expr = column.contains(word)
                else:
                    expr |= column.contains(word)
            if where is None:
                where = expr
            else:
                where &= expr
        if where is None:
            where = False
        statement = al.sql.select(cols, whereclause=where, from_obj=from_obj)
        values_list = self._execute(statement)
        return_maps = self._rows_to_maps(values_list, cols)
        return return_maps

    def _rows_to_maps(self, rows, cols):
        """Translate each result row into a map with optional values."""
        results = []
        col_keys = [c.key for c in cols]
        name_index = [c.key for c in cols].index("name")
        value_index = [c.key for c in cols].index("value")
        id_keys = ["idx", "branch", "revision"]
        prev_id = None
        for row in rows:
            row = [r for r in row]
            id_ = [row[col_keys.index(key)] for key in id_keys]
            if id_ != prev_id:
                prev_id = id_
                results.append({})
                for column, value in zip(cols, row):
                    if column.key not in ["name", "value"]:
                        results[-1].update({column.key: value})
            name = row[col_keys.index("name")]
            value = row[col_keys.index("value")]
            if name.endswith("-list") and value is not None:
                value = value.split()
            results[-1].update({name: value})
        return results


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

    """Event raised when a Rosie database has loaded with I of N revisions."""

    LEVEL = Event.V

    def __str__(self):
        return "%s: DB loaded, r%d of %d." % self.args


class RosieDatabaseLoadSkipEvent(Event):

    """Event raised when a Rosie database load is skipped."""

    KIND = Event.KIND_ERR

    def __str__(self):
        return "%s: DB not loaded." % (self.args[0])


class RosieDatabaseInitiator(object):

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

    def _dummy(*args, **kwargs):
        pass

    def create_and_load(self, db_url, repos_path):
        try:
            self.create(db_url)
        except al.exc.OperationalError as e:
            pass
        else:
            self.load(db_url, repos_path)

    __call__ = create_and_load

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def create(self, db_url):
        """Create database tables."""
        if db_url.startswith(self.SQLITE_PREFIX):
            d = os.path.dirname(db_url[len(self.SQLITE_PREFIX):])
            self.fs_util.makedirs(d)
        try:
            engine = al.create_engine(db_url)
            metadata = al.MetaData()
            db_string = al.String(self.LEN_DB_STRING)
            tables = []
            tables.append(al.Table(
                    LATEST_TABLE_NAME, metadata,
                    al.Column("idx", db_string, nullable=False,
                              primary_key=True),
                    al.Column("branch", db_string, nullable=False,
                              primary_key=True),
                    al.Column("revision", al.Integer, nullable=False,
                              primary_key=True)))
            tables.append(al.Table(
                    MAIN_TABLE_NAME, metadata,
                    al.Column("idx", db_string, nullable=False,
                              primary_key=True),
                    al.Column("branch", db_string, nullable=False,
                              primary_key=True),
                    al.Column("revision", al.Integer, nullable=False,
                              primary_key=True),
                    al.Column("owner", db_string, nullable=False),
                    al.Column("project", db_string, nullable=False),
                    al.Column("title", db_string, nullable=False),
                    al.Column("author", db_string, nullable=False),
                    al.Column("date", al.Integer, nullable=False),
                    al.Column("status", al.String(self.LEN_STATUS),
                              nullable=False),
                    al.Column("from_idx", db_string)))
            tables.append(al.Table(
                    OPTIONAL_TABLE_NAME, metadata,
                    al.Column("idx", db_string, nullable=False,
                              primary_key=True),
                    al.Column("branch", db_string, nullable=False,
                              primary_key=True),
                    al.Column("revision", al.Integer, nullable=False,
                              primary_key=True),
                    al.Column("name", db_string, nullable=False,
                              primary_key=True),
                    al.Column("value", db_string)))
            tables.append(al.Table(
                    META_TABLE_NAME, metadata,
                    al.Column("name", db_string, primary_key=True,
                              nullable=False),
                    al.Column("value", db_string)))
            for table in tables:
                table.create(engine)
            connection = engine.connect()
            self.handle_event(RosieDatabaseCreateEvent(db_url))
        except al.exc.OperationalError as e:
            self.handle_event(RosieDatabaseCreateSkipEvent(db_url))
            raise e

    def load(self, db_url, repos_path):
        """Load database contents from a repository."""
        if not repos_path or not os.path.exists(repos_path):
            self.handle_event(RosieDatabaseLoadSkipEvent(repos_path))
            return
        repos_path = os.path.abspath(repos_path)
        youngest = int(self.popen("svnlook", "youngest", repos_path)[0])
        util_home = ResourceLocator.default().get_util_home()
        rosa = os.path.join(util_home, "sbin", "rosa")
        revision = 1
        while revision <= youngest:
            out, err = self.popen(rosa, "svn-post-commit", repos_path,
                                  str(revision))
            event = RosieDatabaseLoadEvent(repos_path, revision, youngest)
            if revision == youngest:
                # Check if any new revisions have been added.
                youngest = self.popen("svnlook", "youngest", repos_path)[0]
                youngest = int(youngest)
            if revision == youngest:
                event.level = event.DEFAULT
            self.handle_event(event)
            revision += 1
        return revision


def main():
    """rosa db-create."""
    db_conf = ResourceLocator.default().get_conf().get(["rosie-db"])
    databases = {}
    if db_conf is not None:
        opts, args = RoseOptionParser().parse_args()
        reporter = Reporter(opts.verbosity - opts.quietness)
        init = RosieDatabaseInitiator(event_handler=reporter)
        conf = ResourceLocator.default().get_conf()
        for key, node in db_conf.value.items():
            if key.startswith("db."):
                prefix = key.replace("db.", "", 1)
                db_url = conf.get_value(["rosie-db", "db." + prefix])
                repos_path = conf.get_value(["rosie-db", "repos." + prefix])
                init(db_url, repos_path)

if __name__ == "__main__":
    main()
