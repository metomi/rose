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


def get_checksum(name, checksum_func=None):
    """
    Calculate "checksum" of content in a file or directory called "name".

    By default, the "checksum" is MD5 checksum. This can modified by "impl",
    which should be a function with the interface:

        checksum_str = checksum_func(source_str)

    Return a list of 2-element tuples. Each tuple represents a path in "name"
    and the checksum of that path. If the path is a directory, the checksum is
    None.
    
    If "name" is a file, it returns a one-element list with a ("", checksum)
    tuple.

    If "name" does not exist, raise OSError.

    """
    if not os.path.exists(name):
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), name)

    if checksum_func is None:
        checksum_func = get_checksum_func()
    name = os.path.normpath(name)
    path_and_checksum_list = []
    if os.path.isfile(name):
        checksum = checksum_func(name)
        path_and_checksum_list.append(("", checksum))
    else: # if os.path.isdir(path):
        path_and_checksum_list = []
        for dirpath, dirnames, filenames in os.walk(name):
            path = dirpath[len(name) + 1:]
            path_and_checksum_list.append((path, None))
            for filename in filenames:
                filepath = os.path.join(path, filename)
                checksum = checksum_func(os.path.join(dirpath, filename))
                path_and_checksum_list.append((filepath, checksum))
    return path_and_checksum_list


def get_checksum_func(key=None):
    """Return a checksum function suitable for get_checksum.
    
    If key=="md5" or not specified, return function to do MD5 checksum.
    if key=="mtime+size", return function generate a string that contains the
    source name, its modified time and its size.
    Otherwise, raise KeyError(key).

    """
    if not key or key == "md5sum":
        return _md5_hexdigest
    elif key == "mtime+size":
        return _mtime_and_size
    else:
        raise KeyError(key)


def _md5_hexdigest(source):
    """Load content of source into an md5 object, and return its hexdigest."""
    m = md5()
    s = open(source)
    f_bsize = os.statvfs(source).f_bsize
    while True:
        bytes = s.read(f_bsize)
        if not bytes:
            break
        m.update(bytes)
    s.close()
    return m.hexdigest()


def _mtime_and_size(source):
    """Return a string containing the name, its modified time and its size."""
    stat = os.stat(os.path.realpath(source))
    return os.pathsep.join(["source=" + source,
                            "mtime=" + str(stat.st_mtime),
                            "size=" + str(stat.st_size)])
