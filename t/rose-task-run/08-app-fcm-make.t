#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
tests 10
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select -q "$JOB_HOST")
fi
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_PATH=
get_reg
OPTS=(
    "--flow-name=${FLOW}"
    "--no-run-name"
)
if [[ -n ${JOB_HOST:-} ]]; then
    OPTS+=(-S "HOST='$JOB_HOST'")
fi
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        "${OPTS[@]}"
run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host='localhost' \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-status"
sqlite3 $FLOW_RUN_DIR/log/db \
    'SELECT name,status FROM task_states ORDER BY name;' \
    >"$TEST_KEY"
if [[ -n $JOB_HOST ]]; then
    file_cmp "$TEST_KEY" "$TEST_KEY" <<'__DB__'
fcm_make2_t5|succeeded
fcm_make_t1|succeeded
fcm_make_t1_remote|succeeded
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
    "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* fcm make -f .*$FLOW_RUN_DIR/work/1/fcm_make_t1/fcm-make.cfg -C .*$FLOW_RUN_DIR/share/fcm_make_t1 -j 4" \
    $FLOW_RUN_DIR/log/job/1/fcm_make_t1/01/job.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t2" # use-pwd
file_grep "$TEST_KEY.out" "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* fcm make -j 4" \
    $FLOW_RUN_DIR/log/job/1/fcm_make_t2/01/job.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t3" # opt.jobs
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* fcm make -f .*$FLOW_RUN_DIR/work/1/fcm_make_t3/fcm-make.cfg -C .*$FLOW_RUN_DIR/share/fcm_make_t3 -j 1" \
    $FLOW_RUN_DIR/log/job/1/fcm_make_t3/01/job.out
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-t4" # args
file_grep "$TEST_KEY.out" \
    "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* fcm make -f .*$FLOW_RUN_DIR/work/1/fcm_make_t4/fcm-make.cfg -C .*$FLOW_RUN_DIR/share/fcm_make_t4 -j 4 -v -v" \
    $FLOW_RUN_DIR/log/job/1/fcm_make_t4/01/job.out
#-------------------------------------------------------------------------------
if [[ -z $JOB_HOST ]]; then
    skip 3 '[t]job-host not defined'
else
    TEST_KEY="$TEST_KEY_BASE-t5" # mirror
    file_grep "$TEST_KEY.out.env" \
        "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* export ROSE_TASK_MIRROR_TARGET=$JOB_HOST:cylc-run/$FLOW/share/fcm_make_t5" \
        $FLOW_RUN_DIR/log/job/1/fcm_make_t5/01/job.out
    file_grep "$TEST_KEY.out.cmd" \
        "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* fcm make -f .*$FLOW_RUN_DIR/work/1/fcm_make_t5/fcm-make.cfg -C .*$FLOW_RUN_DIR/share/fcm_make_t5 -j 4 mirror\\.target=${JOB_HOST}:cylc-run/${FLOW}/share/fcm_make_t5" \
        $FLOW_RUN_DIR/log/job/1/fcm_make_t5/01/job.out

    TEST_KEY="$TEST_KEY_BASE-t5-part-2"
    # TODO: this test relies on "retrieve job logs = True".
    file_grep "$TEST_KEY.out" \
        "\\[INFO\\] [0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0:9]* fcm make -C .*/cylc-run/${FLOW}/share/fcm_make_t5 -n 2 -j 4" \
        $FLOW_RUN_DIR/log/job/1/fcm_make2_t5/01/job.out
fi
#-------------------------------------------------------------------------------
purge
exit 0
