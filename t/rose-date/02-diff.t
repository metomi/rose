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
# Test "rose date --diff".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check correct diffing of dates
TEST_KEY=$TEST_KEY_BASE-diff-date
run_pass "$TEST_KEY"  rose date 20130301 --diff 20130101T12
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
P58DT12H
__OUT__
#-------------------------------------------------------------------------------
# Check rose date will fail to subtract a future date
TEST_KEY=$TEST_KEY_BASE-fail
run_fail "$TEST_KEY"  rose date 20130301 --diff 20150101T12
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__OUT__
[FAIL] 20150101T12: cannot be subtracted from earlier date: 20130301
__OUT__
#-------------------------------------------------------------------------------
# Check rose date print format options for diff
TEST_KEY=$TEST_KEY_BASE-formatting
run_pass "$TEST_KEY"  rose date 20130301 --diff 20130101T12 -f "y,m,d,h,M,s"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
0,0,58,12,0,0
__OUT__
#-------------------------------------------------------------------------------
exit 0
