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
from io import StringIO
import json
from textwrap import dedent

from metomi.rose.host_select_client import main as host_select


def test_empty(monkeypatch, capsys):
    """It should not return any results for an empty request."""
    monkeypatch.setattr(
        'sys.stdin',
        StringIO(
            dedent(
                '''
        **start**
        []
        **end**
        '''
            )
        ),
    )
    host_select()
    captured = capsys.readouterr()
    assert captured.out == '[]\n'
    assert captured.err == ''


def test_stdin_pollution(monkeypatch, capsys):
    """Any junk before or after the start/end markers should be ignored

    Note this can come from shell profile scripts.
    """
    monkeypatch.setattr(
        'sys.stdin',
        StringIO(
            dedent(
                '''
        hello
        *&^%$**start**
        []
        **end***&^%$E
        world
        '''
            )
        ),
    )
    host_select()
    captured = capsys.readouterr()
    assert captured.out == '[]\n'
    assert captured.err == ''


def test_request(monkeypatch, capsys):
    """Test a simple request."""
    monkeypatch.setattr(
        'sys.stdin',
        StringIO(
            dedent(
                '''
        **start**
        [["virtual_memory"]]
        **end**
        '''
            )
        ),
    )
    host_select()
    captured = capsys.readouterr()
    assert captured.out
    assert captured.err == ''

    results = json.loads(captured.out)
    assert len(results) == 1
    result = results[0]
    for key in ('active', 'available', 'free'):
        assert key in result
