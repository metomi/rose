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
"""Test scheme_handler.py"""

from pathlib import Path

from metomi.rose.scheme_handler import SchemeHandlersManager


def test_get_rose_path():
    """It shares a path with this test."""
    rose_path = SchemeHandlersManager.get_rose_path()
    control = Path(__file__).parent.parent.parent.parent
    assert rose_path == str(control)
