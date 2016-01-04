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
# Test fcm_make built-in application, basic usages.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
if ! fcm help make 1>/dev/null 2>&1; then
    skip_all '"fcm make" unavailable'
fi
if ! gfortran --version 1>/dev/null 2>&1; then
    skip_all '"gfortran" unavailable'
fi
#-------------------------------------------------------------------------------
tests 8
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select -q $JOB_HOST)
fi
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_PATH=
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
if [[ -n ${JOB_HOST:-} ]]; then
    timeout 60 rose suite-run -q \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
        --no-gcontrol --host='localhost' \
        -D "[jinja2:suite.rc]HOST=\"$JOB_HOST\"" -- --debug
else
    timeout 60 rose suite-run -q \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
        --no-gcontrol --host='localhost' -- --debug
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
    "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/1/fcm_make_t1/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t1 -j 4" \
    $SUITE_RUN_DIR/log/job/1/fcm_make_t1/01/job.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t2" # use-pwd
file_grep "$TEST_KEY.out" "\\[INFO\\] fcm make -j 4" \
    $SUITE_RUN_DIR/log/job/1/fcm_make_t2/01/job.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t3" # opt.jobs
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/1/fcm_make_t3/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t3 -j 1" \
    $SUITE_RUN_DIR/log/job/1/fcm_make_t3/01/job.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t4" # args
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/1/fcm_make_t4/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t4 -j 4 -v -v" \
    $SUITE_RUN_DIR/log/job/1/fcm_make_t4/01/job.out
#-------------------------------------------------------------------------------
if [[ -z $JOB_HOST ]]; then
    skip 3 '[t]job-host not defined'
else
    TEST_KEY="$TEST_KEY_BASE-t5" # mirror
    file_grep "$TEST_KEY.out.env" \
        "\\[INFO\\] export ROSE_TASK_MIRROR_TARGET=$JOB_HOST:cylc-run/$NAME/share/fcm_make_t5" \
        $SUITE_RUN_DIR/log/job/1/fcm_make_t5/01/job.out
    file_grep "$TEST_KEY.out.cmd" \
        "\\[INFO\\] fcm make -f .*$SUITE_RUN_DIR/work/1/fcm_make_t5/fcm-make.cfg -C .*$SUITE_RUN_DIR/share/fcm_make_t5 -j 4 mirror\\.target=${JOB_HOST}:cylc-run/${NAME}/share/fcm_make_t5" \
        $SUITE_RUN_DIR/log/job/1/fcm_make_t5/01/job.out

    TEST_KEY="$TEST_KEY_BASE-t5-part-2"
    rose suite-log -q --name=$NAME --update fcm_make2_t5
    file_grep "$TEST_KEY.out" \
        "\\[INFO\\] fcm make -C .*/cylc-run/${NAME}/share/fcm_make_t5 -n 2 -j 4" \
        $SUITE_RUN_DIR/log/job/1/fcm_make2_t5/01/job.out
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
