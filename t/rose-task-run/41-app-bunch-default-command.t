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
tests 27
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=

get_reg
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "$TEST_KEY" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="$FLOW" \
        --no-run-name
TEST_KEY="${TEST_KEY_BASE}-run"
run_pass "$TEST_KEY" \
    cylc run \
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
OFFSET=1
for TASK in buncher_default buncher_import; do
#-------------------------------------------------------------------------------
# Confirm launching set of commands
    TEST_KEY_PREFIX=launch-ok
    FILE=$LOG_DIR/$TASK/NN/job.out
    for INSTANCE in 0 1 2 3; do
        TEST_KEY=$TEST_KEY_PREFIX-$INSTANCE
        file_grep $TEST_KEY \
        "\[INFO\] [-0-9]*T[+:0-9]* $INSTANCE: added to pool"\
         $FILE
    done
#-------------------------------------------------------------------------------
# Check output to separate files is correct
    TEST_KEY_PREFIX=check-logs
    FILE_PREFIX=$LOG_DIR/$TASK/NN
    for INSTANCE in 0 1 2 3; do
        TEST_KEY=$TEST_KEY_PREFIX-$INSTANCE
        file_grep $TEST_KEY \
            "$TASK: $((INSTANCE + OFFSET))" $FILE_PREFIX/bunch.$INSTANCE.out
    done
#-------------------------------------------------------------------------------
    OFFSET=$((OFFSET+4))
done
#-------------------------------------------------------------------------------
# Run suite a second time
# TODO: replace with cylc run --rerun / cylc clean
rm -rf "${FLOW_RUN_DIR}/log"
rm -rf "${FLOW_RUN_DIR}/.service/db"
run_pass "$TEST_KEY" \
    cylc run "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
# Testing successful rerun
#-------------------------------------------------------------------------------
# Confirm launching set of commands
for TASK in buncher_default buncher_import; do
    TEST_KEY_PREFIX=launch-ok-2nd-run
    FILE=$LOG_DIR/$TASK/NN/job.out
    for INSTANCE in 0 1 2 3; do
        TEST_KEY=$TEST_KEY_PREFIX-$INSTANCE
        file_grep $TEST_KEY \
        "\[INFO\] [-0-9]*T[+:0-9]* $INSTANCE: added to pool"\
         $FILE
    done
done
#-------------------------------------------------------------------------------
purge
exit 0
