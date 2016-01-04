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
# Test "rose suite-log --archive *", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

if [[ $TEST_KEY_BASE == *-remote* ]]; then
    JOB_HOST=$(rose config 't' 'job-host')
    if [[ -z $JOB_HOST ]]; then
        skip_all '"[t]job-host" not defined'
    fi
    JOB_HOST=$(rose host-select -q $JOB_HOST)
fi
#-------------------------------------------------------------------------------
tests 14
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
# Test --archive.
TEST_KEY="$TEST_KEY_BASE"

set -e
(cd $SUITE_RUN_DIR/log/job; ls */*/01/{job,job-activity.log,job.err,job.out}) \
    >"$TEST_KEY-list-job-logs-before.out"
if [[ -n ${JOB_HOST:-} ]]; then
    ssh -oBatchMode=yes $JOB_HOST \
        test -f cylc-run/$NAME/log/job/*/my_task_2/01/job.out
    ! test -f $SUITE_RUN_DIR/log/job/*/my_task_2/01/job.out
fi
set +e

sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,path_in_tar,key FROM log_files ORDER BY path,path_in_tar ASC;' \
    >"$TEST_KEY-db-1.out"
file_cmp "$TEST_KEY-db-1.out" "$TEST_KEY-db-1.out" <<'__OUT__'
log/job/2013010100/my_task_1/01/job||job
log/job/2013010100/my_task_1/01/job-activity.log||job-activity.log
log/job/2013010100/my_task_1/01/job.err||job.err
log/job/2013010100/my_task_1/01/job.out||job.out
log/job/2013010112/my_task_1/01/job||job
log/job/2013010112/my_task_1/01/job-activity.log||job-activity.log
log/job/2013010112/my_task_1/01/job.err||job.err
log/job/2013010112/my_task_1/01/job.out||job.out
log/job/2013010200/my_task_1/01/job||job
log/job/2013010200/my_task_1/01/job-activity.log||job-activity.log
log/job/2013010200/my_task_1/01/job.err||job.err
log/job/2013010200/my_task_1/01/job.out||job.out
__OUT__
N_JOB_LOGS=$(wc -l "$TEST_KEY-list-job-logs-before.out" | cut -d' ' -f1)
(cd $SUITE_RUN_DIR/log && ls job/*) | LANG=C sort >foo
run_pass "$TEST_KEY-command" rose suite-log -n $NAME --archive '*' --debug
run_fail "$TEST_KEY-list-job-logs-after" ls $SUITE_RUN_DIR/log/job/*
if [[ -n ${JOB_HOST:-} ]]; then
    ((N_JOB_LOGS += 3)) # job, job.activity.log, job.out and job.err files
    run_fail "$TEST_KEY-job-log.out-after-jobhost" \
        ssh -oBatchMode=yes $JOB_HOST \
        test -f cylc-run/$NAME/log/job/*/my_task_2/01/job.out
else
    pass "$TEST_KEY-job-log.out-after-jobhost"
fi
ALL_JOB_LOGS_ARCH=
for CYCLE in 2013010100 2013010112 2013010200; do
    file_test "$TEST_KEY-$CYCLE-tar-exist" $SUITE_RUN_DIR/log/job-$CYCLE.tar.gz
    JOB_LOGS_ARCH=$(tar -tzf $SUITE_RUN_DIR/log/job-$CYCLE.tar.gz)
    if [[ -n $ALL_JOB_LOGS_ARCH ]]; then
        ALL_JOB_LOGS_ARCH=$(cat <<__LIST__
${ALL_JOB_LOGS_ARCH}
${JOB_LOGS_ARCH}
__LIST__
        )
    else
        ALL_JOB_LOGS_ARCH="$JOB_LOGS_ARCH"
    fi
    run_pass "$TEST_KEY-$CYCLE-after-log.out" \
        grep -q "job/$CYCLE/my_task_2/01/job.out" <<<"$JOB_LOGS_ARCH"
done

N_JOB_LOGS_ARCH=$(echo "$ALL_JOB_LOGS_ARCH" | wc -l | cut -d' ' -f1)
run_pass "$TEST_KEY-n-arch" test "${N_JOB_LOGS}" -eq "${N_JOB_LOGS_ARCH}"

file_cmp "$TEST_KEY-command.err" "$TEST_KEY-command.err" </dev/null
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,path_in_tar,key FROM log_files ORDER BY path,path_in_tar ASC;' \
    >"$TEST_KEY-db-2.out"
file_cmp "$TEST_KEY-db-2.out" "$TEST_KEY-db-2.out" <<'__OUT__'
log/job-2013010100.tar.gz|job/2013010100/my_task_1/01/job|job
log/job-2013010100.tar.gz|job/2013010100/my_task_1/01/job-activity.log|job-activity.log
log/job-2013010100.tar.gz|job/2013010100/my_task_1/01/job.err|job.err
log/job-2013010100.tar.gz|job/2013010100/my_task_1/01/job.out|job.out
log/job-2013010100.tar.gz|job/2013010100/my_task_2/01/job|job
log/job-2013010100.tar.gz|job/2013010100/my_task_2/01/job-activity.log|job-activity.log
log/job-2013010100.tar.gz|job/2013010100/my_task_2/01/job.err|job.err
log/job-2013010100.tar.gz|job/2013010100/my_task_2/01/job.out|job.out
log/job-2013010112.tar.gz|job/2013010112/my_task_1/01/job|job
log/job-2013010112.tar.gz|job/2013010112/my_task_1/01/job-activity.log|job-activity.log
log/job-2013010112.tar.gz|job/2013010112/my_task_1/01/job.err|job.err
log/job-2013010112.tar.gz|job/2013010112/my_task_1/01/job.out|job.out
log/job-2013010112.tar.gz|job/2013010112/my_task_2/01/job|job
log/job-2013010112.tar.gz|job/2013010112/my_task_2/01/job-activity.log|job-activity.log
log/job-2013010112.tar.gz|job/2013010112/my_task_2/01/job.err|job.err
log/job-2013010112.tar.gz|job/2013010112/my_task_2/01/job.out|job.out
log/job-2013010200.tar.gz|job/2013010200/my_task_1/01/job|job
log/job-2013010200.tar.gz|job/2013010200/my_task_1/01/job-activity.log|job-activity.log
log/job-2013010200.tar.gz|job/2013010200/my_task_1/01/job.err|job.err
log/job-2013010200.tar.gz|job/2013010200/my_task_1/01/job.out|job.out
log/job-2013010200.tar.gz|job/2013010200/my_task_2/01/job|job
log/job-2013010200.tar.gz|job/2013010200/my_task_2/01/job-activity.log|job-activity.log
log/job-2013010200.tar.gz|job/2013010200/my_task_2/01/job.err|job.err
log/job-2013010200.tar.gz|job/2013010200/my_task_2/01/job.out|job.out
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
