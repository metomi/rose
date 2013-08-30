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
# Test "rose config", syntax error.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 12
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-indent-below-root
echo '    foo=bar' >rose-bad.conf
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): Expecting "[SECTION]" or "KEY=VALUE" at column 1.
[FAIL]     foo=bar
[FAIL] ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-equal-below-root
echo 'foo' >rose-bad.conf
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): Expecting "[SECTION]" or "KEY=VALUE" at column 1.
[FAIL] foo
[FAIL] ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-indent-below-section
cat >rose-bad.conf <<'__CONF__'
[flower]
    ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(2): Expecting "[SECTION]" or "KEY=VALUE" at column 1.
[FAIL]     ivy=poison
[FAIL] ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-equal-below-section
cat >rose-bad.conf <<'__CONF__'
[flower]
jasmine
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(2): Expecting "[SECTION]" or "KEY=VALUE" at column 1.
[FAIL] jasmine
[FAIL] ^
__ERR__
#-------------------------------------------------------------------------------
exit 0
