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

from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory

from _pytest.monkeypatch import MonkeyPatch
import pytest


@pytest.fixture(scope='module')
def mod_monkeypatch():
    """A monkeypatch fixture with module-level scope."""
    patch = MonkeyPatch()
    yield patch
    patch.undo()


@pytest.fixture(scope='module')
def mod_tmp_path():
    """A tmp_path fixture with module-level scope."""
    path = Path(TemporaryDirectory().name)
    path.mkdir()
    yield path
    rmtree(path)
