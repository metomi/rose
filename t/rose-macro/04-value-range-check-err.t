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
TEST_KEY=$TEST_KEY_BASE-simple-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 3

[namelist:values_nl1=my_int_neg]
range = -1

[namelist:values_nl1=my_real]
range = 7.3

[namelist:values_nl1=my_real_neg]
range = -3.1
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 4
    namelist:values_nl1=my_int=5
        Value 5 is not in the range criteria: 3
    namelist:values_nl1=my_int_neg=-2
        Value -2 is not in the range criteria: -1
    namelist:values_nl1=my_real=678.3
        Value 678.3 is not in the range criteria: 7.3
    namelist:values_nl1=my_real_neg=-345.1
        Value -345.1 is not in the range criteria: -3.1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check multiple allowed values range checking.
TEST_KEY=$TEST_KEY_BASE-multiple-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 3, 4, 6

[namelist:values_nl1=my_int_neg]
range = -1, -3

[namelist:values_nl1=my_real]
range = 4.0e2, 67.3

[namelist:values_nl1=my_real_neg]
range = 456, -34.1

[namelist:values_nl1=my_real_sci_notation_neg]
range = -3.6e-2, -100

[namelist:values_nl1=my_real_sci_notation_pos]
range = -2.3, 5.0e+6, 56, 5, 1, -2
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_int=5
        Value 5 is not in the range criteria: 3, 4, 6
    namelist:values_nl1=my_int_neg=-2
        Value -2 is not in the range criteria: -1, -3
    namelist:values_nl1=my_real=678.3
        Value 678.3 is not in the range criteria: 4.0e2, 67.3
    namelist:values_nl1=my_real_neg=-345.1
        Value -345.1 is not in the range criteria: 456, -34.1
    namelist:values_nl1=my_real_sci_notation_neg=-3.546e-2
        Value -3.546e-2 is not in the range criteria: -3.6e-2, -100
    namelist:values_nl1=my_real_sci_notation_pos=56.0e+67
        Value 56.0e+67 is not in the range criteria: -2.3, 5.0e+6, 56, 5, 1, -2
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check interval range checking.
TEST_KEY=$TEST_KEY_BASE-interval-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 1:3, 7:10

[namelist:values_nl1=my_int_neg]
range = -1:5

[namelist:values_nl1=my_real]
range = 680:680.3

[namelist:values_nl1=my_real_neg]
range = -34:

[namelist:values_nl1=my_real_sci_notation_neg]
range = -100:-1

[namelist:values_nl1=my_real_sci_notation_pos]
range = 1e70:1.1e70
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_int=5
        Value 5 is not in the range criteria: 1:3, 7:10
    namelist:values_nl1=my_int_neg=-2
        Value -2 is not in the range criteria: -1:5
    namelist:values_nl1=my_real=678.3
        Value 678.3 is not in the range criteria: 680:680.3
    namelist:values_nl1=my_real_neg=-345.1
        Value -345.1 is not in the range criteria: -34:
    namelist:values_nl1=my_real_sci_notation_neg=-3.546e-2
        Value -3.546e-2 is not in the range criteria: -100:-1
    namelist:values_nl1=my_real_sci_notation_pos=56.0e+67
        Value 56.0e+67 is not in the range criteria: 1e70:1.1e70
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check interval spacing range checking.
TEST_KEY=$TEST_KEY_BASE-interval-spacing-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = : 4

[namelist:values_nl1=my_int_neg]
range = -0:

[namelist:values_nl1=my_real]
range = -65: 68.3

[namelist:values_nl1=my_real_neg]
range = -36 :

[namelist:values_nl1=my_real_sci_notation_neg]
range = -100: -50

[namelist:values_nl1=my_real_sci_notation_pos]
range = :1e60
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_int=5
        Value 5 is not in the range criteria: : 4
    namelist:values_nl1=my_int_neg=-2
        Value -2 is not in the range criteria: -0:
    namelist:values_nl1=my_real=678.3
        Value 678.3 is not in the range criteria: -65: 68.3
    namelist:values_nl1=my_real_neg=-345.1
        Value -345.1 is not in the range criteria: -36 :
    namelist:values_nl1=my_real_sci_notation_neg=-3.546e-2
        Value -3.546e-2 is not in the range criteria: -100: -50
    namelist:values_nl1=my_real_sci_notation_pos=56.0e+67
        Value 56.0e+67 is not in the range criteria: :1e60
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check composite range checking.
TEST_KEY=$TEST_KEY_BASE-composite-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 4, 3:4, 7:, 8

[namelist:values_nl1=my_int_neg]
range = 0, -6:-8, 2:

[namelist:values_nl1=my_real]
range = :100, 34, 56:67

[namelist:values_nl1=my_real_neg]
range = -36:, 345

[namelist:values_nl1=my_real_sci_notation_neg]
range = -2:-1, -45, 12

[namelist:values_nl1=my_real_sci_notation_pos]
range = 1:-1, 2, 546, :-1
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_int=5
        Value 5 is not in the range criteria: 4, 3:4, 7:, 8
    namelist:values_nl1=my_int_neg=-2
        Value -2 is not in the range criteria: 0, -6:-8, 2:
    namelist:values_nl1=my_real=678.3
        Value 678.3 is not in the range criteria: :100, 34, 56:67
    namelist:values_nl1=my_real_neg=-345.1
        Value -345.1 is not in the range criteria: -36:, 345
    namelist:values_nl1=my_real_sci_notation_neg=-3.546e-2
        Value -3.546e-2 is not in the range criteria: -2:-1, -45, 12
    namelist:values_nl1=my_real_sci_notation_pos=56.0e+67
        Value 56.0e+67 is not in the range criteria: 1:-1, 2, 546, :-1
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check logical range checking.
TEST_KEY=$TEST_KEY_BASE-logical-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = this % 2 == 0

[namelist:values_nl1=my_int_neg]
range = this >= 0

[namelist:values_nl1=my_real]
range = 700 < this <= 600

[namelist:values_nl1=my_real_neg]
range = this < -1000 or this > 10

[namelist:values_nl1=my_real_sci_notation_neg]
range = this / 4560457 > 0

[namelist:values_nl1=my_real_sci_notation_pos]
range = 0 < this / 100 < 6
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_int=5
        Value 5 is not in the range criteria: this % 2 == 0
    namelist:values_nl1=my_int_neg=-2
        Value -2 is not in the range criteria: this >= 0
    namelist:values_nl1=my_real=678.3
        Value 678.3 is not in the range criteria: 700 < this <= 600
    namelist:values_nl1=my_real_neg=-345.1
        Value -345.1 is not in the range criteria: this < -1000 or this > 10
    namelist:values_nl1=my_real_sci_notation_neg=-3.546e-2
        Value -3.546e-2 is not in the range criteria: this / 4560457 > 0
    namelist:values_nl1=my_real_sci_notation_pos=56.0e+67
        Value 56.0e+67 is not in the range criteria: 0 < this / 100 < 6
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
