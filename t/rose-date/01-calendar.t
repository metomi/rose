#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose date calendar swapping".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Check correct setting of 360 day calendar via environment.
TEST_KEY=$TEST_KEY_BASE-360-env
CYLC_CALENDAR=360 \
    run_pass "$TEST_KEY-back"  rose date 20130301 --offset=-P1D
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130230
__OUT__
CYLC_CALENDAR=360 \
    run_pass "$TEST_KEY-fwd" rose date 20130230 --offset=P1D
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
# Check correct setting of 360 day calendar via args.
TEST_KEY=$TEST_KEY_BASE-360-switch
run_pass "$TEST_KEY-back"  rose date 20130301 --offset=-P1D --calendar=360
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130230
__OUT__
run_pass "$TEST_KEY-fwd" rose date 20130230 --offset=P1D --calendar=360
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
# Check args correctly override environment.
TEST_KEY=$TEST_KEY_BASE-gregorian-override
CYLC_CALENDAR=gregorian \
    run_pass "$TEST_KEY-back"  rose date 20130301 --offset=-P1D --calendar=360
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130230
__OUT__
CYLC_CALENDAR=gregorian \
    run_pass "$TEST_KEY-fwd" rose date 20130230 --offset=P1D --calendar=360
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
exit 0
