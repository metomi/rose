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
# Test rose_bunch built-in application.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 67
#-------------------------------------------------------------------------------
# Define some constant patterns
FAIL_PATTERN="\[FAIL\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*"
INFO_PATTERN="\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*"
OK_PATTERN="\[OK\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*"
PASS_PATTERN="\[PASS\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*"
SKIP_PATTERN="\[SKIP\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*"
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --host=localhost -- --no-detach --debug
#-------------------------------------------------------------------------------
CYCLE=20100101T0000Z
LOG_DIR="$SUITE_RUN_DIR/log/job/$CYCLE"
#-------------------------------------------------------------------------------
# Testing successful runs
#-------------------------------------------------------------------------------
APP=bunch
#-------------------------------------------------------------------------------
# Confirm launching set of commands
TEST_KEY_PREFIX=launch-ok
FILE=$LOG_DIR/$APP/NN/job.out
for ARGVALUE in 0 1 2 3; do
    TEST_KEY=$TEST_KEY_PREFIX-$ARGVALUE
    file_grep $TEST_KEY \
    "$INFO_PATTERN $ARGVALUE: added to pool"\
     $FILE
done
#-------------------------------------------------------------------------------
# Check output to separate files is correct
TEST_KEY_PREFIX=check-logs
FILE_PREFIX=$LOG_DIR/$APP/NN
for ARGVALUE in 0 1 2 3; do
    TEST_KEY=$TEST_KEY_PREFIX-$ARGVALUE
    file_grep $TEST_KEY \
        "arg1: $(expr $ARGVALUE + 1)" $FILE_PREFIX/bunch.$ARGVALUE.out
done
#-------------------------------------------------------------------------------
# Testing abort on fail
#-------------------------------------------------------------------------------
APP=bunch_fail
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=abort-on-fail
FILE=$LOG_DIR/$APP/NN/job.out
file_grep_fail $TEST_KEY_PREFIX-no-run \
    "$INFO_PATTERN Adding command 2 to pool: banana" $FILE
file_grep $TEST_KEY_PREFIX-skip \
    "$SKIP_PATTERN  2: banana" $FILE
FILE=$LOG_DIR/$APP/NN/job.err
file_grep $TEST_KEY_PREFIX-record-error \
    "$FAIL_PATTERN 1 # return-code=1" $FILE
#-------------------------------------------------------------------------------
# Testing incremental mode
#-------------------------------------------------------------------------------
APP=bunch_incremental
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=incremental
#-------------------------------------------------------------------------------
# First run files
#-------------------------------------------------------------------------------
FILE=$LOG_DIR/$APP/01/job.err
file_grep $TEST_KEY_PREFIX-record-error \
    "$FAIL_PATTERN 1 # return-code=1" $FILE
FILE=$LOG_DIR/$APP/01/job.out
file_grep $TEST_KEY_PREFIX-ran-0 \
    "$INFO_PATTERN 0: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-ran-1 \
    "$INFO_PATTERN 1: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-ran-2 \
    "$INFO_PATTERN 2: added to pool" $FILE
#-------------------------------------------------------------------------------
# Second run files
#-------------------------------------------------------------------------------
FILE=$LOG_DIR/$APP/02/job.out
file_grep_fail $TEST_KEY_PREFIX-not-ran-0 \
    "$INFO_PATTERN 0: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-skip-0 \
    "$PASS_PATTERN  0" $FILE
file_grep $TEST_KEY_PREFIX-reran-1 \
    "$INFO_PATTERN 1: added to pool" $FILE
file_grep_fail $TEST_KEY_PREFIX-not-ran-2 \
    "$INFO_PATTERN 2: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-skip-2 \
    "$PASS_PATTERN  2" $FILE
#-------------------------------------------------------------------------------
# Testing works ok with double digit population size
#-------------------------------------------------------------------------------
APP=bunch_bigpop
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=big-pop
FILE=$LOG_DIR/$APP/01/job.out
for INSTANCE in $(seq 0 14); do
    file_grep $TEST_KEY_PREFIX-ran-$INSTANCE "$OK_PATTERN  $INSTANCE" $FILE
done
#-------------------------------------------------------------------------------
# Testing names works ok
#-------------------------------------------------------------------------------
APP=bunch_names
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=names
FILE=$LOG_DIR/$APP/01/job.out
for KEY in foo bar baz qux; do
    file_grep $TEST_KEY_PREFIX-ran-$KEY "$OK_PATTERN  $KEY" $FILE
