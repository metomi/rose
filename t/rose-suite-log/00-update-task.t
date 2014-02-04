#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose suite-log --update TASK", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 8
#-------------------------------------------------------------------------------
if [[ $TEST_KEY_BASE == *-remote* ]]; then
    JOB_HOST=$(rose config 't' 'job-host')
    if [[ -z $JOB_HOST ]]; then
        skip_all '[t]job-host not defined'
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
sleep 1
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-db-before"
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,key FROM log_files ORDER BY path ASC;' >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
log/job/my_task_1.1.1|00-script
log/job/my_task_1.1.1.err|02-err
log/job/my_task_1.1.1.out|01-out
__OUT__
TEST_KEY=$TEST_KEY_BASE-before-log.out
if [[ -n ${JOB_HOST:-} ]]; then
    run_fail "$TEST_KEY-log.out" \
        test -f $SUITE_RUN_DIR/log/job/my_task_2.1.1.out
else
    pass "$TEST_KEY-log.out"
fi
TEST_KEY=$TEST_KEY_BASE-command
run_pass "$TEST_KEY" rose suite-log -n $NAME -U 'my_task_2' --debug
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_test "$TEST_KEY-log.out" $SUITE_RUN_DIR/log/job/my_task_2.1.1.out
TEST_KEY="$TEST_KEY_BASE-db-after"
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,key FROM log_files ORDER BY path ASC;' >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
log/job/my_task_1.1.1|00-script
log/job/my_task_1.1.1.err|02-err
log/job/my_task_1.1.1.out|01-out
log/job/my_task_2.1.1|00-script
log/job/my_task_2.1.1.err|02-err
log/job/my_task_2.1.1.out|01-out
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
