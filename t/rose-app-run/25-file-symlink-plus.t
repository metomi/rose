#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-8 Met Office.
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
# Test "rose app-run", file installation, symlink+ mode.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
tests 8
#-------------------------------------------------------------------------------
test_init <<'__CONFIG__'
[command]
default=true

[file:COPYING]
mode=symlink+
source=fantasy.txt
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-yes"
test_setup
run_fail "${TEST_KEY}" rose app-run --config=../config -q
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<'__ERR__'
[FAIL] file:COPYING=source=fantasy.txt: [Errno 2] No such file or directory: 'fantasy.txt'
__ERR__
run_fail "${TEST_KEY}-test-l" test -L 'COPYING'
test_teardown
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-no"
test_setup
run_pass "${TEST_KEY}" rose app-run --config=../config -q \
    --define=[file:COPYING]mode=symlink
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
run_pass "${TEST_KEY}-test-l" test -L 'COPYING'
test_teardown
#-------------------------------------------------------------------------------
exit
