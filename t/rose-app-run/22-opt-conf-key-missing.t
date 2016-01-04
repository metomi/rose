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
# Test "rose app-run -O (key)" syntax.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
tests 6
#-------------------------------------------------------------------------------
test_init <<'__CONFIG__'
[command]
default=printenv FOO BAR

[env]
BAR=bar bar
__CONFIG__
mkdir 'config/opt'
cat >'config/opt/rose-app-num1.conf' <<'__CONF__'
[env]
FOO=foo foo
__CONF__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-cli"
test_setup
run_pass "${TEST_KEY}" \
    rose app-run -O '(num0)' -O 'num1' -O '(num2)' --config='../config' -v
sed '/^\[INFO\] export PATH=/d' "${TEST_KEY}.out" >"${TEST_KEY}.out.edited"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.edited" <<'__OUT__'
[INFO] Configuration: ../config/
[INFO]     file: rose-app.conf
[INFO]     optional key: (num0)
[INFO]     optional key: num1
[INFO]     optional key: (num2)
[INFO] export BAR=bar\ bar
[INFO] export FOO=foo\ foo
[INFO] command: printenv FOO BAR
foo foo
bar bar
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-env"
test_setup
ROSE_APP_OPT_CONF_KEYS='(num0) num1 (num2)' \
run_pass "${TEST_KEY}" rose app-run --config='../config' -v
sed '/^\[INFO\] export PATH=/d' "${TEST_KEY}.out" >"${TEST_KEY}.out.edited"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.edited" <<'__OUT__'
[INFO] Configuration: ../config/
[INFO]     file: rose-app.conf
[INFO]     optional key: (num0)
[INFO]     optional key: num1
[INFO]     optional key: (num2)
[INFO] export BAR=bar\ bar
[INFO] export FOO=foo\ foo
[INFO] command: printenv FOO BAR
foo foo
bar bar
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
test_teardown
#-------------------------------------------------------------------------------
exit
