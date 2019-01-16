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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
# Run the suite.
if [[ "${TEST_KEY_BASE}" == *conf ]]; then
    if ! rose config -q 'rose-suite-run' 'hosts'; then
        skip_all '"[rose-suite-run]hosts" not defined'
    fi
else
    export ROSE_CONF_PATH=
fi

get_host_fqdn() {
    python3 - "$@" <<'__PYTHON__'
import socket
import sys
sys.stdout.write(socket.gethostbyname_ex(sys.argv[1])[0] + "\n")
__PYTHON__
}
#-------------------------------------------------------------------------------
tests 11
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
mkdir -p "${HOME}/cylc-run"
RUND="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${RUND}")"
run_pass "${TEST_KEY}" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol
CONTACT="${HOME}/cylc-run/${NAME}/.service/contact"
SUITE_HOST="$(sed -n 's/CYLC_SUITE_HOST=//p' "${CONTACT}")"
SUITE_OWNER="$(sed -n 's/CYLC_SUITE_OWNER=//p' "${CONTACT}")"
SUITE_PORT="$(sed -n 's/CYLC_SUITE_PORT=//p' "${CONTACT}")"
SUITE_PROCESS="$(sed -n 's/CYLC_SUITE_PROCESS=//p' "${CONTACT}")"
poll ! test -e "${RUND}/log/job/20130101T0000Z/my_task_1/01"
#-------------------------------------------------------------------------------
# "rose suite-run" should not work while suite is running.
# except --reload mode.
for OPTION in -i -l '' --restart; do
    TEST_KEY="${TEST_KEY_BASE}-running${OPTION}"
    run_fail "${TEST_KEY}" rose suite-run "${OPTION}" \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" --no-gcontrol
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] Suite "${NAME}" appears to be running:
[FAIL] Contact info from: "${CONTACT}"
[FAIL]     CYLC_SUITE_HOST=${SUITE_HOST}
[FAIL]     CYLC_SUITE_OWNER=${SUITE_OWNER}
[FAIL]     CYLC_SUITE_PORT=${SUITE_PORT}
[FAIL]     CYLC_SUITE_PROCESS=${SUITE_PROCESS}
[FAIL] Try "cylc stop '${NAME}'" first?
__ERR__
done
# Don't reload until tasks begin
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while (($(date +%s) < TIMEOUT)) && ! (
    cd "${RUND}/log/job/"
    test -f "20130101T0000Z/my_task_1/01/job.out" && test -f "20130101T1200Z/my_task_1/01/job.out"
)
do
    sleep 1
done
TEST_KEY="${TEST_KEY_BASE}-running-reload"
run_pass "${TEST_KEY}" rose suite-run --reload \
    -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" --no-gcontrol \
    --debug
sleep 1
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY="${TEST_KEY_BASE}-suite-run-wait"
touch "${RUND}/flag" # allow the task to die
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
CONTACT="${HOME}/cylc-run/${NAME}/.service/contact"
while [[ -e "${CONTACT}" ]] && (($(date +%s) < TIMEOUT))
do
    sleep 1
done
if [[ -e "${CONTACT}" ]]; then
    fail "${TEST_KEY}"
    exit 1
else
    pass "${TEST_KEY}"
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
