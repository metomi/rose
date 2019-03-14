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
# Test "rose suite-restart" on suites that are still running.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
skip_all "@TODO: Awaiting App upgrade to Python3"
tests 4
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
SUITE_RUN_DIR="$(readlink -f ${SUITE_RUN_DIR})"
NAME="$(basename "${SUITE_RUN_DIR}")"
timeout 120 rose suite-run --debug -q \
    -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" --no-gcontrol \
    -- --no-detach &
ROSE_SUITE_RUN_PID=$!
CONTACT="${HOME}/cylc-run/${NAME}/.service/contact"
poll ! test -e "${CONTACT}"
poll ! test -e "${HOME}/cylc-run/${NAME}/log/job/1/foo/NN/job.status"
SUITE_HOST="$(sed -n 's/CYLC_SUITE_HOST=//p' "${CONTACT}")"
SUITE_OWNER="$(sed -n 's/CYLC_SUITE_OWNER=//p' "${CONTACT}")"
SUITE_PORT="$(sed -n 's/CYLC_SUITE_PORT=//p' "${CONTACT}")"
SUITE_PROCESS="$(sed -n 's/CYLC_SUITE_PROCESS=//p' "${CONTACT}")"

TEST_KEY="${TEST_KEY_BASE}-name"
run_fail "${TEST_KEY}" rose suite-restart --name="${NAME}"
# Note: Error file CYLC_SUITE_* lines contain \t characters
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] Suite "${NAME}" appears to be running:
[FAIL] Contact info from: "${CONTACT}"
[FAIL]     CYLC_SUITE_HOST=${SUITE_HOST}
[FAIL]     CYLC_SUITE_OWNER=${SUITE_OWNER}
[FAIL]     CYLC_SUITE_PORT=${SUITE_PORT}
[FAIL]     CYLC_SUITE_PROCESS=${SUITE_PROCESS}
[FAIL] Try "cylc stop '${NAME}'" first?
__ERR__

TEST_KEY="${TEST_KEY_BASE}-cwd"
run_fail "${TEST_KEY}" bash -c "cd '${SUITE_RUN_DIR}'; rose suite-restart"
# Note: Error file CYLC_SUITE_* lines contain \t characters
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] Suite "${NAME}" appears to be running:
[FAIL] Contact info from: "${CONTACT}"
[FAIL]     CYLC_SUITE_HOST=${SUITE_HOST}
[FAIL]     CYLC_SUITE_OWNER=${SUITE_OWNER}
[FAIL]     CYLC_SUITE_PORT=${SUITE_PORT}
[FAIL]     CYLC_SUITE_PROCESS=${SUITE_PROCESS}
[FAIL] Try "cylc stop '${NAME}'" first?
__ERR__
#-------------------------------------------------------------------------------
rm -f "${SUITE_RUN_DIR}/work/1/foo/file"
wait "${ROSE_SUITE_RUN_PID}"
poll test -e "${CONTACT}"
rm -f "${CONTACT}"  # In case suite takes long time and is killed by timeout
rose suite-clean -q -y "${NAME}"
exit
