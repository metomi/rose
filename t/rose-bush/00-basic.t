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
# Basic tests for "rose bush".
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
if ! python -c 'import cherrypy' 2>'/dev/null'; then
    skip_all '"cherrypy" not installed'
fi

tests 51

ROSE_CONF_PATH= rose_ws_init 'rose' 'bush'
if [[ -z "${TEST_ROSE_WS_PORT}" ]]; then
    exit 1
fi

#-------------------------------------------------------------------------------
# Run a quick cylc suite
mkdir -p "${HOME}/cylc-run"
SUITE_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" "rtb-rose-bush-00-XXXXXXXX")"
SUITE_NAME="$(basename "${SUITE_DIR}")"
cp -pr "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/"* "${SUITE_DIR}"
export CYLC_CONF_PATH=
cylc register "${SUITE_NAME}" "${SUITE_DIR}"
cylc run --debug "${SUITE_NAME}"

#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-curl-root"
run_pass "${TEST_KEY}" curl -I "${TEST_ROSE_WS_URL}"
file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"

TEST_KEY="${TEST_KEY_BASE}-200-curl-root-json"
run_pass "${TEST_KEY}" curl "${TEST_ROSE_WS_URL}/?form=json"
rose_ws_json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('title',), 'Rose Bush']" \
    "[('host',), '$(hostname)']"

TEST_KEY="${TEST_KEY_BASE}-200-curl-suites"
run_pass "${TEST_KEY}" curl -I "${TEST_ROSE_WS_URL}/suites/${USER}"
file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"

TEST_KEY="${TEST_KEY_BASE}-200-curl-suites-json"
run_pass "${TEST_KEY}" curl "${TEST_ROSE_WS_URL}/suites/${USER}?form=json"
rose_ws_json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('title',), 'Rose Bush']" \
    "[('host',), '$(hostname)']" \
    "[('user',), '${USER}']" \
    "[('entries', {'name': '${SUITE_NAME}'}, 'name',), '${SUITE_NAME}']" \
    "[('entries', {'name': '${SUITE_NAME}'}, 'info', 'project'), 'survey']" \
    "[('entries', {'name': '${SUITE_NAME}'}, 'info', 'title'), 'hms beagle']"

TEST_KEY="${TEST_KEY_BASE}-404-curl-suites"
run_pass "${TEST_KEY}" curl -I "${TEST_ROSE_WS_URL}/suites/no-such-user"
file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"

for METHOD in 'cycles' 'jobs'; do
    TEST_KEY="${TEST_KEY_BASE}-200-curl-${METHOD}"
    run_pass "${TEST_KEY}" \
        curl -I "${TEST_ROSE_WS_URL}/${METHOD}/${USER}/${SUITE_NAME}"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"

    TEST_KEY="${TEST_KEY_BASE}-404-1-curl-${METHOD}"
    run_pass "${TEST_KEY}" \
        curl -I "${TEST_ROSE_WS_URL}/${METHOD}/no-such-user/${SUITE_NAME}"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"

    TEST_KEY="${TEST_KEY_BASE}-404-2-curl-${METHOD}"
    run_pass "${TEST_KEY}" \
        curl -I "${TEST_ROSE_WS_URL}/${METHOD}/${USER}/no-such-suite"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"
done

TEST_KEY="${TEST_KEY_BASE}-200-curl-cycles"
run_pass "${TEST_KEY}" \
    curl "${TEST_ROSE_WS_URL}/cycles/${USER}/${SUITE_NAME}?form=json"
rose_ws_json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('title',), 'Rose Bush']" \
    "[('host',), '$(hostname)']" \
    "[('user',), '${USER}']" \
    "[('suite',), '${SUITE_NAME}']" \
    "[('info', 'project',), 'survey']" \
    "[('info', 'title',), 'hms beagle']" \
    "[('page',), 1]" \
    "[('n_pages',), 1]" \
    "[('per_page',), 100]" \
    "[('order',), None]" \
    "[('states', 'is_running',), False]" \
    "[('states', 'is_failed',), False]" \
    "[('of_n_entries',), 2]" \
    "[('entries', {'cycle': '20000101T0000Z'}, 'n_states', 'success',), 2]"

TEST_KEY="${TEST_KEY_BASE}-200-curl-jobs"
run_pass "${TEST_KEY}" \
    curl "${TEST_ROSE_WS_URL}/jobs/${USER}/${SUITE_NAME}?form=json"
