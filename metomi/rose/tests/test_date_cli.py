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
import sys

from metomi.rose.date_cli import (
    _handle_old_offsets,
    _handle_old_datetimes,
    _main,
    main,
)


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
        assert capsys.readouterr().err == warn


@pytest.mark.parametrize(
    'args, expect, warn',
    [
        param(
            'rose-date 20200101T00',
            'rose-date 20200101T00',
            False,
            id='(control) it doesn\'t modify ISO8601 %Y%m%dT%H'
        ),
        param(
            'rose-date Wed_May_11_09:22:00_2022',
            'rose-date Wed_May_11_09:22:00_2022',
            False,
            id='(control) it doesn\'t modify ctime %a %b %d %H:%M:%S %Y'
        ),
        param(
            'rose-date 12150615T1400+05',
            'rose-date 12150615T1400+05',
            False,
            id='(control) it doesn\'t modify ISO8601 %Y%m%dT%H:%M:%S%Z'
        ),
        param(
            'rose-date 2020010100',
            'rose-date 20200101T00',
            (
                '[WARN] This datetime syntax 2020010100 is'
                ' deprecated. Use 20200101T00 instead\n'
            ),
            id='it replaces Cylc5 date'
        ),
        param(
            'rose-date --offset P1D 2020010100',
            'rose-date --offset P1D 20200101T00',
            (
                '[WARN] This datetime syntax 2020010100 is'
                ' deprecated. Use 20200101T00 instead\n'
            ),
            id='it replaces Cylc5 date, offset first'
        ),
        param(
            'rose-date 2020010100 --offset P1D',
            'rose-date 20200101T00 --offset P1D',
            (
                '[WARN] This datetime syntax 2020010100 is'
                ' deprecated. Use 20200101T00 instead\n'
            ),
            id='it replaces Cylc5 date, offset after'
        ),
        param(
            'rose-date --offset=P1D 2020010100',
            'rose-date --offset=P1D 20200101T00',
            (
                '[WARN] This datetime syntax 2020010100 is'
                ' deprecated. Use 20200101T00 instead\n'
            ),
            id='it replaces Cylc5 date, offset before uses ='
        ),
        param(
            'rose-date 2020010100 2021010100',
            'rose-date 20200101T00 20210101T00',
            (
                '[WARN] This datetime syntax 2020010100 is'
                ' deprecated. Use 20200101T00 instead\n'
            ),
            id='it replaces Cylc5 date with 2 date args'
        ),
        param(
            'rose-date Wed_May_11_09:22:00_UTC_2022',
            'rose-date 2022-05-11T09:22:00',
            (
                '[WARN] This datetime syntax Wed May 11 09:22:00 UTC 2022 is'
                ' deprecated. Use 2022-05-11T09:22:00 instead\n'
            ),
            id='it upgrades unix style times'
        ),

    ]
)
def test__handle_old_datetimes(args, expect, warn, capsys):
    """It Identifies dates from Rose 2019 parse formats and turns it into an
    ISO8601 Datetime if required.

    Formats converted:

    - ("%a %b %d %H:%M:%S %Z %Y", True),  # Unix "date"
    - ("%Y%m%d%H", False)                 # Cylc (pre Cylc 5)
    """
    # Parse the input strings:
    args = [arg.replace('_', ' ') for arg in args.split(' ')]
    expect = [i.replace('_', ' ') for i in expect.split()]

    # Run function:
    result = _handle_old_datetimes(args)

    # Check results:
    assert result == expect

    # Check warning message:
    if warn:
        assert warn in capsys.readouterr().err


@pytest.mark.parametrize(
    'args, expect',
    [
        param(
            ['rose-date', 'Mon Jun 6 23:30:12 2022'],
            'Mon Jun 06 23:30:12 2022',
            id='it works on ctime %a %b %d %H:%M:%S %Y'
        ),
        param(
            ['rose-date', 'Mon Jun 6 23:30:12 UTC 2022'],
            '2022-06-06T23:30:12',
            id='it works on Unix date %a %b %d %H:%M:%S %Z %Y'
        ),
        param(
            ['rose-date', '14900618T1440Z'],
            '14900618T1440Z',
            id='it works on ISO8601 %Y-%m-%dT%H:%M%z'
        ),
        param(
            ['rose-date', '1490-06-18T14:40:30'],
            '1490-06-18T14:40:30',
            id='it works on ISO8601 %Y-%m-%dT%H:%M:%S%z'
        ),
        param(
            ['rose-date', '1490061814'],
            '14900618T14',
            id='it works on pre Cylc 5 datetimes %Y%m%d%H'
        ),
    ]
)
def test_main(monkeypatch, capsys, args, expect):
    """Test that Rose Date can handle all formats described in Rose 2019

    For information, possible formats from Rose 2019:

        # strptime formats and their compatibility with the ISO 8601 parser.
        PARSE_FORMATS = [
            ("%a %b %d %H:%M:%S %Y", True),     # ctime
            ("%a %b %d %H:%M:%S %Z %Y", True),  # Unix "date"
            ("%Y-%m-%dT%H:%M:%S", False),       # ISO8601, extended
            ("%Y%m%dT%H%M%S", False),           # ISO8601, basic
            ("%Y%m%d%H", False)                 # Cylc (current[sic])
        ]
    """

    def fake_exit(myfunc):
        return myfunc

    monkeypatch.setattr(sys, 'argv', args)
    monkeypatch.setattr(sys, 'exit', fake_exit)
    main()
    assert capsys.readouterr().out.split('\n')[-2] == expect


def test_cycling_mode(monkeypatch, capsys):
    # it should default to the gregorian calendar
    monkeypatch.setenv('ROSE_CYCLING_MODE', '')
    _main(['rose-date', '2000', '--offset=P360D'])
    out, _ = capsys.readouterr()
    # 2000 + P360D = 20001226
    assert out.splitlines()[0] == '2000'

    # it should ignore the integer cycling mode
    monkeypatch.setenv('ROSE_CYCLING_MODE', 'integer')
    _main(['rose-date', '2000', '--offset=P360D'])
    out, _ = capsys.readouterr()
    # 2000 + P360D = 20001226
    assert out.splitlines()[0] == '2000'

    # but it should switch to alternative calendars as appropriate
    monkeypatch.setenv('ROSE_CYCLING_MODE', '360_day')
    _main(['rose-date', '2000', '--offset=P360D'])
    out, _ = capsys.readouterr()
    # 2000 + P360D = 2001
    assert out.splitlines()[0] == '2001'
