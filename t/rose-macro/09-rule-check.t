#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
# Test "rose macro" in built-in failure condition checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[simple:scalar_test]
test_var_odd_even = 3
test_var_even_even = 4
test_var_lt_control_pass = 5
test_var_lt_control_fail = 3
control_lt = 4
test_var_sum_pass = 6.75
test_var_sum_fail = 6.00
control_sum_1 = 2.0
control_sum_2 = 4
control_sum_3 = 0.75
test_var_mult_pass = 6
test_var_mult_fail = 5
control_mult_1 = 2
control_mult_2 = 3
test_substring_pass = "ABCCEFG"
test_substring_fail = "ABCDEFG"

[simple:array_test]
test_array_pass = '0A', '0A', '0A', '0A'
test_array_fail = '0A', '2A', '0A', '0A'
test_array_any_pass = 2, 5, 6, 7
test_array_any_fail = 2, 0, 6, 7
test_array_all_pass = 0, 0, 0, 1, 0
test_array_all_fail = 0, 0, 0, 0, 0

[complex:scalar_test]
test_var_multi_odd_positive_pass = -2
test_var_multi_odd_positive_fail = 1
test_var_multi_odd_2_positive_pass = -2
test_var_multi_odd_2_positive_fail = 1
test_var_multi_odd_3_positive_pass = -2
test_var_multi_odd_3_positive_fail = 1
test_var_arith_pass = 4
test_var_arith_fail = 3
control_arith1 = 3
control_arith2 = 5

[complex:array_test]
test_array_pass = '0A', '0A', '0A', '0A'
test_array_fail = '0A', '2A', '0A', '0A'
control_var_1 = 'N'
control_var_2 = 'Y'
control_var_3 = Y, N
test_var_any_lt_pass = 3
test_var_any_lt_fail = 6
control_array_any_lt = 9, 8, 5, 7, 13, 45
test_var_all_ne_pass = 3
test_var_all_ne_fail = 6
control_array_all_ne = 1, 2, 3, 4, 5, 7, 8

[simple:warn_test]
test_var_1 = 1
test_var_2 = 50
test_var_3 = -1
__CONFIG__
#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
# Check compulsory checking.
TEST_KEY=$TEST_KEY_BASE-rule
setup
init_meta <<__META_CONFIG__
[simple:scalar_test=test_var_even_pass]
type = integer
fail-if = this % 2 == 0

[simple:scalar_test=test_var_even_fail]
type = integer
fail-if = this % 2 == 0

[simple:scalar_test=test_var_lt_control_pass]
type = integer
fail-if = this < simple:scalar_test=control_lt

[simple:scalar_test=test_var_lt_control_fail]
type = integer
fail-if = this < simple:scalar_test=control_lt

[simple:scalar_test=control_less_than]
type = integer

[simple:scalar_test=test_var_sum_pass]
type = real
fail-if = this != simple:scalar_test=control_sum_1 + simple:scalar_test=control_sum_2 + simple:scalar_test=control_sum_3

[simple:scalar_test=test_var_sum_fail]
type = real
fail-if = this != simple:scalar_test=control_sum_1 + simple:scalar_test=control_sum_2 + simple:scalar_test=control_sum_3

[simple:scalar_test=test_var_mult_pass]
type = real
fail-if = this != simple:scalar_test=control_mult_1 * simple:scalar_test=control_mult_2

[simple:scalar_test=test_var_mult_fail]
type = real
fail-if = this != simple:scalar_test=control_mult_1 * simple:scalar_test=control_mult_2

[simple:scalar_test=test_substring_pass]
fail-if = "D" in this

[simple:scalar_test=test_substring_fail]
fail-if = "D" in this

[simple:array_test=test_array_pass]
length = :
description = Fail if element 2 is not '0A' and element 4 is '0A'
fail-if = this(2) != "'0A'" and this(4) == "'0A'"

[simple:array_test=test_array_fail]
length = :
description = Fail if element 2 is not '0A' and element 4 is '0A'
fail-if = this(2) != "'0A'" and this(4) == "'0A'"

[simple:array_test=test_array_any_pass]
length = :
description = Fail if any elements are zero
fail-if = any(this == 0)

[simple:array_test=test_array_any_fail]
length = :
description = Fail if any elements are zero
fail-if = any(this == 0)

[simple:array_test=test_array_all_pass]
length = :
description = Fail if all elements are zero
fail-if = all(this == 0)

[simple:array_test=test_array_all_fail]
length = :
description = Fail if all elements are zero
fail-if = all(this == 0)

[complex:scalar_test=test_var_multi_odd_positive_pass]
type = real
description = Not allowed to be positive or odd
fail-if = this > 0;  # Not allowed to be positive
          this % 2 == 1  # Not allowed to be odd

[complex:scalar_test=test_var_multi_odd_positive_fail]
type = real
description = Not allowed to be positive or odd
fail-if = this > 0;  # Not allowed to be positive
          this % 2 == 1  # Not allowed to be odd

[complex:scalar_test=test_var_multi_odd_2_positive_pass]
type = real
description = Not allowed to be positive or odd
fail-if = this > 0; this % 2 == 1  # Not allowed to be odd

[complex:scalar_test=test_var_multi_odd_2_positive_fail]
type = real
description = Not allowed to be positive or odd
fail-if = this > 0; this % 2 == 1  # Not allowed to be odd

[complex:scalar_test=test_var_multi_odd_3_positive_pass]
type = real
description = Not allowed to be positive or odd
fail-if = this > 0; this % 2 == 1

