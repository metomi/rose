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
# Test for "rose bush", behaviour of job entry with no "job.out".
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
if ! python -c 'import cherrypy' 2>'/dev/null'; then
    skip_all '"cherrypy" not installed'
fi

tests 3

ROSE_CONF_PATH= rose_ws_init 'rose' 'bush'
if [[ -z "${TEST_ROSE_WS_PORT}" ]]; then
    exit 1
fi

#-------------------------------------------------------------------------------
# Run a quick cylc suite
mkdir -p "${HOME}/cylc-run"
SUITE_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" "rtb-rose-bush-02-XXXXXXXX")"
SUITE_NAME="$(basename "${SUITE_DIR}")"
cp -pr "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/"* "${SUITE_DIR}"
export CYLC_CONF_PATH=
cylc register "${SUITE_NAME}" "${SUITE_DIR}"
cylc run --debug "${SUITE_NAME}"

# Remove the "job.out" entry from the suite's public database.
sqlite3 "${SUITE_DIR}/cylc-suite.db" \
    'DELETE FROM task_job_logs WHERE filename=="job.out";'

#-------------------------------------------------------------------------------

TEST_KEY="${TEST_KEY_BASE}-200-curl-jobs"
run_pass "${TEST_KEY}" \
    curl "${TEST_ROSE_WS_URL}/jobs/${USER}/${SUITE_NAME}?form=json"
FOO0="{'cycle': '20000101T0000Z', 'name': 'foo0', 'submit_num': 1}"
FOO0_OUT='log/job/20000101T0000Z/foo0/01/job.out'
FOO0_OUT_MTIME=$(stat -c'%Y' "${SUITE_DIR}/${FOO0_OUT}")
FOO0_OUT_SIZE=$(stat -c'%s' "${SUITE_DIR}/${FOO0_OUT}")
rose_ws_json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('entries', ${FOO0}, 'logs', 'job.out', 'path'), '${FOO0_OUT}']" \
    "[('entries', ${FOO0}, 'logs', 'job.out', 'size'), ${FOO0_OUT_SIZE}]" \
    "[('entries', ${FOO0}, 'logs', 'job.out', 'mtime'), ${FOO0_OUT_MTIME}]" \
    "[('entries', ${FOO0}, 'logs', 'job.out', 'exists'), True]"

#-------------------------------------------------------------------------------
# Tidy up
rose_ws_kill
cylc unregister "${SUITE_NAME}" 1>'/dev/null' 2>&1
rm -fr "${SUITE_DIR}" "${HOME}/.cylc/ports/${SUITE_NAME}" 2>'/dev/null'
exit 0
