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
"""Unit tests for Rose app-run"""

from io import StringIO
import pytest
from types import SimpleNamespace

from metomi.rose.app_run import AppRunner
from metomi.rose.config import ConfigLoader


@pytest.fixture
def get_conf_tree():
    """Give me a config tree"""
    def _inner():
        raw_config = (
            '[command]\n'
            'default = foo\n'
        )
        return SimpleNamespace(node=ConfigLoader().load(StringIO(raw_config)))
    return _inner


def test___prep_shadow_pythonpath(monkeypatch, get_conf_tree):
    """Copies _PYTHONPATH to PYTHONPATH: If not _PYTHONPATH does nothing.

    Checks that setting _PYTHONPATH sets PYTHONPATH for this rose-app conf.
    """
    # Both variables are set; _PYTHONPATH overwrites PYTHONPATH
    conf_tree = get_conf_tree()
    monkeypatch.setenv('_PYTHONPATH', 'bar')
    monkeypatch.setenv('PYTHONPATH', 'foo')
    AppRunner._prep_shadow_pythonpath(conf_tree)
    assert conf_tree.node.value['env'].value['PYTHONPATH'].value == 'bar'

    # _PYTHONPATH unset; Nothing happens
    conf_tree = get_conf_tree()
    monkeypatch.delenv('_PYTHONPATH')
    AppRunner._prep_shadow_pythonpath(conf_tree)
    assert 'env' not in conf_tree.node.value
