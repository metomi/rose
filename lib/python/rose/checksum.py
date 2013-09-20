# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
"""Calculates the MD5 checksum for a file or files in a directory."""


import errno
from hashlib import md5
import os


def get_checksum(name):
    """
    Calculate the MD5 checksum of content in a file or directory called "name".

    Return a list of 2-element tuples. Each tuple represents a path in "name"
    and the checksum of that path. If the path is a directory, the checksum is
    None.
    
    If "name" is a file, it returns a one-element list with a ("", checksum)
    tuple.

    If "name" does not exist, raise OSError.

    """
    if not os.path.exists(name):
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), name)

    name = os.path.normpath(name)
    path_and_checksum_list = []
    if os.path.isfile(name):
        m = _load(name)
        path_and_checksum_list.append(("", m.hexdigest()))
    else: # if os.path.isdir(path):
        path_and_checksum_list = []
        for dirpath, dirnames, filenames in os.walk(name):
            path = dirpath[len(name) + 1:]
            path_and_checksum_list.append((path, None))
            for filename in filenames:
                m = _load(os.path.join(dirpath, filename))
                filepath = os.path.join(path, filename)
                path_and_checksum_list.append((filepath, m.hexdigest()))
    return path_and_checksum_list

def _load(source):
    """Load content of source into an md5 object, and return it."""
    m = md5()
    s = open(source)
    f_bsize = os.statvfs(source).f_bsize
    while True:
        bytes = s.read(f_bsize)
        if not bytes:
            break
        m.update(bytes)
    s.close()
    return m
