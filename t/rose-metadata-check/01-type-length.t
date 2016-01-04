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
tests 24
#-------------------------------------------------------------------------------
# Check type-length checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_boolean_false]
type=boolean

[namelist:values_nl1=my_boolean_array_any]
length=:
type=boolean

[namelist:values_nl1=my_boolean_array_fixed]
length=5
type=boolean

[namelist:values_nl1=my_char_complex_esc]
type=character

[namelist:values_nl1=my_char_array_any]
length=:
type=character

[namelist:values_nl1=my_char_array_fixed]
length=4
type=character

[namelist:values_nl1=my_int_sci_notation]
type=integer

[namelist:values_nl1=my_int_array_any]
length=:
type=integer

[namelist:values_nl1=my_int_array_fixed]
length=6
type=integer

[namelist:values_nl1=my_python_list]
type=python_list

[namelist:values_nl1=my_real_sci_notation_pos]
type=real

[namelist:values_nl1=my_real_array_any]
type=real
length=:

[namelist:values_nl1=my_real_array_fixed]
type=real
length=5

[namelist:values_nl1=my_quoted_complex_esc]
type=quoted

[namelist:values_nl1=my_quoted_array_any]
length=:
type=quoted

[namelist:values_nl1=my_quoted_array_fixed]
length=4
type=quoted

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

[namelist:values_nl1=my_array_any]
length=:

[namelist:values_nl1=my_array_fixed]
length=8
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check type-length checking (fail).
TEST_KEY=$TEST_KEY_BASE-bad
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

[namelist:values_nl1=my_python_list]
length=:
type=python_list

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
[V] rose.metadata_check.MetadataChecker: issues: 10
    namelist:values_nl1=my_boolean_array_any=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_boolean_false=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid syntax: -1
    namelist:values_nl1=my_char_array_fixed=length=four
        Invalid syntax: four
    namelist:values_nl1=my_derived_type_raw_log_char_real=type=raw, logical, what?, character, real
        Unknown type: what?
    namelist:values_nl1=my_derived_type_str_int_raw_bool=type=quoted, integer, string, raw, boolean
        Unknown type: string
    namelist:values_nl1=my_int_array_any=length=::
        Invalid syntax: ::
    namelist:values_nl1=my_int_sci_notation=type=integer (that means whole numbers)
        Unknown type: integer (that means whole numbers)
    namelist:values_nl1=my_python_list=length=:
        Incompatible with type
    namelist:values_nl1=my_quoted_complex_esc=type=string
        Unknown type: string
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check type-length checking for just the type property (fail).
TEST_KEY=$TEST_KEY_BASE-bad-type-only
setup
run_fail "$TEST_KEY" rose metadata-check -C ../config --property=type
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 7
    namelist:values_nl1=my_boolean_array_any=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_boolean_false=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_derived_type_raw_log_char_real=type=raw, logical, what?, character, real
        Unknown type: what?
    namelist:values_nl1=my_derived_type_str_int_raw_bool=type=quoted, integer, string, raw, boolean
        Unknown type: string
    namelist:values_nl1=my_int_sci_notation=type=integer (that means whole numbers)
        Unknown type: integer (that means whole numbers)
    namelist:values_nl1=my_python_list=length=:
        Incompatible with type
    namelist:values_nl1=my_quoted_complex_esc=type=string
        Unknown type: string
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check type-length checking for just the length property (fail).
TEST_KEY=$TEST_KEY_BASE-bad-length-only
setup
run_fail "$TEST_KEY" rose metadata-check -C ../config --property=length
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 4
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid syntax: -1
    namelist:values_nl1=my_char_array_fixed=length=four
        Invalid syntax: four
    namelist:values_nl1=my_int_array_any=length=::
        Invalid syntax: ::
    namelist:values_nl1=my_python_list=length=:
        Incompatible with type
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check type-length checking for both type and length properties (fail).
TEST_KEY=$TEST_KEY_BASE-bad-length-and-type
setup
run_fail "$TEST_KEY" rose metadata-check -C ../config --property=length --property=type
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 10
    namelist:values_nl1=my_boolean_array_any=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_boolean_false=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid syntax: -1
    namelist:values_nl1=my_char_array_fixed=length=four
        Invalid syntax: four
    namelist:values_nl1=my_derived_type_raw_log_char_real=type=raw, logical, what?, character, real
        Unknown type: what?
    namelist:values_nl1=my_derived_type_str_int_raw_bool=type=quoted, integer, string, raw, boolean
        Unknown type: string
    namelist:values_nl1=my_int_array_any=length=::
        Invalid syntax: ::
    namelist:values_nl1=my_int_sci_notation=type=integer (that means whole numbers)
        Unknown type: integer (that means whole numbers)
    namelist:values_nl1=my_python_list=length=:
        Incompatible with type
    namelist:values_nl1=my_quoted_complex_esc=type=string
        Unknown type: string
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check length checking for a single ID (fail).
TEST_KEY=$TEST_KEY_BASE-bad-length-ID
setup
run_fail "$TEST_KEY" rose metadata-check -C ../config --property=length namelist:values_nl1=my_char_array_any
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid syntax: -1
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check type-length checking for a single ID (fail).
TEST_KEY=$TEST_KEY_BASE-bad-ID
setup
run_fail "$TEST_KEY" rose metadata-check -C ../config namelist:values_nl1=my_char_array_any
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid syntax: -1
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check type-length checking for two IDs (fail).
TEST_KEY=$TEST_KEY_BASE-bad-IDs
setup
run_fail "$TEST_KEY" rose metadata-check -C ../config namelist:values_nl1=my_char_array_any namelist:values_nl1=my_boolean_false
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 2
    namelist:values_nl1=my_boolean_false=type=booleans
        Unknown type: booleans
    namelist:values_nl1=my_char_array_any=length=-1
        Invalid syntax: -1
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
