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
# Test "rose suite-run", reload with a new job host.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
JOB_HOST="$(rose config --default= 't' 'job-host')"
if [[ -n "${JOB_HOST}" ]]; then
    JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
fi
if [[ -z "${JOB_HOST}" ]]; then
    skip_all '"[t]job-host" not defined'
fi
tests 2
export ROSE_CONF_PATH=
rsync -a "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/" '.'
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename ${SUITE_RUN_DIR})"
rose suite-run --debug --name="${NAME}" --no-gcontrol \
    -S "HOST=\"${JOB_HOST}\"" -- --debug --hold &
ROSE_SUITE_RUN_PID=$!

timeout 60 bash -c \
    "while ! test -e '${HOME}/.cylc/ports/${NAME}'; do sleep 1; done"
sed -i "s/host = localhost/host = ${JOB_HOST}/" 'suite.rc'

run_pass "${TEST_KEY_BASE}" \
    rose suite-run --debug --reload --name="${NAME}" --no-gcontrol \
    -S "HOST=\"${JOB_HOST}\""
run_pass "${TEST_KEY_BASE}.out" \
    grep -q -F "[INFO] ${NAME}: will reload on localhost" "${TEST_KEY_BASE}.out"

cylc release "${NAME}"

wait "${ROSE_SUITE_RUN_PID}"
rose suite-clean -q -y "${NAME}"
exit 0
