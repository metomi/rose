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
"""A pre-commit hook on a Rosie Subversion repository.

Ensure that commits conform to the rules of Rosie.

"""


from fnmatch import fnmatch
import re
import shlex
import sys
import traceback

import metomi.rose
from metomi.rose.config import ConfigSyntaxError
from metomi.rose.macro import (
    add_meta_paths,
    get_reports_as_text,
    load_meta_config,
)
from metomi.rose.macros import DefaultValidators
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rose.scheme_handler import SchemeHandlersManager
from metomi.rosie.svn_hook import (
    BadChange,
    BadChanges,
    InfoFileError,
    RosieSvnHook,
)


class RosieSvnPreCommitHook(RosieSvnHook):

    """A pre-commit hook on a Rosie Subversion repository.

    Ensure that commits conform to the rules of Rosie.

    """

    IGNORES = "svnperms.conf"
    RE_ID_NAMES = [r"[Ra-z]", r"[Oa-z]", r"[S\d]", r"[I\d]", r"[E\d]"]
    TRUNK_KNOWN_KEYS_FILE = "trunk/rosie-keys"

    def __init__(self, event_handler=None, popen=None):
        super(RosieSvnPreCommitHook, self).__init__(event_handler, popen)
        self.usertools_manager = SchemeHandlersManager(
            [self.path], "rosie.usertools", ["verify_users"]
        )

    def _get_access_info(self, info_node):
        """Return (owner, access_list) from "info_node"."""
        owner = info_node.get_value(["owner"])
        access_list = info_node.get_value(["access-list"], "").split()
        access_list.sort()
        return owner, access_list

    def _verify_users(
        self, status, path, txn_owner, txn_access_list, bad_changes
    ):
        """Check txn_owner and txn_access_list.

        For any invalid users, append to bad_changes and return True.

        """
        # The owner and names in access list must be real users
        conf = ResourceLocator.default().get_conf()
        user_tool_name = conf.get_value(["rosa-svn", "user-tool"])
        if not user_tool_name:
            return False
        user_tool = self.usertools_manager.get_handler(user_tool_name)
        txn_users = set([txn_owner] + txn_access_list)
        txn_users.discard("*")
        bad_users = user_tool.verify_users(txn_users)
        for bad_user in bad_users:
            if txn_owner == bad_user:
                bad_change = BadChange(
                    status, path, BadChange.USER, "owner=" + bad_user
                )
                bad_changes.append(bad_change)
            if bad_user in txn_access_list:
                bad_change = BadChange(
                    status, path, BadChange.USER, "access-list=" + bad_user
                )
                bad_changes.append(bad_change)
        return bool(bad_users)

    def run(self, repos, txn):
        """Apply the rule engine on transaction "txn" to repository "repos"."""

        changes = set()  # set([(status, path), ...])
        for line in self._svnlook("changed", "-t", txn, repos).splitlines():
            status, path = line.split(None, 1)
            changes.add((status, path))
        bad_changes = []
        author = None
        super_users = None
        rev_info_map = {}
        txn_info_map = {}

        conf = ResourceLocator.default().get_conf()
        ignores_str = conf.get_value(["rosa-svn", "ignores"], self.IGNORES)
        ignores = shlex.split(ignores_str)

        for status, path in sorted(changes):
            if any(fnmatch(path, ignore) for ignore in ignores):
                continue

            names = path.split("/", self.LEN_ID + 1)
            tail = None
            if not names[-1]:
                tail = names.pop()

            # Directories above the suites must match the ID patterns
            is_bad = False
            for name, pattern in zip(names, self.RE_ID_NAMES):
                if not re.compile(r"\A" + pattern + r"\Z").match(name):
                    is_bad = True
                    break
            if is_bad:
                msg = "Directories above the suites must match the ID patterns"
                bad_changes.append(BadChange(status, path, content=msg))
                continue

            # At levels above the suites, can only add directories
            if len(names) < self.LEN_ID:
                if status[0] != self.ST_ADDED:
                    msg = (
                        "At levels above the suites, "
                        "can only add directories"
                    )
                    bad_changes.append(BadChange(status, path, content=msg))
                continue

            # Cannot have a file at the branch level
            if len(names) == self.LEN_ID + 1 and tail is None:
                msg = "Cannot have a file at the branch level"
                bad_changes.append(BadChange(status, path, content=msg))
                continue

            # New suite should have an info file
            if len(names) == self.LEN_ID and status == self.ST_ADDED:
                if (self.ST_ADDED, path + "trunk/") not in changes:
                    bad_changes.append(
                        BadChange(status, path, BadChange.NO_TRUNK)
                    )
                    continue
                path_trunk_info_file = path + self.TRUNK_INFO_FILE
                if (self.ST_ADDED, path_trunk_info_file) not in changes and (
                    self.ST_UPDATED,
                    path_trunk_info_file,
                ) not in changes:
                    bad_changes.append(
                        BadChange(status, path, BadChange.NO_INFO)
                    )
                continue

            sid = "".join(names[0 : self.LEN_ID])
            branch = names[self.LEN_ID] if len(names) > self.LEN_ID else None
            path_head = "/".join(sid) + "/"
            path_tail = path[len(path_head) :]
            is_meta_suite = sid == "ROSIE"

            if status != self.ST_DELETED:
                # Check info file
                if sid not in txn_info_map:
                    try:
                        txn_info_map[sid] = self._load_info(
                            repos, sid, branch=branch, transaction=txn
                        )
                        err = None
                    except ConfigSyntaxError as exc:
                        err = InfoFileError(InfoFileError.VALUE, exc)
                    except RosePopenError as exc:
                        err = InfoFileError(InfoFileError.NO_INFO, exc.stderr)
                    if err:
                        bad_changes.append(err)
                        txn_info_map[sid] = err
                        continue

                    # Suite must have an owner
                    txn_owner, txn_access_list = self._get_access_info(
                        txn_info_map[sid]
                    )
                    if not txn_owner:
                        bad_changes.append(
                            InfoFileError(InfoFileError.NO_OWNER)
                        )
                        continue

            # No need to check other non-trunk changes
            if branch and branch != "trunk":
                continue

            # For meta suite, make sure keys in keys file can be parsed
            if is_meta_suite and path_tail == self.TRUNK_KNOWN_KEYS_FILE:
                out = self._svnlook("cat", "-t", txn, repos, path)
                try:
                    shlex.split(out)
                except ValueError:
                    bad_changes.append(
                        BadChange(status, path, BadChange.VALUE)
                    )
                    continue

            # User IDs of owner and access list must be real
            if (
                status != self.ST_DELETED
                and path_tail == self.TRUNK_INFO_FILE
                and not isinstance(txn_info_map[sid], InfoFileError)
            ):
                txn_owner, txn_access_list = self._get_access_info(
                    txn_info_map[sid]
                )
                if self._verify_users(
                    status, path, txn_owner, txn_access_list, bad_changes
                ):
                    continue
                reports = DefaultValidators().validate(
                    txn_info_map[sid],
                    load_meta_config(
                        txn_info_map[sid],
                        config_type=metomi.rose.INFO_CONFIG_NAME,
                    ),
                )
                if reports:
                    reports_str = get_reports_as_text({None: reports}, path)
                    bad_changes.append(
                        BadChange(status, path, BadChange.VALUE, reports_str)
                    )
                    continue

            # Can only remove trunk information file with suite
            if status == self.ST_DELETED and path_tail == self.TRUNK_INFO_FILE:
                if (self.ST_DELETED, path_head) not in changes:
                    bad_changes.append(
                        BadChange(status, path, BadChange.NO_INFO)
                    )
                continue

            # Can only remove trunk with suite
            # (Don't allow replacing trunk with a copy from elsewhere, either)
            if status == self.ST_DELETED and path_tail == "trunk/":
                if (self.ST_DELETED, path_head) not in changes:
                    bad_changes.append(
                        BadChange(status, path, BadChange.NO_TRUNK)
                    )
                continue

            # New suite trunk: ignore the rest
            if (self.ST_ADDED, path_head + "trunk/") in changes:
                continue

            # See whether author has permission to make changes
            if author is None:
                author = self._svnlook("author", "-t", txn, repos).strip()
            if super_users is None:
                super_users = []
                for s_key in ["rosa-svn", "rosa-svn-pre-commit"]:
                    value = conf.get_value([s_key, "super-users"])
                    if value is not None:
                        super_users = shlex.split(value)
                        break
            if sid not in rev_info_map:
                rev_info_map[sid] = self._load_info(repos, sid, branch=branch)
            owner, access_list = self._get_access_info(rev_info_map[sid])
            admin_users = super_users + [owner]

            # Only admin users can remove the suite
            if author not in admin_users and not path_tail:
                msg = "Only the suite owner can remove the suite"
                bad_changes.append(BadChange(status, path, content=msg))
                continue

            # Admin users and those in access list can modify everything in
            # trunk apart from specific entries in the trunk info file
            if "*" in access_list or author in admin_users + access_list:
                if path_tail != self.TRUNK_INFO_FILE:
                    continue
            else:
                msg = "User not in access list"
                bad_changes.append(BadChange(status, path, content=msg))
                continue

            # Only the admin users can change owner and access list
            if owner == txn_owner and access_list == txn_access_list:
                continue
            if author not in admin_users:
                if owner != txn_owner:
                    bad_changes.append(
                        BadChange(
                            status, path, BadChange.PERM, "owner=" + txn_owner
                        )
                    )
                else:  # access list
                    bad_change = BadChange(
                        status,
                        path,
                        BadChange.PERM,
                        "access-list=" + " ".join(txn_access_list),
                    )
                    bad_changes.append(bad_change)
                continue

        if bad_changes:
            raise BadChanges(bad_changes)

    __call__ = run


def main():
    """Implement "rosa svn-pre-commit"."""
    add_meta_paths()
    opt_parser = RoseOptionParser()
    opts, args = opt_parser.parse_args()
    repos, txn = args
    report = Reporter(opts.verbosity - opts.quietness)
    hook = RosieSvnPreCommitHook(report)
    try:
        hook(repos, txn)
    except Exception as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
