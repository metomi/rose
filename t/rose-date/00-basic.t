#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
tests 104
#-------------------------------------------------------------------------------
# Produce the correct format for the current date/time.
TEST_KEY=$TEST_KEY_BASE-current-format
run_pass "$TEST_KEY" rose date
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
# The altering of the output is necessary until GNU coreutils 8.13.
sed -i 's/:\([0-5][0-9]\)$/\1/g; s/T/ /g' $TEST_KEY.out
DATE_TIME_STR="$(cat $TEST_KEY.out)"
run_pass "$TEST_KEY-parse" date -d "$DATE_TIME_STR" +"%Y-%m-%d %H:%M:%S%z"
file_cmp "$TEST_KEY-parse.out" "$TEST_KEY.out" <<__OUT__
$DATE_TIME_STR
__OUT__
file_cmp "$TEST_KEY-parse.err" "$TEST_KEY.err" </dev/null
# Produce date/time info near the current time.
TEST_KEY=$TEST_KEY_BASE-current-is-correct
T_START=$(date +%s)
run_pass "$TEST_KEY" rose date --print-format="%s"
T_TEST=$(cat $TEST_KEY.out)
T_END=$(date +%s)
if (( $T_TEST >= $T_START )) && (( $T_TEST <= $T_END )); then
    pass "$TEST_KEY.out"
else
    fail "$TEST_KEY.out"
fi
#-------------------------------------------------------------------------------
# Parse its own current date/time output.
TEST_KEY=$TEST_KEY_BASE-current-parse
run_pass "$TEST_KEY" rose date
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
DATE_TIME_STR=$(cat $TEST_KEY.out)
TEST_KEY=$TEST_KEY_BASE-parse
run_pass "$TEST_KEY" rose date "$DATE_TIME_STR"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$DATE_TIME_STR
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Produce an offset from the current date/time.
TEST_KEY=$TEST_KEY_BASE-current-offset
T_START=$(date +%s)
run_pass "$TEST_KEY" rose date --offset=PT1H
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
# The altering of the output is necessary until GNU coreutils 8.13.
sed -i 's/:\([0-5][0-9]\)$/\1/g; s/T/ /g' $TEST_KEY.out
DATE_TIME_STR=$(cat $TEST_KEY.out)
T_OFFSET=$(date -d "$DATE_TIME_STR" +%s)
# Allow a minute either side of the 1 hour, expressed in seconds.
if (( T_OFFSET - T_START > 3540 )) && (( T_OFFSET - T_START < 3660 )); then
    pass "$TEST_KEY.out"
else
    fail "$TEST_KEY.out"
fi
#-------------------------------------------------------------------------------
# Produce a print format from the current date/time.
TEST_KEY=$TEST_KEY_BASE-current-print-format
run_pass "$TEST_KEY" rose date --print-format="%D %R" now
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
DATE_TIME_STR=$(cat $TEST_KEY.out)
run_pass "$TEST_KEY-vs-date" date -d "$DATE_TIME_STR" +"%D %R"
file_cmp "$TEST_KEY-vs-date.err" "$TEST_KEY-vs-date.err" </dev/null
file_cmp "$TEST_KEY-vs-date.out" "$TEST_KEY-vs-date.out" <<__OUT__
$DATE_TIME_STR
__OUT__
#-------------------------------------------------------------------------------
# Parse format and print format (1).
TEST_KEY=$TEST_KEY_BASE-parse-print-1
run_pass "$TEST_KEY" rose date -p '%d/%m/%Y %H:%M:%S' -f '%Y-%m-%dT%H:%M:%S' \
    '24/12/2012 06:00:00'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-24T06:00:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (2).
TEST_KEY=$TEST_KEY_BASE-parse-print-2
run_pass "$TEST_KEY" rose date -p '%Y,%M,%d,%H' -f '%Y%M%d%H' '2014,01,02,05'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2014010205
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (3).
TEST_KEY=$TEST_KEY_BASE-parse-print-3
run_pass "$TEST_KEY" rose date -p "%Y%m%d" -f "%y%m%d" '20141231'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
141231
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (4).
TEST_KEY=$TEST_KEY_BASE-parse-print-4
run_pass "$TEST_KEY" rose date -u -p "%Y%m%d%H%M%S" -f "%s" '20140402100000'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
1396432800
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (5).
TEST_KEY=$TEST_KEY_BASE-parse-print-5
run_pass "$TEST_KEY" rose date -p "%s" -f "%Y%m%dT%H%M%S%z" '1396429200' --utc
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
20140402T090000+0000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (isodatetime print format).
TEST_KEY=$TEST_KEY_BASE-parse-print-iso-print
run_pass "$TEST_KEY" rose date -p '%d/%m/%Y %H:%M:%S' -f 'CCYY-MM-DDThh:mm' \
    '24/12/2012 06:00:00'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-24T06:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse format and print format (isodatetime parse and print format).
