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
# Test "rose suite-log --force", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
N_TESTS=15
tests $N_TESTS
#-------------------------------------------------------------------------------
if [[ $TEST_KEY_BASE == *-remote* ]]; then
    JOB_HOST=$(rose config 't' 'job-host')
    if [[ -z $JOB_HOST ]]; then
        skip $N_TESTS '[t]job-host not defined'
        exit 0
    fi
    JOB_HOST=$(rose host-select $JOB_HOST)
fi
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
if [[ -n ${JOB_HOST:-} ]]; then
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost \
        -D "[jinja2:suite.rc]HOST=\"$JOB_HOST\""
else
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost
fi
#-------------------------------------------------------------------------------
# Wait for the suite to complete, test shutdown on fail
TEST_KEY="$TEST_KEY_BASE-complete"
TIMEOUT=$(($(date +%s) + 300)) # wait 5 minutes
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
# Test --force.
CYCLES='2013010100 2013010112 2013010200'
for CYCLE in $CYCLES; do
    TEST_KEY="$TEST_KEY_BASE-before-$CYCLE"
    run_fail "$TEST_KEY" \
        test -f "$HOME/cylc-run/$NAME/log/rose-suite-log-$CYCLE.json"
done
TEST_KEY="$TEST_KEY_BASE-db-before"
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,key FROM log_files ORDER BY path ASC;' >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
TEST_KEY="$TEST_KEY_BASE-command"
run_pass "$TEST_KEY" rose suite-log -n $NAME -f --debug
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
for CYCLE in $CYCLES; do
    TEST_KEY="$TEST_KEY_BASE-after-$CYCLE"
    file_test "$TEST_KEY-after-log-1.out" \
        $SUITE_RUN_DIR/log/job/my_task_1.$CYCLE.1.out
    file_test "$TEST_KEY-after-log-2.out" \
        $SUITE_RUN_DIR/log/job/my_task_2.$CYCLE.1.out
done
TEST_KEY="$TEST_KEY_BASE-db-after"
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,key FROM log_files ORDER BY path ASC;' >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
log/job/my_task_1.2013010100.1|00-script
log/job/my_task_1.2013010100.1.err|02-err
log/job/my_task_1.2013010100.1.out|01-out
log/job/my_task_1.2013010112.1|00-script
log/job/my_task_1.2013010112.1.err|02-err
log/job/my_task_1.2013010112.1.out|01-out
log/job/my_task_1.2013010200.1|00-script
log/job/my_task_1.2013010200.1.err|02-err
log/job/my_task_1.2013010200.1.out|01-out
log/job/my_task_2.2013010100.1|00-script
log/job/my_task_2.2013010100.1.err|02-err
log/job/my_task_2.2013010100.1.out|01-out
log/job/my_task_2.2013010112.1|00-script
log/job/my_task_2.2013010112.1.err|02-err
log/job/my_task_2.2013010112.1.out|01-out
log/job/my_task_2.2013010200.1|00-script
log/job/my_task_2.2013010200.1.err|02-err
log/job/my_task_2.2013010200.1.out|01-out
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
cylc unregister $NAME 1>/dev/null 2>&1
exit 0
