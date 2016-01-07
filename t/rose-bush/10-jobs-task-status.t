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
# Test for "rose bush", jobs list, task status.
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

cat >'suite.rc' <<'__SUITE_RC__'
#!Jinja2
[cylc]
    UTC mode = True
    abort if any task fails = True
[scheduling]
    initial cycle point = 2000
    final cycle point = 2000
    [[dependencies]]
        [[[P1Y]]]
            graph = foo => bar
[runtime]
    [[foo]]
        script = test "${CYLC_TASK_TRY_NUMBER}" -eq 3
        retry delays = 3*P0Y
    [[bar]]
        script = false
        retry delays = 3*P0Y
__SUITE_RC__

#-------------------------------------------------------------------------------
# Run a quick cylc suite
mkdir -p "${HOME}/cylc-run"
SUITE_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" "rtb-rose-bush-10-XXXXXXXX")"
SUITE_NAME="$(basename "${SUITE_DIR}")"
cp -p 'suite.rc' "${SUITE_DIR}"
export CYLC_CONF_PATH=
cylc register "${SUITE_NAME}" "${SUITE_DIR}"
cylc run --debug "${SUITE_NAME}" 2>'/dev/null'

#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-200-curl-jobs"
run_pass "${TEST_KEY}" curl \
    "${TEST_ROSE_WS_URL}/jobs/${USER}/${SUITE_NAME}?form=json"
FOO1="{'cycle': '20000101T0000Z', 'name': 'foo', 'submit_num': 1}"
FOO2="{'cycle': '20000101T0000Z', 'name': 'foo', 'submit_num': 2}"
FOO3="{'cycle': '20000101T0000Z', 'name': 'foo', 'submit_num': 3}"
BAR1="{'cycle': '20000101T0000Z', 'name': 'bar', 'submit_num': 1}"
BAR2="{'cycle': '20000101T0000Z', 'name': 'bar', 'submit_num': 2}"
BAR3="{'cycle': '20000101T0000Z', 'name': 'bar', 'submit_num': 3}"
rose_ws_json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('entries', ${FOO1}, 'task_status',), 'success']" \
    "[('entries', ${FOO1}, 'status',), 'fail(ERR)']" \
    "[('entries', ${FOO2}, 'task_status',), 'success']" \
    "[('entries', ${FOO2}, 'status',), 'fail(ERR)']" \
    "[('entries', ${FOO3}, 'task_status',), 'success']" \
    "[('entries', ${FOO3}, 'status',), 'success']" \
    "[('entries', ${BAR1}, 'task_status',), 'fail']" \
    "[('entries', ${BAR1}, 'status',), 'fail(ERR)']" \
    "[('entries', ${BAR2}, 'task_status',), 'fail']" \
    "[('entries', ${BAR2}, 'status',), 'fail(ERR)']" \
    "[('entries', ${BAR3}, 'task_status',), 'fail']" \
    "[('entries', ${BAR3}, 'status',), 'fail(ERR)']"
#-------------------------------------------------------------------------------
# Tidy up
rose_ws_kill
cylc unregister "${SUITE_NAME}" 1>'/dev/null' 2>&1
rm -fr "${SUITE_DIR}" "${HOME}/.cylc/ports/${SUITE_NAME}" 2>'/dev/null'
exit 0
