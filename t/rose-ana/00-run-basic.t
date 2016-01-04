#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# Test rose_ana built-in application, basic usage of OutputGrepper
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=34
tests $N_TESTS
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
# Test the output
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t1/01/job.out
TEST_KEY=$TEST_KEY_BASE-exact_numeric_success
file_grep $TEST_KEY "[ OK ].*Semi-major Axis.*all: 0%:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_numeric_fail
file_grep $TEST_KEY "[FAIL].*Orbital Period.*1: 5.234%" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_text_success
file_grep $TEST_KEY "[ OK ].*Atmosphere.*all: 0%" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_text_fail
file_grep $TEST_KEY "[FAIL].*Planet.*1: XX%.* (4 values)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_percentage_success
file_grep $TEST_KEY "[ OK ].*Oxygen Partial Pressure.*all% <= 5%" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_percentage_fail
file_grep $TEST_KEY "[FAIL].*Ocean coverage.*35.3107344633% > 5%:.* (95.8) c.f. .* (70.8)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_absolute_success
file_grep $TEST_KEY "[ OK ].*Surface Gravity.*all% <= 1.0:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_absolute_fail
file_grep $TEST_KEY "[FAIL].*Rotation Period.*7.04623622489% > 0.05:.* (0.927) c.f. .* (0.99727)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_list_success
file_grep $TEST_KEY "[ OK ].*Satellites Natural/Artificial.*all: 0%:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_list_fail
file_grep $TEST_KEY "[FAIL].*Other Planets.*1: XX%:.* (4 values)" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_list_success
file_grep $TEST_KEY "[ OK ].*Periastron/Apastron.*all% <= 5%:" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_list_fail
file_grep $TEST_KEY "[FAIL].*Inclination/Axial Tilt.*285.744234801% > 5%:.* (value 1 of 2)" $OUTPUT
#-------------------------------------------------------------------------------
# Test of ignoring a task
# First, test that the basic task ran ok
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t2_activated/01/job.out
TEST_KEY=$TEST_KEY_BASE-ignore-basic-1
file_grep $TEST_KEY "[FAIL].*Species" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-ignore-basic-2
file_grep $TEST_KEY "[ OK ].*Class" $OUTPUT
# Then test that ignoring a test means the output is not present
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t2_deactivated/01/job.out
TEST_KEY=$TEST_KEY_BASE-ignore-notpresent
file_grep_fail $TEST_KEY "[FAIL].*Species" $OUTPUT
#-------------------------------------------------------------------------------
# Test of comparison database
#
# Regexp for any number of digits (re-used a lot below)
COMP_NUMBER="[0-9][0-9]*"

OUTPUT=$HOME/cylc-run/$NAME/log/job/1/db_check/01/job.out
# For each of the 3 tasks check that a task entry exists with a status of 0
for TASK_NAME in "rose_ana_t1" "rose_ana_t2_activated" "rose_ana_t2_deactivated" ; do
    TEST_KEY=$TEST_KEY_BASE-db_check_${TASK_NAME}_success
    file_grep $TEST_KEY "$COMP_NUMBER | $TASK_NAME | 0" $OUTPUT
done

# File comparison regexp (re-used a lot below) - accept any path but ensure the
# two files are from the same subfolder (as they should be)
COMP_FILES=".*\(\w*\)/kgo.txt | .*\1/results.txt"

# Comparison tasks for the rose_ana_t1 task
TASK_NAME="rose_ana_t1 (Test of Exact Numeric Match Success)"
TASK_STATUS=" OK "
TASK_METHOD=".*Semi-major Axis.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_numeric_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Exact Numeric Match Fail)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Orbital Period.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_numeric_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Exact Text Match Success)"
TASK_STATUS=" OK "
TASK_METHOD=".*Atmosphere.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_text_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Exact Text Match Fail)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Planet.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_text_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Within Match Percentage Success)"
TASK_STATUS=" OK "
TASK_METHOD=".*Oxygen Partial Pressure.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_percentage_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Within Match Percentage Fail)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Ocean coverage.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_percentage_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Within Match Absolute Success)"
TASK_STATUS=" OK "
TASK_METHOD=".*Surface Gravity.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_absolute_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Within Match Absolute Fail)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Rotation Period.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_absolute_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Exact List Match Success)"
TASK_STATUS=" OK "
TASK_METHOD=".*Satellites Natural/Artificial.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_list_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Exact List Match Fail)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Other Planets.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_list_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Within List Match Success)"
TASK_STATUS=" OK "
TASK_METHOD=".*Periastron/Apastron.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_within_list_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 (Test of Within List Match Fail)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Inclination/Axial Tilt.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_within_list_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

# Comparison tasks for the rose_ana_t2 task(s)
TASK_NAME="rose_ana_t2_activated (First Test)"
TASK_STATUS="FAIL"
TASK_METHOD=".*Species.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t2_ignore_basic_1
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t2_activated (Second Test)"
TASK_STATUS=" OK "
TASK_METHOD=".*Class.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t2_ignore_basic_2
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

# Specifically test that there is *no* entry for the ignored task
TASK_NAME="rose_ana_t2_deactivated (Second Test)"
TASK_STATUS=" OK "
TASK_METHOD=".*Species.*"
TEST_KEY=$TEST_KEY_BASE-db_check_t2_ignore_notpresent
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS | $TASK_METHOD"
file_grep_fail $TEST_KEY "$REGEXP" $OUTPUT

#-------------------------------------------------------------------------------
#Clean suite
rose suite-clean -q -y $NAME
#-------------------------------------------------------------------------------
exit 0
