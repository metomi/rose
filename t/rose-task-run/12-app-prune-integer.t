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
# Test "rose prune" with integer cycling
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select -q $JOB_HOST)
    tests 16
else
    tests 13
fi


#-------------------------------------------------------------------------------
# Run the suite.
# export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
get_reg
OPTS=(
    "--workflow-name=$FLOW"
    --no-run-name
)
if [[ -n ${JOB_HOST:-} ]]; then
    OPTS+=(
        -S "HOST='$JOB_HOST'"
    )
fi
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "${TEST_KEY}" \
    cylc install \
        "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        "${OPTS[@]}"
TEST_KEY="${TEST_KEY_BASE}-play"
run_pass "${TEST_KEY}" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-work
run_fail "$TEST_KEY.1" ls -d "$FLOW_RUN_DIR/work/1"
run_fail "$TEST_KEY.2" ls -d "$FLOW_RUN_DIR/work/2"
run_pass "$TEST_KEY.3" ls -d "$FLOW_RUN_DIR/work/3"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-share
run_fail "$TEST_KEY.1" ls -d "$FLOW_RUN_DIR/share/cycle/1"
run_fail "$TEST_KEY.2" ls -d "$FLOW_RUN_DIR/share/cycle/2"
run_pass "$TEST_KEY.3" ls -d "$FLOW_RUN_DIR/share/cycle/3"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-archive
TEST_KEY=$TEST_KEY_BASE-share
run_fail "$TEST_KEY.1" ls -d "$FLOW_RUN_DIR/log/job/1"
run_pass "$TEST_KEY.1-tar" ls -d "$FLOW_RUN_DIR/log/job-1.tar.gz"
run_fail "$TEST_KEY.2" ls -d "$FLOW_RUN_DIR/log/job/2"
run_pass "$TEST_KEY.2-tar" ls -d "$FLOW_RUN_DIR/log/job-2.tar.gz"
run_pass "$TEST_KEY.3" ls -d "$FLOW_RUN_DIR/log/job/3"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-remote
if [[ -n "$JOB_HOST" ]]; then
    run_fail "$TEST_KEY.1" ssh "$JOB_HOST" "ls -d $FLOW_RUN_DIR/log/job/1"
    run_fail "$TEST_KEY.2" ssh "$JOB_HOST" "ls -d $FLOW_RUN_DIR/log/job/2"
    run_pass "$TEST_KEY.3" ssh "$JOB_HOST" "ls -d $FLOW_RUN_DIR/log/job/3"
fi
#-------------------------------------------------------------------------------
purge
exit 0
