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
my_array_any = x, 4, 2, 'something', "'anything"
my_array_fixed = 'x,', y, 5.0e-3, 5, 6, y, 21, -4
my_array_any_null =
my_array_any_one = 57
my_boolean_true = true
my_boolean_false = false
my_boolean_array_any = ,true, false, true
my_boolean_array_fixed = false, true, false, true, true
my_char = 'Character string'
my_char_null = ''
my_char_esc = 'Character string that''s escaped'
my_char_complex_esc = '''Character string that''s "very escaped'''
my_char_array_any = 'a', 'b', 'c', 'd''',, 7*'''e', 'f''g', '"h'
my_char_array_fixed = 'a', 'b''', '''c', 'd'
my_int = 1
my_int_as_float = -0103
my_int_array_any = 1, 2, 3, 4,, 5, 6,, 2*10, 5*-3, 1*0
my_int_array_fixed = -1, 2, 003, -4, 600001, 2
my_raw = Raw string
my_real = 1.0
my_real_as_int_pos = 7
my_real_as_int_neg = -5
my_real_neg = -1.0
my_real_sci_notation_neg = -5.6e+10
my_real_sci_notation_pos = +21.3e-5
my_real_array_any = ,1.0, 2.0, 3.0, 4*2.000e-2, 3*-67.32e2, 2*-5.1e+02
my_real_array_fixed = 1, 2, -67.3, 843e-2, 10
my_string = "String string"
my_string_null = ""
my_string_esc = "String says, \"This is escaped!\"""
my_string_complex_esc = "\"Very, \"\", very escaped\""
my_string_array_any = "a", "b", "c", "d\"", "\"e", "f\"g", "\'h",,
my_string_array_fixed = "a", "b\"", "\"c", "d"
my_logical_false = .false.
my_logical_true = .true.
my_logical_array_any = .false., .true., .false.,, 6*.true.
my_logical_array_fixed = .true., .true., .false., .true., .false., .false.
my_derived_type_str_int_raw_bool = "I escape \" quotes like this: \"", -45, $something, false
my_derived_type_str_int_raw_bool_array = "A string string", -23, 456.x45, false,
                                       = "\"Hello\", said the string", 3456, ^%£2, true,
                                       = "I do not contain quotes", -45, i be a raw entry, true
my_derived_type_raw_log_char_real = raw ^%75\\, .true., 'a simple character string', 45.0
my_derived_type_raw_log_char_real_array = xlkdf",", .true., 'I''m a character string', 3.0e-3,
                                          asp'\,', .false., 'I also like to quote ''stuff''', -42
my_derived_type_real_int_null_array = 2.0,,4.0,,2.3e+2, 1
my_real_array_element(5)=5.0
my_real_array_slice(5:8)=5.0,6.0,7.0,8.0
my_real_array_slice_2d(5:90,1)=5.0,6.0,3.0
my_python_list=["Spam", True, "Cheese", False, 2000.0]
my_python_list_empty=[]
my_spaced_list=1 2 3 "bob"
my_python_boolean_true=True
my_python_boolean_false=False
__CONFIG__
#-------------------------------------------------------------------------------
tests 39
#-------------------------------------------------------------------------------
# Check boolean type checking.
TEST_KEY=$TEST_KEY_BASE-boolean-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_boolean_true]
type=boolean

[namelist:values_nl1=my_boolean_false]
type=boolean

[namelist:values_nl1=my_boolean_array_any]
length=:
type=boolean

[namelist:values_nl1=my_boolean_array_fixed]
length=5
type=boolean
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown

#-------------------------------------------------------------------------------
# Check character type checking.
TEST_KEY=$TEST_KEY_BASE-character-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_char]
type=character

[namelist:values_nl1=my_char_null]
type=character

[namelist:values_nl1=my_char_esc]
type=character

[namelist:values_nl1=my_char_complex_esc]
type=character

[namelist:values_nl1=my_char_array_any]
length=:
type=character

[namelist:values_nl1=my_char_array_fixed]
length=4
type=character
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check integer type checking.
TEST_KEY=$TEST_KEY_BASE-int-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_int]
type=integer

