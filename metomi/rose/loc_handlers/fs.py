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
"""A handler of file system locations."""

import errno
import os

from metomi.rose.checksum import get_checksum


class FileSystemLocHandler:

    """Handler of file system locations."""

    SCHEME = "fs"

    def __init__(self, manager):
        self.manager = manager

    @classmethod
    def can_pull(cls, loc):
        """Return true if loc.name exists in the file system."""
        return os.path.exists(loc.name)

    @classmethod
    def parse(cls, loc, _):
        """Set loc.scheme, loc.loc_type, loc.paths."""
        loc.scheme = "fs"
        name = os.path.expanduser(loc.name)
        if not os.path.exists(name):
            raise ValueError(loc.name)
        paths_and_checksums = get_checksum(name)
        for path, checksum, access_mode in paths_and_checksums:
            loc.add_path(path, checksum, access_mode)
        if len(paths_and_checksums) == 1 and paths_and_checksums[0][0] == "":
            loc.loc_type = loc.TYPE_BLOB
        else:
            loc.loc_type = loc.TYPE_TREE

    @classmethod
    async def pull(cls, loc, _):
        """If loc is in the file system, sets loc.cache to loc.name.

        Otherwise, raise an OSError.

        """
        name = os.path.expanduser(loc.name)
        if not os.path.exists(name):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), name)
        loc.cache = name
