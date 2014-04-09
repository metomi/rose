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
# Test "rose suite-log --update CYCLE", without site/user configurations.
# Test "rose suite-log --archive CYCLE", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
if [[ $TEST_KEY_BASE == *-remote* ]]; then
    JOB_HOST=$(rose config 't' 'job-host')
    if [[ -z $JOB_HOST ]]; then
        skip_all '[t]job-host not defined'
    fi
    JOB_HOST=$(rose host-select $JOB_HOST)
fi
#-------------------------------------------------------------------------------
tests 18
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
# Test --archive.
CYCLE=2013010100
TEST_KEY="$TEST_KEY_BASE-archive-$CYCLE"
set -e
ls $SUITE_RUN_DIR/log/job/*$CYCLE* >"$TEST_KEY-list-job-logs-before.out"
if [[ -n ${JOB_HOST:-} ]]; then
    ssh -oBatchMode=yes $JOB_HOST \
        test -f cylc-run/$NAME/log/job/my_task_2.$CYCLE.1.out
    ! test -f $SUITE_RUN_DIR/log/job/my_task_2.$CYCLE.1.out
fi
set +e
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,path_in_tar,key FROM log_files ORDER BY path,path_in_tar ASC;' \
    >"$TEST_KEY-db-1.out"
file_cmp "$TEST_KEY-db-1.out" "$TEST_KEY-db-1.out" <<'__OUT__'
log/job/my_task_1.2013010100.1||00-script
log/job/my_task_1.2013010100.1.err||02-err
log/job/my_task_1.2013010100.1.out||01-out
log/job/my_task_1.2013010112.1||00-script
log/job/my_task_1.2013010112.1.err||02-err
log/job/my_task_1.2013010112.1.out||01-out
log/job/my_task_1.2013010200.1||00-script
log/job/my_task_1.2013010200.1.err||02-err
log/job/my_task_1.2013010200.1.out||01-out
__OUT__
N_JOB_LOGS=$(wc -l "$TEST_KEY-list-job-logs-before.out" | cut -d' ' -f1)
run_pass "$TEST_KEY-command" rose suite-log -n $NAME --archive $CYCLE --debug
run_fail "$TEST_KEY-list-job-logs-after" ls $SUITE_RUN_DIR/log/job/*$CYCLE*
if [[ -n ${JOB_HOST:-} ]]; then
    ((N_JOB_LOGS += 3)) # script, out and err files
    run_fail "$TEST_KEY-job-log.out-after-jobhost" \
        ssh -oBatchMode=yes $JOB_HOST \
        test -f cylc-run/$NAME/log/job/my_task_2.$CYCLE.1.out
else
    pass "$TEST_KEY-job-log.out-after-jobhost"
fi
file_test "$TEST_KEY-tar-exist" $SUITE_RUN_DIR/log/job-$CYCLE.tar.gz
JOB_LOGS_ARCH=$(tar -tzf $SUITE_RUN_DIR/log/job-$CYCLE.tar.gz)
run_pass "$TEST_KEY-after-log.out" \
    grep -q "job/my_task_2.$CYCLE.1.out" <<<"$JOB_LOGS_ARCH"
N_JOB_LOGS_ARCH=$(echo "$JOB_LOGS_ARCH" | wc -l | cut -d' ' -f1)
if ((N_JOB_LOGS == N_JOB_LOGS_ARCH)); then
    pass "$TEST_KEY-n-arch"
else
    fail "$TEST_KEY-n-arch"
fi
file_cmp "$TEST_KEY-command.err" "$TEST_KEY-command.err" </dev/null
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,path_in_tar,key FROM log_files ORDER BY path,path_in_tar ASC;' \
    >"$TEST_KEY-db-2.out"
file_cmp "$TEST_KEY-db-2.out" "$TEST_KEY-db-2.out" <<'__OUT__'
log/job-2013010100.tar.gz|job/my_task_1.2013010100.1|00-script
log/job-2013010100.tar.gz|job/my_task_1.2013010100.1.err|02-err
log/job-2013010100.tar.gz|job/my_task_1.2013010100.1.out|01-out
log/job-2013010100.tar.gz|job/my_task_2.2013010100.1|00-script
log/job-2013010100.tar.gz|job/my_task_2.2013010100.1.err|02-err
log/job-2013010100.tar.gz|job/my_task_2.2013010100.1.out|01-out
log/job/my_task_1.2013010112.1||00-script
log/job/my_task_1.2013010112.1.err||02-err
log/job/my_task_1.2013010112.1.out||01-out
log/job/my_task_1.2013010200.1||00-script
log/job/my_task_1.2013010200.1.err||02-err
log/job/my_task_1.2013010200.1.out||01-out
__OUT__
#-------------------------------------------------------------------------------
# Test --update.
for CYCLE in 2013010112 2013010200; do
    TEST_KEY="$TEST_KEY_BASE-$CYCLE"
    run_pass "$TEST_KEY-command" rose suite-log -n $NAME --update $CYCLE --debug
    file_cmp "$TEST_KEY-command.err" "$TEST_KEY-command.err" </dev/null
    file_test "$TEST_KEY-after-log.out" \
        $SUITE_RUN_DIR/log/job/my_task_2.$CYCLE.1.out
done
sqlite3 "$HOME/cylc-run/$NAME/log/rose-job-logs.db" \
    'SELECT path,path_in_tar,key FROM log_files ORDER BY path,path_in_tar ASC;' \
    >"$TEST_KEY_BASE-db-final.out"
file_cmp "$TEST_KEY_BASE-db-final.out" "$TEST_KEY_BASE-db-final.out" <<'__OUT__'
log/job-2013010100.tar.gz|job/my_task_1.2013010100.1|00-script
log/job-2013010100.tar.gz|job/my_task_1.2013010100.1.err|02-err
log/job-2013010100.tar.gz|job/my_task_1.2013010100.1.out|01-out
log/job-2013010100.tar.gz|job/my_task_2.2013010100.1|00-script
log/job-2013010100.tar.gz|job/my_task_2.2013010100.1.err|02-err
log/job-2013010100.tar.gz|job/my_task_2.2013010100.1.out|01-out
log/job/my_task_1.2013010112.1||00-script
log/job/my_task_1.2013010112.1.err||02-err
log/job/my_task_1.2013010112.1.out||01-out
log/job/my_task_1.2013010200.1||00-script
log/job/my_task_1.2013010200.1.err||02-err
log/job/my_task_1.2013010200.1.out||01-out
log/job/my_task_2.2013010112.1||00-script
log/job/my_task_2.2013010112.1.err||02-err
log/job/my_task_2.2013010112.1.out||01-out
log/job/my_task_2.2013010200.1||00-script
log/job/my_task_2.2013010200.1.err||02-err
log/job/my_task_2.2013010200.1.out||01-out
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
