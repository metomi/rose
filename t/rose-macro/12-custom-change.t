#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
#-------------------------------------------------------------------------------
tests 11
#-------------------------------------------------------------------------------
# Check macro finding.
TEST_KEY=$TEST_KEY_BASE-discovery
setup
init_meta </dev/null
init_macro envswitch.py < $TEST_SOURCE_DIR/lib/custom_macro_change.py
run_pass "$TEST_KEY" rose macro --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[T] envswitch.LogicalTransformer
    # Test class to change the value of a boolean environment variable.
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check changing.
TEST_KEY=$TEST_KEY_BASE-change
setup
init_meta </dev/null
init_macro envswitch.py < $TEST_SOURCE_DIR/lib/custom_macro_change.py
CONFIG_DIR=$(cd ../config && pwd -P)
run_pass "$TEST_KEY" \
    rose macro -v --non-interactive --config=../config envswitch.LogicalTransformer
sed 's/[0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0-9]*/YYYY-MM-DDTHHMM/g'\
    "$TEST_KEY.out" > edited.log
file_cmp "$TEST_KEY.out" "edited.log" <<__CONTENT__
[T] envswitch.LogicalTransformer: changes: 1
    env=TRANSFORM_SWITCH=false
        false -> true
[INFO] YYYY-MM-DDTHHMM M $CONFIG_DIR
__CONTENT__
file_cmp ../config/rose-app.conf ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=true
__CONFIG__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check changing in quiet mode.
TEST_KEY=$TEST_KEY_BASE-change-quiet
setup
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
init_meta </dev/null
init_macro envswitch.py < $TEST_SOURCE_DIR/lib/custom_macro_change.py
run_pass "$TEST_KEY" \
    rose macro -q --non-interactive --config=../config envswitch.LogicalTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp ../config/rose-app.conf ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=true
__CONFIG__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
