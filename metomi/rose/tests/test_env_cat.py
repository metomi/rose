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
"""Tests for metomi.rose.env_cat

Incomplete coverage - scenarios covered:
- If input file not found log sensible error.
- Output file is written.
"""

import pytest

from types import SimpleNamespace

from metomi.rose.env_cat import rose_env_cat


def test_output_to_file(tmp_path, monkeypatch):
    """It writes output to file.
    """
    inputfile = tmp_path / 'inputfile'
    outputfile = tmp_path / 'outputfile'
    inputfile.write_text(r'Hello ${WORLD}')
    monkeypatch.setenv('WORLD', 'Jupiter')

    opts = SimpleNamespace(
        match_mode=None,
        output_file=str(outputfile),
        unbound=None
    )
    args = [str(inputfile)]

    assert rose_env_cat(args, opts) is None
    assert outputfile.read_text() == 'Hello Jupiter'


@pytest.mark.parametrize('debug_mode', (True, False))
def test_no_input_file_handled(tmp_path, debug_mode, capsys):
    """It raises a nice error when there is no input file.
    """
    inputfile = tmp_path / 'inputfile'
    opts = SimpleNamespace(
        match_mode=None,
        output_file=None,
        unbound=None,
        debug_mode=debug_mode
    )
    args = [str(inputfile)]
    if debug_mode:
        with pytest.raises(FileNotFoundError):
            rose_env_cat(args, opts)
    else:
        rose_env_cat(args, opts)
        assert 'No such file or directory' in capsys.readouterr().err
