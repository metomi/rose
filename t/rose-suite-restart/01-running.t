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
# Test "rose suite-restart" on suites that are still running.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
tests 4
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
SUITE_RUN_DIR="$(readlink -f ${SUITE_RUN_DIR})"
NAME="$(basename "${SUITE_RUN_DIR}")"
rose suite-run --debug -q \
    -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" --no-gcontrol

TEST_KEY="${TEST_KEY_BASE}-name"
run_fail "${TEST_KEY}" rose suite-restart --name="${NAME}"
file_grep "${TEST_KEY}.err" \
    "\[FAIL\] Suite \"${NAME}\" may still be running." "${TEST_KEY}.err"

TEST_KEY="${TEST_KEY_BASE}-cwd"
run_fail "${TEST_KEY}" bash -c "cd '${SUITE_RUN_DIR}'; rose suite-restart"
file_grep "${TEST_KEY}.err" \
    "\[FAIL\] Suite \"${NAME}\" may still be running." "${TEST_KEY}.err"
#-------------------------------------------------------------------------------
rm -f "${SUITE_RUN_DIR}/work/1/foo/file"
timeout 60 \
    bash -c "while test -e '${HOME}/.cylc/ports/${NAME}'; do sleep 1; done"
rose suite-clean -q -y "${NAME}"
exit
