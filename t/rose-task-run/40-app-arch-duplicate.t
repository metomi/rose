#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
skip_all "@TODO: Awaiting App upgrade to Python3"

#-------------------------------------------------------------------------------
tests 1
#-------------------------------------------------------------------------------
# Run the suite, and wait for it to complete
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d "${HOME}/cylc-run/rose-test-battery.XXXXXX")"
NAME="$(basename "${SUITE_RUN_DIR}")"
rose suite-run -q -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host=localhost -- --no-detach
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
file_grep "${TEST_KEY}" 'duplicate archive target: "foo"' \
    "${SUITE_RUN_DIR}/log/job/1/archive_fail_duplicate/NN/job.err"
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
