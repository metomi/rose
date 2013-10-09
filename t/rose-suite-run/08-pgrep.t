#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
#
# This file is part of Rose, a framework for scientific suites.
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
# Test "rose suite-run" when a running suite's port file is removed,
# so will rely on pgrep to detect whether it is still running or not.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/.cylc/ports
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
set -e
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
TIME_OUT=$(($(date +%s) + 120))
while ! grep -q 'CYLC_JOB_EXIT=' "$SUITE_RUN_DIR/log/job/my_task_1.1.1.status" \
    2>/dev/null
do
    if (($(date +%s) > $TIME_OUT)); then
        break
    fi
    sleep 1
done
mv $HOME/.cylc/ports/$NAME $NAME.port
run_fail "$TEST_KEY" \
    rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol
file_grep "$TEST_KEY.err" \
    '\[FAIL\] '$NAME': is still running (detected localhost:process=' \
    "$TEST_KEY.err"
run_pass "$TEST_KEY.NAME1" \
    rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=${NAME}1 \
    --no-gcontrol
mv $NAME.port $HOME/.cylc/ports/$NAME
#-------------------------------------------------------------------------------
cylc shutdown --timeout=120 --kill --wait $NAME 1>/dev/null 2>&1
rose suite-clean --debug -q -y $NAME
cylc shutdown --timeout=120 --kill --wait ${NAME}1 1>/dev/null 2>&1
rose suite-clean --debug -q -y ${NAME}1
exit 0
