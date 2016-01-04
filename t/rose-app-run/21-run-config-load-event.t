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
# Test "rose app-run -v" prints out configuration load event.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
tests 6
#-------------------------------------------------------------------------------
test_init <<'__CONFIG__'
[command]
default=true
__CONFIG__
mkdir 'config/opt'
cat >'config/opt/rose-app-foo.conf' <<'__CONF__'
[command]
foo=echo "$FOO"
__CONF__
cat >'config/opt/rose-app-bar.conf' <<'__CONF__'
[command]
bar=echo "$BAR"
__CONF__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
test_setup
run_pass "${TEST_KEY}" rose app-run --config=../config -v
sed '/^\[INFO\] export PATH=/d' "${TEST_KEY}.out" >"${TEST_KEY}.out.edited"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.edited" <<'__OUT__'
[INFO] Configuration: ../config/
[INFO]     file: rose-app.conf
[INFO] command: true
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
test_setup
run_pass "${TEST_KEY}" rose app-run --config=../config -v -Ofoo -Obar \
    -D'[env]FOO=food festival' -D'[env]BAR=barley drink'
sed '/^\[INFO\] export PATH=/d' "${TEST_KEY}.out" >"${TEST_KEY}.out.edited"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.edited" <<'__OUT__'
[INFO] Configuration: ../config/
[INFO]     file: rose-app.conf
[INFO]     optional key: foo
[INFO]     optional key: bar
[INFO]     optional define: [env]FOO=food festival
[INFO]     optional define: [env]BAR=barley drink
[INFO] export BAR=barley\ drink
[INFO] export FOO=food\ festival
[INFO] command: true
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
exit
