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
# Test "rose macro" in built-in value checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check type-length checking.
TEST_KEY=$TEST_KEY_BASE-type-length-ok
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_int]
range = 5

[namelist:values_nl1=my_int_neg]
range = -2

[namelist:values_nl1=my_real]
range = 678.3

[namelist:values_nl1=my_real_neg]
range = -345.1

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
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check type-length checking (fail).
TEST_KEY=$TEST_KEY_BASE-type-length-bad
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_boolean_false]
type=booleans

[namelist:values_nl1=my_boolean_array_any]
length=:
type=booleans

[namelist:values_nl1=my_boolean_array_fixed]
length=5
type=boolean

[namelist:values_nl1=my_char_complex_esc]
type=character

[namelist:values_nl1=my_char_array_any]
length=-1
type=character

[namelist:values_nl1=my_char_array_fixed]
length=four
type=character

[namelist:values_nl1=my_int_sci_notation]
type=integer (that means whole numbers)

[namelist:values_nl1=my_int_array_any]
length=::
type=integer

[namelist:values_nl1=my_int_array_fixed]
length=6
type=integer

[namelist:values_nl1=my_real_sci_notation_pos]
type=real

[namelist:values_nl1=my_real_array_any]
type=real
length=:

[namelist:values_nl1=my_real_array_fixed]
type=real
length=5

[namelist:values_nl1=my_quoted_complex_esc]
type=string

[namelist:values_nl1=my_derived_type_str_int_raw_bool]
type=quoted, integer, string, raw, boolean

[namelist:values_nl1=my_derived_type_raw_log_char_real]
type=raw, logical, what?, character, real

[namelist:values_nl1=my_derived_type_str_int_raw_bool_array]
type=quoted, integer, raw, boolean
length=3

[namelist:values_nl1=my_derived_type_raw_log_char_real_array]
type=raw, logical, character, real
length=:

[namelist:values_nl1=my_derived_type_real_int_null_array]
type=real, integer
length=:

[namelist:values_nl1=my_array_any]
length=:

[namelist:values_nl1=my_array_fixed]
length=8
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] MetadataChecker: issues: 9
    namelist:values_nl1=my_boolean_array_any=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_boolean_false=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid length - should be : or positive integer
    namelist:values_nl1=my_char_array_fixed=length=four
        Invalid length - should be : or positive integer
    namelist:values_nl1=my_derived_type_raw_log_char_real=type=raw, logical, what?, character, real
        Unknown type: what?
    namelist:values_nl1=my_derived_type_str_int_raw_bool=type=quoted, integer, string, raw, boolean
        Unknown type: string
    namelist:values_nl1=my_int_array_any=length=::
        Invalid length - should be : or positive integer
    namelist:values_nl1=my_int_sci_notation=type=integer (that means whole numbers)
        Unknown type: integer (that means whole numbers)
    namelist:values_nl1=my_quoted_complex_esc=type=string
        Unknown type: string
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
