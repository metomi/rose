#!/usr/bin/env bash
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
# Test rose_ana built-in application, basic usage of builtin grepper module
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 82
#-------------------------------------------------------------------------------

# The database test is only valid if the user has set things up to use it, so
# provide a simple config here which turns it on
mkdir -p conf
cat >conf/rose.conf <<'__CONF__'
[rose-ana]
kgo-database=.true.
__CONF__

# Run the suite.
get_reg
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=$PWD/conf

TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "$TEST_KEY" \
    cylc install \
        "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --workflow-name="${FLOW}" \
        --no-run-name

TEST_KEY="${TEST_KEY_BASE}-run"
run_fail "$TEST_KEY" \
    cylc play \
        "${FLOW}" \
        --host=localhost \
        --no-detach \
        --debug

#-------------------------------------------------------------------------------
# Test the output
#
# Note that t1 and t5 are identical except t5 uses threading, so use a loop here
for t in t1 t5 ; do
  OUTPUT="${FLOW_RUN_DIR}/log/job/1/rose_ana_$t/01/job.out"
  file_pcregrep "${TEST_KEY_BASE}-$t-exact_list_fail" \
      'Running task #([0-9]+).*\n.*Exact List Match Fail.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-exact_list_success" \
      'Running task #([0-9]+).*\n.*Exact List Match Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-exact_numeric_fail" \
      'Running task #([0-9]+).*\n.*Exact Numeric Match Fail.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-exact_numeric_success" \
      'Running task #([0-9]+).*\n.*Exact Numeric Match Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-exact_text_fail" \
      'Running task #([0-9]+).*\n.*Exact Text Match Fail.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-exact_text_success" \
      'Running task #([0-9]+).*\n.*Exact Text Match Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-within_list_fail" \
      'Running task #([0-9]+).*\n.*Within List Match Fail.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-within_list_success" \
      'Running task #([0-9]+).*\n.*Within List Match Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-within_absolute_fail" \
      'Running task #([0-9]+).*\n.*Within Match Absolute Fail.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-within_absolute_success" \
      'Running task #([0-9]+).*\n.*Within Match Absolute Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-within_percentage_fail" \
      'Running task #([0-9]+).*\n.*Within Match Percentage Fail.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-within_percentage_success" \
      'Running task #([0-9]+).*\n.*Within Match Percentage Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-simple_command_success" \
      'Running task #([0-9]+).*\n.*Simple-Command Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-simple_command_fail" \
      'Running task #([0-9]+).*\n.*Simple-Command Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-file_command_success" \
      'Running task #([0-9]+).*\n.*File-Command Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-file_command_fail" \
      'Running task #([0-9]+).*\n.*File-Command Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-simple_command_pattern_success" \
      'Running task #([0-9]+).*\n.*Simple-Command Pattern Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-simple_command_pattern_fail" \
      'Running task #([0-9]+).*\n.*Simple-Command Pattern Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-file_command_pattern_success" \
      'Running task #([0-9]+).*\n.*File-Command Pattern Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-file_command_pattern_fail" \
      'Running task #([0-9]+).*\n.*File-Command Pattern Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-file_command_fail_but_pattern_success" \
      'Running task #([0-9]+).*\n.*File-Command Fail but Pattern Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-multi_command_success" \
      'Running task #([0-9]+).*\n.*Multi-Command Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-multi_command_fail" \
      'Running task #([0-9]+).*\n.*Multi-Command Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-multi_group_success" \
      'Running task #([0-9]+).*\n.*Multi-Group Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-multi_group_fail" \
      'Running task #([0-9]+).*\n.*Multi-Group Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-multi_group_multi_occurence_success" \
      'Running task #([0-9]+).*\n.*Multi-Group Multi-Occurence Success.*\n.*Task #\1 passed' \
      "${OUTPUT}"
  file_pcregrep "${TEST_KEY_BASE}-$t-multi_group_multi_occurence_fail" \
      'Running task #([0-9]+).*\n.*Multi-Group Multi-Occurence Failure.*\n.*Task #\1 did not pass' \
      "${OUTPUT}"
done

# Now check that the threading option is reflected in the output
OUTPUT="${FLOW_RUN_DIR}/log/job/1/rose_ana_t1/01/job.out"
TEST_KEY=$TEST_KEY_BASE-t1-serial_statement
REGEXP="Running in SERIAL mode"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

OUTPUT="${FLOW_RUN_DIR}/log/job/1/rose_ana_t5/01/job.out"
TEST_KEY=$TEST_KEY_BASE-t5-threading_statement
REGEXP="Running in THREADED mode, with 4 threads"
file_grep $TEST_KEY "$REGEXP" $OUTPUT

#-------------------------------------------------------------------------------
# Test of ignoring a task
# First, test that the basic task ran ok
OUTPUT="${FLOW_RUN_DIR}/log/job/1/rose_ana_t2_activated/01/job.out"
file_pcregrep "${TEST_KEY_BASE}-ignore-basic-1" \
    'Running task #([0-9]+).*\n.*First Test.*\n.*Task #\1 did not pass' \
    "${OUTPUT}"
file_pcregrep "${TEST_KEY_BASE}-ignore-basic-2" \
    'Running task #([0-9]+).*\n.*Second Test.*\n.*Task #\1 passed' "${OUTPUT}"
# Then test that ignoring a test means the output is not present
file_pcregrep "${TEST_KEY_BASE}-ignore-notpresent" \
    'Running task #([0-9]+).*\n.*Second Test.*\n.*Task #\1 passed' \
    "${FLOW_RUN_DIR}/log/job/1/rose_ana_t2_deactivated/01/job.out"
#-------------------------------------------------------------------------------
# Test tolerance as an environment variable
# First, test that the basic task ran ok
file_pcregrep "${TEST_KEY_BASE}-tolerance-env-var-pass" \
    'Running task #([0-9]+).*\n.*First Test.*\n.*Task #\1 passed' \
    "${FLOW_RUN_DIR}/log/job/1/rose_ana_t3_within_tolerance/01/job.out"
file_pcregrep "${TEST_KEY_BASE}-tolerance-env-var-fail" \
    'Running task #([0-9]+).*\n.*First Test.*\n.*Task #\1 did not pass' \
    "${FLOW_RUN_DIR}/log/job/1/rose_ana_t3_outside_tolerance/01/job.out"
#-------------------------------------------------------------------------------

# Test of comparison database
#
# Regexp for any number of digits (re-used a lot below)
COMP_NUMBER="[0-9][0-9]*"

OUTPUT="$FLOW_RUN_DIR/log/job/1/db_check/01/job.out"
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
# Test of a few config options

OUTPUT="${FLOW_RUN_DIR}/log/job/1/rose_ana_t4/01/job.out"
file_pcregrep "${TEST_KEY_BASE}-report_limit_working" \
    'Running task #([0-9]+).*Check report limit is active.*Some output omitted due to limit.*Task #\1 passed' \
    "${OUTPUT}"
file_pcregrep "${TEST_KEY_BASE}-missing_skip_working" \
    'Running task #(\d+).*\n.*Check non-existent files are skipped.*\n.*All file arguments are missing, skipping task.*\n.*Task #\1 skipped by method' \
    "${OUTPUT}"

#-------------------------------------------------------------------------------
purge
exit 0
