#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2018 British Crown (Met Office) & Contributors.
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
tests 12
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
        -D "[jinja2:suite.rc]HOST=\"$JOB_HOST\"" -- --no-detach --debug
else
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost -- --no-detach --debug
fi
#-------------------------------------------------------------------------------
# Test --archive.
TEST_KEY="$TEST_KEY_BASE"

set -e
(cd $SUITE_RUN_DIR/log/job; ls */*/01/{job,job-activity.log,job.err,job.out,job.xtrace}) \
    >"$TEST_KEY-list-job-logs-before.out"
if [[ -n ${JOB_HOST:-} ]]; then
    ssh -oBatchMode=yes $JOB_HOST \
        test -f cylc-run/$NAME/log/job/*/my_task_2/01/job.out
    ! test -f $SUITE_RUN_DIR/log/job/*/my_task_2/01/job.out
fi
set +e

N_JOB_LOGS=$(wc -l "$TEST_KEY-list-job-logs-before.out" | cut -d' ' -f1)
run_pass "$TEST_KEY-command" rose suite-log -n $NAME --archive '*' --debug
run_fail "$TEST_KEY-list-job-logs-after" ls $SUITE_RUN_DIR/log/job/*
if [[ -n ${JOB_HOST:-} ]]; then
    ((N_JOB_LOGS += 4)) # job, job.activity.log, job.out, job.err, job.xtrace files
    run_fail "$TEST_KEY-job-log.out-after-jobhost" \
        ssh -oBatchMode=yes $JOB_HOST \
        test -f cylc-run/$NAME/log/job/*/my_task_2/01/job.out
else
    pass "$TEST_KEY-job-log.out-after-jobhost"
fi
ALL_JOB_LOGS_ARCH=
for CYCLE in 20130101T0000Z 20130101T1200Z 20130102T0000Z; do
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
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
