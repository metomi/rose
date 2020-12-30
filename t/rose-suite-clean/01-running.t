#!/bin/bash
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
# Test "rose suite-clean", while the suite is running.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"


#-------------------------------------------------------------------------------
tests 7
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
TEST_KEY="${TEST_KEY_BASE}"
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
SUITE_RUN_DIR="$(readlink -f "${SUITE_RUN_DIR}")"
NAME="$(basename "${SUITE_RUN_DIR}")"
# Install suite, and prove that directories are created
rose suite-run --debug -q \
    -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    -- --no-detach --debug &
ROSE_SUITE_RUN_PID=$!
poll ! test -e "${SUITE_RUN_DIR}/log/job/2013010100/my_task_1/01/job"
CONTACT="${HOME}/cylc-run/${NAME}/.service/contact"
SUITE_HOST="$(sed -n 's/CYLC_SUITE_HOST=//p' "${CONTACT}")"
SUITE_OWNER="$(sed -n 's/CYLC_SUITE_OWNER=//p' "${CONTACT}")"
SUITE_PORT="$(sed -n 's/CYLC_SUITE_PORT=//p' "${CONTACT}")"
SUITE_PROCESS="$(sed -n 's/CYLC_SUITE_PROCESS=//p' "${CONTACT}")"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-running"
run_fail "${TEST_KEY}" rose suite-clean -y "${NAME}"
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
if [[ ! -d "${HOME}/cylc-run/${NAME}" ]]; then
    exit 1
fi
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-running-name"
run_fail "${TEST_KEY}" rose suite-clean -y -n "${NAME}"
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
if [[ ! -d "${HOME}/cylc-run/${NAME}" ]]; then
    exit 1
fi
#-------------------------------------------------------------------------------
touch $SUITE_RUN_DIR/flag # let the suite stop
# Wait for the suite to complete
TIMEOUT=$(($(date +%s) + 120)) # wait 2 minutes
while [[ -e "${CONTACT}" ]] && (($(date +%s) < TIMEOUT))
do
    sleep 1
done
if [[ -e "${CONTACT}" ]]; then
    exit 1
fi
wait "${ROSE_SUITE_RUN_PID}"
TEST_KEY="${TEST_KEY_BASE}-stopped"
run_pass "${TEST_KEY}" rose suite-clean -y "${NAME}"
sed -i '/\/\.cylc\//d' "$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: localhost:cylc-run/${NAME}/work
[INFO] delete: localhost:cylc-run/${NAME}/share/cycle
[INFO] delete: localhost:cylc-run/${NAME}/share
[INFO] delete: localhost:cylc-run/${NAME}
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
#-------------------------------------------------------------------------------
exit 0
