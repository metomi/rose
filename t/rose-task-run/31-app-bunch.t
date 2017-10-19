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
# Test rose_bunch built-in application.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 52
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
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
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* $ARGVALUE: added to pool"\
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
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* Adding command 2 to pool: banana" $FILE
file_grep $TEST_KEY_PREFIX-skip \
    "\[SKIP\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  2: banana" $FILE
FILE=$LOG_DIR/$APP/NN/job.err
file_grep $TEST_KEY_PREFIX-record-error \
    "\[FAIL\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 1 # return-code=127, stderr=" $FILE
file_grep $TEST_KEY_PREFIX-output-error \
    "\[FAIL\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* .*: oops:.* not found" $FILE
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
    "\[FAIL\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 1 # return-code=1" $FILE
FILE=$LOG_DIR/$APP/01/job.out
file_grep $TEST_KEY_PREFIX-ran-0 \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 0: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-ran-1 \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 1: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-ran-2 \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 2: added to pool" $FILE
#-------------------------------------------------------------------------------
# Second run files
#-------------------------------------------------------------------------------
FILE=$LOG_DIR/$APP/02/job.out
file_grep_fail $TEST_KEY_PREFIX-not-ran-0 \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 0: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-skip-0 \
    "\[PASS\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  0" $FILE
file_grep $TEST_KEY_PREFIX-reran-1 \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 1: added to pool" $FILE
file_grep_fail $TEST_KEY_PREFIX-not-ran-2 \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 2: added to pool" $FILE
file_grep $TEST_KEY_PREFIX-skip-2 \
    "\[PASS\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  2" $FILE
#-------------------------------------------------------------------------------
# Testing works ok with double digit population size
#-------------------------------------------------------------------------------
APP=bunch_bigpop
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=big-pop
FILE=$LOG_DIR/$APP/01/job.out
for INSTANCE in $(seq 0 14); do
    file_grep $TEST_KEY_PREFIX-ran-$INSTANCE "\[OK\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  $INSTANCE" $FILE
done
#-------------------------------------------------------------------------------
# Testing names works ok
#-------------------------------------------------------------------------------
APP=bunch_names
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=names
FILE=$LOG_DIR/$APP/01/job.out
for KEY in foo bar baz qux; do
    file_grep $TEST_KEY_PREFIX-ran-$KEY "\[OK\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  $KEY" $FILE
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
file_grep $TEST_KEY_PREFIX-ran-0 "\[OK\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  0" $FILE_PREFIX.out
file_grep $TEST_KEY_PREFIX-fail-1 "\[FAIL\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 1" $FILE_PREFIX.err
file_grep $TEST_KEY_PREFIX-ran-2 "\[OK\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]*  2" $FILE_PREFIX.out
#-------------------------------------------------------------------------------
# Second run files
#-------------------------------------------------------------------------------
FILE=$LOG_DIR/$APP/02/job.err
file_grep $TEST_KEY_PREFIX-fail-1 "\[FAIL\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* 1" $FILE
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
rose suite-clean -q -y $NAME
exit 0
