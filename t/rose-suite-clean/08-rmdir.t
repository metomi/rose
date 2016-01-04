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
# Test "rose suite-clean", normal mode.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${SUITE_RUN_DIR}")"

cp -pr "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" "${NAME}"

JOB_HOST="$(rose config 't' 'job-host')"
JOB_HOST_RUN_ROOT="$(rose config 't' 'job-host-run-root')"
JOB_HOST_OPT=
if [[ -n "${JOB_HOST}" && -n "${JOB_HOST_RUN_ROOT}" ]]; then
    export JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
    export JOB_HOST_RUN_ROOT
    cat >>"${NAME}/rose-suite.conf" <<__CONF__
root-dir{share/cycle}=${JOB_HOST}=${JOB_HOST_RUN_ROOT}
                     =*=\${ROSE_TEST_ROOT_DIR}
root-dir{work}=${JOB_HOST}=${JOB_HOST_RUN_ROOT}
              =*=\${ROSE_TEST_ROOT_DIR}

[jinja2:suite.rc]
JOB_HOST="${JOB_HOST}"
__CONF__
    tests 7
else
    tests 5
fi

# Run suite, create lots of directories
export ROSE_CONF_PATH=
export ROSE_TEST_ROOT_DIR="${PWD}/root.d"
set -e
rose suite-run -C "${PWD}/${NAME}" --no-gcontrol --host='localhost' -- --debug
# Prove that the directories exist before clean
test -d "${HOME}/cylc-run/${NAME}"
test -e "${HOME}/.cylc/${NAME}"
test -e "${HOME}/.cylc/REGDB/${NAME}"
test -d "${PWD}/root.d/cylc-run/${NAME}"
if [[ -n "${JOB_HOST}" && -n "${JOB_HOST_RUN_ROOT}" ]]; then
    SSH='ssh -n -oBatchMode=yes'
    ${SSH} "${JOB_HOST}" \
        "bash -l -c 'ls -d cylc-run/${NAME} ${JOB_HOST_RUN_ROOT}/cylc-run/${NAME}'"
fi
set +e

TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" rose suite-clean -y -v -v --debug "${NAME}"
run_fail "${TEST_KEY}-test-d-cylc-run" test -d "${HOME}/cylc-run/${NAME}"
run_fail "${TEST_KEY}-test-d-dot-cylc-1" test -e "${HOME}/.cylc/${NAME}"
run_fail "${TEST_KEY}-test-d-dot-cylc-2" test -e "${HOME}/.cylc/REGDB/${NAME}"
run_fail "${TEST_KEY}-test-d-root-x" test -d "${PWD}/root.d/cylc-run/${NAME}"
if [[ -n "${JOB_HOST}" && -n "${JOB_HOST_RUN_ROOT}" ]]; then
    run_pass "${TEST_KEY}-test-d-at-${JOB_HOST}" ${SSH} "${JOB_HOST}" \
        "bash -l -c '! test -d cylc-run/${NAME}'"
    run_pass "${TEST_KEY}-test-d-at-${JOB_HOST}" ${SSH} "${JOB_HOST}" \
        "bash -l -c '! test -d ${JOB_HOST_RUN_ROOT}/cylc-run/${NAME}'"
fi
#-------------------------------------------------------------------------------
exit 0
