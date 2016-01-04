#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# Test "rose macro" current working directory.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3

#-------------------------------------------------------------------------------
# Check current working directory.
init </dev/null
setup
init_meta </dev/null
init_macro cwd.py < $TEST_SOURCE_DIR/lib/custom_macro_cwd.py
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-validate
# Check a validator macro has the current working directory
CONFIG_DIR=$(cd ../config && pwd -P)
run_pass "$TEST_KEY" rose macro -C ../config cwd.PrintCwd
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
Current directory: $CONFIG_DIR
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
