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
# Test "rose macro" in built-in value changing mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:values_nl1]
my_array_fixed = 'x,', y, 5.0e-3, 5, 6, y, 21, o, (), opsdf, sdfkl
my_boolean_true = T
my_boolean_false = .false.
my_boolean_array_any = true, False, true
my_boolean_array_fixed = false, true, false, true, true, false
my_char = Character string with no surrounding quotes
my_int = 1.4
my_int_sci_notation = XeY
my_int_array_any = 1, 2, three, 4, 5, 6
my_int_array_fixed = elephant, 2.0, 3.0, -4.0, 6.0e4, 2
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
my_logical_false = .False.
my_logical_true = true
my_logical_array_any = .false., .true., maybe, .false.
my_logical_array_fixed = .true., .t., .false., .tRue., .false., .false.
my_derived_type_quo_int_raw_bool = "I escape "quotes" badly", -45.e, $something, false
my_derived_type_quo_int_raw_bool_array = "String string,  23", 456.x45, false,
                                       = "I like to quote \"stuff\"", 3456, ^xx2, true,
                                       = I do not contain quotes, -45, i be a raw entry, true
__CONFIG__
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
# Check type transforms.
TEST_KEY=$TEST_KEY_BASE-change
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

[namelist:values_nl1=my_char]
type=character

[namelist:values_nl1=my_char_esc]
type=character

[namelist:values_nl1=my_char_complex_esc]
type=character

[namelist:values_nl1=my_char_array_any]
length=:
type=character

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

[namelist:values_nl1=my_real]
type=real

[namelist:values_nl1=my_real_sci_notation_neg]
type=real

[namelist:values_nl1=my_real_sci_notation_pos]
type=real

[namelist:values_nl1=my_real_array_any]
type=real
length=:

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
run_pass "$TEST_KEY" rose macro --fix --non-interactive --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[T] rose.macros.DefaultTransforms: changes: 8
    namelist:values_nl1=my_boolean_array_any=true,false,true
        true,False,true -> true,false,true
    namelist:values_nl1=my_char='Character string with no surrounding quotes'
        Character string with no surrounding quotes -> 'Character string with no surrounding quotes'
    namelist:values_nl1=my_logical_array_fixed=.true.,.true.,.false.,.true.,.false.,.false.
        .true.,.t.,.false.,.tRue.,.false.,.false. -> .true.,.true.,.false.,.true.,.false.,.false.
    namelist:values_nl1=my_logical_false=.false.
        .False. -> .false.
    namelist:values_nl1=my_quoted_ends_quote="Bad quoted"
        Bad quoted" -> "Bad quoted"
    namelist:values_nl1=my_quoted_no_quotes="something"
        something -> "something"
    namelist:values_nl1=my_quoted_starts_quote="bad quoted"
        "bad quoted -> "bad quoted"
    namelist:values_nl1=my_quoted_wrong_kind_quotes="'"double quoted"'"
        '"double quoted"' -> "'"double quoted"'"
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.conf" ../config/rose-app.conf <<'__CONTENT__'
[namelist:values_nl1]
my_array_fixed='x,',y,5.0e-3,5,6,y,21,o,(),opsdf,sdfkl
my_boolean_array_any=true,false,true
my_boolean_array_fixed=false,true,false,true,true,false
my_boolean_false=.false.
my_boolean_true=T
my_char='Character string with no surrounding quotes'
my_derived_type_quo_int_raw_bool="I escape "quotes" badly",-45.e,$something,false
my_derived_type_quo_int_raw_bool_array="String string,  23",456.x45,false,
                                      ="I like to quote \"stuff\"",3456,^xx2,true,
                                      =I do not contain quotes,-45,i be a raw entry,true
my_int=1.4
my_int_array_any=1,2,three,4,5,6
my_int_array_fixed=elephant,2.0,3.0,-4.0,6.0e4,2
my_int_sci_notation=XeY
my_logical_array_any=.false.,.true.,maybe,.false.
my_logical_array_fixed=.true.,.true.,.false.,.true.,.false.,.false.
my_logical_false=.false.
my_logical_true=true
my_quoted="\\" Bad quoted quoted"
my_quoted_array_fixed="a, "b\"", "\"c", "d"
my_quoted_array_null_comp="a",,"c",
my_quoted_ends_quote="Bad quoted"
my_quoted_no_quotes="something"
my_quoted_ok_quotes="quoted again\""
my_quoted_starts_quote="bad quoted"
my_quoted_wrong_kind_quotes="'"double quoted"'"
my_real=1.0x6
my_real_array_any=1.0,2.0,three point zero,4.0
my_real_sci_notation_neg=minus two
my_real_sci_notation_pos=+45 e 2
__CONTENT__
teardown
#-------------------------------------------------------------------------------

exit
