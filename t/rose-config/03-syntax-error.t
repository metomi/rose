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
# Test "rose config", syntax error.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 60
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-indent-below-root
echo '    foo=bar' >rose-bad.conf
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): expecting "[SECTION]" or "KEY=VALUE"
[FAIL]     foo=bar
[FAIL] ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-equal-below-root
echo 'foo' >rose-bad.conf
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): expecting "[SECTION]" or "KEY=VALUE"
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
[FAIL] $TEST_DIR/rose-bad.conf(2): expecting "[SECTION]" or "KEY=VALUE"
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
[FAIL] $TEST_DIR/rose-bad.conf(2): expecting "[SECTION]" or "KEY=VALUE"
[FAIL] jasmine
[FAIL] ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-open-sq-brace-in-section"
cat >rose-bad.conf <<'__CONF__'
[[flower]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [[flower]
[FAIL]  ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-open-sq-brace-in-section-with-state"
cat >rose-bad.conf <<'__CONF__'
[![flower]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [![flower]
[FAIL]   ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-open-sq-brace-in-section-with-space"
cat >rose-bad.conf <<'__CONF__'
[ what [flower]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [ what [flower]
[FAIL]        ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-close-sq-brace-in-section"
cat >rose-bad.conf <<'__CONF__'
[flower]]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower]]
[FAIL]        ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-open-bracket-not-closed"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy(21]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy(21]
[FAIL]                 ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-close-bracket-not-opened"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy)]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy)]
[FAIL]              ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-open-brace-not-closed"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy{white]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy{white]
[FAIL]                    ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-close-brace-not-opened"
cat >rose-bad.conf <<'__CONF__'
[flower:daisywhite}]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisywhite}]
[FAIL]                   ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-close-bracket-before-open"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy)2(]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy)2(]
[FAIL]              ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-close-brace-before-open"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy}white{]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy}white{]
[FAIL]              ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-2-open-bracket"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy((2)]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy((2)]
[FAIL]               ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-2-close-bracket"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy(2))]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy(2))]
[FAIL]                 ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-2-open-braces"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy{{2}]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy{{2}]
[FAIL]               ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-2-close-braces"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy{2}}]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy{2}}]
[FAIL]                 ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bracket-before-brace"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy(2){white}]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy(2){white}]
[FAIL]                 ^
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-bracket-open-before-brace-close"
cat >rose-bad.conf <<'__CONF__'
[flower:daisy{white(2)}]
ivy=poison
__CONF__
run_fail "$TEST_KEY" rose config -f rose-bad.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $TEST_DIR/rose-bad.conf(1): unexpected character or end of value
[FAIL] [flower:daisy{white(2)}]
[FAIL]                    ^
__ERR__
#-------------------------------------------------------------------------------
exit 0
