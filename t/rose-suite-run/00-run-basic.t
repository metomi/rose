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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
N_TESTS=10
tests $N_TESTS
#-------------------------------------------------------------------------------
# Run the suite.
if [[ $TEST_KEY_BASE == *conf ]]; then
    if ! rose config -q 'rose-suite-run' 'hosts'; then
        skip $N_TESTS '[rose-suite-run]hosts not defined'
        exit 0
    fi
else
    export ROSE_CONF_IGNORE=true
fi
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
HOST=$(<$SUITE_RUN_DIR/log/rose-suite-run.host)
#-------------------------------------------------------------------------------
# "rose suite-run" should not work while suite is running.
# except --reload mode.
TEST_KEY=$TEST_KEY_BASE-running-run
run_fail "$TEST_KEY" rose suite-run -i \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $NAME: is already running on $HOST
__ERR__
run_fail "$TEST_KEY" rose suite-run \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $NAME: is already running on $HOST
__ERR__
TEST_KEY=$TEST_KEY_BASE-running-restart
run_fail "$TEST_KEY" rose suite-run --restart \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $NAME: is already running on $HOST
__ERR__
TEST_KEY=$TEST_KEY_BASE-running-reload
run_pass "$TEST_KEY" rose suite-run --reload \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
touch $SUITE_RUN_DIR/flag # allow the task to die
TIMEOUT=$(($(date +%s) + 300)) # wait 5 minutes
OK=false
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    OK=true
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-clean
run_pass "$TEST_KEY" rose suite-clean -y $NAME
rmdir $SUITE_RUN_DIR 2>/dev/null || true
exit 0
