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
# Test "rose_arch" built-in application, archive with optional sources.
. "$(dirname "$0")/test_header"
tests 8
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=

get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --workflow-name="${FLOW}" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-job.status"
file_grep "${TEST_KEY}-archive1-01" \
    'CYLC_JOB_EXIT=SUCCEEDED' \
    "${FLOW_RUN_DIR}/log/job/1/archive1/01/job.status"
file_grep "${TEST_KEY}-archive2-01" \
    'CYLC_JOB_EXIT=ERR' \
    "${FLOW_RUN_DIR}/log/job/1/archive2/01/job.status"
file_grep "${TEST_KEY}-archive2-02" \
    'CYLC_JOB_EXIT=SUCCEEDED' \
    "${FLOW_RUN_DIR}/log/job/1/archive2/02/job.status"
TEST_KEY="${TEST_KEY_BASE}-find"
(cd "${FLOW_RUN_DIR}/share/backup" && find . -type f) | sort >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__FIND__'
./archive1.d/2014.txt
./archive1.d/2016.txt
./archive2.d/2015.txt
__FIND__
sed -n 's/^\[INFO\] \([+!=0] [^ ]*\) .*$/\1/p' \
    "${FLOW_RUN_DIR}/log/job/1/archive"*"/0"*"/job.out" \
    | sort >'job.out.sorted'
sort >'job.out.expected' <<__LOG__
! ${FLOW_RUN_DIR}/share/backup/archive2.d/
+ ${FLOW_RUN_DIR}/share/backup/archive1.d/
+ ${FLOW_RUN_DIR}/share/backup/archive2.d/
0 ${FLOW_RUN_DIR}/share/backup/nobody.d/
__LOG__
file_cmp "${TEST_KEY}-job.out.sorted" 'job.out.sorted' 'job.out.expected'
sed -n 's/^\[FAIL\] \(! [^ ]*\) .*$/\1/p' \
    "${FLOW_RUN_DIR}/log/job/1/archive"*"/0"*"/job.err" \
    | sort >'job.err.sorted'
sort >'job.err.expected' <<__LOG__
! ${FLOW_RUN_DIR}/share/backup/archive2.d/
__LOG__
file_cmp "${TEST_KEY}-job.err.sorted" 'job.err.sorted' 'job.err.expected'
#-------------------------------------------------------------------------------
purge
exit 0
