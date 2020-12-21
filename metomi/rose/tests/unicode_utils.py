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

import io

from metomi.rose.unicode_utils import write_safely

TESTSTR = "Hello World"
TESTBYTES = b"Bonjour, Le Monde!"


def test_try_BufferedWriter_and_str(tmpdir):
    with open(tmpdir.join("test.txt"), "wb") as handle:
        assert isinstance(handle, io.BufferedWriter)
        write_safely(TESTSTR, handle)
    with open(tmpdir.join("test.txt"), "r") as handle:
        assert handle.read() == TESTSTR


def test_try_BufferedWriter_and_bytes(tmpdir):
    with open(tmpdir.join("test.txt"), "wb") as handle:
        assert isinstance(handle, io.BufferedWriter)
        write_safely(TESTBYTES, handle)
    with open(tmpdir.join("test.txt"), "rb") as handle:
        assert handle.read() == TESTBYTES


def test_try_StringIO_and_str():
    with io.StringIO() as handle:
        write_safely(TESTSTR, handle)
        assert isinstance(handle, io.StringIO)
        assert handle.getvalue() == TESTSTR


def test_try_StringIO_and_bytes():
    with io.StringIO() as handle:
        write_safely(TESTBYTES, handle)
        assert isinstance(handle, io.StringIO)
        assert handle.getvalue() == TESTBYTES.decode()
