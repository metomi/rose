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
"""Rosie web service data access object.

Classes:
    DAO - data access object.

"""

import sqlalchemy as al

LATEST_TABLE_NAME = "latest"
MAIN_TABLE_NAME = "main"
META_TABLE_NAME = "meta"
OPTIONAL_TABLE_NAME = "optional"


def _col_by_key(table, key):
    """Return the column in "table" matched by "key"."""
    for col in table.c:
        if col.key == key:
            return col


def _col_keys(table):
    """Return the column keys in "table"."""
    return [c.key for c in table.c]


class RosieDatabaseConnectError(al.exc.OperationalError):

    """Exception raised when unable to establish a database connection."""

    def __init__(self, bad_db_url, message):
        self.bad_db_url = bad_db_url
        self.message = message
        super(RosieDatabaseConnectError, self).__init__(
            self.message, "None", self.bad_db_url
        )

    def __str__(self):
        return "Failed to connect to DB '%s'." % self.bad_db_url


class DAO:

    """Retrieves data from the suite database.

    It stores the results of the request in the attribute "results"
    (self.results). This is always a list.

    """

    QUERY_OP_ALIASES = {
        "eq": "__eq__",
        "ge": "__ge__",
        "gt": "__gt__",
        "le": "__le__",
        "lt": "__lt__",
        "ne": "__ne__",
    }

    QUERY_OPERATORS = [
        "eq",
        "ge",
        "gt",
        "le",
        "lt",
        "ne",
        "contains",
        "endswith",
        "ilike",
        "like",
        "match",
        "startswith",
    ]
    TEXT_ST_DELETED = "D "

    def __init__(self, db_url):
        self.db_url = db_url
        self.db_engine = None
        self.db_connection = None
        self.db_metadata = None
        self.results = None
        self.tables = {}

    def _connect(self):
        """Connect to the database file."""
        self.db_engine = al.create_engine(self.db_url)
        self.db_metadata = al.MetaData(self.db_engine)
        self.results = None

        try:
            self.db_connection = self.db_engine.connect()
        except al.exc.OperationalError as exc:
            raise RosieDatabaseConnectError(self.db_url, exc)

        self.tables = {}
        for name in [
            LATEST_TABLE_NAME,
            MAIN_TABLE_NAME,
            META_TABLE_NAME,
            OPTIONAL_TABLE_NAME,
        ]:
            self.tables[name] = al.Table(name, self.db_metadata, autoload=True)

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
        join_main_clause = latest_table.c.idx == main_table.c.idx
        join_main_clause &= latest_table.c.branch == main_table.c.branch
        join_main_clause &= latest_table.c.revision == main_table.c.revision
        from_obj = latest_table.join(main_table, onclause=join_main_clause)
        join_optional_clause = main_table.c.idx == optional_table.c.idx
        join_optional_clause &= main_table.c.branch == optional_table.c.branch
        join_optional_clause &= (
            main_table.c.revision == optional_table.c.revision
        )
        from_obj = from_obj.outerjoin(
            optional_table, onclause=join_optional_clause
        )
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
        join_optional_clause = main_table.c.idx == optional_table.c.idx
        join_optional_clause &= main_table.c.branch == optional_table.c.branch
        join_optional_clause &= (
            main_table.c.revision == optional_table.c.revision
        )
        from_obj = main_table.outerjoin(
            optional_table, onclause=join_optional_clause
        )
        return_cols = []
        for key in joined_column_keys:
            for col in from_obj.c:
                if col.key == key:
                    return_cols.append(col)
                    break
        return from_obj, return_cols

    def get_common_keys(self, *_):
        """Return the names of the main and changeset table fields."""
        self._connect()
        self.results = _col_keys(self.tables["main"])
        return self.results

    def get_known_keys(self):
        """Return all known field names."""
        common_keys = self.get_common_keys()
        meta_table = self.tables[META_TABLE_NAME]
        self._connect()
        where = meta_table.c.name == "known_keys"
        select = al.sql.select([meta_table.c.value], whereclause=where)
        self.results = [r[0] for r in self._execute(select)]  # De-proxy.
        if any(self.results):
            self.results = self.results[0].split()  # shlex.split garbles it.
        self.results = common_keys + self.results
        self.results.sort()
        return self.results

    def get_optional_keys(self, *_):
        """Return the names of the optional fields."""
        self._connect()
        select = al.sql.select([self.tables["optional"].c.name])
        self._execute(select.distinct())
        self.results = [r.pop() for r in self.results]
        self.results.sort()
        return self.results

    def get_query_operators(self, *_):
        """Return the query operators."""
        return self.QUERY_OPERATORS

    def query(self, filters, all_revs=0):
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

        If all_revs == 1, matching deleted suites and old revisions
        of suites will be returned.
        If all_revs == 0, they won't be.

        """
        self._connect()
        all_revs = int(all_revs)  # so distinguish 0 or 1 below, else both True
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
            from_obj = self._get_join_and_columns()[0]
        item_list = []
        current_expr = []
        for filter_tuple in filters:
            for i, entry in enumerate(filter_tuple):
                if (
                    (entry in ["and", "or"] and i == 0)
                    or entry
                    and (
                        all([e == "(" for e in entry])
                        or all([e == ")" for e in entry])
                    )
                ):
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
            for j in range(level + 1):
                levels[j][-1].append(item)
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
                            for _ in range(down_items.count(items[1])):
                                ind = down_items.index(items[1], ind + 1) - 1
                                if down_items[ind : ind + len(items)] == items:
                                    del down_items[ind : ind + len(items)]
                                    down_items.insert(ind, expr)
                                    substituted = True
                                    break
                            if substituted:
                                break
        return False

    def _get_sql_expr(self, expr_tuple, from_obj):
        """Return database expression."""
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

    @staticmethod
    def _get_expr_join(expr_items):
        """Return an operator-precedence left-to-right logical join."""
        items = list(expr_items)
        while "and" in items:
            i = items.index("and")
            expr = al.and_(items[i - 1], items[i + 1])
            del items[i - 1 : i + 2]
            items.insert(i - 1, expr)
        while "or" in items:
            i = items.index("or")
            expr = al.or_(items[i - 1], items[i + 1])
            del items[i - 1 : i + 2]
            items.insert(i - 1, expr)
        return items.pop()

    def search(self, s, all_revs=0):
        """Search database for rows with values matching the words in "s".

        If all_revs == 1, matching deleted suites and old revisions
        of suites will be returned.
        If all_revs == 0, they won't be.

        """
        self._connect()
        all_revs = int(all_revs)  # so distinguish 0 or 1 below, else both True
        if all_revs:
            from_obj, cols = self._get_hist_join_and_columns()
        else:
            from_obj, cols = self._get_join_and_columns()
        where = None
        if not isinstance(s, list):
            s = [s]
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

    @staticmethod
    def _rows_to_maps(rows, cols):
        """Translate each result row into a map with optional values."""
        results = []
        col_keys = [c.key for c in cols]
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
            if name is None:
                continue
            value = row[col_keys.index("value")]
            if name.endswith("-list") and value is not None:
                value = value.split()
            results[-1].update({name: value})
        return results
