# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
# -----------------------------------------------------------------------------
"""
Tests for Python 2 compatibility types

These types Int, Float and Str over-ride Python3 types
to produce Python2 behaviour to provide back compatibility for Rose.

The tests were generated as follows:

#!/usr/bin/env python2
# Examine what python2 does in a variety of cases

import itertools

floats = [-999.0, -5.1, -1., 0., 1., 5.1, 999.]
ints = [-999, -5, -1, 0, 1, 5, 999]
strings = ['aardvaark', 'zebra']

data = {}
for combo in itertools.permutations(floats + ints + strings, 2):
    gt = combo[0] > combo[1]
    eq = combo[0] == combo[1]
    data[combo] = {}
    data[combo]["gt"] = gt
    data[combo]["eq"] = eq

print(data)

"""
import pytest
from metomi.rose.macros.rule import Float, Int, Str

TESTS = {
    (1.0, "zebra"): {"gt": False, "eq": False},
    ("zebra", 0.0): {"gt": True, "eq": False},
    (-1.0, 0.0): {"gt": False, "eq": False},
    (1.0, -5): {"gt": True, "eq": False},
    (-999.0, 1.0): {"gt": False, "eq": False},
    (5.1, "zebra"): {"gt": False, "eq": False},
    ("zebra", -1.0): {"gt": True, "eq": False},
    (-5, 1.0): {"gt": False, "eq": False},
    (-5.1, 1.0): {"gt": False, "eq": False},
    (999.0, -1.0): {"gt": True, "eq": False},
    (-5.1, "aardvaark"): {"gt": False, "eq": False},
    (-5, -5.1): {"gt": True, "eq": False},
    (-999.0, -5): {"gt": False, "eq": False},
    ("aardvaark", -999.0): {"gt": True, "eq": False},
    ("zebra", 5): {"gt": True, "eq": False},
    (-5.1, -5): {"gt": False, "eq": False},
    (-1.0, 999.0): {"gt": False, "eq": False},
    (1.0, 1): {"gt": False, "eq": True},
    ("aardvaark", -5.1): {"gt": True, "eq": False},
    (5, 999.0): {"gt": False, "eq": False},
    (-999.0, 5.1): {"gt": False, "eq": False},
    (0.0, "aardvaark"): {"gt": False, "eq": False},
    (-1.0, "aardvaark"): {"gt": False, "eq": False},
    (0.0, 1.0): {"gt": False, "eq": False},
    (-5.1, "zebra"): {"gt": False, "eq": False},
    (5.1, -5): {"gt": True, "eq": False},
    (-999.0, -5.1): {"gt": False, "eq": False},
    ("aardvaark", 0.0): {"gt": True, "eq": False},
    (5, -1.0): {"gt": True, "eq": False},
    (-999.0, 999.0): {"gt": False, "eq": False},
    (-999.0, 5): {"gt": False, "eq": False},
    (-5, 5.1): {"gt": False, "eq": False},
    (-5, "aardvaark"): {"gt": False, "eq": False},
    (5.1, 1.0): {"gt": True, "eq": False},
    (-5, 5): {"gt": False, "eq": False},
    (5.1, -1.0): {"gt": True, "eq": False},
    (999.0, 5.1): {"gt": True, "eq": False},
    (-1.0, 1.0): {"gt": False, "eq": False},
    (5.1, "aardvaark"): {"gt": False, "eq": False},
    (999.0, 1.0): {"gt": True, "eq": False},
    ("aardvaark", 5): {"gt": True, "eq": False},
    ("aardvaark", 1.0): {"gt": True, "eq": False},
    (0.0, 999.0): {"gt": False, "eq": False},
    (999.0, "aardvaark"): {"gt": False, "eq": False},
    (1.0, 5): {"gt": False, "eq": False},
    (-999.0, 0.0): {"gt": False, "eq": False},
    (-1.0, -1): {"gt": False, "eq": True},
    (-1.0, -5.1): {"gt": True, "eq": False},
    (-5, 0.0): {"gt": False, "eq": False},
    (-5, 999.0): {"gt": False, "eq": False},
    (-5.1, 0.0): {"gt": False, "eq": False},
    (0.0, 5.1): {"gt": False, "eq": False},
    (999.0, 999): {"gt": False, "eq": True},
    (-999.0, -999): {"gt": False, "eq": True},
    (0.0, 5): {"gt": False, "eq": False},
    (-999.0, "zebra"): {"gt": False, "eq": False},
    (1.0, 0.0): {"gt": True, "eq": False},
    (-1.0, -5): {"gt": True, "eq": False},
    ("zebra", 5.1): {"gt": True, "eq": False},
    (-5, "zebra"): {"gt": False, "eq": False},
    ("aardvaark", -1.0): {"gt": True, "eq": False},
    (-5.1, 5.1): {"gt": False, "eq": False},
    (0.0, -1.0): {"gt": True, "eq": False},
    (5.1, 5): {"gt": True, "eq": False},
    (-5, -999.0): {"gt": True, "eq": False},
    (-1.0, 5): {"gt": False, "eq": False},
    (1.0, -5.1): {"gt": True, "eq": False},
    (1.0, -1.0): {"gt": True, "eq": False},
    ("zebra", "aardvaark"): {"gt": True, "eq": False},
    (0.0, -5): {"gt": True, "eq": False},
    (0.0, "zebra"): {"gt": False, "eq": False},
    (1.0, -999.0): {"gt": True, "eq": False},
    (5, 5.1): {"gt": False, "eq": False},
    ("zebra", -5): {"gt": True, "eq": False},
    (5.1, 0.0): {"gt": True, "eq": False},
    (0.0, -5.1): {"gt": True, "eq": False},
    (-5.1, -1.0): {"gt": False, "eq": False},
    (999.0, 5): {"gt": True, "eq": False},
    (-5, -1.0): {"gt": False, "eq": False},
    (999.0, -5): {"gt": True, "eq": False},
    (-1.0, 5.1): {"gt": False, "eq": False},
    (5, -5.1): {"gt": True, "eq": False},
    (-999.0, -1.0): {"gt": False, "eq": False},
    (5, 0.0): {"gt": True, "eq": False},
    (-999.0, "aardvaark"): {"gt": False, "eq": False},
    (0.0, -999.0): {"gt": True, "eq": False},
    (5.1, -999.0): {"gt": True, "eq": False},
    ("aardvaark", -5): {"gt": True, "eq": False},
    ("aardvaark", "zebra"): {"gt": False, "eq": False},
    ("zebra", 999.0): {"gt": True, "eq": False},
    (999.0, -5.1): {"gt": True, "eq": False},
    ("zebra", -999.0): {"gt": True, "eq": False},
    (5, "aardvaark"): {"gt": False, "eq": False},
    (5.1, 999.0): {"gt": False, "eq": False},
    (-5.1, -999.0): {"gt": True, "eq": False},
    (5, 1.0): {"gt": True, "eq": False},
    (5, -5): {"gt": True, "eq": False},
    (1.0, 999.0): {"gt": False, "eq": False},
    (999.0, 0.0): {"gt": True, "eq": False},
    (5.1, -5.1): {"gt": True, "eq": False},
    (1.0, 5.1): {"gt": False, "eq": False},
    (5, -999.0): {"gt": True, "eq": False},
    (-5.1, 5): {"gt": False, "eq": False},
    ("aardvaark", 5.1): {"gt": True, "eq": False},
    (-1.0, -999.0): {"gt": True, "eq": False},
    ("aardvaark", 999.0): {"gt": True, "eq": False},
    (0.0, 0): {"gt": False, "eq": True},
    (-1.0, "zebra"): {"gt": False, "eq": False},
    (-5.1, 999.0): {"gt": False, "eq": False},
    (5, "zebra"): {"gt": False, "eq": False},
    ("zebra", -5.1): {"gt": True, "eq": False},
    (999.0, "zebra"): {"gt": False, "eq": False},
    (1.0, "aardvaark"): {"gt": False, "eq": False},
    (999.0, -999.0): {"gt": True, "eq": False},
    ("zebra", 1.0): {"gt": True, "eq": False},
}
MYTYPES = {int: Int, float: Float, str: Str}


@pytest.mark.parametrize('test', TESTS.items())
def test_python2_compat_classes(test):
    """Subclassed types (MYTYPES.values) behave like Python2 types.
    """
    first, second = test[0]
    # Convert test values from base to subclassed types:
    for basetype, mytype in MYTYPES.items():
        if isinstance(first, basetype):
            first = mytype(first)
        if isinstance(second, basetype):
            second = mytype(second)
    assert (first > second) == test[1]['gt']
    assert (first == second) == test[1]['eq']
