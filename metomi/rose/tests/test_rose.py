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
"""Test metomi/rose/rose.py
"""

import os
import sys

from metomi.rose.rose import pythonpath_manip


def test_pythonpath_manip(monkeypatch):
    """pythonpath_manip removes items in PYTHONPATH from sys.path
    and adds items from ROSE_PYTHONPATH
    """
    # If PYTHONPATH is set...
    monkeypatch.setenv('PYTHONPATH', '/remove1:/remove2')
    monkeypatch.setattr('sys.path', ['/leave-alone', '/remove1', '/remove2'])
    pythonpath_manip()
    # ... we don't change PYTHONPATH
    assert os.environ['PYTHONPATH'] == '/remove1:/remove2'
    # ... but we do remove PYTHONPATH items from sys.path, and don't remove
    # items there not in PYTHONPATH
    assert sys.path == ['/leave-alone']

    # If ROSE_PYTHONPATH is set we retrieve its contents and
    # add them to the sys.path:
    monkeypatch.setenv('ROSE_PYTHONPATH', '/add1:/add2')
    pythonpath_manip()
    assert sys.path == ['/add1', '/add2', '/leave-alone']
