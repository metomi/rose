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
tests 15
#-------------------------------------------------------------------------------
setup
#-------------------------------------------------------------------------------
# Test adding sections and options via macros.
#-------------------------------------------------------------------------------
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4
__CONFIG__
init_opt colour <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
init_meta </dev/null
init_macro add.py <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
#-----------------------------------------------------------------------------

import rose.macro


class AddSpoiler(rose.macro.MacroBase):

    """Add a spoiler."""

    def transform(self, config, meta_config=None):
        """Spoilers are cool."""
        self.reports = []
        config.set(["car", "spoilers"], "1")
        info = "Added a spoiler, woohoo!"
        self.add_report("car", "spoilers", "1", info)
        return config, self.reports


class AddGarageRoof(rose.macro.MacroBase):

    """Add garage roof."""

    def transform(self, config, meta_config=None):
        """Now with fewer puddles."""
        self.reports = []
        config.set(["garage", "roof"], "flat")
        info = "Added garage roof!"
        self.add_report("garage", "roof", "flat", info)
        return config, self.reports


class AddElectricBike(rose.macro.MacroBase):

    """Add an electric bike!"""

    def transform(self, config, meta_config=None):
        """'If you're exerting yourself, you're doing it wrong.'"""
        self.reports = []
        config.set(["electric_bike"])
        info = "Added electric bike!"
        self.add_report("bike", None, None, info)
        return config, self.reports
__MACRO__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-add-option-to-main
run_pass "$TEST_KEY" rose macro -y --config=../config add.AddSpoiler
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] add.AddSpoiler: changes: 1
    car=spoilers=1
        Added a spoiler, woohoo!
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
spoilers=1
wheels=4
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-add-option-to-section-from-opt-conf
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4
__CONFIG__
init_opt colour <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
run_pass "$TEST_KEY" rose macro -y --config=../config add.AddGarageRoof
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] add.AddGarageRoof: changes: 1
    garage=roof=flat
        Added garage roof!
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

[garage]
roof=flat
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-add-section-to-main
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__OPT_CONFIG__
run_pass "$TEST_KEY" rose macro -y --config=../config add.AddElectricBike
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] add.AddElectricBike: changes: 1
    bike=None=None
        Added electric bike!
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
wheels=4

[electric_bike]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[car]
paint_job=sparkly

[garage]
door_paint_job=boring
__CONFIG__
teardown
#-------------------------------------------------------------------------------
exit