[complex:scalar_test=test_var_multi_odd_3_positive_fail]
type = real
description = Not allowed to be positive or odd
fail-if = this > 0; this % 2 == 1

[complex:scalar_test=test_var_arith_pass]
type = real
fail-if = this != 1 + complex:scalar_test=control_arith1 * (complex:scalar_test=control_arith2 - this )

[complex:scalar_test=test_var_arith_fail]
type = real
fail-if = this != 1 + complex:scalar_test=control_arith1 * (complex:scalar_test=control_arith2 - this )

[complex:scalar_test=control_arith1]
type = integer

[complex:scalar_test=control_arith2]
type = real

[complex:array_test=test_array_pass]
length = :
description = Check for failure if element 2 is not '0A' and element 4 is '0A'
fail-if = this(2) != "'0A'" and this(4) == "'0A'" and (complex:array_test=control_var_1 != "'N'" or complex:array_test=control_var_2 != "'Y'" or complex:array_test=control_var_3(2) == 'N')

[complex:array_test=test_array_fail]
length = :
description = Check for failure if element 2 is not '0A' and element 4 is '0A'
fail-if = this(2) != "'0A'" and this(4) == "'0A'" and (complex:array_test=control_var_1 != "'N'" or complex:array_test=control_var_2 != "'Y'" or all(complex:array_test=control_var_3 == 'N'))

[complex:array_test=control_var_1]
description = If 'N', fail the check
values = 'Y', 'N'

[complex:array_test=control_var_2]
description = If 'Y', fail the check
values = 'Y', 'N'

[complex:array_test=control_var_3]
description = If element 2 is not N, fail the check
values = Y, N
length = :

[complex:array_test=test_var_any_lt_pass]
length = :
description = Fail if any elements in the control_array_any_lt are less than this value
fail-if = any(complex:array_test=control_array_any_lt < this)

[complex:array_test=test_var_any_lt_fail]
length = :
description = Fail if any elements in the control_array_any_lt are less than this value
fail-if = any(complex:array_test=control_array_any_lt < this)

[complex:array_test=test_var_all_ne_pass]
length = :
description = Fail if all elements in the control_array_all_ne are not equal to this value
fail-if = all(complex:array_test=control_array_all_ne != this)

[complex:array_test=test_var_all_ne_fail]
length = :
description = Fail if all elements in the control_array_all_ne are not equal to this value
fail-if = all(complex:array_test=control_array_all_ne != this)

[complex:array_test=control_array_all_ne]
type = integer
length = :

[complex:array_test=control_array_any_lt]
type = integer
length = :

[simple:warn_test=test_var_1]
type = integer
warn-if = this > 0

[simple:warn_test=test_var_2]
type = integer
warn-if = this < 0  # Probably should not be negative.

[simple:warn_test=test_var_3]
type = integer
warn-if = this % 3 == 0;  # Probably should not be a multiple of 3.
          this < 0;  # Probably should not be less than 0.
          this * this * this < 100;  # Cube should be less than 100.
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 16
    complex:array_test=test_var_all_ne_fail=6
        failed because: all(complex:array_test=control_array_all_ne != this)
    complex:array_test=test_var_any_lt_fail=6
        failed because: any(complex:array_test=control_array_any_lt < this)
    complex:scalar_test=test_var_arith_fail=3
        failed because: this != 1 + complex:scalar_test=control_arith1 * (complex:scalar_test=control_arith2 - this )
    complex:scalar_test=test_var_multi_odd_2_positive_fail=1
        failed because: this > 0
    complex:scalar_test=test_var_multi_odd_2_positive_fail=1
        (Not allowed to be odd) failed because: this % 2 == 1
    complex:scalar_test=test_var_multi_odd_3_positive_fail=1
        failed because: this > 0
    complex:scalar_test=test_var_multi_odd_3_positive_fail=1
        failed because: this % 2 == 1
    complex:scalar_test=test_var_multi_odd_positive_fail=1
        (Not allowed to be positive) failed because: this > 0
    complex:scalar_test=test_var_multi_odd_positive_fail=1
        (Not allowed to be odd) failed because: this % 2 == 1
    simple:array_test=test_array_all_fail=0, 0, 0, 0, 0
        failed because: all(this == 0)
    simple:array_test=test_array_any_fail=2, 0, 6, 7
        failed because: any(this == 0)
    simple:array_test=test_array_fail='0A', '2A', '0A', '0A'
        failed because: this(2) != "'0A'" and this(4) == "'0A'"
    simple:scalar_test=test_substring_fail="ABCDEFG"
        failed because: "D" in this
    simple:scalar_test=test_var_lt_control_fail=3
        failed because: this < simple:scalar_test=control_lt
    simple:scalar_test=test_var_mult_fail=5
        failed because: this != simple:scalar_test=control_mult_1 * simple:scalar_test=control_mult_2
    simple:scalar_test=test_var_sum_fail=6.00
        failed because: this != simple:scalar_test=control_sum_1 + simple:scalar_test=control_sum_2 + simple:scalar_test=control_sum_3
[V] rose.macros.DefaultValidators: warnings: 3
    simple:warn_test=test_var_1=1
        warn because: this > 0
    simple:warn_test=test_var_3=-1
        (Probably should not be less than 0.) warn because: this < 0
    simple:warn_test=test_var_3=-1
        (Cube should be less than 100.) warn because: this * this * this < 100
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
