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


import shutil
import pytest
from secrets import token_hex

from metomi.rose.config_processors.fileinstall import (
    PullableLocHandlersManager,
)
from metomi.rose.loc_handlers.git import GitLocHandler


require_git = pytest.mark.skipif(
    shutil.which('git') is None,
    reason="git is not installed"
)


@require_git
def test_init_ok():
    handler = GitLocHandler(PullableLocHandlersManager())
    assert len(handler.git_version) > 1
    assert all(isinstance(i, int) for i in handler.git_version)


def test_init_no_git(monkeypatch: pytest.MonkeyPatch):
    """Test the handler doesn't throw a tantrum if git is not installed."""
    monkeypatch.setattr(GitLocHandler, 'GIT', token_hex(8))
    handler = GitLocHandler(PullableLocHandlersManager())
    assert handler.git_version is None
