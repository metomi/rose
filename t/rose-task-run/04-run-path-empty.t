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
# Test "rose task-run --path=", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

export ROSE_CONF_PATH=

#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
# Run the suite.
get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="$FLOW" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-run" \
    cylc run \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
PREV_CYCLE=
for CYCLE in 20130101T0000Z 20130101T1200Z 20130102T0000Z; do
    TEST_KEY=$TEST_KEY_BASE-file-$CYCLE
    TASK=my_task_1
    FILE="$FLOW_RUN_DIR/log/job/$CYCLE/$TASK/01/job.txt"
    file_grep "$TEST_KEY-PATH" \
        "PATH=$FLOW_RUN_DIR/app/$TASK/bin:$FLOW_RUN_DIR/etc/your-path" $FILE
    PREV_CYCLE=$CYCLE
done
#-------------------------------------------------------------------------------
purge
exit 0
