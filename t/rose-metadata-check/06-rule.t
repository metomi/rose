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
# Test "rose metadata-check".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check fail-if/warn-if syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
[complex:array_test]

[complex:array_test=control_array_all_ne]
length=:
type=integer

[complex:array_test=control_array_any_lt]
length=:
type=integer

[complex:array_test=control_len_array]
length=5
type=integer

[complex:array_test=control_var_1]
description=If 'N', fail the check
values='Y', 'N'

[complex:array_test=control_var_2]
description=If 'Y', fail the check
values='Y', 'N'

[complex:array_test=control_var_3]
description=If element 2 is not N, fail the check
length=:
values=Y, N

[complex:array_test=test_array_fail]
description=Check for failure if element 2 is not '0A' and element 4 is '0A'
fail-if=this(2) != "'0A'" and this(4) == "'0A'" and (complex:array_test=control_var_1 != "'N'" or complex:array_test=control_var_2 != "'Y'" or all(complex:array_test=control_var_3 == 'N'))
length=:

[complex:array_test=test_array_len_fail]
description=Fail if array is wrong length
fail-if=len(this) > len(complex:array_test=control_len_array) or len(this) < len(complex:array_test=control_len_array)
length=:

[complex:array_test=test_array_len_pass]
description=Fail if array is wrong length
fail-if=len(this) > len(complex:array_test=control_len_array) or len(this) < len(complex:array_test=control_len_array)
length=:

[complex:array_test=test_array_pass]
description=Check for failure if element 2 is not '0A' and element 4 is '0A'
fail-if=this(2) != "'0A'" and this(4) == "'0A'" and (complex:array_test=control_var_1 != "'N'" or complex:array_test=control_var_2 != "'Y'" or complex:array_test=control_var_3(2) == 'N')
length=:

[complex:array_test=test_var_all_ne_fail]
description=Fail if all elements in the control_array_all_ne are not equal to this value
fail-if=all(complex:array_test=control_array_all_ne != this)
length=:

[complex:array_test=test_var_all_ne_pass]
description=Fail if all elements in the control_array_all_ne are not equal to this value
fail-if=all(complex:array_test=control_array_all_ne != this)
length=:

[complex:array_test=test_var_any_lt_fail]
description=Fail if any elements in the control_array_any_lt are less than this value
fail-if=any(complex:array_test=control_array_any_lt < this)
length=:

[complex:array_test=test_var_any_lt_pass]
description=Fail if any elements in the control_array_any_lt are less than this value
fail-if=any(complex:array_test=control_array_any_lt < this)
length=:

[complex:scalar_test]

[complex:scalar_test=control_arith1]
type=integer

[complex:scalar_test=control_arith2]
type=real

[complex:scalar_test=test_var_arith_fail]
fail-if=this != 1 + complex:scalar_test=control_arith1 * (complex:scalar_test=control_arith2 - this )
type=real

[complex:scalar_test=test_var_arith_pass]
fail-if=this != 1 + complex:scalar_test=control_arith1 * (complex:scalar_test=control_arith2 - this )
type=real

[complex:scalar_test=test_var_multi_odd_2_positive_fail]
description=Not allowed to be positive or odd
fail-if=this > 0; this % 2 == 1  # Not allowed to be odd
type=real

[complex:scalar_test=test_var_multi_odd_2_positive_pass]
description=Not allowed to be positive or odd
fail-if=this > 0; this % 2 == 1  # Not allowed to be odd
type=real

[complex:scalar_test=test_var_multi_odd_3_positive_fail]
description=Not allowed to be positive or odd
fail-if=this > 0; this % 2 == 1
type=real

[complex:scalar_test=test_var_multi_odd_3_positive_pass]
description=Not allowed to be positive or odd
fail-if=this > 0; this % 2 == 1
type=real

[complex:scalar_test=test_var_multi_odd_positive_fail]
description=Not allowed to be positive or odd
fail-if=this > 0;  # Not allowed to be positive
       =this % 2 == 1  # Not allowed to be odd
type=real

[complex:scalar_test=test_var_multi_odd_positive_pass]
description=Not allowed to be positive or odd
fail-if=this > 0;  # Not allowed to be positive
       =this % 2 == 1  # Not allowed to be odd
type=real

[simple:array_test]

[simple:array_test=test_array_1_all_pass]
description=Fail if all elements are zero
fail-if=all(this == 0)
length=:

