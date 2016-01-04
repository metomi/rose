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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
JOB_HOST="$(rose config --default= 't' 'job-host')"
if [[ -n "${JOB_HOST}" ]]; then
    JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
fi
#-------------------------------------------------------------------------------
if [[ "${TEST_KEY_BASE}" == *conf ]]; then
    if ! rose config -q 'rose-suite-run' 'hosts'; then
        skip_all '"[rose-suite-run]hosts" not defined'
    fi
else
    export ROSE_CONF_PATH=
fi
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"
OPTION='-i'
if [[ "${TEST_KEY_BASE}" == *local* ]]; then
    OPTION='-l'
fi
mkdir "${TEST_KEY_BASE}"
cp -pr "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/"* "${TEST_KEY_BASE}"
touch "${TEST_KEY_BASE}/colon:is:ok"
if [[ -n "${JOB_HOST}" ]]; then
    run_pass "${TEST_KEY}" rose suite-run --debug \
        -C "${TEST_KEY_BASE}" "${OPTION}" \
        --name="${NAME}" --no-gcontrol \
        -S "HOST=\"${JOB_HOST}\""
else
    run_pass "${TEST_KEY}" rose suite-run --debug \
        -C "${TEST_KEY_BASE}" "${OPTION}" \
        --name="${NAME}" --no-gcontrol
fi
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-port-file"
run_fail "${TEST_KEY}" test -e "${HOME}/.cylc/ports/${NAME}"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-items"
run_pass "${TEST_KEY}" find "${SUITE_RUN_DIR}/"{app,colon:is:ok,etc} -type f
sort "${TEST_KEY}.out" >"${TEST_KEY}.out.sort"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.sort" <<__OUT__
${SUITE_RUN_DIR}/app/my_task_1/rose-app.conf
${SUITE_RUN_DIR}/colon:is:ok
${SUITE_RUN_DIR}/etc/junk
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-items-${JOB_HOST}"
if [[ "${TEST_KEY_BASE}" == *local* ]]; then
    skip 2 "${TEST_KEY}: local-install-only"
elif [[ -n "${JOB_HOST}" ]]; then
    run_pass "${TEST_KEY}" \
        ssh -oBatchMode=yes "${JOB_HOST}" \
        "find 'cylc-run/${NAME}/'{app,colon:is:ok,etc} -type f"
    sort "${TEST_KEY}.out" >"${TEST_KEY}.out.sort"
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.sort" <<__OUT__
cylc-run/${NAME}/app/my_task_1/rose-app.conf
cylc-run/${NAME}/colon:is:ok
cylc-run/${NAME}/etc/junk
__OUT__
else
    skip 2 "${TEST_KEY_BASE}-items: [t]job-host not defined"
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
