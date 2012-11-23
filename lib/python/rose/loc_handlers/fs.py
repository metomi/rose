# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
#-----------------------------------------------------------------------------
"""A handler of file system locations."""

import errno
from rose.checksum import get_checksum
import os

class FileSystemLocHandler(object):
    """Handler of file system locations."""

    def __init__(self, manager):
        self.manager = manager

    def can_pull(self, loc):
        return os.path.exists(loc.name)

    def parse(self, loc, config):
        """Set loc.scheme, loc.loc_type, loc.paths."""
        loc.scheme = "fs"
        name = os.path.expanduser(loc.name)
        paths_and_checksums = get_checksum(name)
        for path, checksum in paths_and_checksums:
            loc.add_path(path, checksum)
        if len(paths_and_checksums) == 1 and paths_and_checksums[0][0] == "":
            loc.loc_type = loc.TYPE_BLOB
        else:
            loc.loc_type = loc.TYPE_TREE

    def pull(self, loc, config):
        """If loc is in the file system, sets loc.cache to loc.name.

        Otherwise, raise an OSError.

        """
        name = os.path.expanduser(loc.name)
        if not os.path.exists(name):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), name)
        loc.cache = name
