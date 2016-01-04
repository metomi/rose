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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
# Run the suite.
if [[ $TEST_KEY_BASE == *conf ]]; then
    if ! rose config -q 'rose-suite-run' 'hosts'; then
        skip_all '"[rose-suite-run]hosts" not defined'
    fi
else
    export ROSE_CONF_PATH=
fi
#-------------------------------------------------------------------------------
N_TESTS=11
tests $N_TESTS
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
HOST=$(<$SUITE_RUN_DIR/log/rose-suite-run.host)
poll ! test -e $SUITE_RUN_DIR/log/job/my_task_1.2013010100.1
if [[ $HOST == 'localhost' ]]; then
    SUITE_PROC=$(pgrep -u$USER -fl "python.*cylc-run .*\\<$NAME\\>")
else
    CMD_PREFIX="ssh -oBatchMode=yes $HOST"
    SUITE_PROC=$($CMD_PREFIX "pgrep -u\$USER -fl 'python.*cylc-run .*\\<$NAME\\>'")
fi
SUITE_PROC=$(awk '{print "[FAIL]     " $0}' <<<"$SUITE_PROC")
#-------------------------------------------------------------------------------
# "rose suite-run" should not work while suite is running.
# except --reload mode.
for OPTION in -i -l '' --restart; do
    TEST_KEY=$TEST_KEY_BASE-running$OPTION
    run_fail "$TEST_KEY" rose suite-run $OPTION \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
    file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] Suite "$NAME" may still be running.
[FAIL] Host "${HOST:-localhost}" has process:
$SUITE_PROC
[FAIL] Try "rose suite-shutdown --name=$NAME" first?
__ERR__
done
# Don't reload until tasks begin
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while (($(date +%s) < TIMEOUT)) && ! (
    cd $SUITE_RUN_DIR/log/job/
    test -f 2013010100/my_task_1/01/job.out && test -f 2013010112/my_task_1/01/job.out
)
do
    sleep 1
done
TEST_KEY=$TEST_KEY_BASE-running-reload
run_pass "$TEST_KEY" rose suite-run --reload \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
sleep 1
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
touch $SUITE_RUN_DIR/flag # allow the task to die
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
