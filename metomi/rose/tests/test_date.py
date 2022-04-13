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
"""Test functionality from metomi.rose.date
"""

import pytest

from metomi.rose.date import upgrade_offset


param = pytest.param


@pytest.mark.parametrize(
    'sign', ('-', '')
)
@pytest.mark.parametrize(
    'input_, expect',
    [
        param('1w', 'P7DT0H0M0S', id='it parses w alone'),
        param('1d', 'P1DT0H0M0S', id='it parses d alone'),
        param('1h', 'P0DT1H0M0S', id='it parses h alone'),
        param('1m', 'P0DT0H1M0S', id='it parses m alone'),
        param('1s', 'P0DT0H0M1S', id='it parses s alone'),
        param('1w1d1h1m1s', 'P8DT1H1M1S', id='it parses all wdhms'),
        param('1s1m1h1d1w', 'P8DT1H1M1S', id='it parses all smhdw'),
        param(
            '4s12m180h42dw100', 'P42DT180H12M4S', id='it parses large numbers'
        ),
        param('5h3m7s', 'P0DT5H3M7S', id='it parses it parses times only'),
    ]
)
def test_upgrade_offset(sign, input_, expect):
    assert upgrade_offset(f'{sign}{input_}') == f'{sign}{expect}'
