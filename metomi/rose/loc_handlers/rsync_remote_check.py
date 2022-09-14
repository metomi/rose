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
"""
A script for running over ssh to establish whether a file
is available for installation.

This is a Python file but we read it and pass it to stdin
to avoid reliance on remote platforms having rose installed.

Warning:
    This script will not necessarily be run in the Rose Python environment.
    It should not have any dependencies outside of the stdlib and should be
    compatible with as wide a range of Python versions as possible.

"""
from __future__ import print_function
import os
import sys


def main(path, str_blob, str_tree):
    """Check file exists and print some info:

    Args:
        path (str): Path to a file or directory.
        str_blob: return this string if path is a file. Default='blob'
        str_tree: return this string if path is a directory. Default='tree'

    Prints:
        1. Access Mode information.
        2. Last modified time.
        3. Filesize.
        4. Path, which has been checked.
    """
    if os.path.isdir(path):
        print(str_tree)
        os.chdir(path)
        for dirpath, dirnames, filenames in os.walk(path):
            good_dirnames = []
            for dirname in dirnames:
                if not dirname.startswith("."):
                    good_dirnames.append(dirname)
                    name = os.path.join(dirpath, dirname)
                    print("-", "-", "-", name)
            dirnames[:] = good_dirnames
            for filename in filenames:
                if filename.startswith("."):
                    continue
                name = os.path.join(dirpath, filename)
                stat = os.stat(name)
                print(stat.st_mode, stat.st_mtime, stat.st_size, name)
    elif os.path.isfile(path):
        print(str_blob)
        stat = os.stat(path)
        print(stat.st_mode, stat.st_mtime, stat.st_size, path)


if __name__ == '__main__':
    main(*sys.argv[1:])
