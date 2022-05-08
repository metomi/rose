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
# Test "rose prune" removal of logs
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
tests 11
#-------------------------------------------------------------------------------
# Run the suite.
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
get_reg
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "$TEST_KEY" \
    cylc install \
        "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --workflow-name="$FLOW" \
        --no-run-name
TEST_KEY="${TEST_KEY_BASE}-play"
run_pass "$TEST_KEY" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-log
run_fail "$TEST_KEY.1" ls -d "$FLOW_RUN_DIR/log/job/20100101T0000Z"
run_fail "$TEST_KEY.2" ls -d "$FLOW_RUN_DIR/log/job/20100102T0000Z"
run_fail "$TEST_KEY.3" ls -d "$FLOW_RUN_DIR/log/job/20100103T0000Z"
run_fail "$TEST_KEY.4" ls -d "$FLOW_RUN_DIR/log/job/20100104T0000Z"
run_pass "$TEST_KEY.5" ls -d "$FLOW_RUN_DIR/log/job/20100105T0000Z"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-archived
run_fail "$TEST_KEY.1" ls -d "$FLOW_RUN_DIR/log/job-20100101T0000Z.tar.gz"
run_fail "$TEST_KEY.2" ls -d "$FLOW_RUN_DIR/log/job-20100102T0000Z.tar.gz"
run_fail "$TEST_KEY.3" ls -d "$FLOW_RUN_DIR/log/job-20100103T0000Z.tar.gz"
run_pass "$TEST_KEY.4" ls -d "$FLOW_RUN_DIR/log/job-20100104T0000Z.tar.gz"
#-------------------------------------------------------------------------------
purge
exit 0
