#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
# Test rose_ana built-in application, basic usage of builtin grepper module
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=50
tests $N_TESTS
#-------------------------------------------------------------------------------

# The database test is only valid if the user has set things up to use it, so
# provide a simple config here which turns it on
mkdir -p conf
cat >conf/rose.conf <<'__CONF__'
[rose-ana]
kgo-database=.true.
__CONF__

# Run the suite.
export ROSE_CONF_PATH=$PWD/conf
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_fail "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
# Test the output
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t1/01/job.out
TEST_KEY=$TEST_KEY_BASE-exact_list_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Exact List Match Fail.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_list_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Exact List Match Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_numeric_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Exact Numeric Match Fail.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_numeric_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Exact Numeric Match Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_text_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Exact Text Match Fail.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-exact_text_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Exact Text Match Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_list_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Within List Match Fail.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_list_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Within List Match Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_absolute_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Within Match Absolute Fail.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_absolute_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Within Match Absolute Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_percentage_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Within Match Percentage Fail.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-within_percentage_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Within Match Percentage Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-simple_command_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Simple-Command Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-simple_command_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Simple-Command Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-file_command_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*File-Command Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-file_command_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*File-Command Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-simple_command_pattern_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Simple-Command Pattern Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-simple_command_pattern_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Simple-Command Pattern Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-file_command_pattern_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*File-Command Pattern Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-file_command_pattern_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*File-Command Pattern Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-file_command_fail_but_pattern_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*File-Command Fail but Pattern Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi_command_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Multi-Command Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi_command_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Multi-Command Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi_group_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Multi-Group Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi_group_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Multi-Group Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi_group_multi_occurence_success
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Multi-Group Multi-Occurence Success.*(\n.*)*Task #\1 passed" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-multi_group_multi_occurence_fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Multi-Group Multi-Occurence Failure.*(\n.*)*Task #\1 did not pass" $OUTPUT
#-------------------------------------------------------------------------------
# Test of ignoring a task
# First, test that the basic task ran ok
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t2_activated/01/job.out
TEST_KEY=$TEST_KEY_BASE-ignore-basic-1
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*First Test.*(\n.*)*Task #\1 did not pass" $OUTPUT
TEST_KEY=$TEST_KEY_BASE-ignore-basic-2
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Second Test.*(\n.*)*Task #\1 passed" $OUTPUT
# Then test that ignoring a test means the output is not present
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t2_deactivated/01/job.out
TEST_KEY=$TEST_KEY_BASE-ignore-notpresent
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*Second Test.*(\n.*)*Task #\1 passed" $OUTPUT
#-------------------------------------------------------------------------------
# Test tolerance as an environment variable
# First, test that the basic task ran ok
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t3_within_tolerance/01/job.out
TEST_KEY=$TEST_KEY_BASE-tolerance-env-var-pass
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*First Test.*(\n.*)*Task #\1 passed" $OUTPUT
OUTPUT=$HOME/cylc-run/$NAME/log/job/1/rose_ana_t3_outside_tolerance/01/job.out
TEST_KEY=$TEST_KEY_BASE-tolerance-env-var-fail
file_pcregrep $TEST_KEY "Running task #([0-9]+).*\n.*First Test.*(\n.*)*Task #\1 did not pass" $OUTPUT
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
TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Exact Numeric Match Success)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_numeric_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Exact Numeric Match Fail)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_numeric_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Exact Text Match Success)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_text_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Exact Text Match Fail)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_text_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Within Match Percentage Success)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t1_percentage_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Within Match Percentage Fail)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_percentage_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Within Match Absolute Success)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t1_absolute_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Within Match Absolute Fail)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_absolute_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Exact List Match Success)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_list_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Exact List Match Fail)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_exact_list_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Within List Match Success)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t1_within_list_success
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t1 - grepper.FilePattern(Test of Within List Match Fail)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t1_within_list_fail
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

# Comparison tasks for the rose_ana_t2 task(s)
TASK_NAME="rose_ana_t2_activated - grepper.FilePattern(First Test)"
TASK_STATUS="FAIL"
TEST_KEY=$TEST_KEY_BASE-db_check_t2_ignore_basic_1
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

TASK_NAME="rose_ana_t2_deactivated - grepper.FilePattern(Second Test)"
TASK_STATUS=" OK "
TEST_KEY=$TEST_KEY_BASE-db_check_t2_ignore_basic_2
REGEXP="$COMP_NUMBER | $TASK_NAME | $COMP_FILES | $TASK_STATUS"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

#-------------------------------------------------------------------------------
#Clean suite
rose suite-clean -q -y $NAME
#-------------------------------------------------------------------------------
exit 0
