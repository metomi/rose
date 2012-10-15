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
# Test "rose app-run" in the absence of a rose-app.conf.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
rm config/rose-app.conf
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Normal mode.
TEST_KEY=$TEST_KEY_BASE
setup
run_fail "$TEST_KEY" rose app-run
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "$PWD/rose-app.conf" "$TEST_KEY.err"
teardown
#-------------------------------------------------------------------------------
# Normal mode, --config.
TEST_KEY=$TEST_KEY_BASE--config
setup
run_fail "$TEST_KEY" rose app-run --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "../config/rose-app.conf" "$TEST_KEY.err"
teardown
#-------------------------------------------------------------------------------
# Verbose mode.
TEST_KEY=$TEST_KEY_BASE-v
setup
run_fail "$TEST_KEY" rose app-run -v
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "$PWD/rose-app.conf" "$TEST_KEY.err"
teardown
#-------------------------------------------------------------------------------
# Unknown option.
TEST_KEY=$TEST_KEY_BASE-uknown-option
setup
run_fail "$TEST_KEY" rose app-run --unknown-option
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
Usage: rose app-run [OPTIONS] [--] [COMMAND ...]

rose app-run: error: no such option: --unknown-option
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
