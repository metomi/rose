#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
# Test "rose date".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 14
#-------------------------------------------------------------------------------
# Ensure it can parse its own output.
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose date
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
DATE_TIME_STR="$(cat $TEST_KEY.out)"
TEST_KEY=$TEST_KEY_BASE-parse
run_pass "$TEST_KEY" rose date "$DATE_TIME_STR"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$DATE_TIME_STR
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse an ISO date time with some offsets.
TEST_KEY=$TEST_KEY_BASE-offsets
run_pass "$TEST_KEY" rose date -s 18h -s 6d "2012-12-24T06:00:00"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-31T00:00:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse a Cylc date time with some negative offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-neg
run_pass "$TEST_KEY" rose date -s -6h -s -12h -s -12d "2013010618"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012122500
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse a Cylc date and print in ISO format.
TEST_KEY=$TEST_KEY_BASE-format-iso
run_pass "$TEST_KEY" rose date --print-format="%Y%m%dT%H%M%S" "2012122515"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T150000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
exit 0
