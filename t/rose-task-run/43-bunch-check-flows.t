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
# Test "rose_bunch" built-in application:
# Test that CYLC_FLOW_TASK_NUMBERS is stored in the rose_bunch database
# and incremental mode turned off if changes made to its value in a later run.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

tests 24

grep_incrementals() {
    # Check that a rose app-run runs, skips, and fails the desired number of
    # Tasks;
    local TEST_SET="$1"
    local OK="$2"
    local FAIL="$3"
    local SKIP="$4"
    run_fail "${TEST_SET}" rose app-run
    file_grep "${TEST_SET}-ok" "OK: ${OK}" "${TEST_SET}.out"
    file_grep "${TEST_SET}-fail" "FAIL: ${FAIL}" "${TEST_SET}.out"
    file_grep "${TEST_SET}-skip" "SKIP: ${SKIP}" "${TEST_SET}.out"
}

# App with one bunch member which will fail and one which will pass:
cat > "rose-app.conf" <<__HERE__
mode=rose_bunch
meta=rose_bunch

[bunch-args]
arg1=true false

[bunch]
command-format=%(arg1)s
incremental=true
fail-mode=continue
__HERE__


# App outside Cylc task
unset CYLC_FLOW_TASK_NUMBERS
# It doesn't skip running anything the first time through:
grep_incrementals "no-flow" 1 1 0
# It doesn't run the OK task again:
grep_incrementals "no-flow-again" 0 1 1


# App inside Cylc Task:
export CYLC_TASK_FLOW_NUMBERS="1"
# It runs when we are now have CYLC_FLOW_TASK_NUMBERS set
grep_incrementals "flow1" 1 1 0
# It doesn't run the OK task again
grep_incrementals "flow1-again" 0 1 1

# It runs all jobs when CYLC_TASK_FLOW_NUMBERS changed:
export CYLC_TASK_FLOW_NUMBERS="2"
grep_incrementals "flow2" 1 1 0

# It runs all jobs if the task has multiple flow numbers:
export CYLC_TASK_FLOW_NUMBERS="1,2"
grep_incrementals "flow2" 1 1 0