TEST_KEY=$TEST_KEY_BASE-parse-print-iso-parse-print
run_pass "$TEST_KEY" rose date -f 'CCYY-MM-DDThh:mm+01:00' '2014-091T15:14:03Z'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2014-04-01T16:14+01:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (1).
TEST_KEY=$TEST_KEY_BASE-print-1
run_pass "$TEST_KEY" rose date -f "%m" '2014-02-01T04:05:06'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
02
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (2).
TEST_KEY=$TEST_KEY_BASE-print-2
run_pass "$TEST_KEY" rose date -f "%Y" '2014-02-01T04:05:06'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2014
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (3).
TEST_KEY=$TEST_KEY_BASE-print-3
run_pass "$TEST_KEY" rose date -f "%H" '2014-02-01T04:05:06'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
04
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (4).
TEST_KEY=$TEST_KEY_BASE-print-4
run_pass "$TEST_KEY" rose date -f "%Y%m%d_%H%M%S" '2014-02-01T04:05:06'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20140201_040506
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (5).
TEST_KEY=$TEST_KEY_BASE-print-5
run_pass "$TEST_KEY" rose date -f "%Y.file" '2014-02-01T04:05:06'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2014.file
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (6).
TEST_KEY=$TEST_KEY_BASE-print-6
run_pass "$TEST_KEY" rose date -f "y%Ym%md%d" '2014-02-01T04:05:06'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
y2014m02d01
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format (7).
TEST_KEY=$TEST_KEY_BASE-print-7
run_pass "$TEST_KEY" rose date -f "%F" '2014-092'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2014-04-02
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse an ISO date time with some offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-iso
run_pass "$TEST_KEY" rose date -s PT18H -s P6D "2012-12-24T06:00:00"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2012-12-31T00:00:00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Parse a Cylc date time with some negative offsets.
TEST_KEY=$TEST_KEY_BASE-offsets-negative
run_pass "$TEST_KEY" rose date -s=-PT6H -s=-P12DT12H "20130106T18"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T00
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Bad offsets, ISO 8601.
TEST_KEY=$TEST_KEY_BASE-offsets-bad-iso
run_fail "$TEST_KEY" rose date -s Pjunk "20130106T18"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
Pjunk: bad offset value
__ERR__
#-------------------------------------------------------------------------------
# Parse a Cylc date and print in ISO format.
TEST_KEY=$TEST_KEY_BASE-format-iso
run_pass "$TEST_KEY" rose date --print-format="%Y%m%dT%H%M%S" "20121225T15"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T150000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Print format with offset.
TEST_KEY=$TEST_KEY_BASE-format-and-offset
run_pass "$TEST_KEY" rose date --offset=-PT3H -f "%y%m" "20121125T15"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
1211
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option
TEST_KEY=$TEST_KEY_BASE-c
ROSE_TASK_CYCLE_TIME=20121225T0000Z \
    run_pass "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T0000Z
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option with ISODATETIMEREF
TEST_KEY=$TEST_KEY_BASE-c-isodatetimeref
ISODATETIMEREF=20121225T0000Z \
    run_pass "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T0000Z
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option, --utc
TEST_KEY=$TEST_KEY_BASE-c-utc
ROSE_TASK_CYCLE_TIME=20121225T0000+0100 \
    run_pass "$TEST_KEY" rose date -c --utc
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121224T2300+0000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option, ROSE_TASK_CYCLE_TIME not defined.
TEST_KEY=$TEST_KEY_BASE-c-undef
unset ROSE_TASK_CYCLE_TIME
unset ISODATETIMEREF
run_fail "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] [UNDEFINED ENVIRONMENT VARIABLE] ROSE_TASK_CYCLE_TIME
__ERR__
#-------------------------------------------------------------------------------
# Test rose date --as-total runs without error
TEST_KEY=$TEST_KEY_BASE-as-total
run_pass "$TEST_KEY" rose date --as-total=s PT1M
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test rose date --as-total=s P1DT1H1M1S
TEST_KEY=$TEST_KEY_BASE-as-total-P1DT1H1M1S-s
run_pass "$TEST_KEY" rose date --as-total=s P1DT1H1M1S
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
90061.0
__OUT__
#-------------------------------------------------------------------------------
# Test rose date --as-total=m PT1S
TEST_KEY=$TEST_KEY_BASE-as-total-PT1S-m
run_pass "$TEST_KEY" rose date --as-total=m PT1S
head -c 10 "$TEST_KEY.out" > $TEST_KEY.out.truncated
echo "" >> $TEST_KEY.out.truncated
file_cmp "$TEST_KEY.out.truncated" "$TEST_KEY.out.truncated" <<'__OUT__'
0.01666666
__OUT__
#-------------------------------------------------------------------------------
# Test rose date --as-total=h P832DT23H12M45S
TEST_KEY=$TEST_KEY_BASE-as-total-P832DT23H12M45S-h
run_pass "$TEST_KEY" rose date --as-total=h P832DT23H12M45S
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
19991.2125
__OUT__
#-------------------------------------------------------------------------------
# Test rose date --as-total=FORMAT fails for invalid format
TEST_KEY=$TEST_KEY_BASE-as-total-invalid-format
run_fail "$TEST_KEY" rose date --as-total=y PT1M
#-------------------------------------------------------------------------------
# Test rose date --as-total=FORMAT for negative durations
TEST_KEY=$TEST_KEY_BASE-as-total-negative
run_pass "$TEST_KEY" rose date --as-total=S \\-PT1M1S
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
-61.0
__OUT__
#-------------------------------------------------------------------------------
# Test rose date --as-total=FORMAT for use case 2
TEST_KEY=$TEST_KEY_BASE-as-total-between-dates
run_pass "$TEST_KEY" rose date 2000-01-01T00:00:00 2000-01-01T01:00:00 --as-total=s
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
3600.0
__OUT__
#-------------------------------------------------------------------------------
# Test rose date --as-total=FORMAT for use case 2 with an offset
if python3 -c "import argparse; argparse.ArgumentParser.parse_intermixed_args"; then
  TEST_KEY=$TEST_KEY_BASE-as-total-between-dates-with-offset
  run_pass "$TEST_KEY" rose date 2000-01-01T00:00:00 --offset=PT1H   2000-01-01T01:00:00 --as-total=s
else
  run_pass "$TEST_KEY" rose date 2000-01-01T00:00:00  2000-01-01T01:00:00 --as-total=s --offset=PT1H
fi
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
0.0
__OUT__
#-------------------------------------------------------------------------------
exit 0
