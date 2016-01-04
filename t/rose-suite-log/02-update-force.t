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
# Test "rose suite-log --force", without site/user configurations.
# Test "rose suite-log -U --prune-remote", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
if [[ $TEST_KEY_BASE == *-remote* ]]; then
    JOB_HOST=$(rose config 't' 'job-host')
    if [[ -z $JOB_HOST ]]; then
        skip_all '"[t]job-host" not defined'
    fi
    JOB_HOST=$(rose host-select -q $JOB_HOST)
fi
#-------------------------------------------------------------------------------
tests 17
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
        -D "[jinja2:suite.rc]HOST=\"$JOB_HOST\"" -- --debug
else
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost -- --debug
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
        $SUITE_RUN_DIR/log/job/$CYCLE/my_task_1/01/job.out
    file_test "$TEST_KEY-after-log-2.out" \
        $SUITE_RUN_DIR/log/job/$CYCLE/my_task_2/01/job.out
done
TEST_KEY="$TEST_KEY_BASE-db-after"
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,key FROM log_files ORDER BY path ASC;' >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
log/job/2013010100/my_task_1/01/job|job
log/job/2013010100/my_task_1/01/job-activity.log|job-activity.log
log/job/2013010100/my_task_1/01/job.err|job.err
log/job/2013010100/my_task_1/01/job.out|job.out
log/job/2013010100/my_task_2/01/job|job
log/job/2013010100/my_task_2/01/job-activity.log|job-activity.log
log/job/2013010100/my_task_2/01/job.err|job.err
log/job/2013010100/my_task_2/01/job.out|job.out
log/job/2013010112/my_task_1/01/job|job
log/job/2013010112/my_task_1/01/job-activity.log|job-activity.log
log/job/2013010112/my_task_1/01/job.err|job.err
log/job/2013010112/my_task_1/01/job.out|job.out
log/job/2013010112/my_task_2/01/job|job
log/job/2013010112/my_task_2/01/job-activity.log|job-activity.log
log/job/2013010112/my_task_2/01/job.err|job.err
log/job/2013010112/my_task_2/01/job.out|job.out
log/job/2013010200/my_task_1/01/job|job
log/job/2013010200/my_task_1/01/job-activity.log|job-activity.log
log/job/2013010200/my_task_1/01/job.err|job.err
log/job/2013010200/my_task_1/01/job.out|job.out
log/job/2013010200/my_task_2/01/job|job
log/job/2013010200/my_task_2/01/job-activity.log|job-activity.log
log/job/2013010200/my_task_2/01/job.err|job.err
log/job/2013010200/my_task_2/01/job.out|job.out
__OUT__
#-------------------------------------------------------------------------------
# Test --prune-remote.
TEST_KEY="$TEST_KEY_BASE-prune-remote"
if [[ -n ${JOB_HOST:-} ]]; then
    run_pass "$TEST_KEY" \
        rose suite-log -U -n $NAME --prune-remote 2013010100 2013010112
    grep "\[INFO\] delete: $JOB_HOST:" "$TEST_KEY.out" >"$TEST_KEY.out.expected"
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out.expected" <<__OUT__
[INFO] delete: $JOB_HOST:log/job/2013010100/
[INFO] delete: $JOB_HOST:log/job/2013010112/
__OUT__
    ssh -oBatchMode=yes $JOB_HOST ls "~/cylc-run/$NAME/log/job" \
        | LANG=C sort >"$TEST_KEY.ls"
    file_cmp "$TEST_KEY.ls" "$TEST_KEY.ls" <<<'2013010200'
else
    skip 3 "$TEST_KEY: [t]job-host not defined"
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
