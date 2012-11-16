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
from hashlib import md5
import os

class FileSystemLocHandler(object):
    """Handler of file system locations."""

    def __init__(self, manager):
        self.manager = manager

    def can_pull(self, loc):
        return os.path.exists(loc.name)

    def parse(self, loc):
        """Set loc.scheme, loc.loc_type, loc.paths."""
        loc.scheme = "fs"
        if os.path.isfile(loc.name):
            loc.loc_type = loc.TYPE_BLOB
            m = md5()
            m.update(open(loc.name).read())
            loc.add_path(loc.BLOB, m.hexdigest())
        else: # os.path.isdir(loc.name):
            loc.loc_type = loc.TYPE_TREE
            for dirpath, dirnames, filenames in os.walk(loc.name):
                for dirname in dirnames:
                    loc.add_path(os.path.join(dirpath, dirname))
                for filename in filenames:
                    name = os.path.join(dirpath, filename)
                    m = md5()
                    m.update(open(name).read())
                    loc.add_path(name, m.hexdigest())

    def pull(self, loc, work_dir):
        """If loc is in the file system, sets loc.cache to loc.name.

        Otherwise, raise an OSError.

        """
        if not os.path.exists(loc.name):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), loc.name)
        loc.cache = loc.name
