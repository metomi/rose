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
skip_all "TEST-DISABLED: Awaiting App upgrade to Python3"
#-------------------------------------------------------------------------------
tests 26
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --no-detach --debug
#-------------------------------------------------------------------------------
CYCLE=20100101T0000Z
LOG_DIR="$SUITE_RUN_DIR/log/job/$CYCLE"
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
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --no-detach --debug
#-------------------------------------------------------------------------------
# Testing successful rerun
#-------------------------------------------------------------------------------
for TASK in buncher_default buncher_import; do
#-------------------------------------------------------------------------------
# Confirm launching set of commands
    TEST_KEY_PREFIX=launch-ok-2nd-run
    FILE=$LOG_DIR/$TASK/NN/job.out
    for INSTANCE in 0 1 2 3; do
        TEST_KEY=$TEST_KEY_PREFIX-$INSTANCE
        file_grep $TEST_KEY \
        "\[INFO\] [-0-9]*T[+:0-9]* $INSTANCE: added to pool"\
         $FILE
    done
#-------------------------------------------------------------------------------
done
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