done
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Testing names works ok
#-------------------------------------------------------------------------------
APP=bunch_env_pass
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=env_vars
FILE_PREFIX=$LOG_DIR/$APP/01/job
#-------------------------------------------------------------------------------
# First run files
#-------------------------------------------------------------------------------
file_grep $TEST_KEY_PREFIX-ran-0 "$OK_PATTERN  0" $FILE_PREFIX.out
file_grep $TEST_KEY_PREFIX-fail-1 "$FAIL_PATTERN 1" $FILE_PREFIX.err
file_grep $TEST_KEY_PREFIX-ran-2 "$OK_PATTERN  2" $FILE_PREFIX.out
#-------------------------------------------------------------------------------
# Second run files
#-------------------------------------------------------------------------------
FILE=$LOG_DIR/$APP/02/job.err
file_grep $TEST_KEY_PREFIX-fail-1 "$FAIL_PATTERN 1" $FILE
#-------------------------------------------------------------------------------
FILE_DIR=$LOG_DIR/$APP/01/
for KEY in $(seq 0 2); do
    file_grep $TEST_KEY_PREFIX-cmd_eval_ran-$KEY \
        "a comment" $FILE_DIR/bunch.$KEY.out
done
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Testing ROSE_BUNCH_LOG_PREFIX is correctly set
#-------------------------------------------------------------------------------
APP=bunch_print_envar
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=log_prefix
FILE_DIR=$LOG_DIR/$APP/01/
for KEY in $(seq 0 3); do
    file_grep $TEST_KEY_PREFIX-ok-$KEY \
        "ROSE_BUNCH_LOG_PREFIX: $KEY" $FILE_DIR/bunch.$KEY.out
done
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Testing ROSE_BUNCH_ARGUMENT_MODE_IZIP shortens all bunch-args to the length
# of the shortest bunch-arg
#-------------------------------------------------------------------------------
APP=bunch_argument_mode_izip
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=argument_mode_izip
FILE=$LOG_DIR/$APP/01/job.out
ARG1=1
ARG2=a
ARG3=9
file_grep "$TEST_KEY_PREFIX-RUN-$ARG1-$ARG2-$ARG3" \
    "$INFO_PATTERN echo arg1: $ARG1 - arg2: $ARG2 - arg3: $ARG3" \
    "$FILE"
file_grep "$TEST_KEY_PREFIX-TOTAL-RAN" \
    "$INFO_PATTERN TOTAL: 1" \
    "$FILE"
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Testing ROSE_BUNCH_ARGUMENT_MODE_IZIP_LONGEST lengthens all bunch-args to
# the length of the longest bunch-arg, padding any which are shorter with
# empty arguments
#-------------------------------------------------------------------------------
APP=bunch_argument_mode_izip_longest
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=argument_mode_izip_longest
FILE=$LOG_DIR/$APP/01/job.out
# Four permutations should exist from the izip_longest bunch run
# There are three arguments in bunch-args of varying length, so the expected
# arguments are in comma separated values to show what each bunch-args values
# are expected to become, where no value indicates an empty string
for VALUES in 1,a,9 2,,23 3,, 4,,; do
    # Split VALUES on ',' into an ARGS array to account for empty strings
    IFS=, read -r -a ARGS <<< "$VALUES"
    EXPECTED_LINE="echo arg1: ${ARGS[0]:-} - arg2: ${ARGS[1]:-}"
    EXPECTED_LINE="$EXPECTED_LINE - arg3: ${ARGS[2]:-}"
    file_grep "$TEST_KEY_PREFIX-RUN-${ARGS[0]:-}-${ARGS[1]:-}-${ARGS[2]:-}" \
        "$INFO_PATTERN $EXPECTED_LINE" \
        "$FILE"
done
file_grep "$TEST_KEY_PREFIX-TOTAL-RAN" \
    "$INFO_PATTERN TOTAL: 4" \
    "$FILE"
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Testing ROSE_BUNCH_ARGUMENT_MODE_PRODUCT updates all bunch-args to be all
# possible permutations for the provided bunch-args
#-------------------------------------------------------------------------------
APP=bunch_argument_mode_product
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=argument_mode_product
FILE=$LOG_DIR/$APP/01/job.out
# Product mode creates all permutations, so loop over all permutations and
# check that they exist in the log output
for ARG1 in 1 2 3 4; do
    for ARG2 in a; do
        for ARG3 in 9 23; do
            file_grep "$TEST_KEY_PREFIX-RUN-$ARG1-$ARG2-$ARG3" \
                "$INFO_PATTERN echo arg1: $ARG1 - arg2: $ARG2 - arg3: $ARG3"\
                "$FILE"
        done
    done
done
file_grep "$TEST_KEY_PREFIX-TOTAL-RAN" \
    "$INFO_PATTERN TOTAL: 8" \
    "$FILE"
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
