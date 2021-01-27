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
# Test "rose task-run" and "rose task-env", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

export ROSE_CONF_PATH=

tests 48

#-------------------------------------------------------------------------------
# Run the suite.
get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="${FLOW}" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-run" \
    cylc run \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
MY_PATH=
for P in $(ls -d $FLOW_RUN_DIR/etc/my-path/*); do
    if [[ -n $MY_PATH ]]; then
        MY_PATH="$P:$MY_PATH"
    else
        MY_PATH="$P"
    fi
done
if [[ -d $FLOW_RUN_DIR/etc/your-path ]]; then
    if [[ -n $MY_PATH ]]; then
        MY_PATH="$FLOW_RUN_DIR/etc/your-path:$MY_PATH"
    else
        MY_PATH="$FLOW_RUN_DIR/etc/your-path"
    fi
fi
PREV_CYCLE=
for CYCLE in 20130101T0000Z 20130101T1200Z 20130102T0000Z; do
    TEST_KEY=$TEST_KEY_BASE-file-$CYCLE
    TASK=my_task_1
    FILE="$FLOW_RUN_DIR/log/job/$CYCLE/$TASK/01/job.txt"
    file_test "$TEST_KEY" $FILE
    file_grep "$TEST_KEY-ROSE_SUITE_DIR" "ROSE_SUITE_DIR=$FLOW_RUN_DIR" $FILE
    file_grep "$TEST_KEY-ROSE_SUITE_DIR_REL" \
        "ROSE_SUITE_DIR_REL=${FLOW_RUN_DIR#$HOME/}" $FILE
    file_grep "$TEST_KEY-ROSE_SUITE_NAME" "ROSE_SUITE_NAME=${FLOW}" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_NAME" "ROSE_TASK_NAME=$TASK" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_CYCLE_TIME" \
        "ROSE_TASK_CYCLE_TIME=$CYCLE" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_LOG_DIR" \
        "ROSE_TASK_LOG_DIR=${FILE%/job.txt}" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_LOG_ROOT" \
        "ROSE_TASK_LOG_ROOT=${FILE%job.txt}job" $FILE
    file_grep "$TEST_KEY-ROSE_DATA" "ROSE_DATA=$FLOW_RUN_DIR/share/data" $FILE
    file_grep "$TEST_KEY-ROSE_DATAC" \
        "ROSE_DATAC=$FLOW_RUN_DIR/share/cycle/$CYCLE" $FILE
    if [[ -n $PREV_CYCLE ]]; then
        file_grep "$TEST_KEY-ROSE_DATACPT12H" \
            "ROSE_DATACPT12H=$FLOW_RUN_DIR/share/cycle/$PREV_CYCLE" $FILE
    fi
    file_grep "$TEST_KEY-ROSE_ETC" "ROSE_ETC=$FLOW_RUN_DIR/etc" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_PREFIX" "ROSE_TASK_PREFIX=my" $FILE
    file_grep "$TEST_KEY-ROSE_TASK_SUFFIX" "ROSE_TASK_SUFFIX=1" $FILE
    file_grep "$TEST_KEY-MY_PATH" "MY_PATH=$MY_PATH" $FILE
    PREV_CYCLE=$CYCLE
done
# Test ROSE_DATAC__???? (offset to a future cycle)
NEXT_CYCLE=
for CYCLE in 20130102T0000Z 20130101T1200Z 20130101T0000Z; do
    if [[ -n "${NEXT_CYCLE}" ]]; then
        TEST_KEY="${TEST_KEY_BASE}-file-${CYCLE}"
        FILE="${HOME}/cylc-run/${FLOW}/log/job/${CYCLE}/my_task_1/01/job.txt"
        file_grep "${TEST_KEY}-ROSE_DATAC__PT12H" \
            "ROSE_DATAC__PT12H=${FLOW_RUN_DIR}/share/cycle/${NEXT_CYCLE}" \
            "${FILE}"
    fi
    NEXT_CYCLE="${CYCLE}"
done
#-------------------------------------------------------------------------------
purge
exit 0
