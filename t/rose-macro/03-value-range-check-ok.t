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
# Test "rose macro" in built-in value checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:values_nl1]
my_int_array = -1, 2, 3, 5
my_real_array = -1, 2.0, 3.0, 5.0
my_int = 5
my_int_neg = -2
my_real = 678.3
my_real_neg = -345.1
my_real_sci_notation_neg = -3.546e-2
my_real_sci_notation_pos = 56.0e+67
__CONFIG__
#-------------------------------------------------------------------------------
tests 18
#-------------------------------------------------------------------------------
# Check simple range checking.
TEST_KEY=$TEST_KEY_BASE-simple-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 5

[namelist:values_nl1=my_int_neg]
range = -2

[namelist:values_nl1=my_real]
range = 678.3

[namelist:values_nl1=my_real_neg]
range = -345.1
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check multiple allowed values range checking.
TEST_KEY=$TEST_KEY_BASE-multiple-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 3, 5

[namelist:values_nl1=my_int_neg]
range = -1, -2, -3

[namelist:values_nl1=my_real]
range = 4.0e2, 678.3

[namelist:values_nl1=my_real_neg]
range = 456, -345.1

[namelist:values_nl1=my_real_sci_notation_neg]
range = -3.546e-2, -100

[namelist:values_nl1=my_real_sci_notation_pos]
range = -2.3, 56.0e+67, 56, 5, 1, -2
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check interval range checking.
TEST_KEY=$TEST_KEY_BASE-interval-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 3:5

[namelist:values_nl1=my_int_neg]
range = -3:-1

[namelist:values_nl1=my_real]
range = 670:680.3

[namelist:values_nl1=my_real_neg]
range = -346:

[namelist:values_nl1=my_real_sci_notation_neg]
range = -1:0

[namelist:values_nl1=my_real_sci_notation_pos]
range = 0:1e70
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check interval spacing range checking.
TEST_KEY=$TEST_KEY_BASE-interval-spacing-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = : 5

[namelist:values_nl1=my_int_neg]
range = -3:

[namelist:values_nl1=my_real]
range = -670: 680.3

[namelist:values_nl1=my_real_neg]
range = -346 :

[namelist:values_nl1=my_real_sci_notation_neg]
range = -1: 0

[namelist:values_nl1=my_real_sci_notation_pos]
range = :1e70
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check composite range checking.
TEST_KEY=$TEST_KEY_BASE-composite-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 4, 3:5, 5, 7

[namelist:values_nl1=my_int_neg]
range = 0, -6:-8, -2:

[namelist:values_nl1=my_real]
range = :100, 34, 56:679

[namelist:values_nl1=my_real_neg]
range = -346:, 345

[namelist:values_nl1=my_real_sci_notation_neg]
range = -1: 0, -45, 12

[namelist:values_nl1=my_real_sci_notation_pos]
range = 1, 2:, 546, :-1
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check logical range checking.
TEST_KEY=$TEST_KEY_BASE-logical-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = this % 2 == 1

[namelist:values_nl1=my_int_neg]
range = this < 0

[namelist:values_nl1=my_real]
range = 600 < this < 700

[namelist:values_nl1=my_real_neg]
range = this < 0 and this > -1000

[namelist:values_nl1=my_real_sci_notation_neg]
range = this / 4350384059 < 1

[namelist:values_nl1=my_real_sci_notation_pos]
range = 1e99 > this - 100
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
