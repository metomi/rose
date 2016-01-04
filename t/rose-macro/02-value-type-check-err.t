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
my_array_fixed = 'x,', y, 5.0e-3, 5, 6, y, 21, o, (), opsdf, sdfkl
my_boolean_true = T
my_boolean_false = .false.
my_boolean_array_any = true, False, true
my_boolean_array_fixed = false, true, false, true, true, false
my_boolean_array_null_comp = false, ,    true,,
my_char = 'Character string ending in unescaped''
my_char_esc = 'Character string that\'s escaped in a string way'
my_char_complex_esc = ''Character string that's "very escaped'''
my_char_array_any = 'a', 'b', "h",
my_char_array_null_comp = 'a', 'b',,'c', 'd'
my_int = 1.4
my_int_sci_notation = XeY
my_int_array_any = 1, 2, three, 4, 5, 6
my_int_array_fixed = elephant, 2.0, 3.0, -4.0, 6.0e4, 2
my_int_array_null_comp = 3, , 4, 56,,4
my_quoted = "\\" Bad quoted quoted"
my_quoted_ends_quote = Bad quoted"
my_quoted_starts_quote = "bad quoted
my_quoted_no_quotes = something
my_quoted_ok_quotes = "quoted again\""
my_quoted_wrong_kind_quotes = '"double quoted"'
my_quoted_array_fixed = "a, "b\"", "\"c", "d"
my_quoted_array_null_comp = "a", , "c",
my_real = 1.0x6
my_real_sci_notation_neg = minus two
my_real_sci_notation_pos = +45 e 2
my_real_array_any = 1.0, 2.0, three point zero, 4.0
my_real_array_null_comp = 2.0, 34.672e-2, ,1
my_logical_false = .False.
my_logical_true = true
my_logical_array_any = .false., .true., maybe, .false.
my_logical_array_fixed = .true., .t., .false., .true., .false., .false.
my_logical_array_null_comp = .false.,,,.true.
my_derived_type_quo_int_raw_bool = 'I escape '' quotes badly', -45.e, $something, false
my_derived_type_quo_int_raw_bool_array = 'quoted quoted,  23', 456.x45, false,
                                       = 'I like to quote \'stuff\'', 3456, ^xx2, true,
                                       = 'I do not contain quotes', -45, i be a raw entry, true
my_derived_type_raw_log_char_real = raw ^%75\\, .true., 'a simple character quoted', 45.0p2
my_derived_type_raw_log_char_real_array = xlkdf",", .true., 'I\'m a bad character quoted', 3.0e-3,
                                          asp'\,', .false., 'I also like to quote ''stuff''', -42
my_derived_type_real_int_null_comp_array = 2.0,,4.0,,2.3e+2, 1
my_python_list=["Spam", True, "Cheese, False, 2000.0]
my_python_list_empty=
my_spaced_list=1 2 3 "bob"
__CONFIG__
#-------------------------------------------------------------------------------
tests 30
#-------------------------------------------------------------------------------
# Check boolean type checking.
TEST_KEY=$TEST_KEY_BASE-boolean-err
setup
init_meta <<__META_CONFIG__
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
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 4
    namelist:values_nl1=my_boolean_array_any=False
        Not true/false: 'False'
    namelist:values_nl1=my_boolean_array_fixed=false,true,false,true,true,false
        Array longer than max length: 6 instead of 5
    namelist:values_nl1=my_boolean_false=.false.
        Not true/false: '.false.'
    namelist:values_nl1=my_boolean_true=T
        Not true/false: 'T'
__CONTENT__
teardown

#-------------------------------------------------------------------------------
# Check character type checking.
TEST_KEY=$TEST_KEY_BASE-character-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_char]
type=character

[namelist:values_nl1=my_char_esc]
type=character

[namelist:values_nl1=my_char_complex_esc]
type=character

[namelist:values_nl1=my_char_array_any]
length=:
type=character
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 4
    namelist:values_nl1=my_char='Character string ending in unescaped''
        Not in a valid single quoted format: "'Character string ending in unescaped''"
    namelist:values_nl1=my_char_array_any="h"
        Not in a valid single quoted format: '"h"'
    namelist:values_nl1=my_char_complex_esc=''Character string that's "very escaped'''
        Not in a valid single quoted format: '\'\'Character string that\'s "very escaped\'\'\''
    namelist:values_nl1=my_char_esc='Character string that\'s escaped in a string way'
        Not in a valid single quoted format: "'Character string that\\'s escaped in a string way'"
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check integer type checking.
TEST_KEY=$TEST_KEY_BASE-int-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_int]
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
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 4
    namelist:values_nl1=my_int=1.4
        Not an integer: '1.4'
    namelist:values_nl1=my_int_array_any=three
        Not an integer: 'three'
    namelist:values_nl1=my_int_array_fixed=elephant
        Not an integer: 'elephant'
    namelist:values_nl1=my_int_sci_notation=XeY
        Not an integer: 'XeY'
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check real type checking.
TEST_KEY=$TEST_KEY_BASE-real-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_real]
type=real

[namelist:values_nl1=my_real_sci_notation_neg]
type=real

[namelist:values_nl1=my_real_sci_notation_pos]
type=real

[namelist:values_nl1=my_real_array_any]
type=real
length=:
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 4
    namelist:values_nl1=my_real=1.0x6
        Not a real number: '1.0x6'
    namelist:values_nl1=my_real_array_any=three point zero
        Not a real number: 'three point zero'
    namelist:values_nl1=my_real_sci_notation_neg=minus two
        Not a real number: 'minus two'
    namelist:values_nl1=my_real_sci_notation_pos=+45 e 2
        Not a real number: '+45 e 2'
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check quoted string type checking.
TEST_KEY=$TEST_KEY_BASE-quoted-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_quoted]
type=quoted