[namelist:values_nl1=my_int_as_float]
type=integer

[namelist:values_nl1=my_int_sci_notation]
type=integer

[namelist:values_nl1=my_int_array_any]
length=:
type=integer

[namelist:values_nl1=my_int_array_fixed]
length=6
type=integer
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check raw (None) type checking.
TEST_KEY=$TEST_KEY_BASE-value-type-raw-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_raw]
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check real type checking.
TEST_KEY=$TEST_KEY_BASE-real-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_real]
type=real

[namelist:values_nl1=my_real_as_int_pos]
type=real

[namelist:values_nl1=my_real_as_int_neg]
type=real

[namelist:values_nl1=my_real_neg]
type=real

[namelist:values_nl1=my_real_sci_notation_neg]
type=real

[namelist:values_nl1=my_real_sci_notation_pos]
type=real

[namelist:values_nl1=my_real_array_any]
type=real
length=:

[namelist:values_nl1=my_real_array_fixed]
type=real
length=5
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --validate --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check quoted string type checking.
TEST_KEY=$TEST_KEY_BASE-string-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_quoted]
type=quoted

[namelist:values_nl1=my_quoted_null]
type=quoted

[namelist:values_nl1=my_quoted_esc]
type=quoted

[namelist:values_nl1=my_quoted_complex_esc]
type=quoted

[namelist:values_nl1=my_quoted_array_any]
length=:
type=quoted

[namelist:values_nl1=my_quoted_array_fixed]
length=4
type=quoted
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown

#-------------------------------------------------------------------------------
# Check logical type checking.
TEST_KEY=$TEST_KEY_BASE-logical-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_logical_true]
type=logical

[namelist:values_nl1=my_logical_false]
type=logical

[namelist:values_nl1=my_logical_array_any]
length=:
type=logical

[namelist:values_nl1=my_logical_array_fixed]
length=6
type=logical
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check derived type checking.
TEST_KEY=$TEST_KEY_BASE-derived-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_derived_type_str_int_raw_bool]
type=quoted, integer, raw, boolean

[namelist:values_nl1=my_derived_type_raw_log_char_real]
type=raw, logical, character, real

[namelist:values_nl1=my_derived_type_str_int_raw_bool_array]
type=quoted, integer, raw, boolean
length=3

[namelist:values_nl1=my_derived_type_raw_log_char_real_array]
type=raw, logical, character, real
length=:

[namelist:values_nl1=my_derived_type_real_int_null_array]
type=real, integer
length=:

__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check Python List type checking.
TEST_KEY=$TEST_KEY_BASE-python-list-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_python_list]
type=python_list

[namelist:values_nl1=my_python_list_empty]
type=python_list
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check Spaced List type checking.
TEST_KEY=$TEST_KEY_BASE-spaced-list-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_spaced_list]
type=spaced_list
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check length checking.
TEST_KEY=$TEST_KEY_BASE-array-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_array_any]
length=:

[namelist:values_nl1=my_array_fixed]
length=8

[namelist:values_nl1=my_array_any_null]
length=:

[namelist:values_nl1=my_array_any_one]
length=:

[namelist:values_nl1=my_real_array_element]
type=real
length=6

[namelist:values_nl1=my_real_array_slice]
type=real
length=8

[namelist:values_nl1=my_real_array_slice_2d]
type=real
length=:
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check ignored option/section skipping.
TEST_KEY=$TEST_KEY_BASE-skip-ignored-ok
setup
init <<'__CONFIG__'
[!namelist:values_nl1]
my_boolean_true=oh no a bad boolean

[namelist:values_nl2]
!my_boolean_true=oh no an ignored boolean
__CONFIG__
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_boolean_true]
type=boolean

[namelist:values_nl2=my_boolean_true]
type=boolean
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check python boolean type checking.
TEST_KEY=$TEST_KEY_BASE-boolean-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_python_boolean_true]
type=python_boolean

[namelist:values_nl1=my_python_boolean_false]
type=python_boolean
__META_CONFIG__
run_pass "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
exit
