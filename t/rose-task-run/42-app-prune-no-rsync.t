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
# Test rose_prune built-in application, basic cycle housekeep usage.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -z $JOB_HOST ]]; then
    skip_all "This test requires a remote host to be setup in your rose.conf file."
elif [[ $JOB_HOST = $HOSTNAME ]]; then
    skip_all "This test requires a remote host to be setup in your rose.conf file."
else
    JOB_HOST="$(rose host-select "$JOB_HOST")"
fi
tests 3

export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
#-------------------------------------------------------------------------------
get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="$FLOW" \
        --no-run-name \
        -S "HOST='${JOB_HOST}'"

run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "$FLOW" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-logs-not-rsync'd"
file_grep "${TEST_KEY}" "handkerchief" "${FLOW_RUN_DIR}/log/job/20130101T0000Z/my_task/NN/job.out"

purge
exit 0
