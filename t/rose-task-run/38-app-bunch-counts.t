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
# Test rose_bunch built-in application.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 17
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "$TEST_KEY" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="$NAME" \
        --no-run-name \
TEST_KEY="${TEST_KEY_BASE}-run"
run_pass "$TEST_KEY" \
    cylc run \
        "${NAME}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
CYCLE=1
LOG_DIR="$SUITE_RUN_DIR/log/job/$CYCLE"
#-------------------------------------------------------------------------------
# Testing successful runs
#-------------------------------------------------------------------------------
APP=cutoff
#-------------------------------------------------------------------------------
# Confirm counts are correct for first try
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=counts-try-1
FILE=$LOG_DIR/$APP/01/job.out

TEST_KEY=${TEST_KEY_PREFIX}-OK
file_grep $TEST_KEY "\[INFO\] OK: 2" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-FAIL
file_grep $TEST_KEY "\[INFO\] FAIL: 1" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-SKIP
file_grep $TEST_KEY "\[INFO\] SKIP: 0" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-NOTCONSIDERED
file_grep $TEST_KEY "\[INFO\] NOT CONSIDERED: 2" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-TOTAL
file_grep $TEST_KEY "\[INFO\] TOTAL: 5" $FILE

#-------------------------------------------------------------------------------
# Confirm counts are correct for second try
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=counts-try-2
FILE=$LOG_DIR/$APP/02/job.out

TEST_KEY=${TEST_KEY_PREFIX}-OK
file_grep $TEST_KEY "\[INFO\] OK: 1" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-FAIL
file_grep $TEST_KEY "\[INFO\] FAIL: 1" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-SKIP
file_grep $TEST_KEY "\[INFO\] SKIP: 2" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-NOTCONSIDERED
file_grep $TEST_KEY "\[INFO\] NOT CONSIDERED: 1" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-TOTAL
file_grep $TEST_KEY "\[INFO\] TOTAL: 5" $FILE

#-------------------------------------------------------------------------------
# Confirm counts are correct for third try
#-------------------------------------------------------------------------------
TEST_KEY_PREFIX=counts-try-3
FILE=$LOG_DIR/$APP/03/job.out

TEST_KEY=${TEST_KEY_PREFIX}-OK
file_grep $TEST_KEY "\[INFO\] OK: 2" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-FAIL
file_grep $TEST_KEY "\[INFO\] FAIL: 0" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-SKIP
file_grep $TEST_KEY "\[INFO\] SKIP: 3" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-NOTCONSIDERED
file_grep $TEST_KEY "\[INFO\] NOT CONSIDERED: 0" $FILE

TEST_KEY=${TEST_KEY_PREFIX}-TOTAL
file_grep $TEST_KEY "\[INFO\] TOTAL: 5" $FILE

#-------------------------------------------------------------------------------
cylc clean $NAME
exit 0