FOO0="{'cycle': '20000101T0000Z', 'name': 'foo0', 'submit_num': 1}"
FOO0_JOB='log/job/20000101T0000Z/foo0/01/job'
FOO1="{'cycle': '20000101T0000Z', 'name': 'foo1', 'submit_num': 1}"
FOO1_JOB='log/job/20000101T0000Z/foo1/01/job'
rose_ws_json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('title',), 'Rose Bush']" \
    "[('host',), '$(hostname)']" \
    "[('user',), '${USER}']" \
    "[('suite',), '${SUITE_NAME}']" \
    "[('info', 'project',), 'survey']" \
    "[('info', 'title',), 'hms beagle']" \
    "[('is_option_on',), False]" \
    "[('page',), 1]" \
    "[('n_pages',), 1]" \
    "[('per_page',), 15]" \
    "[('per_page_default',), 15]" \
    "[('per_page_max',), 300]" \
    "[('cycles',), None]" \
    "[('order',), None]" \
    "[('no_statuses',), None]" \
    "[('states', 'is_running',), False]" \
    "[('states', 'is_failed',), False]" \
    "[('of_n_entries',), 2]" \
    "[('entries', ${FOO0}, 'status',), 'success']" \
    "[('entries', ${FOO0}, 'host',), 'localhost']" \
    "[('entries', ${FOO0}, 'submit_method',), 'background']" \
    "[('entries', ${FOO0}, 'logs', 'job', 'path'), '${FOO0_JOB}']" \
    "[('entries', ${FOO0}, 'logs', 'job.err', 'path'), '${FOO0_JOB}.err']" \
    "[('entries', ${FOO0}, 'logs', 'job.out', 'path'), '${FOO0_JOB}.out']" \
    "[('entries', ${FOO0}, 'logs', 'job.txt.01', 'seq_key'), 'job.txt.*']" \
    "[('entries', ${FOO0}, 'logs', 'job.txt.05', 'seq_key'), 'job.txt.*']" \
    "[('entries', ${FOO0}, 'logs', 'job.txt.10', 'seq_key'), 'job.txt.*']" \
    "[('entries', ${FOO1}, 'status',), 'success']" \
    "[('entries', ${FOO1}, 'host',), 'localhost']" \
    "[('entries', ${FOO1}, 'submit_method',), 'background']" \
    "[('entries', ${FOO1}, 'logs', 'job', 'path'), '${FOO1_JOB}']" \
    "[('entries', ${FOO1}, 'logs', 'job.err', 'path'), '${FOO1_JOB}.err']" \
    "[('entries', ${FOO1}, 'logs', 'job.out', 'path'), '${FOO1_JOB}.out']" \
    "[('entries', ${FOO1}, 'logs', 'job.txt.01', 'seq_key'), 'job.txt.*']" \
    "[('entries', ${FOO1}, 'logs', 'job.txt.05', 'seq_key'), 'job.txt.*']" \
    "[('entries', ${FOO1}, 'logs', 'job.txt.10', 'seq_key'), 'job.txt.*']"

# A suite run directory with only a "cylc-suite.db", and nothing else
SUITE_DIR2="$(mktemp -d --tmpdir="${HOME}/cylc-run" "rtb-rose-bush-00-XXXXXXXX")"
SUITE_NAME2="$(basename "${SUITE_DIR2}")"
cp -pr "${SUITE_DIR}/cylc-suite.db" "${SUITE_DIR2}/"
run_pass "${TEST_KEY}-bare" \
    curl "${TEST_ROSE_WS_URL}/jobs/${USER}/${SUITE_NAME2}?form=json"
rose_ws_json_greps "${TEST_KEY}-bare.out" "${TEST_KEY}-bare.out" \
    "[('suite',), '${SUITE_NAME2}']"

for FILE in \
    'log/suite/log' \
    'log/job/20000101T0000Z/foo0/01/job' \
    'log/job/20000101T0000Z/foo0/01/job.out' \
    'log/job/20000101T0000Z/foo1/01/job' \
    'log/job/20000101T0000Z/foo1/01/job.out'
do
    TEST_KEY="${TEST_KEY_BASE}-200-curl-view-$(tr '/' '-' <<<"${FILE}")"
    run_pass "${TEST_KEY}" \
        curl -I "${TEST_ROSE_WS_URL}/view/${USER}/${SUITE_NAME}?path=${FILE}"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"
    MODE='&mode=download'
    run_pass "${TEST_KEY}-download" \
        curl "${TEST_ROSE_WS_URL}/view/${USER}/${SUITE_NAME}?path=${FILE}${MODE}"
    file_cmp "${TEST_KEY}-download.out" \
        "${TEST_KEY}-download.out" "${HOME}/cylc-run/${SUITE_NAME}/${FILE}"
done

TEST_KEY="${TEST_KEY_BASE}-404-curl-view-garbage"
run_pass "${TEST_KEY}" \
    curl -I \
    "${TEST_ROSE_WS_URL}/view/${USER}/${SUITE_NAME}?path=log/of/minus-one"
file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"

#-------------------------------------------------------------------------------
# Tidy up
rose_ws_kill
cylc unregister "${SUITE_NAME}" 1>'/dev/null' 2>&1
rm -fr "${SUITE_DIR}" "${SUITE_DIR2}" "${HOME}/.cylc/ports/${SUITE_NAME}" \
    2>'/dev/null'
exit 0
