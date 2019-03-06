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
# Test "rose date calendar swapping".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 20
#-------------------------------------------------------------------------------
# Check correct setting of 360 day calendar via environment.
TEST_KEY=$TEST_KEY_BASE-360-env
ROSE_CYCLING_MODE=360day \
    run_pass "$TEST_KEY-back"  rose date 20130301 --offset=-P1D
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130230
__OUT__
ROSE_CYCLING_MODE=360day \
    run_pass "$TEST_KEY-fwd" rose date 20130230 --offset=P1D
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
# Check correct setting of 360 day calendar via args.
TEST_KEY=$TEST_KEY_BASE-360-switch
run_pass "$TEST_KEY-back"  rose date 20130301 --offset=-P1D --calendar=360day
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130230
__OUT__
run_pass "$TEST_KEY-fwd" rose date 20130230 --offset=P1D --calendar=360day
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
# Check correct setting of 365 day calendar via args.
TEST_KEY=$TEST_KEY_BASE-365-switch
run_pass "$TEST_KEY-back" rose date 20130301 --offset=-P1D --calendar=365day
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130228
__OUT__
run_pass "$TEST_KEY-fwd" rose date 20130228 --offset=P1D --calendar=365day
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
# Check correct setting of 366 day calendar via args.
TEST_KEY=$TEST_KEY_BASE-366-switch
run_pass "$TEST_KEY-back" rose date 20130301 --offset=-P1D --calendar=366day
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130229
__OUT__
run_pass "$TEST_KEY-fwd" rose date 20130229 --offset=P1D --calendar=366day
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
# Check args correctly override environment.
TEST_KEY=$TEST_KEY_BASE-gregorian-override
ROSE_CYCLING_MODE=gregorian \
    run_pass "$TEST_KEY-back"  rose date 20130301 --offset=-P1D --calendar=360day
file_cmp "$TEST_KEY-back.out" "$TEST_KEY-back.out" <<__OUT__
20130230
__OUT__
ROSE_CYCLING_MODE=gregorian \
    run_pass "$TEST_KEY-fwd" rose date 20130230 --offset=P1D --calendar=360day
file_cmp "$TEST_KEY-fwd.out" "$TEST_KEY-fwd.out" <<__OUT__
20130301
__OUT__
#-------------------------------------------------------------------------------
exit 0
