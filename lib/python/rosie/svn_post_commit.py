#!/usr/bin/env python
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
"""A post-commit hook on a Rosie Subversion repository.

Update the Rosie discovery database on changes.

"""


import os
import re
import rose.config
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
import shlex
import sqlalchemy as al
import sys
import tempfile
import time
import traceback


class RosieWriteDAO(object):

    """Data Access Object for writing to the Rosie web service database."""

    T_CHANGESET = "changeset"
    T_MAIN = "main"
    T_OPTIONAL = "optional"
    T_MODIFIED = "modified"
    T_META = "meta"

    def __init__(self, db_url):
        engine = al.create_engine(db_url)
        self.connection = engine.connect()
        self.metadata = al.MetaData(engine)
        self.tables = {}

    def _get_table(self, key):
        if not self.tables.has_key(key):
            self.tables[key] = al.Table(key, self.metadata, autoload=True)
        return self.tables[key]

    def delete(self, key, **kwargs):
        """Perform a delete on table key, using kwargs to select rows."""
        table = self._get_table(key)
        where = None
        for col, value in kwargs.items():
            if where is None:
                where = table.c[col] == value
            else:
                where &= table.c[col] == value
        statement = table.delete(whereclause=where)
        self.connection.execute(statement)

    def insert(self, key, **kwargs):
        """Insert values kwargs into table key."""
        statement = self._get_table(key).insert().values(**kwargs)
        self.connection.execute(statement)

    def update(self, key, where_match_cols, **kwargs):
        """Update the table 'key' with kwargs, using where_match_cols."""
        table = self._get_table(key)
        where = None
        for col in where_match_cols:
            if where is None:
                where = table.c[col] == kwargs[col]
            else:
                where &= table.c[col] == kwargs[col]
        statement = table.update(whereclause=where).values(**kwargs)
        self.connection.execute(statement)


