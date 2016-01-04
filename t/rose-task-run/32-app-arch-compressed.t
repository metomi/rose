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
tests 2
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
file_grep "${TEST_KEY}-archive-01" \
    'CYLC_JOB_EXIT=SUCCEEDED' \
    "${SUITE_RUN_DIR}/log/job/1/archive/01/job.status"
TEST_KEY="${TEST_KEY_BASE}-find"
(cd "${SUITE_RUN_DIR}/share/backup" && find -type f) | sort >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__FIND__'
./archive.d/2016.txt.gz
./archive.d/whatever.tar.gz
__FIND__
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
