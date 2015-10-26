#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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

# Load JSON content in argument 1
# Each remaining argument is an expected content in the JSON data in the form:
# [keys, value]
# Where "keys" is a list containing keys or indexes to an
# expected item in the data structure, and the value is an expected value.
# A key in keys can be a simple dict key or an array index.
# It can also be a dict {attr_key: attr_value, ...}. In which case, the
# expected data item is under a list of dicts, where a unique dict in the list
# contains all elements attr_key: attr_value.
json_greps() {
    local TEST_KEY="$1"
    shift 1
    run_pass "${TEST_KEY}" python - "$@" <<'__PYTHON__'
import ast
import simplejson as json
import sys

data = json.load(open(sys.argv[1]))
for item in sys.argv[2:]:
    keys, value = ast.literal_eval(item)
    datum = data
    try:
        for key in keys:
            if isinstance(key, dict):
                for datum_item in datum:
                    if all([datum_item.get(k) == v for k, v in key.items()]):
                        datum = datum_item
                        break
                else:
                    raise KeyError
            else:
                datum = datum[key]
        if datum != value:
            raise ValueError(item)
    except (IndexError, KeyError):
        raise KeyError(item)
__PYTHON__
    if [[ -s "${TEST_KEY}.err" ]]; then
        cat "${TEST_KEY}.err" >&2
    fi
}

tests 47

#-------------------------------------------------------------------------------
# Run a quick cylc suite
mkdir -p "${HOME}/cylc-run"
SUITE_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" "rtb-rose-bush-00-XXXXXXXX")"
SUITE_NAME="$(basename "${SUITE_DIR}")"
cat >"${SUITE_DIR}/rose-suite.info" <<__ROSE_SUITE_INFO__
owner=${USER}
project=rose-test
title=${TEST_KEY_BASE}
__ROSE_SUITE_INFO__
cat >"${SUITE_DIR}/suite.rc" <<'__SUITE_RC__'
#!Jinja2
[cylc]
    UTC mode = True
    abort if any task fails = True
[scheduling]
    initial cycle point = 2000
    final cycle point = 2000
    [[dependencies]]
        [[[P1Y]]]
            graph = FOO
[runtime]
    [[FOO]]
        script = echo "Hello from ${CYLC_TASK_ID}.${CYLC_SUITE_NAME}"
    [[foo0, foo1]]
        inherit = FOO
__SUITE_RC__
export CYLC_CONF_PATH=
cylc register "${SUITE_NAME}" "${SUITE_DIR}"
cylc run --debug "${SUITE_NAME}"

#-------------------------------------------------------------------------------
# Set up and start Rose Bush server
PORT="$((${RANDOM} + 10000))"
while port_is_busy "${PORT}"; do
    PORT="$((${RANDOM} + 10000))"
done

TEST_KEY="${TEST_KEY_BASE}-rose-bush"
rose bush 'start' "${PORT}" \
    0<'/dev/null' 1>'rose-bush.out' 2>'rose-bush.err' &
ROSE_BUSH_PID=$!
T_INIT="$(date '+%s')"
while ! port_is_busy "${PORT}" && (($(date '+%s') < ${T_INIT} + 60)); do
    sleep 1
done
if port_is_busy "${PORT}"; then
    pass "${TEST_KEY}"
else
    fail "${TEST_KEY}"
    exit 1
fi
URL="http://${HOSTNAME}:${PORT}/"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-curl-root"
run_pass "${TEST_KEY}" curl -I "${URL}"
file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"

TEST_KEY="${TEST_KEY_BASE}-200-curl-suites"
run_pass "${TEST_KEY}" curl -I "${URL}/suites/${USER}"
file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"

TEST_KEY="${TEST_KEY_BASE}-200-curl-suites-json"
run_pass "${TEST_KEY}" curl "${URL}/suites/${USER}?form=json"
json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('host',), '$(hostname)']" \
    "[('user',), '${USER}']" \
    "[('entries', {'name': '${SUITE_NAME}'}, 'name',), '${SUITE_NAME}']" \
    "[('entries', {'name': '${SUITE_NAME}'}, 'info', 'project'), 'rose-test']" \
    "[('entries', {'name': '${SUITE_NAME}'}, 'info', 'title'), '${TEST_KEY_BASE}']"

TEST_KEY="${TEST_KEY_BASE}-404-curl-suites"
run_pass "${TEST_KEY}" curl -I "${URL}/suites/no-such-user"
file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"

