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
# Test "rose macro" in custom changing mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 19
#-------------------------------------------------------------------------------
# Check bad macro comments.
TEST_KEY=$TEST_KEY_BASE-bad-comments
setup
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
init_meta </dev/null
init_macro bad.py < $TEST_SOURCE_DIR/lib/custom_macro_change_bad.py
run_fail "$TEST_KEY" rose macro --config=../config \
    bad.InvalidCommentsTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "node\.comments: invalid returned type" "$TEST_KEY.err"
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
teardown
#-------------------------------------------------------------------------------
# Check bad macro config keys.
TEST_KEY=$TEST_KEY_BASE-bad-keys
setup
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
init_meta </dev/null
init_macro bad.py < $TEST_SOURCE_DIR/lib/custom_macro_change_bad.py
run_fail "$TEST_KEY" rose macro --config=../config \
    bad.InvalidConfigKeysTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "key: invalid returned type" "$TEST_KEY.err"
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
teardown
#-------------------------------------------------------------------------------
# Check bad macro config object.
TEST_KEY=$TEST_KEY_BASE-bad-object
setup
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
init_meta </dev/null
init_macro bad.py < $TEST_SOURCE_DIR/lib/custom_macro_change_bad.py
run_fail "$TEST_KEY" rose macro --config=../config \
    bad.InvalidConfigObjectTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
teardown
#-------------------------------------------------------------------------------
# Check bad macro state.
TEST_KEY=$TEST_KEY_BASE-bad-state
setup
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
init_meta </dev/null
init_macro bad.py < $TEST_SOURCE_DIR/lib/custom_macro_change_bad.py
run_fail "$TEST_KEY" rose macro --config=../config \
    bad.InvalidStateTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "node\.state: invalid returned value" "$TEST_KEY.err"
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
teardown
#-------------------------------------------------------------------------------
# Check bad macro value.
TEST_KEY=$TEST_KEY_BASE-bad-value
setup
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
init_meta </dev/null
init_macro bad.py < $TEST_SOURCE_DIR/lib/custom_macro_change_bad.py
run_fail "$TEST_KEY" rose macro --config=../config \
    bad.InvalidValueTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "node\.value: invalid returned type" "$TEST_KEY.err"
file_cmp "$TEST_KEY.config" ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
teardown
#-------------------------------------------------------------------------------
exit
