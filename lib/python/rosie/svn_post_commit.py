#!/usr/bin/env python
#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------
"""A post-commit hook on a Rosie Subversion repository.

Update the Rosie discovery database on changes.

"""


from email.mime.text import MIMEText
import os
import re
import rose.config
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Reporter
from rose.resource import ResourceLocator
from rose.scheme_handler import SchemeHandlersManager
from rosie.db import (
    LATEST_TABLE_NAME, MAIN_TABLE_NAME, META_TABLE_NAME, OPTIONAL_TABLE_NAME)
import shlex
from smtplib import SMTP
import socket
import sqlalchemy as al
import sys
import tempfile
import time
import traceback


class RosieWriteDAO(object):

    """Data Access Object for writing to the Rosie web service database."""

    def __init__(self, db_url):
        engine = al.create_engine(db_url)
        self.connection = engine.connect()
        self.metadata = al.MetaData(engine)
        self.tables = {}

    def _get_table(self, key):
        """(Create and) return table of a given key."""
        if key not in self.tables:
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
    ST_UPDATED = "U"
    TRUNK = "trunk"

    def __init__(self, event_handler=None, popen=None):
        if event_handler is None:
            event_handler = Reporter()
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(self.event_handler)
        self.popen = popen
        path = os.path.dirname(os.path.dirname(sys.modules["rosie"].__file__))
        self.usertools_manager = SchemeHandlersManager(
            [path], "rosie.usertools", ["get_emails"])

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

    def run(self, repos, revision):
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
        idx_branch_rev_info = {}
        author = self._svnlook("author", "-r", revision, repos).strip()
        os.environ["TZ"] = "UTC"
        date_time_str = self._svnlook("date", "-r", revision, repos)
        date, dtime, _ = date_time_str.split(None, 2)
        date = time.mktime(time.strptime(" ".join([date, dtime, "UTC"]),
                           self.DATE_FMT))

        # Retrieve copied information on the suite-idx-level.
        path_copies = {}
        path_num = -1
        copy_changes = self._svnlook("changed", "--copy-info", "-r", revision,
                                     repos)
        for i, change in enumerate(copy_changes.splitlines()):
            copy_match = self.REC_COPY_INFO.match(change)
            if copy_match:
                path_copies[path_num] = copy_match.groups()[0]
            else:
                path_num += 1

        changes = self._svnlook("changed", "-r", revision, repos)
        suite_statuses = {}
        path_statuses = []
        for i, line in enumerate(changes.splitlines()):
            path_status, path = line.rsplit(None, 1)
            if not self._check_path_is_sid(path):
                # The path must contain a full suite id (e.g. a/a/0/0/1/).
                continue
            path_statuses.append((path_status, path, i))

        # Loop through a stack of statuses, paths, and copy info pointers.
        configs = {}
        while path_statuses:
            path_status, path, path_num = path_statuses.pop(0)
            names = path.split("/")
            sid = "".join(names[0:self.LEN_ID])
            idx = prefix + "-" + sid
            branch = names[self.LEN_ID]
            branch_path = "/".join(sid) + "/" + branch
            info_file_path = branch_path + "/" + self.INFO_FILE
            if not branch and path_status[0] == self.ST_DELETED:
                # The suite has been deleted at the a/a/0/0/1/ level.
                out = self._svnlook("tree", "-r", str(int(revision) - 1),
                                    "-N", repos, path)
                # Include all branches of the suite in the deletion info.
                for line in out.splitlines()[1:]:
                    del_branch = line.strip().rstrip("/")
                    path_statuses.append((path_status, path.rstrip("/") +
                                          "/" + del_branch, None))
            if (sid == "ROSIE" and branch == self.TRUNK and
                    path == branch_path + "/" + self.KNOWN_KEYS_FILE):
                # The known keys in the special R/O/S/I/E/ suite have changed.
                keys_str = self._svnlook("cat", "-r", revision, repos, path)
                keys_str = " ".join(shlex.split(keys_str))
                if keys_str:
                    try:
                        dao.insert(META_TABLE_NAME, name="known_keys",
                                   value=keys_str)
                    except al.exc.IntegrityError:
                        dao.update(META_TABLE_NAME, ("name",),
                                   name="known_keys", value=keys_str)
            status_0 = " "
            from_idx = None
            if (path_num in path_copies and
                    self._check_path_is_sid(path_copies[path_num])):
                copy_names = path_copies[path_num].split("/")
                copy_sid = "".join(copy_names[:self.LEN_ID])
                if copy_sid != sid and branch:
                    # This has been copied from a different suite.
                    from_idx = prefix + "-" + copy_sid

            # Figure out our status information.
            if path.rstrip("/") == branch_path:
                if path_status[0] == self.ST_DELETED:
                    status_0 = self.ST_DELETED
                if path_status[0] == self.ST_ADDED:
                    status_0 = self.ST_ADDED
            if (len(path.rstrip("/")) > len(branch_path) and
                    path != info_file_path and status_0.isspace()):
                status_0 = self.ST_MODIFIED
            suite_statuses.setdefault((idx, branch, revision),
                                      {0: status_0, 1: " "})
            status_info = suite_statuses[(idx, branch, revision)]
            if not branch:
                continue
            if path.rstrip("/") not in [branch_path, info_file_path]:
                if branch_path not in [i[1] for i in path_statuses]:
                    # Make sure the branch gets noticed.
                    path_statuses.append((self.ST_UPDATED, branch_path, None))
                continue

            # Start populating the idx+branch+revision info for this suite.
            suite_info = idx_branch_rev_info.setdefault(
                (idx, branch, revision), {})
            suite_info["author"] = author
            suite_info["date"] = date
            suite_info.setdefault("from_idx", None)
            if from_idx is not None:
                suite_info["from_idx"] = from_idx
            suite_info.setdefault("owner", "")
            suite_info.setdefault("project", "")
            suite_info.setdefault("title", "")
            suite_info.setdefault("optional", {})

            if (idx, branch, revision) not in configs:
                new_config = self._get_config_node(
                    repos, info_file_path, revision)
                old_config = self._get_config_node(
                    repos, info_file_path, str(int(revision) - 1))
                configs[(idx, branch, revision)] = (new_config, old_config)

                if branch == self.TRUNK:
                    self._notify_access_changes(
                        "%s/%s@%s" % (idx, branch, revision),
                        suite_info["author"],
                        old_config,
                        new_config)

            new_config, old_config = configs[(idx, branch, revision)]

            if new_config is None and old_config is None:
                # A technically-invalid commit (likely to be historical).
                idx_branch_rev_info.pop((idx, branch, revision))
                continue

            if new_config is None and status_info[0] == self.ST_DELETED:
                new_config = old_config
            if old_config is None and status_info[0] == self.ST_ADDED:
                old_config = new_config

            if self._get_configs_differ(old_config, new_config):
                status_info[1] = self.ST_MODIFIED

            for key, node in new_config.value.items():
                if node.is_ignored():
                    continue
                if key in ["owner", "project", "title"]:
                    suite_info[key] = node.value
                else:
                    suite_info["optional"][key] = node.value

        # Now loop over all idx+branch+revision suite groups.
        for suite_id, suite_info in idx_branch_rev_info.items():
            idx, branch, revision = suite_id
            status = suite_statuses.get((idx, branch, revision),
                                        {0: " ", 1: " "})
            suite_info["status"] = (status[0] +
                                    status[1])
            optional = suite_info.pop("optional")
            for key, value in optional.items():
                dao.insert(OPTIONAL_TABLE_NAME, idx=idx, branch=branch,
                           revision=revision, name=key, value=value)
            dao.insert(MAIN_TABLE_NAME, idx=idx, branch=branch,
                       revision=revision, **suite_info)
            try:
                dao.delete(LATEST_TABLE_NAME, idx=idx, branch=branch)
            except al.exc.IntegrityError:
                # idx and branch were just added: there is no previous record.
                pass
            if suite_info["status"][0] != self.ST_DELETED:
                dao.insert(LATEST_TABLE_NAME, idx=idx, branch=branch,
                           revision=revision)

    __call__ = run

    def _get_config_node(self, repos, info_file_path, revision):
        """Load configuration file from info_file_path in repos @revision."""
        t_handle = tempfile.TemporaryFile()
        try:
            t_handle.write(
                self._svnlook("cat", "-r", revision, repos, info_file_path))
        except RosePopenError:
            return None
        t_handle.seek(0)
        config = rose.config.load(t_handle)
        t_handle.close()
        return config

    @classmethod
    def _get_configs_differ(cls, old_config, new_config):
        """Return True if old_config differs from new_config."""
        for keys1, node1 in old_config.walk(no_ignore=True):
            node2 = new_config.get(keys1, no_ignore=True)
            if type(node1) != type(node2):
                return True
            if (not isinstance(node1.value, dict) and
                    node1.value != node2.value):
                return True
            if node1.comments != node2.comments:
                return True
        for keys2, node2 in new_config.walk(no_ignore=True):
            node1 = old_config.get(keys2, no_ignore=True)
            if node1 is None:
                return True
        return False

    def _notify_access_changes(self, full_id, author, old_config, new_config):
        """Email owner and/or access-list users on changes."""
        conf = ResourceLocator.default().get_conf()
        user_tool_name = conf.get_value(["rosa-svn", "user-tool"])
        if not user_tool_name:
            return

        users = set()
        if old_config is None:
            new_access_str = new_config.get_value(["access-list"], "")
            changes = {
                ("owner", "+"): new_config.get_value(["owner"]),
                ("access-list", "+"): new_access_str,
            }
            users.update(new_access_str.split())

        elif new_config is None:
            old_owner = old_config.get_value(["owner"])
            old_access_str = old_config.get_value(["access-list"], "")
            changes = {
                ("owner", "-"): old_owner,
                ("access-list", "-"): old_access_str,
            }
            users.add(old_owner)
            users.update(old_access_str.split())

        else:
            changes = {}
            old_owner = old_config.get_value(["owner"])
            new_owner = new_config.get_value(["owner"])
            if old_owner != new_owner:
                changes[("owner", "-")] = old_owner
                changes[("owner", "+")] = new_owner
                users.add(old_owner)
                users.add(new_owner)
            old_access_str = old_config.get_value(["access-list"], "")
            new_access_str = new_config.get_value(["access-list"], "")
            old_access_set = set(old_access_str.split())
            new_access_set = set(new_access_str.split())
            if old_access_set != new_access_set:
                changes[("access-list", "-")] = old_access_str
                changes[("access-list", "+")] = new_access_str
                users.update(old_access_set ^ new_access_set)

        users.discard("*")
        users.discard(author)
        if not users or users == set([author]):
            return

        user_tool = self.usertools_manager.get_handler(user_tool_name)
        users.add(author)
        emails = sorted(user_tool.get_emails(users))
        from_email = conf.get_value(["rosa-svn", "notification-from"],
                                    "notications@" + socket.getfqdn())

        text = ""
        for key, status in [
                ("owner", "-"),
                ("owner", "+"),
                ("access-list", "-"),
                ("access-list", "+")]:
            if (key, status) in changes:
                text += "%s %s=%s\n" % (status, key, changes[(key, status)])
        msg = MIMEText(text)
        msg.set_charset("utf-8")
        msg["From"] = from_email
        msg["To"] = ", ".join(emails)
        msg["Subject"] = "[%s] owner/access-list change" % full_id
        smtp_host = conf.get_value(["rosa-svn", "smtp-host"],
                                   default="localhost")
        smtp = SMTP(smtp_host)
        smtp.sendmail(msg["From"], emails, msg.as_string())
        smtp.quit()


def main():
    """Implement "rosa svn-post-commit"."""
    opt_parser = RoseOptionParser()
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    hook = RosieSvnPostCommitHook(report)
    try:
        repos, revision = args[0:2]
        hook(repos, revision)
    except Exception as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