[namelist:values_nl1=my_quoted_ends_quote]
type=quoted

[namelist:values_nl1=my_quoted_starts_quote]
type=quoted

[namelist:values_nl1=my_quoted_no_quotes]
type=quoted

[namelist:values_nl1=my_quoted_ok_quotes]
type=quoted

[namelist:values_nl1=my_quoted_wrong_kind_quotes]
type=quoted

[namelist:values_nl1=my_quoted_array_fixed]
length=4
type=quoted
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_quoted="\\" Bad quoted quoted"
        Not in a valid double quoted format: '"\\\\" Bad quoted quoted"'
    namelist:values_nl1=my_quoted_array_fixed="a, "b\"", "\"c", "d"
        Not in a valid double quoted format: '"a, "b\\"", "\\"c", "d"'
    namelist:values_nl1=my_quoted_ends_quote=Bad quoted"
        Not in a valid double quoted format: 'Bad quoted"'
    namelist:values_nl1=my_quoted_no_quotes=something
        Not in a valid double quoted format: 'something'
    namelist:values_nl1=my_quoted_starts_quote="bad quoted
        Not in a valid double quoted format: '"bad quoted'
    namelist:values_nl1=my_quoted_wrong_kind_quotes='"double quoted"'
        Not in a valid double quoted format: '\'"double quoted"\''
__CONTENT__
teardown

#-------------------------------------------------------------------------------
# Check logical type checking.
TEST_KEY=$TEST_KEY_BASE-logical-err
setup
init_meta <<__META_CONFIG__
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
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 4
    namelist:values_nl1=my_logical_array_any=maybe
        Not Fortran true/false: 'maybe'
    namelist:values_nl1=my_logical_array_fixed=.t.
        Not Fortran true/false: '.t.'
    namelist:values_nl1=my_logical_false=.False.
        Not Fortran true/false: '.False.'
    namelist:values_nl1=my_logical_true=true
        Not Fortran true/false: 'true'
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check derived type checking.
TEST_KEY=$TEST_KEY_BASE-derived-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_derived_type_quo_int_raw_bool]
type=quoted, integer, raw, boolean

[namelist:values_nl1=my_derived_type_raw_log_char_real]
type=raw, logical, character, real

[namelist:values_nl1=my_derived_type_quo_int_raw_bool_array]
type=quoted, integer, raw, boolean
length=3

[namelist:values_nl1=my_derived_type_raw_log_char_real_array]
type=raw, logical, character, real
length=:
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 3
    namelist:values_nl1=my_derived_type_quo_int_raw_bool_array='quoted quoted,  23',456.x45,false,'I like to quote \'stuff\'',3456,^xx2,true,'I do not contain quotes',-45,i be a raw entry,true
        Derived type has an invalid length: 11
    namelist:values_nl1=my_derived_type_raw_log_char_real=45.0p2
        Not a real number: '45.0p2'
    namelist:values_nl1=my_derived_type_raw_log_char_real_array='I\'m a bad character quoted'
        Not in a valid single quoted format: "'I\\'m a bad character quoted'"
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check Python List type checking.
TEST_KEY=$TEST_KEY_BASE-python-list-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_python_list]
type=python_list

[namelist:values_nl1=my_python_list_empty]
type=python_list
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
# Note - the format of the value changes due to the namelist-specific formatting.
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 2
    namelist:values_nl1=my_python_list=["Spam",True,"Cheese, False, 2000.0]
        Not a valid Python list format: '["Spam",True,"Cheese, False, 2000.0]'
    namelist:values_nl1=my_python_list_empty=
        Not a valid Python list format: ''
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check length checking.
TEST_KEY=$TEST_KEY_BASE-array-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_array_fixed]
length=8

[namelist:values_nl1=my_spaced_list]
length=2
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 2
    namelist:values_nl1=my_array_fixed='x,',y,5.0e-3,5,6,y,21,o,(),opsdf,sdfkl
        Array longer than max length: 11 instead of 8
    namelist:values_nl1=my_spaced_list=1 2 3 "bob"
        Array longer than max length: 4 instead of 2
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check derived type checking.
TEST_KEY=$TEST_KEY_BASE-null-compulsory-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_boolean_array_null_comp]
compulsory=true
type=boolean
length=:


[namelist:values_nl1=my_char_array_null_comp]
compulsory=true
type=character
length=:

[namelist:values_nl1=my_int_array_null_comp]
compulsory=true
type=integer
length=:

[namelist:values_nl1=my_logical_array_null_comp]
compulsory=true
type=logical
length=:

[namelist:values_nl1=my_quoted_array_null_comp]
compulsory=true
type=quoted
length=3

[namelist:values_nl1=my_real_array_null_comp]
compulsory=true
type=real
length=:

[namelist:values_nl1=my_derived_type_real_int_null_comp_array]
compulsory=true
type=real, integer
length=:
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 7
    namelist:values_nl1=my_boolean_array_null_comp=
        Not true/false: ''
    namelist:values_nl1=my_char_array_null_comp=
        Not in a valid single quoted format: ''
    namelist:values_nl1=my_derived_type_real_int_null_comp_array=
        Not an integer: ''
    namelist:values_nl1=my_int_array_null_comp=
        Not an integer: ''
    namelist:values_nl1=my_logical_array_null_comp=
        Not Fortran true/false: ''
    namelist:values_nl1=my_quoted_array_null_comp="a",,"c",
        Array longer than max length: 4 instead of 3
    namelist:values_nl1=my_real_array_null_comp=
        Not a real number: ''
__CONTENT__
teardown

#-------------------------------------------------------------------------------

exit
