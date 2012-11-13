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

import os
import errno

class FileSystemLocHandler(object):
    """Handler of file system locations."""

    def __init__(self, manager):
        self.manager = manager

    def can_handle(self, loc):
        return True

    def parse(self, loc):
        pass # TODO

    def pull(self, loc):
        """If loc is in the file system, sets loc.cache to loc.name.

        Otherwise, raise an OSError.

        """
        if not os.path.exists(loc.name):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), loc.name)
        if os.path.isdir(loc.name):
            loc.loc_type = loc.TYPE_TREE
        elif os.path.isfile(loc.name):
            loc.loc_type = loc.TYPE_BLOB
        loc.cache = loc.name
