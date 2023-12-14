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
# Test "rose_bunch" built-in application's interaction with Cylc tasks:
# Run a task
# * Once: Should run all subtasks.
# * A second time in the same flow: Should skip the OK task from the first
#   run/
# * Run task with --flow=new: Should run all subtasks.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

tests 9

get_reg

APP_LOG_PATH="${HOME}/cylc-run/${FLOW}/log/job/2000/bunchapp"
SCHD_LOG_PATH="${HOME}/cylc-run/${FLOW}/log/scheduler/log"
SPACER_STATUS="${HOME}/cylc-run/${FLOW}/log/job/2000/spacer/job.status"

grep_incrementals() {
    # Check that a rose app-run runs, skips, and fails the desired number of
    # Tasks;
    local TEST_SET="$1"
    local OK="$2"
    local SKIP="$3"
    file_grep "${TEST_SET}-ok" "OK: ${OK}" "${TEST_SET}/job.out"
    file_grep "${TEST_SET}-skip" "SKIP: ${SKIP}" "${TEST_SET}/job.out"
}

mkdir -p app/bunchapp
touch "rose-suite.conf"

# Create a Cylc Workflow
cat > "flow.cylc" <<__HERE__
[scheduler]
    cycle point format = %Y
    allow implicit tasks = true

[scheduling]
    initial cycle point = 2000

    [[graph]]
        R1 = """
            bunchapp => spacer => long
        """

[runtime]
    [[bunchapp]]
        script = rose task-run
    [[long]]
        script = sleep 500

__HERE__

# App with one bunch member which will fail and one which will pass:
cat > "app/bunchapp/rose-app.conf" <<__HERE__
mode=rose_bunch
meta=rose_bunch

[bunch-args]
arg1=true

[bunch]
command-format=%(arg1)s
incremental=true
fail-mode=continue
__HERE__

# install and play the workflow
TEST_SET="play-once"
run_pass "${TEST_SET}" \
    cylc vip . --host=localhost --workflow-name "${FLOW}" --no-run-name

# Wait for first run of the task to finish - bunch should have one
# success and one failure:
poll ! grep CYLC_JOB_EXIT "${APP_LOG_PATH}/01/job.status" 2>&1 /dev/null
grep_incrementals "${APP_LOG_PATH}/01" 1 0

# Re trigger task in same flow - bunch should skip previously succeeded tasks:
poll ! grep CYLC_JOB_EXIT "${SPACER_STATUS}" 2>&1 /dev/null
cylc trigger "${FLOW}//2000/bunchapp/"
poll ! grep CYLC_JOB_EXIT "${APP_LOG_PATH}/02/job.status" 2>&1 /dev/null
grep_incrementals "${APP_LOG_PATH}/02" 0 1

# Re trigger task in new flow - bunch should treat as a new task:
poll ! grep CYLC_JOB_EXIT "${SPACER_STATUS}" 2>&1 /dev/null
cylc trigger "${FLOW}//2000/bunchapp/" --flow=new
poll ! grep CYLC_JOB_EXIT "${APP_LOG_PATH}/03/job.status" 2>&1 /dev/null
grep_incrementals "${APP_LOG_PATH}/03" 1 0

run_pass "stop workflow" cylc stop "${FLOW}" --kill
poll ! grep DONE "${SCHD_LOG_PATH}"

run_pass "cleanup" cylc clean -y "${FLOW}"
