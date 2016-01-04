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
# Test "rose app-run" messages for unchanged file install.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
# mode=auto, source is a file
mkdir $TEST_DIR/hello
echo "Fred" >$TEST_DIR/hello/foo.txt

test_init <<__CONFIG__
[command]
default=true

[file:melody]
source=$TEST_DIR/hello/foo.txt
__CONFIG__

#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Test unchanged message not output on first time install
TEST_KEY="$TEST_KEY_BASE-first-time"
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config pwd -v -v --debug
file_grep_fail "$TEST_KEY.out" "unchanged: melody" "$TEST_KEY.out"
#-------------------------------------------------------------------------------
# Test unchanged output in verbose mode
TEST_KEY="$TEST_KEY_BASE-unchanged-verbose"
run_pass "$TEST_KEY" rose app-run --config=../config pwd -v -v --debug
file_grep "$TEST_KEY.out" "unchanged: melody" "$TEST_KEY.out"
#-------------------------------------------------------------------------------
# Test unchanged output in regular verbosity
TEST_KEY="$TEST_KEY_BASE-unchanged-regular"
run_pass "$TEST_KEY" rose app-run --config=../config pwd
file_grep_fail "$TEST_KEY.out" "unchanged: melody" "$TEST_KEY.out"
#-------------------------------------------------------------------------------
test_teardown
#-------------------------------------------------------------------------------
exit
