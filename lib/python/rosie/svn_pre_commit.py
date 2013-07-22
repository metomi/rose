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
"""A pre-commit hook on a Rosie Subversion repository.

Ensure that commits conform to the rules of Rosie.

"""


import os
import re
from rose.config import ConfigLoader
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
import shlex
import subprocess
import sys
import tempfile
import traceback


class BadChangesError(Exception):

    """An error raised when there are bad changes in a commit transaction."""

    def __str__(self):
        ret = ""
        for status, path in sorted(self.args[0]):
            ret += "PERMISSION DENIED: %-4s%s\n" % (status, path)
        return ret


class RosieSvnPreCommitHook(object):

    """A pre-commit hook on a Rosie Subversion repository.

    Ensure that commits conform to the rules of Rosie.

    """

    RE_ID_NAMES = [r"[a-z]", r"[a-z]", r"\d", r"\d", r"\d"]
    LEN_ID = len(RE_ID_NAMES)
    TRUNK_INFO_FILE = "trunk/rose-suite.info"
    TRUNK_KNOWN_KEYS_FILE = "trunk/rosie-keys"
    ST_ADD = "A"
    ST_DELETE = "D"
    ST_UPDATE = "U"

    def __init__(self, event_handler=None, popen=None):
        if event_handler is None:
            event_handler = Reporter()
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(self.event_handler)
        self.popen = popen

    def get_access_info(self, repos, path_head, txn=None):
        """Return the owner and the access list of a suite (path_head)."""
        opt_txn = []
        if txn is not None:
            opt_txn = ["-t", txn]
        f = tempfile.TemporaryFile()
        f.write(self.svnlook("cat", repos, path_head + self.TRUNK_INFO_FILE,
                             *opt_txn))
        f.seek(0)
        node = ConfigLoader()(f)
        f.close()
        owner = node.get_value(["owner"])
        access_list = node.get_value(["access-list"], "").split()
        access_list.sort()
        return owner, access_list

    def svnlook(self, *args):
        """Return the standard output from "svnlook"."""
        command = ["svnlook"] + list(args)
        return self.popen(*command, stderr=sys.stderr)[0]

    def run(self, repos, txn):
        """Apply the rule engine on transaction "txn" to repository "repos"."""
        changes = set() # set([(status, path), ...])
        for line in self.svnlook("changed", "-t", txn, repos).splitlines():
            status, path = line.split(None, 1)
            changes.add((status, path))
        bad_changes = set()
        author = None
        super_users = None
        access_info_map = {} # {path-id: (owner, access-list), ...}
        txn_access_info_map = {}
        for status, path in sorted(changes):
            names = path.split("/", self.LEN_ID + 1)
            if not names[-1]:
                names.pop()

            # Directories above the suites must match the ID patterns
            is_meta_suite = False
            if len(names) >= self.LEN_ID and names[0:self.LEN_ID] == "ROSIE":
                is_meta_suite = True
            else:
                is_bad = False
                for name, pattern in zip(names, self.RE_ID_NAMES):
                    if not re.compile(r"\A" + pattern + r"\Z").match(name):
                        is_bad = True
                        break
                if is_bad:
                    bad_changes.add((status, path))
                    continue

            # Can only add directories at levels above the suites
            if len(names) < self.LEN_ID:
                if status[0] != self.ST_ADD:
                    bad_changes.add((status, path))
                continue

            # No need to check non-trunk changes
            if len(names) > self.LEN_ID and names[self.LEN_ID] != "trunk":
                continue

            # New suite should have an info file
            if status[0] == self.ST_ADD and len(names) == self.LEN_ID:
                if (self.ST_ADD, path + "trunk/") not in changes:
                    bad_changes.add((status, path))
                path_trunk_info_file = path + self.TRUNK_INFO_FILE
                if ((self.ST_ADD, path_trunk_info_file) not in changes and
                    (self.ST_UPDATE, path_trunk_info_file) not in changes):
                    bad_changes.add((status, path))
                continue

            # The rest are trunk changes in a suite
            path_head = "/".join(names[0:self.LEN_ID]) + "/"
            path_tail = path[len(path_head):]
            
            # For meta suite, make sure keys in keys file can be parsed
            if is_meta_suite and path_tail == self.TRUNK_KNOWN_KEYS_FILE:
                out = self.svnlook("cat", "-t", txn, repos, path)
                try:
                    shlex.split(out)
                except ValueError:
                    bad_changes.add((status, path))
                    continue

            # New suite trunk information file must have an owner
            if status == self.ST_ADD and path_tail == self.TRUNK_INFO_FILE:
                owner, access_list = self.get_access_info(repos, path_head,
                                                          txn)
                if not owner:
                    bad_changes.add((status, path))
                continue

            # New suite trunk: ignore the rest
            if (self.ST_ADD, path_head + "trunk/") in changes:
                continue

            # Can only remove trunk information file with suite
            if status == self.ST_DELETE and path_tail == self.TRUNK_INFO_FILE:
                if (self.ST_DELETE, path_head) not in changes:
                    bad_changes.add((status, path))
                continue

            # Can only remove trunk with suite
            if status == self.ST_DELETE and path_tail == "trunk/":
                if (self.ST_DELETE, path_head) not in changes:
                    bad_changes.add((status, path))
                continue

            # See whether author has permission to make changes
            if author is None:
                author = self.svnlook("author", "-t", txn, repos).strip()
            if super_users is None:
                conf = ResourceLocator.default().get_conf()
                keys = ["rosa-svn-pre-commit", "super-users"]
                super_users = conf.get_value(keys, "").split()
            if not access_info_map.has_key(path_head):
                access_info = self.get_access_info(repos, path_head)
                access_info_map[path_head] = access_info
            owner, access_list = access_info_map[path_head]
            admin_users = super_users + [owner]

            # Only admin users can remove the suite
            if author not in admin_users and not path_tail:
                bad_changes.add((status, path))
                continue

            # Admin users and those in access list can modify everything in trunk
            # apart from specific entries in the trunk info file
            if "*" in access_list or author in admin_users + access_list:
                if path_tail != self.TRUNK_INFO_FILE:
                    continue
            else:
                bad_changes.add((status, path))

            # The owner must not be deleted
            if not txn_access_info_map.has_key(path_head):
                txn_access_info = self.get_access_info(repos, path_head, txn)
                txn_access_info_map[path_head] = txn_access_info
            txn_owner, txn_access_list = txn_access_info_map[path_head]
            if not txn_owner:
                bad_changes.add((status, path))
                continue

            # Only the admin users can change owner and access list
            if author in admin_users:
                continue
            if owner != txn_owner or access_list != txn_access_list:
                bad_changes.add((status, path))
                continue

        if bad_changes:
            raise BadChangesError(bad_changes)

    __call__ = run


if __name__ == "__main__":
    opt_parser = RoseOptionParser()
    opts, args = opt_parser.parse_args()
    repos, txn = args
    report = Reporter(opts.verbosity - opts.quietness)
    hook = RosieSvnPreCommitHook(report)
    try:
        hook(repos, txn)
    except Exception as e:
        report(e)
        if opts.debug_mode:
            traceback.print_exc(e)
        sys.exit(1)
