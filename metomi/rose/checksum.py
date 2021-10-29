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
"""Calculates the MD5 checksum for a file or files in a directory."""


import errno
import hashlib
import inspect
import os

from metomi.rose.resource import ResourceLocator

_DEFAULT_DEFAULT_KEY = "md5"
_DEFAULT_KEY = None
_HASH_LENGTHS = None

MTIME_AND_SIZE = "mtime+size"


def get_checksum(name, checksum_func=None):
    """
    Calculate "checksum" of content in a file or directory called "name".

    By default, the "checksum" is MD5 checksum. This can modified by "impl",
    which should be a function with the interface:

        checksum_str = checksum_func(source_str)

    Return a list of 3-element tuples. Each tuple represents a path in "name",
    the checksum, and the access mode. If the path is a directory, the checksum
    and the access mode will both be set to None.

    If "name" is a file, it returns a one-element list with a
    ("", checksum, mode) tuple.

    If "name" does not exist, raise OSError.

    """
    if not os.path.exists(name):
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), name)

    if checksum_func is None:
        checksum_func = get_checksum_func()
    path_and_checksum_list = []
    if os.path.isfile(name):
        checksum = checksum_func(name, "")
        path_and_checksum_list.append(
            ("", checksum, os.stat(os.path.realpath(name)).st_mode)
        )
    else:  # if os.path.isdir(path):
        name = os.path.normpath(name)
        path_and_checksum_list = []
        for dirpath, _, filenames in os.walk(name):
            path = dirpath[len(name) + 1 :]
            path_and_checksum_list.append((path, None, None))
            for filename in filenames:
                filepath = os.path.join(path, filename)
                source = os.path.join(name, filepath)
                checksum = checksum_func(source, name)
                mode = os.stat(os.path.realpath(source)).st_mode
                path_and_checksum_list.append((filepath, checksum, mode))
    return path_and_checksum_list


def get_checksum_func(algorithm=None):
    """Return a checksum function suitable for get_checksum.

    "algorithm" can be "mtime+size" or the name of a hash object from hashlib.
    If "algorithm" is not specified, return function to do MD5 checksum.

    Raise ValueError(algorithm) if "algorithm" is not a recognised hash object.

    """
    if not algorithm:
        global _DEFAULT_KEY
        if _DEFAULT_KEY is None:
            _DEFAULT_KEY = (
                ResourceLocator.default()
                .get_conf()
                .get_value(["checksum-method"], _DEFAULT_DEFAULT_KEY)
            )
        algorithm = _DEFAULT_KEY
    if algorithm == MTIME_AND_SIZE:
        return _mtime_and_size
    algorithm = algorithm.replace("sum", "")
    hashlib.new(algorithm)  # raise ValueError for a bad "algorithm" string
    return lambda source, *_: _get_hexdigest(algorithm, source)


def guess_checksum_algorithm(checksum):
    """Guess algorithm of "checksum".

    If "checksum" starts with "source=", returns MTIME_AND_SIZE.
    Otherwise, use length of checksum to guess algorithm, based on the built-in
    functions from hashlib.
    Return None if it fails to make a guess.

    """
    if checksum.startswith("source="):
        return MTIME_AND_SIZE
    global _HASH_LENGTHS
    if _HASH_LENGTHS is None:
        _HASH_LENGTHS = {}
        for algorithm, func in inspect.getmembers(hashlib, inspect.isbuiltin):
            try:
                _HASH_LENGTHS[len(func().hexdigest())] = algorithm
            except TypeError:
                pass
    return _HASH_LENGTHS.get(len(checksum))


def _get_hexdigest(algorithm, source):
    """Load content of source into an hash object, and return its hexdigest.

    Args:
        algorithm (str):
            Hash algorithm as namespaced in hashlib.
        source (str, file):
            The item to hexdigest, can be:

            * Path to a file (``str``).
            * Path to a directory (``str``).
            * A file object ``readable`` in bytes mode.

    """
    if hasattr(source, "read"):
        handle = source
    else:
        handle = open(source, 'rb')

    # Attempt to find the preferred file system block size
    try:
        f_bsize = os.statvfs(handle.name).f_bsize
    except (AttributeError, OSError):
        f_bsize = 4096

    # Spoon the data into a hashobj
    hashobj = hashlib.new(algorithm)
    while True:
        bytes_ = handle.read(f_bsize)
        if not bytes_:
            break
        hashobj.update(bytes_)
    handle.close()

    return hashobj.hexdigest()


def _mtime_and_size(source, root):
    """Return a string containing the name, its modified time and its size."""
    stat = os.stat(os.path.realpath(source))
    if root:
        source = os.path.relpath(source, root)
    return os.pathsep.join(
        [
            "source=" + source,
            "mtime=" + str(stat.st_mtime),
            "size=" + str(stat.st_size),
        ]
    )
