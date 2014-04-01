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
# Test "rose date".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 47
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
# Parse format and print format.
TEST_KEY=$TEST_KEY_BASE-offsets
run_pass "$TEST_KEY" rose date -p '%d/%m/%Y %H:%M:%S' -f '%Y-%m-%dT%H:%M:%S' \
    '24/12/2012 06:00:00'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-24T06:00:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (isodatetime parse format).
TEST_KEY=$TEST_KEY_BASE-offsets-iso-parse
run_pass "$TEST_KEY" rose date -p 'DD/MM/YYThh:mm:ss' -f '%Y-%m-%dT%H:%M:%S' \
    '24/12/2012T06:00:00'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-24T06:00:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (isodatetime print format).
TEST_KEY=$TEST_KEY_BASE-offsets-iso-print
run_pass "$TEST_KEY" rose date -p '%d/%m/%Y %H:%M:%S' -f 'CCYY-MM-DDThh:mm' \
    '24/12/2012 06:00:00'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-24T06:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (isodatetime parse and print format).
TEST_KEY=$TEST_KEY_BASE-offsets-iso-parse-print
run_pass "$TEST_KEY" rose date -p 'DDD-CCYYThh:mm:ssZ' \
    -f 'CCYY-MM-DDThh:mm+01:00' '091-2014T15:14:03Z'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2014-04-01T16:14+01:00
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
# Parse an ISO date time with some offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-iso
run_pass "$TEST_KEY" rose date -s PT18H -s PT6D "2012-12-24T06:00:00"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-31T00:00:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse a Cylc date time with some negative offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-neg
run_pass "$TEST_KEY" rose date -s -6h -s -12d12h "2013010618"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012122500
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse a Cylc date time with some negative offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-neg-iso
run_pass "$TEST_KEY" rose date -s -PT6H -s -P12DT12H "2013010618"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012122500
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Bad offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-bad
run_fail "$TEST_KEY" rose date -s junk "2013010618"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] junk: bad offset value
__ERR__
#-------------------------------------------------------------------------------
# Parse a Cylc date and print in ISO format.
TEST_KEY=$TEST_KEY_BASE-format-iso
run_pass "$TEST_KEY" rose date --print-format="%Y%m%dT%H%M%S" "2012122515"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T150000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format with offset.
TEST_KEY=$TEST_KEY_BASE-format-and-offset
run_pass "$TEST_KEY" rose date --offset=-3h -f "%y%m" "2012112515" --debug
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
1211
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option.
TEST_KEY=$TEST_KEY_BASE-c
ROSE_TASK_CYCLE_TIME=2012122500 \
    run_pass "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012122500
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option, ISO 8601.
TEST_KEY=$TEST_KEY_BASE-c-iso8601
ROSE_TASK_CYCLE_TIME=20121225T0000Z \
    run_pass "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T0000Z
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option, ROSE_TASK_CYCLE_TIME not defined.
TEST_KEY=$TEST_KEY_BASE-c-undef
unset ROSE_TASK_CYCLE_TIME
run_fail "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] [UNDEFINED ENVIRONMENT VARIABLE] ROSE_TASK_CYCLE_TIME
__ERR__
#-------------------------------------------------------------------------------
exit 0
