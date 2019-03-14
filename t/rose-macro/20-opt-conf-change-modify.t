#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
#-------------------------------------------------------------------------------
# Test "rose macro" for optional configuration validating.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 25
#-------------------------------------------------------------------------------
setup
#-------------------------------------------------------------------------------
# Test modifying sections and options via macros.
#-------------------------------------------------------------------------------
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

# In the middle of our
[our_house]
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__OPT_CONFIG__
init_meta </dev/null
init_macro modify.py <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
#-----------------------------------------------------------------------------

import rose.macro


class InvisibleCarPaint(rose.macro.MacroBase):

    """The coolest colour is... invisible."""

    def transform(self, config, meta_config=None):
        """Check paint can isn't empty."""
        self.reports = []
        config.set(["car", "paint_job"], "invisible")
        info = "Where did I park?"
        self.add_report("car", "paint_job", "invisible", info)
        return config, self.reports


class ExtraWheels(rose.macro.MacroBase):

    """Add some more wheels."""

    def transform(self, config, meta_config=None):
        """Make the car a 6x6."""
        self.reports = []
        config.set(["car", "wheels"], "6")
        info = "Added 2 more wheels"
        self.add_report("car", "wheels", "6", info)
        return config, self.reports


class ChangeHouseComments(rose.macro.MacroBase):

    """Change comments for our house."""

    def transform(self, config, meta_config=None):
        """Complete the lyric."""
        self.reports = []
        config.set(["our_house"], comments=[" In the middle of our street"])
        info = "Much better now."
        self.add_report("our_house", None, None, info)
        return config, self.reports


class IgnoreGarage(rose.macro.MacroBase):

    """Park outside."""

    def transform(self, config, meta_config=None):
        """Garages are for boxes and junk."""
        self.reports = []
        node = config.get(["garage"])
        if node is not None:
            config.get(["garage"]).state = config.STATE_USER_IGNORED
            info = "Ignore garage"
            self.add_report("garage", None, None, info)
        return config, self.reports
__MACRO__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-option-in-opt
run_pass "$TEST_KEY" rose macro -y --config=../config modify.InvisibleCarPaint
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] modify.InvisibleCarPaint: changes: 1
    car=paint_job=invisible
        Where did I park?
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=invisible
wheels=4

# In the middle of our
[our_house]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-option-in-main
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

# In the middle of our
[our_house]
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__OPT_CONFIG__
run_pass "$TEST_KEY" rose macro -y --config=../config modify.ExtraWheels
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] modify.ExtraWheels: changes: 1
    car=wheels=6
        Added 2 more wheels
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=6

# In the middle of our
[our_house]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-comments-in-main
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

# In the middle of our
[our_house]
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__OPT_CONFIG__
run_pass "$TEST_KEY" rose macro -y --config=../config modify.ChangeHouseComments
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] modify.ChangeHouseComments: changes: 1
    our_house=None=None
        Much better now.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

# In the middle of our street
[our_house]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ignore-section-in-opt
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

# In the middle of our
[our_house]
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__OPT_CONFIG__
run_pass "$TEST_KEY" rose macro -y --config=../config modify.IgnoreGarage
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] modify.IgnoreGarage: changes: 1
    (opts=colour)garage=None=None
        Ignore garage
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

# In the middle of our
[our_house]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[car]
paint_job=sparkly

[!garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-comment-in-section-bug
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

[garage]
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly

# Garages are for boats, not cars.
[garage]
door_paint_job=boring
__OPT_CONFIG__
run_pass "$TEST_KEY" rose macro -y --config=../config modify.InvisibleCarPaint
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] modify.InvisibleCarPaint: changes: 1
    car=paint_job=invisible
        Where did I park?
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=invisible
wheels=4

[garage]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
# Garages are for boats, not cars.
[garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
teardown
exit
