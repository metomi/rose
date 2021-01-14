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
# Test "rose_arch" built-in application, duplicate targets.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"


#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d "${HOME}/cylc-run/rose-test-battery.XXXXXX")"
NAME="$(basename "${SUITE_RUN_DIR}")"
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --flow-name="${NAME}" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-run" \
    cylc run \
        "${NAME}" \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
file_grep "${TEST_KEY}" 'duplicate archive target: "foo"' \
    "${SUITE_RUN_DIR}/log/job/1/archive_fail_duplicate/NN/job.err"
#-------------------------------------------------------------------------------
cylc clean "${NAME}"
exit 0