for METHOD in 'cycles' 'jobs'; do
    TEST_KEY="${TEST_KEY_BASE}-200-curl-${METHOD}"
    run_pass "${TEST_KEY}" curl -I "${URL}/${METHOD}/${USER}/${SUITE_NAME}"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"

    TEST_KEY="${TEST_KEY_BASE}-404-1-curl-${METHOD}"
    run_pass "${TEST_KEY}" curl -I "${URL}/${METHOD}/no-such-user/${SUITE_NAME}"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"

    TEST_KEY="${TEST_KEY_BASE}-404-2-curl-${METHOD}"
    run_pass "${TEST_KEY}" curl -I "${URL}/${METHOD}/${USER}/no-such-suite"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"
done

run_pass "${TEST_KEY}" curl "${URL}/cycles/${USER}/${SUITE_NAME}?form=json"
json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('host',), '$(hostname)']" \
    "[('user',), '${USER}']" \
    "[('suite',), '${SUITE_NAME}']" \
    "[('info', 'project',), 'rose-test']" \
    "[('info', 'title',), '${TEST_KEY_BASE}']" \
    "[('page',), 1]" \
    "[('n_pages',), 1]" \
    "[('per_page',), 100]" \
    "[('offset',), 0]" \
    "[('cycles',), None]" \
    "[('order',), None]" \
    "[('states', 'is_running',), False]" \
    "[('states', 'is_failed',), False]" \
    "[('of_n_entries',), 2]" \
    "[('entries', {'cycle': '20000101T0000Z'}, 'n_states', 'success',), 2]"

run_pass "${TEST_KEY}" curl "${URL}/jobs/${USER}/${SUITE_NAME}?form=json"
FOO0="{'cycle': '20000101T0000Z', 'name': 'foo0', 'submit_num': 1}"
FOO1="{'cycle': '20000101T0000Z', 'name': 'foo1', 'submit_num': 1}"
json_greps "${TEST_KEY}.out" "${TEST_KEY}.out" \
    "[('rose_version',), '$(rose version | cut -d' ' -f 2)']" \
    "[('host',), '$(hostname)']" \
    "[('user',), '${USER}']" \
    "[('suite',), '${SUITE_NAME}']" \
    "[('info', 'project',), 'rose-test']" \
    "[('info', 'title',), '${TEST_KEY_BASE}']" \
    "[('is_option_on',), None]" \
    "[('page',), 1]" \
    "[('n_pages',), 1]" \
    "[('per_page',), 15]" \
    "[('per_page_default',), 15]" \
    "[('per_page_max',), 300]" \
    "[('offset',), 0]" \
    "[('cycles',), None]" \
    "[('order',), None]" \
    "[('no_statuses',), None]" \
    "[('states', 'is_running',), False]" \
    "[('states', 'is_failed',), False]" \
    "[('of_n_entries',), 2]" \
    "[('entries', ${FOO0}, 'status',), 'success']" \
    "[('entries', ${FOO0}, 'host',), 'localhost']" \
    "[('entries', ${FOO0}, 'submit_method',), 'background']" \
    "[('entries', ${FOO1}, 'status',), 'success']" \
    "[('entries', ${FOO1}, 'host',), 'localhost']" \
    "[('entries', ${FOO1}, 'submit_method',), 'background']"

for FILE in \
    'log/suite/log' \
    'log/job/20000101T0000Z/foo0/01/job' \
    'log/job/20000101T0000Z/foo0/01/job.out' \
    'log/job/20000101T0000Z/foo1/01/job' \
    'log/job/20000101T0000Z/foo1/01/job.out'
do
    TEST_KEY="${TEST_KEY_BASE}-200-curl-view-$(tr '/' '-' <<<"${FILE}")"
    run_pass "${TEST_KEY}" \
        curl -I "${URL}/view/${USER}/${SUITE_NAME}?path=${FILE}"
    file_grep "${TEST_KEY}.out" 'HTTP/.* 200 OK' "${TEST_KEY}.out"
    run_pass "${TEST_KEY}-download" \
        curl "${URL}/view/${USER}/${SUITE_NAME}?path=${FILE}&mode=download"
    file_cmp "${TEST_KEY}-download.out" \
        "${TEST_KEY}-download.out" "${HOME}/cylc-run/${SUITE_NAME}/${FILE}"
done

TEST_KEY="${TEST_KEY_BASE}-404-curl-view-garbage"
run_pass "${TEST_KEY}" \
    curl -I "${URL}/view/${USER}/${SUITE_NAME}?path=log/of/minus-one"
file_grep "${TEST_KEY}.out" 'HTTP/.* 404 Not Found' "${TEST_KEY}.out"

#-------------------------------------------------------------------------------
# Tidy up
kill "${ROSE_BUSH_PID}"
wait 2>'/dev/null'
cylc unregister "${SUITE_NAME}" 1>'/dev/null' 2>&1
rm -fr "${SUITE_DIR}" "${HOME}/.cylc/ports/${SUITE_NAME}" 2>'/dev/null'
exit 0
