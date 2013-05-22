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
# Test "rose macro" in custom changing mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=false
__CONFIG__
#-------------------------------------------------------------------------------
tests 7
#-------------------------------------------------------------------------------
# Check macro finding.
TEST_KEY=$TEST_KEY_BASE-discovery
setup
init_meta </dev/null
init_macro envswitch.py < $(dirname $0)/lib/custom_macro_change.py
run_pass "$TEST_KEY" rose macro --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] envswitch.LogicalTransformer
    # Test class to change the value of a boolean environment variable.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check changing.
TEST_KEY=$TEST_KEY_BASE-change
setup
init_meta </dev/null
init_macro envswitch.py < $(dirname $0)/lib/custom_macro_change.py
run_pass "$TEST_KEY" rose macro --non-interactive --config=../config envswitch.LogicalTransformer
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[T] envswitch.LogicalTransformer: changes: 1
    env=TRANSFORM_SWITCH=false
        false -> true
__CONTENT__
file_cmp ../config/rose-app.conf ../config/rose-app.conf <<'__CONFIG__'
[env]
TRANSFORM_SWITCH=true
__CONFIG__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
