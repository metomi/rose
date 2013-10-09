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
test_init <<'__CONFIG__'
[command]
default=true
[poll]
delays=2*0.0001h,0.005m,3*0.1s,1*0.5
all-files=file1 file2
any-files=file3 file4
test=test -e file5
__CONFIG__
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# Timeout test 1.
TEST_KEY=$TEST_KEY_BASE-timeout-1
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err.0" \
    '\[FAIL\] ....-..-..T..:..:.. poll timeout after .s' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.1" '* test' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.2" '* any-files' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.3" '* all-files:file1 file2' "$TEST_KEY.err"
test_teardown
#-------------------------------------------------------------------------------
# OK test 1.
TEST_KEY=$TEST_KEY_BASE-ok-1
test_setup
(sleep 2; touch file1 file2) &
(sleep 2; touch file3) &
(sleep 2; touch file5) &
run_pass "$TEST_KEY" rose app-run --config=../config -q -D '[poll]delays=5*1'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
wait
test_teardown
#-------------------------------------------------------------------------------
# OK test 2.
TEST_KEY=$TEST_KEY_BASE-ok-2
test_setup
touch file1 file2 file4
(sleep 2; echo "hello" | tee file1 >file2) &
(sleep 2; echo "hello" >file4) &
(sleep 2; touch file5) &
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    -D '[poll]delays=5*1' \
    -D '[poll]file-test=test -e {} && grep -q hello {}'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
wait
test_teardown
#-------------------------------------------------------------------------------
# OK test 3 (no delay).
TEST_KEY=$TEST_KEY_BASE-ok-3
test_setup
touch file1 file2 file4
(sleep 2; echo "hello" | tee file1 >file2) &
(sleep 2; echo "hello" >file4) &
(sleep 2; touch file5) &
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    -D '[poll]file-test=test -e {} && grep -q hello {}'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
wait
test_teardown
#-------------------------------------------------------------------------------
exit