[simple:array_test=test_array_1_any_pass]
description=Fail if any elements are zero
fail-if=any(this == 0)
length=:

[simple:array_test=test_array_1_len_pass]
description=Fail if array is wrong length
fail-if=len(this) != 1
length=:

[simple:array_test=test_array_all_fail]
description=Fail if all elements are zero
fail-if=all(this == 0)
length=:

[simple:array_test=test_array_all_pass]
description=Fail if all elements are zero
fail-if=all(this == 0)
length=:

[simple:array_test=test_array_any_fail]
description=Fail if any elements are zero
fail-if=any(this == 0)
length=:

[simple:array_test=test_array_any_pass]
description=Fail if any elements are zero
fail-if=any(this == 0)
length=:

[simple:array_test=test_array_fail]
description=Fail if element 2 is not '0A' and element 4 is '0A'
fail-if=this(2) != "'0A'" and this(4) == "'0A'"
length=:

[simple:array_test=test_array_len_fail]
description=Fail if array is wrong length
fail-if=len(this) != 5
length=:

[simple:array_test=test_array_len_pass]
description=Fail if array is wrong length
fail-if=len(this) != 5
length=:

[simple:array_test=test_array_pass]
description=Fail if element 2 is not '0A' and element 4 is '0A'
fail-if=this(2) != "'0A'" and this(4) == "'0A'"
length=:

[simple:scalar_test]

[simple:scalar_test=control_less_than]
type=integer

[simple:scalar_test=control_lt]
type=integer

[simple:scalar_test=control_mult_1]
type=integer

[simple:scalar_test=control_mult_2]
type=integer

[simple:scalar_test=control_sum_1]
type=real

[simple:scalar_test=control_sum_2]
type=integer

[simple:scalar_test=control_sum_3]
type=real

[simple:scalar_test=test_substring_fail]
fail-if="D" in this

[simple:scalar_test=test_substring_pass]
fail-if="D" in this

[simple:scalar_test=test_var_div_zero_fail]
fail-if=24 % this == 0

[simple:scalar_test=test_var_even_even]
type=integer

[simple:scalar_test=test_var_even_fail]
fail-if=this % 2 == 0
type=integer

[simple:scalar_test=test_var_even_pass]
fail-if=this % 2 == 0
type=integer

[simple:scalar_test=test_var_lt_control_fail]
fail-if=this < simple:scalar_test=control_lt
type=integer

[simple:scalar_test=test_var_lt_control_pass]
fail-if=this < simple:scalar_test=control_lt
type=integer

[simple:scalar_test=test_var_mult_fail]
fail-if=this != simple:scalar_test=control_mult_1 * simple:scalar_test=control_mult_2
type=real

[simple:scalar_test=test_var_mult_pass]
fail-if=this != simple:scalar_test=control_mult_1 * simple:scalar_test=control_mult_2
type=real

[simple:scalar_test=test_var_odd_even]
type=integer

[simple:scalar_test=test_var_sum_fail]
fail-if=this != simple:scalar_test=control_sum_1 + simple:scalar_test=control_sum_2 + simple:scalar_test=control_sum_3
type=real

[simple:scalar_test=test_var_sum_pass]
fail-if=this != simple:scalar_test=control_sum_1 + simple:scalar_test=control_sum_2 + simple:scalar_test=control_sum_3
type=real

[simple:warn_test]

[simple:warn_test=test_var_1]
type=integer
warn-if=this > 0

[simple:warn_test=test_var_2]
type=integer
warn-if=this < 0  # Probably should not be negative.

[simple:warn_test=test_var_3]
type=integer
warn-if=this % 3 == 0;  # Probably should not be a multiple of 3.
       =this < 0;  # Probably should not be less than 0.
       =this * this * this < 100;  # Cube should be less than 100.
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-err-ids
setup
init <<__META_CONFIG__
[kitchen=coffee_pot]
warn-if=freezer=COFFEE is None

[zoo=elephant]
fail-if=zoo=num_mice > 0
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.metadata_check.MetadataChecker: issues: 2
    kitchen=coffee_pot=warn-if=freezer=COFFEE is None
        Not found: freezer=COFFEE
    zoo=elephant=fail-if=zoo=num_mice > 0
        Not found: zoo=num_mice
__ERR__
teardown
#-------------------------------------------------------------------------------
exit
