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
"""Test the CLI for Rose Date
"""
import pytest

from metomi.rose.date_cli import _handle_old_offsets


param = pytest.param


@pytest.mark.parametrize(
    'args, expect, warn',
    [
        param(
            'rose-date --offset=1d',
            'rose-date --offset=P1DT0H0M0S',
            '[WARN] This offset syntax 1d is deprecated: Using P1DT0H0M0S\n',
            id='it parses --offset=<offset>'
        ),
        param(
            'rose-date --offset 1d',
            'rose-date --offset P1DT0H0M0S',
            '[WARN] This offset syntax 1d is deprecated: Using P1DT0H0M0S\n',
            id='it parses --offset <offset>'
        ),
        param(
            'rose-date -s 1d',
            'rose-date -s P1DT0H0M0S',
            '[WARN] This offset syntax 1d is deprecated: Using P1DT0H0M0S\n',
            id='it parses -s <offset>'
        ),
        param(
            'rose-date -s 1d --offset=1w',
            'rose-date -s P1DT0H0M0S --offset=P7DT0H0M0S',
            '[WARN] This offset syntax 1d is deprecated: Using P1DT0H0M0S\n'
            '[WARN] This offset syntax 1w is deprecated: Using P7DT0H0M0S\n',
            id='it parses multiple args'
        ),
        param(
            'rose-date -s P1D',
            'rose-date -s P1D',
            False,
            id='it doesn\'t do anything to modern offsets'
        ),
        param(
            'rose-date -s P1W',
            'rose-date -s P1W',
            False,
            id='it doesn\'t do anything to modern offsets'
        ),
        param(
            'rose-date 2000 -s -1d',
            'rose-date 2000 -s -P1DT0H0M0S',
            '[WARN] This offset syntax -1d is deprecated: Using -P1DT0H0M0S\n',
            id='it copes with negative offsets'
        ),
        param(
            'rose-date 2000 -s=-1d',
            'rose-date 2000 -s=-P1DT0H0M0S',
            '[WARN] This offset syntax -1d is deprecated: Using -P1DT0H0M0S\n',
            id='it copes with negative offsets'
        ),
        param(
            'rose-date 2000 -s=',
            'rose-date 2000 -s=',
            False,
            id='it copes with unfilled opts'
        ),
        param(
            'rose-date 2000 -s= 1d',
            'rose-date 2000 -s P1DT0H0M0S',
            '[WARN] This offset syntax 1d is deprecated: Using P1DT0H0M0S\n',
            id=r'it copes with -s=\s\d[wdhms]'
        ),
    ]
)
def test__handle_old_offsets(args, expect, warn, capsys):
    """Only test _handle_old_offsets logic, not upgrade_offset.
    """
    assert _handle_old_offsets(args.split(' ')) == expect.split(' ')
    if warn:
        assert capsys.readouterr().out == warn
