#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
# Test "rose app-run" in the presence of an empty rose-app.conf.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
#-------------------------------------------------------------------------------
tests 18
#-------------------------------------------------------------------------------
# Normal mode, no command.
TEST_KEY=$TEST_KEY_BASE-no-command
setup
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[FAIL] command not defined
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Verbose mode, no command.
TEST_KEY=$TEST_KEY_BASE-no-command-v1
setup
run_fail "$TEST_KEY" rose app-run -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[FAIL] command not defined
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Normal mode, runs pwd.
TEST_KEY=$TEST_KEY_BASE-pwd
setup
run_pass "$TEST_KEY" rose app-run --config=../config -q pwd
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<$(pwd)
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Verbose mode, runs pwd.
TEST_KEY=$TEST_KEY_BASE-pwd-v
setup
run_pass "$TEST_KEY" rose app-run --config=../config pwd
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] command: pwd
$(pwd)
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Install-only mode, runs pwd.
TEST_KEY=$TEST_KEY_BASE-pwd-n
setup
run_pass "$TEST_KEY" rose app-run --config=../config -i pwd
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[INFO] export PATH=$PATH
[INFO] command: pwd
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Normal mode, runs cat, pipe result of pwd into STDIN.
TEST_KEY=$TEST_KEY_BASE-cat-pwd
setup
run_pass "$TEST_KEY" rose app-run --config=../config -q cat <<<$(pwd)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<$(pwd)
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
