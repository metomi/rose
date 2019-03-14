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
tests 5
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

[electric_bike]
__CONFIG__
init_opt colour <<'__OPT_CONFIG__'
[car]
motor=electric
paint_job=sparkly

[garage]
door_paint_job=boring

[skateboard]
__OPT_CONFIG__
init_meta </dev/null
init_macro remove.py <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
#-----------------------------------------------------------------------------

import rose.macro


class RemoveLotsOfStuff(rose.macro.MacroBase):

    """Remove many things."""

    def transform(self, config, meta_config=None):
        """Get rid of selected stuff."""
        self.reports = []
        if config.get_value(["car", "motor"]) == "electric":
            if config.get(["electric_bike"]) is not None:
                config.unset(["electric_bike"])
                self.add_report("electric_bike", None, None, "No bike")
        if config.get(["car", "motor"]) is not None:
            config.unset(["car", "motor"])
            self.add_report("car", "motor", None, "No motor")
        if config.get(["car", "wheels"]) is not None:
            config.unset(["car", "wheels"])
            self.add_report("car", "wheels", "4", "No wheels")
        if config.get(["garage", "door_paint_job"]) is not None:
            config.unset(["garage", "door_paint_job"])
            self.add_report("garage", "door_paint_job", "boring", "No door")
        if config.get(["car", "paint_job"]) is not None:
            config.unset(["car", "paint_job"])
            self.add_report("car", "paint_job", None, "No paint")
        if config.get(["skateboard"]) is not None:
            config.unset(["skateboard"])
            self.add_report("skateboard", None, None, "No skateboard")
        return config, self.reports
__MACRO__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-remove-lots-of-stuff
run_pass "$TEST_KEY" rose macro -y --config=../config remove.RemoveLotsOfStuff
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] remove.RemoveLotsOfStuff: changes: 6
    car=wheels=4
        No wheels
    car=paint_job=None
        No paint
    (opts=colour)electric_bike=None=None
        No bike
    (opts=colour)car=motor=None
        No motor
    (opts=colour)garage=door_paint_job=boring
        No door
    (opts=colour)skateboard=None=None
        No skateboard
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[car]
budget=1000

[electric_bike]
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-colour.conf <<'__CONFIG__'
[!electric_bike]

[garage]
__CONFIG__
teardown
#-------------------------------------------------------------------------------
exit
