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
tests 15
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=

get_reg
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "$TEST_KEY" \
    cylc install \
        "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --workflow-name="$FLOW" \
        --no-run-name
TEST_KEY="${TEST_KEY_BASE}-play-1"
run_pass "$TEST_KEY" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
CYCLE=20100101T0000Z
LOG_DIR="$FLOW_RUN_DIR/log/job/$CYCLE"
#-------------------------------------------------------------------------------
# Testing successful runs
#-------------------------------------------------------------------------------
APP=buncher
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
# Run suite a second time
# TODO: replace with cylc clean when required functionality is implemented
rm -rf "${FLOW_RUN_DIR}/log"
rm -rf "${FLOW_RUN_DIR}/.service/db"
run_pass "$TEST_KEY-play-2" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
# Confirm launching set of commands
TEST_KEY_PREFIX=launch-ok-2nd-run
FILE=$LOG_DIR/$APP/NN/job.out
for ARGVALUE in 0 1 2 3; do
    TEST_KEY=$TEST_KEY_PREFIX-$ARGVALUE
    file_grep $TEST_KEY \
    "\[INFO\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* $ARGVALUE: added to pool"\
     $FILE
done
#-------------------------------------------------------------------------------
purge
exit 0