class RosieSvnPostCommitHook(object):

    """A post-commit hook on a Rosie Subversion repository.

    Update the Rosie discovery database on changes.

    """

    DATE_FMT = "%Y-%m-%d %H:%M:%S %Z"
    RE_ID_NAMES = [r"[a-z]", r"[a-z]", r"\d", r"\d", r"\d"]
    LEN_ID = len(RE_ID_NAMES)
    INFO_FILE = "rose-suite.info"
    KNOWN_KEYS_FILE = "rosie-keys"
    REC_COPY_INFO = re.compile("^\s+\(from\s([^\s]+)\)$")
    ST_ADDED = "A"
    ST_DELETED = "D"
    ST_MODIFIED = "M"

    def __init__(self, event_handler=None, popen=None):
        if event_handler is None:
            event_handler = Reporter()
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(self.event_handler)
        self.popen = popen

    def _svnlook(self, *args):
        """Return the standard output from "svnlook"."""
        command = ["svnlook"] + list(args)
        return self.popen(*command)[0]


    def _check_path_is_sid(self, path):
        """Return whether the path contains a suffix-id."""
        names = path.split("/")
        if len(names) < self.LEN_ID + 1:
            return False
        if "".join(names)[:self.LEN_ID] == "ROSIE":
            return True
        for name, pattern in zip(names, self.RE_ID_NAMES):
            if not re.compile(r"\A" + pattern + r"\Z").match(name):
                return False
        return True


    def run(self, repos, rev, *args):
        """Update database with changes in a changeset."""
        conf = ResourceLocator.default().get_conf()
        rosie_db_node = conf.get(["rosie-db"], no_ignore=True)
        for key, node in rosie_db_node.value.items():
            if node.is_ignored() or not key.startswith("repos."):
                continue
            if os.path.realpath(repos) == os.path.realpath(node.value):
                prefix = key[len("repos."):]
                break
        else:
            return
        dao = RosieWriteDAO(conf.get_value(["rosie-db", "db." + prefix]))
        statuses = {}
        copies = {}
        author = self._svnlook("author", "-r", rev, repos).strip()
        os.environ["TZ"] = "UTC"
        d, t, junk = self._svnlook("date", "-r", rev, repos).split(None, 2)
        date = time.mktime(time.strptime(" ".join([d, t, "UTC"]),
                           self.DATE_FMT))

        path_copies = {}
        path_num = -1
        copy_changes = self._svnlook("changed", "--copy-info", "-r", rev,
                                     repos)
        for i, change in enumerate(copy_changes.splitlines()):
            copy_match = self.REC_COPY_INFO.match(change)
            if copy_match:
                path_copies[path_num] = copy_match.groups()[0]
            else:
                path_num += 1
        changes = self._svnlook("changed", "-r", rev, repos)
        for i, line in enumerate(changes.splitlines()):
            is_new_copied_branch = False
            status, path = line.split(None, 1)
            if not self._check_path_is_sid(path):
                continue
            names = path.split("/")
            sid = "".join(names[0:self.LEN_ID])
            idx = prefix + "-" + sid
            branch = names[self.LEN_ID]
            if branch:
                statuses.setdefault((rev, idx, branch), {0: " ", 1: " "})
            branch_path = "/".join(sid) + "/" + branch
            info_file_path = branch_path + "/" + self.INFO_FILE
            if not branch and status[0] == self.ST_DELETED:
                out = self._svnlook("tree", "-r", str(int(rev) - 1), "-N",
                                    repos, path)
                for line in out.splitlines()[1:]:
                    del_branch = line.strip().rstrip("/")
                    statuses.setdefault((rev, idx, del_branch),
                                        {0: " ", 1: " "})
                    statuses[(rev, idx, del_branch)][0] = self.ST_DELETED
            if i in path_copies and self._check_path_is_sid(path_copies[i]):
                copy_names = path_copies[i].split("/")
                copy_sid = "".join(copy_names[:self.LEN_ID])
                if copy_sid != sid:
                    copies.setdefault((rev, idx, branch), copy_sid)
                elif branch_path + "/" == path:
                    is_new_copied_branch = True
            if (sid == "ROSIE" and branch == "trunk" and
                path == branch_path + "/" + self.KNOWN_KEYS_FILE):
                keys_str = self._svnlook("cat", "-r", rev, repos, path)
                keys_str = " ".join(shlex.split(keys_str))
                if keys_str:
                    try:
                        dao.insert(dao.T_META, name="known_keys",
                                   value=keys_str)
                    except al.exc.IntegrityError:
                        dao.update(dao.T_META, ("name",), name="known_keys",
                                   value=keys_str)

            if path.rstrip("/") == branch_path:
                if status[0] == self.ST_DELETED:
                    statuses[(rev, idx, branch)][0] = self.ST_DELETED
                    continue
                if status[0] == self.ST_ADDED:
                    statuses[(rev, idx, branch)][0] = self.ST_ADDED
            if (len(path) > len(branch_path) and path != info_file_path and
                statuses[(rev, idx, branch)][0].isspace()):
                statuses[(rev, idx, branch)][0] = self.ST_MODIFIED
            if (status[0] == self.ST_DELETED or
                path != info_file_path and not is_new_copied_branch):
                continue

            f = tempfile.TemporaryFile()
            f.write(self._svnlook("cat", "-r", rev, repos, info_file_path))
            f.seek(0)
            config = rose.config.load(f)
            f.close()

            is_added = False
            if status[0] == self.ST_ADDED:
                old_config = rose.config.ConfigNode()
                is_added = True
            else:
                f = tempfile.TemporaryFile()
                try:
                    f.write(self._svnlook("cat", "-r", str(int(rev) -1), repos,
                                    info_file_path))
                except RosePopenError:
                    is_added = True
                f.seek(0)
                old_config = rose.config.load(f)
                f.close()

            items = {"revision": rev, "idx": idx, "branch":branch}
            for key, node in old_config.value.items():
                if node.is_ignored():
                    continue
                new_node = config.get([key], no_ignore=True)
                if new_node is None:
                    statuses[(rev, idx, branch)].update({1: self.ST_MODIFIED})
                    dao.insert(dao.T_MODIFIED, name=key, old_value=node.value,
                               new_value=None, **items)
                    if key not in ["owner", "project", "title"]:
                        dao.delete(dao.T_OPTIONAL, idx=idx, branch=branch,
                                   name=key)
                elif node.value != new_node.value:
                    statuses[(rev, idx, branch)].update({1: self.ST_MODIFIED})
                    dao.insert(dao.T_MODIFIED, name=key, old_value=node.value,
                               new_value=new_node.value, **items)
                    if key not in ["owner", "project", "title"]:
                        dao.update(dao.T_OPTIONAL, ("idx", "branch", "name"),
                                   idx=idx, branch=branch, name=key,
                                   value=new_node.value)
            for key, node in config.value.items():
                if node.is_ignored():
                    continue
                old_node = old_config.get([key], no_ignore=True)
                if old_node is None:
                    statuses[(rev, idx, branch)].update({1: self.ST_MODIFIED})
                    dao.insert(dao.T_MODIFIED, name=key, old_value=None,
                               new_value=node.value, **items)
                    if key not in ["owner", "project", "title"]:
                        dao.insert(dao.T_OPTIONAL, idx=idx, branch=branch,
                                   name=key, value=node.value)

            items = {}
            for key in ["owner", "project", "title"]:
                items[key] = config.get([key], no_ignore=True).value
            if is_added:
                try:
                    dao.insert(dao.T_MAIN, idx=idx, branch=branch, **items)
                except al.exc.IntegrityError:
                    dao.update(dao.T_MAIN, ("idx", "branch"), idx=idx,
                               branch=branch, **items)
            else:
                dao.update(dao.T_MAIN, ("idx", "branch"), idx=idx,
                           branch=branch, **items)

        # End loop over changes, update statuses.
        for key, value in statuses.items():
            rev, idx, branch = key
            copy_idx = None
            copy_sid = copies.get(key)
            if copy_sid is not None:
                copy_idx = prefix + "-" + copy_sid
            status = ""
            if value[0] == self.ST_ADDED:
                value[1] = " "
            for num in sorted(value.keys()):
                status += value[num]
            if not (status.isspace() and copy_idx is None):
                dao.insert(dao.T_CHANGESET, revision=rev, idx=idx,
                           branch=branch, author=author, date=date,
                           status=status, from_idx=copy_idx)

    __call__ = run


if __name__ == "__main__":
    opt_parser = RoseOptionParser()
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    hook = RosieSvnPostCommitHook(report)
    try:
        hook(*args)
    except Exception as e:
        report(e)
        if opts.debug_mode:
            traceback.print_exc(e)
        sys.exit(1)
