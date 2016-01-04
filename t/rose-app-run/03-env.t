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
# Test "rose app-run", environment variables.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
FOO='foo foolish food'
BAR='bar barley barcelona barcode'
BAZ='baz'
USER=${USER:-$(whoami)}
test_init <<__CONFIG__
[command]
default = printenv FOO BAR BAZ

[env]
FOO = $FOO
BAR = $BAR
BAZ = $BAZ
MY_NAME = \$USER
__CONFIG__
#-------------------------------------------------------------------------------
tests 24
#-------------------------------------------------------------------------------
# Normal mode.
TEST_KEY=$TEST_KEY_BASE
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
$FOO
$BAR
$BAZ
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Verbose mode.
TEST_KEY=$TEST_KEY_BASE-v1
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export BAR=bar\ barley\ barcelona\ barcode
[INFO] export BAZ=baz
[INFO] export FOO=foo\ foolish\ food
[INFO] export MY_NAME=$USER
[INFO] export PATH=$PATH
[INFO] command: printenv FOO BAR BAZ
$FOO
$BAR
$BAZ
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, redefine BAR using --define=SECTION=KEY=VALUE.
TEST_KEY=$TEST_KEY_BASE--define
test_setup
REDEFINED_BAR='a man walks into a bar'
run_pass "$TEST_KEY" \
    rose app-run --config=../config -q "--define=[env]BAR=$REDEFINED_BAR"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
$FOO
$REDEFINED_BAR
$BAZ
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, redefine BAR to an undefined environment variable.
TEST_KEY=$TEST_KEY_BASE-unbound-env
test_setup
if printenv NO_SUCH_VARIABLE 1>/dev/null; then
    unset NO_SUCH_VARIABLE
fi
run_fail "$TEST_KEY" \
    rose app-run --config=../config -q -D '[env]BAR=$NO_SUCH_VARIABLE'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] env=BAR: NO_SUCH_VARIABLE: unbound variable
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, redefine BAR to UNDEF.
TEST_KEY=$TEST_KEY_BASE-undef-env
test_setup
export UNDEF=false
run_fail "$TEST_KEY" rose app-run --config=../config -q -D '[env]BAR=$UNDEF'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] env=BAR: UNDEF: unbound variable
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, disable the env section.
TEST_KEY=$TEST_KEY_BASE-env-disabled
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q -D '[!env]'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # return-code=1
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, disable the env=BAR.
TEST_KEY=$TEST_KEY_BASE-env-BAR-disabled
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q -D '[env]!BAR'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
$FOO
$BAZ
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # return-code=1
__CONTENT__
test_teardown
#-------------------------------------------------------------------------------
# Normal mode, tilde expansion.
TEST_KEY=$TEST_KEY_BASE-env-tilde
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q -D '[env]MY_HOME=~' \
    printenv FOO BAR BAZ MY_HOME
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
$FOO
$BAR
$BAZ
$HOME
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
exit
