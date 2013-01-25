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
# Test "rose app-run", optional configuration selection.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[command]
default = printenv FOO BAR BAZ

[env]
FOO = foo
BAR = bar
BAZ = baz
__CONFIG__
mkdir -p config/opt
OPT_1=env-foo
OPT_2=no-env-bar
OPT_3=no-env
cat >config/opt/rose-app-$OPT_1.conf <<'__CONFIG__'
[env]
FOO = foolish fool
__CONFIG__
cat >config/opt/rose-app-$OPT_2.conf <<'__CONFIG__'
[env]
!BAR =
__CONFIG__
cat >config/opt/rose-app-$OPT_3.conf <<'__CONFIG__'
[!env]
__CONFIG__
#-------------------------------------------------------------------------------
tests 27
#-------------------------------------------------------------------------------
# Control run.
TEST_KEY=$TEST_KEY_BASE-control
setup
run_pass "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foo
bar
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Bad option.
TEST_KEY=$TEST_KEY_BASE-bad
setup
run_fail "$TEST_KEY" rose app-run --config=../config --opt-conf-key=bad -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "../config/opt/rose-app-bad.conf" "$TEST_KEY.err"
teardown
#-------------------------------------------------------------------------------
# Add option 1.
TEST_KEY=$TEST_KEY_BASE-opt-1
setup
run_pass "$TEST_KEY" rose app-run --config=../config --opt-conf-key=$OPT_1 -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foolish fool
bar
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Add option 2.
TEST_KEY=$TEST_KEY_BASE-opt-2
setup
run_fail "$TEST_KEY" rose app-run --config=../config --opt-conf-key=$OPT_2 -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foo
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # rc=1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Add option 3.
TEST_KEY=$TEST_KEY_BASE-opt-3
setup
run_fail "$TEST_KEY" rose app-run --config=../config --opt-conf-key=$OPT_3 -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # rc=1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Add option 1 and 2.
TEST_KEY=$TEST_KEY_BASE-opt-1-2
setup
run_fail "$TEST_KEY" rose app-run --config=../config \
    --opt-conf-key=$OPT_1 --opt-conf-key=$OPT_2 -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foolish fool
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # rc=1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Add option 3, 1 and 2.
TEST_KEY=$TEST_KEY_BASE-opt-3-1-2
setup
run_fail "$TEST_KEY" rose app-run --config=../config \
    --opt-conf-key=$OPT_3 --opt-conf-key=$OPT_1 --opt-conf-key=$OPT_2 -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foolish fool
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # rc=1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Add option 3, 1 and 2, with environment variable.
TEST_KEY=$TEST_KEY_BASE-env-opt-3-1-2
setup
ROSE_APP_OPT_CONF_KEYS="$OPT_3 $OPT_1 $OPT_2" \
    run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foolish fool
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] printenv FOO BAR BAZ # rc=1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Add option 1 and 2 + define.
TEST_KEY=$TEST_KEY_BASE-opt-1-2-d
setup
run_pass "$TEST_KEY" rose app-run --config=../config \
    --opt-conf-key=$OPT_1 --opt-conf-key=$OPT_2 \
    '--define=[env]BAR=barman' -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
foolish fool
barman
baz
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
