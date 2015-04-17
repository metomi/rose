#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Test "rose suite-run" when similarly-named suites are running.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
set -eu
#-------------------------------------------------------------------------------
tests 19
#-------------------------------------------------------------------------------
cat >$TEST_DIR/cylc-run <<'__PYTHON__'
#!/usr/bin/env python
import time
time.sleep(60)
__PYTHON__
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery-XXXXXX')
NAME=$(basename "${SUITE_RUN_DIR}")
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-self-check-suite-check
# Check that the suite actually runs by itself.
run_pass "$TEST_KEY" rose suite-run -q --no-gcontrol \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME
#------------------------------------------------------------------------------
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while (($(date +%s) < TIMEOUT)) && [[ -f ~/.cylc/ports/$NAME ]]
do
    sleep 1
done
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-self-check
# Check that this approach causes rose suite-run failure.
python $TEST_DIR/cylc-run $NAME 1>/dev/null 2>&1 &
FAKE_SUITE_PID=$!
run_fail rose suite-run -q --no-gcontrol \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME
disown $FAKE_SUITE_PID  # Don't report 'Terminated...' stuff on kill.
kill $FAKE_SUITE_PID
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-self-check-hold
# Check that this approach causes rose suite-run failure.
python $TEST_DIR/cylc-run $NAME --hold 1>/dev/null 2>&1 &
FAKE_SUITE_PID=$!
run_fail rose suite-run -q --no-gcontrol \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME
disown $FAKE_SUITE_PID
kill $FAKE_SUITE_PID
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-similar-suite-names
for ALT_NAME in foo$NAME foo-$NAME foo_$NAME \
                ${NAME}bar $NAME-bar ${NAME}_bar $NAME. .$NAME
do
    python $TEST_DIR/cylc-run $ALT_NAME 1>/dev/null 2>&1 &
    FAKE_SUITE_PID=$!
    run_fail rose suite-run -q --no-gcontrol \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME
    disown $FAKE_SUITE_PID
    kill $FAKE_SUITE_PID
    python $TEST_DIR/cylc-run $ALT_NAME --debug 1>/dev/null 2>&1 &
    FAKE_SUITE_PID=$!
    run_fail rose suite-run -q --no-control \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME
    disown $FAKE_SUITE_PID
    kill $FAKE_SUITE_PID
done
#-------------------------------------------------------------------------------
exit 0
