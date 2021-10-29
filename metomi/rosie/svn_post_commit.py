#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
"""A post-commit hook on a Rosie Subversion repository.

Update the Rosie discovery database on changes to info file.
Notify owner and users on access-list on changes to trunk.

"""


from difflib import unified_diff
from email.mime.text import MIMEText
from io import StringIO
import os
import re
import shlex
from smtplib import SMTP
import socket
import sys
from time import mktime, strptime
import traceback

import sqlalchemy as al

import metomi.rose.config
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rose.scheme_handler import SchemeHandlersManager
from metomi.rosie.db import (
    LATEST_TABLE_NAME,
    MAIN_TABLE_NAME,
    META_TABLE_NAME,
    OPTIONAL_TABLE_NAME,
)
from metomi.rosie.svn_hook import InfoFileError, RosieSvnHook


class RosieWriteDAO:

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


class RosieSvnPostCommitHook(RosieSvnHook):

    """A post-commit hook on a Rosie Subversion repository.

    Update the Rosie discovery database on changes to info file.
    Notify owner and users on access-list on trunk changes.

    """

    KNOWN_KEYS_FILE_PATH = "R/O/S/I/E/trunk/rosie-keys"
    REC_COPY_INFO = re.compile(r"\A\s+\(from\s(\S+):r(\d+)\)\s*\Z")

    def __init__(self, event_handler=None, popen=None):
        super(RosieSvnPostCommitHook, self).__init__(event_handler, popen)
        self.usertools_manager = SchemeHandlersManager(
            [self.path], "rosie.usertools", ["get_emails"]
        )

    def run(self, repos, revision, no_notification=False):
        """Update database with changes in a changeset."""
        # Lookup prefix of repos
        # Do nothing if prefix is not registered
        conf = ResourceLocator.default().get_conf()
        metomi.rosie.db_node = conf.get(["rosie-db"], no_ignore=True)
        for key, node in metomi.rosie.db_node.value.items():
            if node.is_ignored() or not key.startswith("repos."):
                continue
            if os.path.realpath(repos) == os.path.realpath(node.value):
                prefix = key[len("repos.") :]
                break
        else:
            return
        # Locate Rosie DB of repos
        dao = RosieWriteDAO(conf.get_value(["rosie-db", "db." + prefix]))

        # Date-time of this commit
        os.environ["TZ"] = "UTC"
        date_time = self._svnlook("date", "-r", revision, repos)
        date, dtime, _ = date_time.split(None, 2)
        date = mktime(strptime(" ".join([date, dtime, "UTC"]), self.DATE_FMT))
        # Detail of changes
        changeset_attribs = {
            "repos": repos,
            "revision": revision,
            "prefix": prefix,
            "author": self._svnlook("author", "-r", revision, repos).strip(),
            "date": date,
        }
        branch_attribs_dict = self._get_suite_branch_changes(repos, revision)

        for key, branch_attribs in sorted(branch_attribs_dict.items()):
            # Update known keys in suite info database meta table
            if branch_attribs["has_changed_known_keys_file"]:
                self._update_known_keys(dao, changeset_attribs)
            # Update suite info database
            self._update_info_db(dao, changeset_attribs, branch_attribs)
            # Notification on trunk changes
            # Notification on owner and access-list changes
            if not no_notification and branch_attribs["branch"] == "trunk":
                self._notify_trunk_changes(changeset_attribs, branch_attribs)

    def _get_suite_branch_changes(self, repos, revision):
        """Retrieve changed statuses."""
        branch_attribs_dict = {}
        changed_lines = self._svnlook(
            "changed", "--copy-info", "-r", revision, repos
        ).splitlines(True)
        while changed_lines:
            changed_line = changed_lines.pop(0)
            # A normal status changed_line
            # Column 1: content status
            # Column 2: tree status
            # Column 3: "+" sign denotes a copy history
            # Column 5+: path
            path = changed_line[4:].strip()
            path_status = changed_line[0]
            if path.endswith("/") and path_status == "_":
                # Ignore property change on a directory
                continue
            # Path must be (under) a valid suite branch, including the special
            # ROSIE suite
            names = path.split("/", self.LEN_ID + 1)
            if len(names) < self.LEN_ID + 1 or (
                "".join(names[0 : self.LEN_ID]) != "ROSIE"
                and any(
                    name not in id_chars
                    for name, id_chars in zip(names, self.ID_CHARS_LIST)
                )
            ):
                continue
            sid = "".join(names[0 : self.LEN_ID])
            branch = names[self.LEN_ID]
            if branch:
                # Change to a path in a suite branch
                if (sid, branch) not in branch_attribs_dict:
                    branch_attribs_dict[
                        (sid, branch)
                    ] = self._new_suite_branch_change(sid, branch)
                branch_attribs = branch_attribs_dict[(sid, branch)]
                try:
                    tail = names[self.LEN_ID + 1]
                except IndexError:
                    tail = None
                if tail == self.INFO_FILE:
                    # Suite info file change
                    if branch_attribs["info"] is None:
                        try:
                            branch_attribs["info"] = self._load_info(
                                repos,
                                sid,
                                branch,
                                revision=revision,
                                allow_popen_err=True,
                            )
                        except metomi.rose.config.ConfigSyntaxError as exc:
                            raise InfoFileError(InfoFileError.VALUE, exc)
                    if path_status != self.ST_ADDED:
                        branch_attribs["old_info"] = self._load_info(
                            repos,
                            sid,
                            branch,
                            revision=int(revision) - 1,
                            allow_popen_err=True,
                        )
                        if (
                            branch_attribs["old_info"]
                            != branch_attribs["info"]
                            and branch_attribs["status"] != self.ST_ADDED
                        ):
                            branch_attribs[
                                "status_info_file"
                            ] = self.ST_MODIFIED
                elif tail:
                    # ROSIE meta known keys file change
                    if path == self.KNOWN_KEYS_FILE_PATH:
                        branch_attribs["has_changed_known_keys_file"] = True
                    if branch_attribs["status"] == self.ST_EMPTY:
                        branch_attribs["status"] = self.ST_MODIFIED
                elif path_status in [self.ST_ADDED, self.ST_DELETED]:
                    # Branch add/delete
                    branch_attribs["status"] = path_status
                # Load suite info and old info regardless
                if branch_attribs["info"] is None:
                    try:
                        branch_attribs["info"] = self._load_info(
                            repos,
                            sid,
                            branch,
                            revision=revision,
                            allow_popen_err=True,
                        )
                    except metomi.rose.config.ConfigSyntaxError as exc:
                        raise InfoFileError(InfoFileError.VALUE, exc)
                    # Note: if (allowed) popen err, no DB entry will be created
                if (
                    branch_attribs["old_info"] is None
                    and branch_attribs["status"] == self.ST_DELETED
                ):
                    branch_attribs["old_info"] = self._load_info(
                        repos,
                        sid,
                        branch,
                        revision=int(revision) - 1,
                        allow_popen_err=True,
                    )
                # Append changed lines, so they can be used for notification
                branch_attribs["changed_lines"].append(changed_line)
                if changed_line[2] == "+":
                    changed_line_2 = changed_lines.pop(0)
                    branch_attribs["changed_lines"].append(changed_line_2)
                    if path_status != self.ST_ADDED or tail:
                        continue
                    # A line containing the copy info for a branch
                    # Column 5+ looks like: (from PATH:rREV)
                    match = self.REC_COPY_INFO.match(changed_line_2)
                    if match:
                        from_path, from_rev = match.groups()
                        branch_attribs_dict[(sid, branch)].update(
                            {"from_path": from_path, "from_rev": from_rev}
                        )
            elif path_status == self.ST_DELETED:
                # The suite has been deleted
                tree_out = self._svnlook(
                    "tree", "-r", str(int(revision) - 1), "-N", repos, path
                )
                # Include all branches of the suite in the deletion info
                for tree_line in tree_out.splitlines()[1:]:
                    del_branch = tree_line.strip().rstrip("/")
                    branch_attribs_dict[
                        (sid, del_branch)
                    ] = self._new_suite_branch_change(
                        sid,
                        del_branch,
                        {
                            "old_info": self._load_info(
                                repos,
                                sid,
                                del_branch,
                                revision=int(revision) - 1,
                                allow_popen_err=True,
                            ),
                            "status": self.ST_DELETED,
                            "status_info_file": self.ST_EMPTY,
                            "changed_lines": [
                                "D   %s/%s/" % (path, del_branch)
                            ],
                        },
                    )
        return branch_attribs_dict

    def _new_suite_branch_change(self, sid, branch, attribs=None):
        """Return a dict to represent a suite branch change."""
        branch_attribs = {
            "sid": sid,
            "branch": branch,
            "from_path": None,
            "from_rev": None,
            "has_changed_known_keys_file": False,
            "old_info": None,
            "info": None,
            "status": self.ST_EMPTY,
            "status_info_file": self.ST_EMPTY,
            "changed_lines": [],
        }
        if attribs:
            branch_attribs.update(attribs)
        return branch_attribs

    def _notify_trunk_changes(self, changeset_attribs, branch_attribs):
        """Email owner and/or access-list users on changes to trunk."""

        # Notify only if users' email addresses can be determined
        conf = ResourceLocator.default().get_conf()
        user_tool_name = conf.get_value(["rosa-svn", "user-tool"])
        if not user_tool_name:
            return
        notify_who_str = conf.get_value(
            ["rosa-svn", "notify-who-on-trunk-commit"], ""
        )
        if not notify_who_str.strip():
            return
        notify_who = shlex.split(notify_who_str)

        # Build the message text
        info_file_path = "%s/trunk/%s" % (
            "/".join(branch_attribs["sid"]),
            self.INFO_FILE,
        )
        text = ""
        for changed_line in branch_attribs["changed_lines"]:
            text += changed_line
            # For suite info file change, add diff as well
            if (
                changed_line[4:].strip() == info_file_path
                and branch_attribs["status_info_file"] == self.ST_MODIFIED
            ):
                old_strio = StringIO()
                metomi.rose.config.dump(branch_attribs["old_info"], old_strio)
                new_strio = StringIO()
                metomi.rose.config.dump(branch_attribs["info"], new_strio)
                for diff_line in unified_diff(
                    old_strio.getvalue().splitlines(True),
                    new_strio.getvalue().splitlines(True),
                    "@%d" % (int(changeset_attribs["revision"]) - 1),
                    "@%d" % (int(changeset_attribs["revision"])),
                ):
                    text += " " * 4 + diff_line

        # Determine who to notify
        users = set()
        for key in ["old_info", "info"]:
            if branch_attribs[key] is not None:
                info_conf = branch_attribs[key]
                if "owner" in notify_who:
                    users.add(info_conf.get_value(["owner"]))
                if "access-list" in notify_who:
                    users.update(
                        info_conf.get_value(["access-list"], "").split()
                    )
        users.discard("*")

        # Determine email addresses
        user_tool = self.usertools_manager.get_handler(user_tool_name)
        if "author" in notify_who:
            users.add(changeset_attribs["author"])
        else:
            users.discard(changeset_attribs["author"])
        emails = sorted(user_tool.get_emails(users))
        if not emails:
            return

        # Send notification
        msg = MIMEText(text)
        msg.set_charset("utf-8")
        msg["From"] = conf.get_value(
            ["rosa-svn", "notification-from"],
            "notications@" + socket.getfqdn(),
        )
        msg["To"] = ", ".join(emails)
        msg["Subject"] = "%s-%s/trunk@%d" % (
            changeset_attribs["prefix"],
            branch_attribs["sid"],
            int(changeset_attribs["revision"]),
        )
        smtp_host = conf.get_value(
            ["rosa-svn", "smtp-host"], default="localhost"
        )
        smtp = SMTP(smtp_host)
        smtp.sendmail(msg["From"], emails, msg.as_string())
        smtp.quit()

    def _update_info_db(self, dao, changeset_attribs, branch_attribs):
        """Update the suite info database for a suite branch."""
        idx = "{0}-{1}".format(
            changeset_attribs["prefix"], branch_attribs["sid"]
        )
        vc_attrs = {
            "idx": idx,
            "branch": branch_attribs["branch"],
            "revision": changeset_attribs["revision"],
        }
        # Latest table
        try:
            dao.delete(
                LATEST_TABLE_NAME,
                idx=vc_attrs["idx"],
                branch=vc_attrs["branch"],
            )
        except al.exc.IntegrityError:
            # idx and branch were just added: there is no previous record.
            pass
        if branch_attribs["status"] != self.ST_DELETED:
            dao.insert(LATEST_TABLE_NAME, **vc_attrs)
        # N.B. deleted suite branch only has old info
        info_key = "info"
        if branch_attribs["status"] == self.ST_DELETED:
            info_key = "old_info"
        if branch_attribs[info_key] is None:
            return
        # Main table
        cols = dict(vc_attrs)
        cols.update(
            {
                "author": changeset_attribs["author"],
                "date": changeset_attribs["date"],
            }
        )
        for name in ["owner", "project", "title"]:
            cols[name] = branch_attribs[info_key].get_value([name], "null")
        if branch_attribs["from_path"] and vc_attrs["branch"] == "trunk":
            from_names = branch_attribs["from_path"].split("/")[: self.LEN_ID]
            cols["from_idx"] = "{0}-{1}".format(
                changeset_attribs["prefix"], "".join(from_names)
            )
        cols["status"] = (
            branch_attribs["status"] + branch_attribs["status_info_file"]
        )
        dao.insert(MAIN_TABLE_NAME, **cols)
        # Optional table
        for name in branch_attribs[info_key].value:
            if name in ["owner", "project", "title"]:
                continue
            value = branch_attribs[info_key].get_value([name])
            if value is None:  # setting may have ignore flag (!)
                continue
            cols = dict(vc_attrs)
            cols.update({"name": name, "value": value})
            dao.insert(OPTIONAL_TABLE_NAME, **cols)

    def _update_known_keys(self, dao, changeset_attribs):
        """Update the known_keys in the meta table."""
        repos = changeset_attribs["repos"]
        revision = changeset_attribs["revision"]
        keys_str = self._svnlook(
            "cat", "-r", revision, repos, self.KNOWN_KEYS_FILE_PATH
        )
        keys_str = " ".join(shlex.split(keys_str))
        if keys_str:
            try:
                dao.insert(META_TABLE_NAME, name="known_keys", value=keys_str)
            except al.exc.IntegrityError:
                dao.update(
                    META_TABLE_NAME,
                    ("name",),
                    name="known_keys",
                    value=keys_str,
                )


def main():
    """Implement "rosa svn-post-commit"."""
    opt_parser = RoseOptionParser()
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    hook = RosieSvnPostCommitHook(report)
    try:
        repos, revision = args[0:2]
        hook.run(repos, revision)
    except Exception as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
