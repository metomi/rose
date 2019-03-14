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
# Test rose.variable trigger parsing.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
rm config/rose-app.conf
TEST_PARSER="python3 $TEST_SOURCE_DIR/$TEST_KEY_BASE.py"
#-------------------------------------------------------------------------------
tests 24
#-------------------------------------------------------------------------------

# Easy no-value trigger.
TEST_KEY=$TEST_KEY_BASE-single-no-value
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_single_var"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_single_var': []}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Easy no-value trigger, ending with semi-colon.
TEST_KEY=$TEST_KEY_BASE-single-no-value-end
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_single_var;"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_single_var': []}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Easy single-value trigger.
TEST_KEY=$TEST_KEY_BASE-single-value
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_single_var: red"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_single_var': ['red']}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Easy multiple-value trigger.
TEST_KEY=$TEST_KEY_BASE-single-multiple-values
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_single_var: red, 40, blue, x"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_single_var': ['red', '40', 'blue', 'x']}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Easy logical-expression trigger.
TEST_KEY=$TEST_KEY_BASE-single-logical-expression
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_single_var: this != green or this != blue"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_single_var': ['this != green or this != blue']}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------

# Standard trigger expression.
TEST_KEY=$TEST_KEY_BASE-standard
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_numeric: 40, 50; namelist:nl1=my_no_values; namelist:nl1=my_other_no_values;"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_numeric': ['40', '50'], 'namelist:nl1=my_no_values': [], 'namelist:nl1=my_other_no_values': []}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# More complex expression
TEST_KEY=$TEST_KEY_BASE-complex
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_numeric: 40, 50; namelist:nl1=my_logical_expr: this != 40; namelist:nl1=my_strings: \;range\;, quadrillion, 'hopefully, a joined-up string; a block of characters'"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_numeric': ['40', '50'], 'namelist:nl1=my_logical_expr': ['this != 40'], 'namelist:nl1=my_strings': [';range;', 'quadrillion', "'hopefully, a joined-up string; a block of characters'"]}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Lots of escaped characters in an expression.
TEST_KEY=$TEST_KEY_BASE-escaped-chars
setup
run_pass "$TEST_KEY" $TEST_PARSER "namelist:nl1=my_escaped_strings: comma\,comma\,, slash\\\\, semicolon\;, colon:;"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
{'namelist:nl1=my_escaped_strings': ['comma,comma,', 'slash\\\\', 'semicolon;', 'colon:']}
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
