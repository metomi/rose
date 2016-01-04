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
# Test "rose macro" in custom checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[env]
BAD_URL=htpp://www.google.co.uk
__CONFIG__
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check macro finding.
TEST_KEY=$TEST_KEY_BASE-discovery
setup
init_meta </dev/null
init_macro url.py < $TEST_SOURCE_DIR/lib/custom_macro_check.py
run_pass "$TEST_KEY" rose macro --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[V] url.URLChecker
    # Class to check if a URL is valid.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check checking.
TEST_KEY=$TEST_KEY_BASE-check
setup
init_meta </dev/null
init_macro url.py < $TEST_SOURCE_DIR/lib/custom_macro_check.py
run_fail "$TEST_KEY" rose macro --config=../config url.URLChecker
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] url.URLChecker: issues: 1
    env=BAD_URL=htpp://www.google.co.uk
        htpp://www.google.co.uk: [Errno -2] Name or service not known
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
