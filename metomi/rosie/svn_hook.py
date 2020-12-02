#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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

import os
import sys
import metomi.rose
from metomi.rose.popen import RosePopener, RosePopenError
from metomi.rose.reporter import Reporter
from tempfile import TemporaryFile


class RosieSvnHook(object):
    """A parent class for hooks on a Rosie Subversion repository."""

    DATE_FMT = "%Y-%m-%d %H:%M:%S %Z"
    ID_CHARS_LIST = ["abcdefghijklmnopqrstuvwxyz"] * 2 + ["0123456789"] * 3
    LEN_ID = len(ID_CHARS_LIST)
    TRUNK = "trunk"
    INFO_FILE = "rose-suite.info"
    TRUNK_INFO_FILE = "trunk/rose-suite.info"
    ST_ADDED = "A"
    ST_DELETED = "D"
    ST_MODIFIED = "M"
    ST_UPDATED = "U"
    ST_EMPTY = " "

    def __init__(self, event_handler=None, popen=None):
        if event_handler is None:
            event_handler = Reporter()
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(self.event_handler)
        self.popen = popen
        self.path = os.path.dirname(
            os.path.dirname(sys.modules["metomi.rosie"].__file__))

    def _svnlook(self, *args):
        """Return the standard output from "svnlook"."""
        command = ["svnlook", *args]
        return self.popen(*command)[0].decode()

    def _load_info(self, repos, sid, branch=None, revision=None,
                   transaction=None, allow_popen_err=False):
        """Load info file from branch_path in repos @revision.

        Returns a ConfigNode for the "rose-suite.info" of a suite at a
        particular revision or transaction.

        Args:
            repos (str): The path of the repository.
            sid (str): The Rosie suite unique identifier, e.g. "ay327".
            branch (str): The branch that the info file is under.
            revision (int, str): A commit revision number. Cannot be used with
                transaction.
            transaction (str): A commit transaction identifer. Cannot be used
                with revision.
            allow_popen_err (bool): If True, return None if a RosePopenError
                occurs during svnlook command.
        """
        if branch is None:
            branch = self.TRUNK
        commit_opts = []
        # TODO: warn or raise if both supplied?
        if transaction is not None:
            commit_opts = ["-t", transaction]
        if revision is not None:
            commit_opts = ["-r", str(revision)]
        info_file_path = "%s/%s/%s" % ("/".join(sid), branch, self.INFO_FILE)
        t_handle = TemporaryFile()
        try:
            t_handle.write(
                self._svnlook(
                    "cat", repos, info_file_path, *commit_opts).encode()
            )
        except RosePopenError as err:
            if allow_popen_err:
                return None
            raise err
        t_handle.seek(0)
        config_node = metomi.rose.config.load(t_handle)
        t_handle.close()
        return config_node
