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
rose suite-run --debug --name="${NAME}" \
    -S "HOST=\"${JOB_HOST}\"" -- --no-detach --debug --hold 1>'/dev/null' 2>&1 &
ROSE_SUITE_RUN_PID=$!

timeout 60 bash -c \
    "while ! test -e '${HOME}/cylc-run/${NAME}/.service/contact'; do sleep 1; done"
sed -i "s/host = localhost/host = ${JOB_HOST}/" 'suite.rc'

TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" \
    rose suite-run --debug --reload --name="${NAME}" \
    -S "HOST=\"${JOB_HOST}\""
sed -n '/\(delete\|install\): suite\.rc/p' \
    "${TEST_KEY}.out" >"${TEST_KEY}.out.edited"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.edited" <<'__OUT__'
[INFO] delete: suite.rc
[INFO] install: suite.rc
__OUT__

cylc release "${NAME}"

wait "${ROSE_SUITE_RUN_PID}"
rose suite-clean -q -y "${NAME}"
exit 0
