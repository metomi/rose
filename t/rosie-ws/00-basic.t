#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
#
# This file is part of Rose, a framework for scientific suites.
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
# Basic tests for "rosie.ws".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 13
#-------------------------------------------------------------------------------
mkdir svn
svnadmin create svn/foo
URL=file://$PWD/svn/foo
PORT=8080
while nc -z localhost $PORT; do
    ((++PORT))
done
cat >rose.conf <<__ROSE_CONF__
[rosie-db]
db.foo=sqlite:///$PWD/rosie/foo.db.sqlite
repos.foo=$PWD/svn/foo

[rosie-id]
prefix-default=foo
prefix-location.foo=$URL

[rosie-ws]
log-dir=$PWD/rosie/log
port=$PORT
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD
$ROSE_HOME/sbin/rosa db-create -q
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-rosa-ws
$ROSE_HOME/sbin/rosa ws 0</dev/null 1>rosa-ws.out 2>rosa-ws.err &
ROSA_WS_PID=$!
T_INIT=$(date +%s)
while ! nc -z localhost $PORT && (($(date +%s) < T_INIT + 60)); do
    sleep 1
done
if nc -z localhost $PORT; then
    pass "$TEST_KEY"
else
    fail "$TEST_KEY"
    kill $ROSA_WS_PID 1>/dev/null 2>&1 || true
    exit 1
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-root
run_pass "$TEST_KEY" curl -I http://localhost:$PORT/
file_grep "$TEST_KEY.out" 'HTTP/.* 200 OK' "$TEST_KEY.out"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo
run_pass "$TEST_KEY" curl -I http://localhost:$PORT/foo/
file_grep "$TEST_KEY.out" 'HTTP/.* 200 OK' "$TEST_KEY.out"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-get_query_operators
run_pass "$TEST_KEY" \
    curl http://localhost:$PORT/foo/get_query_operators?format=json
run_pass "$TEST_KEY.out" python - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
d = sorted(json.load(open(sys.argv[1])))
sys.exit(d != ["contains", "endswith", "eq", "ge", "gt", "ilike", "le",
               "like", "lt", "match", "ne", "startswith"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-get_known_keys
run_pass "$TEST_KEY" \
    curl http://localhost:$PORT/foo/get_known_keys?format=json
run_pass "$TEST_KEY.out" python - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
d = sorted(json.load(open(sys.argv[1])))
sys.exit(d != ["author", "branch", "date", "from_idx", "idx", "owner",
               "project", "revision", "status", "title"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-empty-search
run_pass "$TEST_KEY" \
    curl "http://localhost:$PORT/foo/search?s=fish+and+chips&format=json"
echo -n '[]' >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-empty-query
Q="http://localhost:$PORT/foo/query"
run_pass "$TEST_KEY" \
    curl "$Q?q=project+eq+food+and+title+contains+fish+and+chips&format=json"
echo -n '[]' >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
#-------------------------------------------------------------------------------
kill $ROSA_WS_PID 1>/dev/null 2>&1 || true
exit 0
