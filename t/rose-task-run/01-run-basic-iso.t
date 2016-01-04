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
# Test "rose task-run" and "rose task-env", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=

#-------------------------------------------------------------------------------
# Run the suite.
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME -l \
    1>/dev/null 2>&1
if (($? != 0)); then
    skip_all "cylc version not compatible with ISO 8601"
    exit 0
fi
#-------------------------------------------------------------------------------
tests 44
#-------------------------------------------------------------------------------
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
MY_PATH=
for P in $(ls -d $SUITE_RUN_DIR/etc/my-path/*); do
    if [[ -n $MY_PATH ]]; then
        MY_PATH="$P:$MY_PATH"
    else
        MY_PATH="$P"
    fi
done
if [[ -d $SUITE_RUN_DIR/etc/your-path ]]; then
    if [[ -n $MY_PATH ]]; then
        MY_PATH="$SUITE_RUN_DIR/etc/your-path:$MY_PATH"
    else
        MY_PATH="$SUITE_RUN_DIR/etc/your-path"
    fi
fi
PREV_CYCLE=
for CYCLE in 20130101T0000Z 20130101T1200Z 20130102T0000Z; do
    TEST_KEY=$TEST_KEY_BASE-file-$CYCLE
    TASK=my_task_1
    FILE=$HOME/cylc-run/$NAME/log/job/$CYCLE/$TASK/01/job.txt
    file_test "$TEST_KEY" $FILE
    file_grep "$TEST_KEY-ROSE_SUITE_DIR" "ROSE_SUITE_DIR=$SUITE_RUN_DIR" $FILE
    file_grep "$TEST_KEY-ROSE_SUITE_DIR_REL" \
        "ROSE_SUITE_DIR_REL=${SUITE_RUN_DIR#$HOME/}" $FILE
    file_grep "$TEST_KEY-ROSE_SUITE_NAME" "ROSE_SUITE_NAME=$NAME" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_NAME" "ROSE_TASK_NAME=$TASK" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_CYCLE_TIME" \
        "ROSE_TASK_CYCLE_TIME=$CYCLE" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_LOG_DIR" \
        "ROSE_TASK_LOG_DIR=${FILE%/job.txt}" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_LOG_ROOT" \
        "ROSE_TASK_LOG_ROOT=${FILE%job.txt}job" $FILE
    file_grep "$TEST_KEY-ROSE_DATA" "ROSE_DATA=$SUITE_RUN_DIR/share/data" $FILE
    file_grep "$TEST_KEY-ROSE_DATAC" \
        "ROSE_DATAC=$SUITE_RUN_DIR/share/cycle/$CYCLE" $FILE
    if [[ -n $PREV_CYCLE ]]; then
        file_grep "$TEST_KEY-ROSE_DATACPT12H" \
            "ROSE_DATACPT12H=$SUITE_RUN_DIR/share/cycle/$PREV_CYCLE" $FILE
    fi
    file_grep "$TEST_KEY-ROSE_ETC" "ROSE_ETC=$SUITE_RUN_DIR/etc" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_PREFIX" "ROSE_TASK_PREFIX=my" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_SUFFIX" "ROSE_TASK_SUFFIX=1" $FILE
    file_grep "$TEST_KEY-MY_PATH" "MY_PATH=$MY_PATH" $FILE
    PREV_CYCLE=$CYCLE
done
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
