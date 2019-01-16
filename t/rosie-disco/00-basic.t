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
# Basic tests for "rosie disco".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
if ! python3 -c 'import cherrypy, sqlalchemy' 2>/dev/null; then
    skip_all '"cherrypy" or "sqlalchemy" not installed'
fi
#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------
mkdir svn
svnadmin create svn/foo
SVN_URL=file://$PWD/svn/foo
cat >rose.conf <<__ROSE_CONF__
[rosie-db]
db.foo=sqlite:///$PWD/rosie/foo.db.sqlite
repos.foo=$PWD/svn/foo

[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-location.foo=$SVN_URL
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD
$ROSE_HOME/sbin/rosa db-create -q
#-------------------------------------------------------------------------------
rose_ws_init 'rosie' 'disco'
if [[ -z "${TEST_ROSE_WS_PORT}" ]]; then
    exit 1
fi

URL_FOO="${TEST_ROSE_WS_URL}/foo/"
URL_FOO_S=${URL_FOO}search?
URL_FOO_Q=${URL_FOO}query?
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-root
run_pass "$TEST_KEY" curl -I "${TEST_ROSE_WS_URL}"
file_grep "$TEST_KEY.out" 'HTTP/.* 200 OK' "$TEST_KEY.out"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo
run_pass "$TEST_KEY" curl -I $URL_FOO
file_grep "$TEST_KEY.out" 'HTTP/.* 200 OK' "$TEST_KEY.out"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-get_query_operators
run_pass "$TEST_KEY" curl ${URL_FOO}get_query_operators?format=json
run_pass "$TEST_KEY.out" python3 - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
d = sorted(json.load(open(sys.argv[1])))
sys.exit(d != ["contains", "endswith", "eq", "ge", "gt", "ilike", "le",
               "like", "lt", "match", "ne", "startswith"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-get_known_keys
run_pass "$TEST_KEY" curl ${URL_FOO}get_known_keys?format=json
run_pass "$TEST_KEY.out" python3 - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
d = sorted(json.load(open(sys.argv[1])))
sys.exit(d != ["author", "branch", "date", "from_idx", "idx", "owner",
               "project", "revision", "status", "title"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-empty-search
run_pass "$TEST_KEY" curl "${URL_FOO_S}s=fish+and+chips&format=json"
echo -n '[]' >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-empty-query
run_pass "$TEST_KEY" \
    curl "${URL_FOO_Q}q=project+eq+food&q=title+contains+fish+and+chips&format=json"
echo -n '[]' >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
#-------------------------------------------------------------------------------
for FILE in $(ls $TEST_SOURCE_DIR/$TEST_KEY_BASE/*.conf); do
    rosie create -q -y --info-file=$FILE --no-checkout
    $ROSE_HOME/sbin/rosa svn-post-commit \
        $PWD/svn/foo $(svnlook youngest $PWD/svn/foo)
done
#-------------------------------------------------------------------------------
for FILE in $(ls $TEST_SOURCE_DIR/$TEST_KEY_BASE/*.conf.1); do
    ID=foo-$(basename $FILE .conf.1)
    rosie checkout -q $ID
    cat <$FILE >$PWD/roses/$ID/rose-suite.info
    svn ci -q -m 'test' $PWD/roses/$ID
    $ROSE_HOME/sbin/rosa svn-post-commit \
        $PWD/svn/foo $(svnlook youngest $PWD/svn/foo)
done
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-search
run_pass "$TEST_KEY" curl "${URL_FOO_S}s=apple&format=json"
run_pass "$TEST_KEY-out" python3 - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
expected_d = [{"idx": "foo-aa001",
               "title": "apple cider",
               "project": "drink",
               "owner": "ben"},
              {"idx": "foo-aa006",
               "title": "apple tart",
               "access-list": ["*"],
               "project": "food",
               "owner": "rosie"}]
d = json.load(open(sys.argv[1]))
sys.exit(len(d) != len(expected_d) or
         d[0]["idx"] != expected_d[0]["idx"] or
         d[0]["title"] != expected_d[0]["title"] or
         d[0]["project"] != expected_d[0]["project"] or
         d[0]["owner"] != expected_d[0]["owner"] or
         d[1]["idx"] != expected_d[1]["idx"] or
         d[1]["title"] != expected_d[1]["title"] or
         d[1]["project"] != expected_d[1]["project"] or
         d[1]["owner"] != expected_d[1]["owner"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-query
Q='q=project+eq+food&q=and+title+contains+apple'
run_pass "$TEST_KEY" \
    curl "${URL_FOO_Q}${Q}&format=json"
run_pass "$TEST_KEY-out" python3 - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
expected_d = [{"idx": "foo-aa006",
               "title": "apple tart",
               "project": "food",
               "owner": "rosie"}]
d = json.load(open(sys.argv[1]))
sys.exit(len(d) != len(expected_d) or
         d[0]["idx"] != expected_d[0]["idx"] or
         d[0]["title"] != expected_d[0]["title"] or
         d[0]["project"] != expected_d[0]["project"] or
         d[0]["owner"] != expected_d[0]["owner"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-query-all-revs
Q='q=project+eq+food&q=and+title+contains+apple'
run_pass "$TEST_KEY" \
    curl "${URL_FOO_Q}${Q}&all_revs=1&format=json"
run_pass "$TEST_KEY-out" python3 - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
expected_d = [{"idx": "foo-aa006",
               "title": "apple pie",
               "project": "food",
               "owner": "rosie",
               "revision": 7},
              {"idx": "foo-aa006",
               "title": "apple tart",
               "project": "food",
               "owner": "rosie",
               "revision": 9}]
d = json.load(open(sys.argv[1]))
sys.exit(len(d) != len(expected_d) or
         d[0]["idx"] != expected_d[0]["idx"] or
         d[0]["title"] != expected_d[0]["title"] or
         d[0]["project"] != expected_d[0]["project"] or
         d[0]["owner"] != expected_d[0]["owner"] or
         d[0]["revision"] != expected_d[0]["revision"] or
         d[1]["idx"] != expected_d[1]["idx"] or
         d[1]["title"] != expected_d[1]["title"] or
         d[1]["project"] != expected_d[1]["project"] or
         d[1]["owner"] != expected_d[1]["owner"] or
         d[1]["revision"] != expected_d[1]["revision"])
__PYTHON__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-curl-foo-query-brace
# (=%28 and )=%29
Q='q=%28+owner+eq+rose&q=or+owner+eq+rosie+%29&q=and+project+eq+food'
run_pass "$TEST_KEY" \
    curl "${URL_FOO_Q}${Q}&format=json"
run_pass "$TEST_KEY-out" python3 - "$TEST_KEY.out" <<'__PYTHON__'
import json, sys
expected_d = [{"idx": "foo-aa005",
               "title": "carrot cake",
               "project": "food",
               "owner": "rose",
               "revision": 6},
              {"idx": "foo-aa006",
               "title": "apple tart",
               "project": "food",
               "owner": "rosie",
               "revision": 9}]
d = json.load(open(sys.argv[1]))
sys.exit(len(d) != len(expected_d) or
         d[0]["idx"] != expected_d[0]["idx"] or
         d[0]["title"] != expected_d[0]["title"] or
         d[0]["project"] != expected_d[0]["project"] or
         d[0]["owner"] != expected_d[0]["owner"] or
         d[0]["revision"] != expected_d[0]["revision"] or
         d[1]["idx"] != expected_d[1]["idx"] or
         d[1]["title"] != expected_d[1]["title"] or
         d[1]["project"] != expected_d[1]["project"] or
         d[1]["owner"] != expected_d[1]["owner"] or
         d[1]["revision"] != expected_d[1]["revision"])
__PYTHON__
#-------------------------------------------------------------------------------
rose_ws_kill
exit 0
