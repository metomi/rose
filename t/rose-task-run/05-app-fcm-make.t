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
# Test fcm_make built-in application, basic usages.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
N_TESTS=10
tests $N_TESTS
#-------------------------------------------------------------------------------
if ! fcm help make 1>/dev/null 2>&1; then
    skip $N_TESTS 'fcm make unavailable'
    exit 0
fi
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select $JOB_HOST)
fi
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
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
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
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
TEST_KEY="$TEST_KEY_BASE-status"
sqlite3 $SUITE_RUN_DIR/cylc-suite.db \
    'SELECT name,status FROM task_states ORDER BY name;' \
    >"$TEST_KEY"
if [[ -n $JOB_HOST ]]; then
    file_cmp "$TEST_KEY" "$TEST_KEY" <<'__DB__'
fcm_make2_t5|succeeded
fcm_make_t1|succeeded
fcm_make_t2|succeeded
fcm_make_t3|succeeded
fcm_make_t4|succeeded
fcm_make_t5|succeeded
__DB__
else
    file_cmp "$TEST_KEY" "$TEST_KEY" <<'__DB__'
fcm_make_t1|succeeded
fcm_make_t2|succeeded
fcm_make_t3|succeeded
fcm_make_t4|succeeded
__DB__
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t1" # normal
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/fcm_make_t1.1/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t1 -j 4" \
    $SUITE_RUN_DIR/log/job/fcm_make_t1.1.1.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t2" # use-pwd
file_grep "$TEST_KEY.out" "\\[INFO\\] fcm make -j 4" \
    $SUITE_RUN_DIR/log/job/fcm_make_t2.1.1.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t3" # opt.jobs
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/fcm_make_t3.1/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t3 -j 1" \
    $SUITE_RUN_DIR/log/job/fcm_make_t3.1.1.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t4" # args
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/fcm_make_t4.1/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t4 -j 4 -v -v" \
    $SUITE_RUN_DIR/log/job/fcm_make_t4.1.1.out
#-------------------------------------------------------------------------------
if [[ -z $JOB_HOST ]]; then
    skip 3 '[t]job-host not defined'
else
    TEST_KEY="$TEST_KEY_BASE-t5" # mirror
    file_grep "$TEST_KEY.out.env" \
        "\\[INFO\\] export ROSE_TASK_MIRROR_TARGET=$JOB_HOST:cylc-run/$NAME/share/fcm_make_t5" \
        $SUITE_RUN_DIR/log/job/fcm_make_t5.1.1.out
    file_grep "$TEST_KEY.out.cmd" \
        "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/fcm_make_t5.1/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t5 -j 4" \
        $SUITE_RUN_DIR/log/job/fcm_make_t5.1.1.out

    TEST_KEY="$TEST_KEY_BASE-t5-part-2"
    rose suite-log -q --name=$NAME --update fcm_make2_t5
    file_grep "$TEST_KEY.out" \
        "\\[INFO\\] fcm make -C .*$NAME/share/fcm_make_t5 -j 4" \
        $SUITE_RUN_DIR/log/job/fcm_make2_t5.1.1.out
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
