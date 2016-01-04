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
# Test "rose app-run", poll.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
test_init <<'__CONFIG__'
[command]
default=true
[poll]
delays=2*0.0001h,0.005m,3*0.1s,1*0.5
all-files=file0* file1 file2
any-files=file3 file4 file6*
test=test -e file5
__CONFIG__
#-------------------------------------------------------------------------------
tests 31
#-------------------------------------------------------------------------------
# Garbage syntax.
TEST_KEY="${TEST_KEY_BASE}-garbage"
test_setup
run_fail "${TEST_KEY}" \
    rose app-run --config=../config -q -D '[poll]delays=it will take ages'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] [poll]delays=it will take ages: configuration value error: syntax
__ERR__
test_teardown
#-------------------------------------------------------------------------------
# Mix ISO8601 and legacy syntax.
TEST_KEY="${TEST_KEY_BASE}-mix"
test_setup
run_fail "${TEST_KEY}" \
    rose app-run --config=../config -q -D '[poll]delays=PT1S,1s'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] [poll]delays=PT1S,1s: configuration value error: ISO8601 duration mixed with legacy duration
__ERR__
test_teardown
#-------------------------------------------------------------------------------
# Timeout test 1.
TEST_KEY=$TEST_KEY_BASE-timeout-1
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err.0" \
    '\[FAIL\] ....-..-..T..:..:....* poll timeout after PT..*S' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.1" '* test' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.2" '* any-files' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.3" '* all-files:file0\* file1 file2' "$TEST_KEY.err"
test_teardown
#-------------------------------------------------------------------------------
# Timeout test 2. Missing a file in all-files.
TEST_KEY=$TEST_KEY_BASE-timeout-2
test_setup
(sleep 1; touch file0 file1) &
(sleep 2; touch file4) &
(sleep 2; touch file5) &
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err.0" \
    '\[FAIL\] ....-..-..T..:..:....* poll timeout after PT..*S' "$TEST_KEY.err"
file_grep "$TEST_KEY.err.1" '* all-files:file2' "$TEST_KEY.err"
wait
test_teardown
#-------------------------------------------------------------------------------
# Timeout test 3. With ISO8601 syntax.
TEST_KEY="${TEST_KEY_BASE}-timeout-iso8601"
test_setup
run_fail "${TEST_KEY}" \
    rose app-run --config=../config -q -D '[poll]delays=PT0S,2*PT0M,3*PT0H0S'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
file_grep "$TEST_KEY.err.0" \
    '\[FAIL\] ....-..-..T..:..:....* poll timeout after PT..*S' "$TEST_KEY.err"
test_teardown
#-------------------------------------------------------------------------------
# OK test 1.
TEST_KEY=$TEST_KEY_BASE-ok-1
test_setup
(sleep 2; touch file0 file1 file2) &
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
(sleep 2; echo "hello" | tee file0 file1 >file2) &
(sleep 2; echo "hello" >file4) &
(sleep 2; touch file5) &
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    -D '[poll]delays=5*1' \
    -D '[poll]file-test=ls {} 1>/dev/null 2>&1 && grep -q hello {}'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
wait
test_teardown
#-------------------------------------------------------------------------------
# OK test 3 (no delay).
TEST_KEY=$TEST_KEY_BASE-ok-3
test_setup
touch file1 file2 file4
(sleep 2; echo "hello" | tee file0 file1 >file2) &
(sleep 2; echo "hello" >file4) &
(sleep 2; touch file5) &
run_pass "$TEST_KEY" rose app-run --config=../config -q \
    -D '[poll]file-test=ls {} 1>/dev/null 2>&1 && grep -q hello {}'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
wait
test_teardown
#-------------------------------------------------------------------------------
# OK test 4.
TEST_KEY=$TEST_KEY_BASE-ok-4
test_setup
(sleep 2; touch file0 file1 file2) &
(sleep 2; touch file66) &
(sleep 2; touch file5) &
run_pass "$TEST_KEY" rose app-run --config=../config -q -D '[poll]delays=5*1'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
wait
test_teardown
#-------------------------------------------------------------------------------
exit
