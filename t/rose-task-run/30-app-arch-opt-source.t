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
# Test "rose_arch" built-in application, archive with optional sources.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d "${HOME}/cylc-run/rose-test-battery.XXXXXX")"
NAME="$(basename "${SUITE_RUN_DIR}")"
rose suite-run -q -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-job.status"
file_grep "${TEST_KEY}-archive1-01" \
    'CYLC_JOB_EXIT=SUCCEEDED' \
    "${SUITE_RUN_DIR}/log/job/1/archive1/01/job.status"
file_grep "${TEST_KEY}-archive2-01" \
    'CYLC_JOB_EXIT=ERR' \
    "${SUITE_RUN_DIR}/log/job/1/archive2/01/job.status"
file_grep "${TEST_KEY}-archive2-02" \
    'CYLC_JOB_EXIT=SUCCEEDED' \
    "${SUITE_RUN_DIR}/log/job/1/archive2/02/job.status"
TEST_KEY="${TEST_KEY_BASE}-find"
(cd "${SUITE_RUN_DIR}/share/backup" && find -type f) | sort >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__FIND__'
./archive1.d/2014.txt
./archive1.d/2016.txt
./archive2.d/2015.txt
__FIND__
sed -n 's/^\[INFO\] \([+!=0] [^ ]*\) .*$/\1/p' \
    "${SUITE_RUN_DIR}/log/job/1/archive"*"/0"*"/job.out" \
    | sort >'job.out.sorted'
file_cmp "${TEST_KEY}-job.out.sorted" 'job.out.sorted' <<__LOG__
! ${SUITE_RUN_DIR}/share/backup/archive2.d/
+ ${SUITE_RUN_DIR}/share/backup/archive1.d/
+ ${SUITE_RUN_DIR}/share/backup/archive2.d/
0 ${SUITE_RUN_DIR}/share/backup/nobody.d/
__LOG__
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
