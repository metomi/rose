# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
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
"""
import os
import sys


def main():
    """Check file exists and print some info:

    1. Octal protection bits.
    2. Last modified time.
    3. Filesize.
    4. Path, which has been checked.
    """
    path, str_blob, str_tree = sys.argv[1:]
    if os.path.isdir(path):
        print(str_tree)
        os.chdir(path)
        for dirpath, dirnames, filenames in os.walk(path):
            good_dirnames = []
            for dirname in dirnames:
                if not dirname.startswith("."):
                    good_dirnames.append(dirname)
                    name = os.path.join(dirpath, dirname)
                    print(("-", "-", "-", name))
            dirnames[:] = good_dirnames
            for filename in filenames:
                if filename.startswith("."):
                    continue
                name = os.path.join(dirpath, filename)
                stat = os.stat(name)
                print((oct(stat.st_mode), stat.st_mtime, stat.st_size, name))
    elif os.path.isfile(path):
        print(str_blob)
        stat = os.stat(path)
        print(oct(stat.st_mode), stat.st_mtime, stat.st_size, path)


if __name__ == '__main__':
    main()
