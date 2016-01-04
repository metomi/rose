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
my_array = 1, 2, 4, 6
my_char = 'something'
my_date = 07/06/12 14:28:13
my_nocase = CamelCase
my_int = 56
my_raw = This is some kind of sentence.
my_raw_ends = This ends with orange
__CONFIG__
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check pattern checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_array]
length=:
pattern = ^(\d*,\s*)*\d*$

[namelist:values_nl1=my_char]
pattern = ^'.*'$

[namelist:values_nl1=my_date]
pattern = ^\d\d/\d\d/\d\d\s\d\d:\d\d:\d\d$

[namelist:values_nl1=my_int]
pattern = ^\d+$

[namelist:values_nl1=my_nocase]
pattern = (?i)^camelcase$

[namelist:values_nl1=my_raw]
pattern = ^[A-Z][\w\s,]+\.$

[namelist:values_nl1=my_raw_ends]
pattern = orange$
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check pattern checking.
TEST_KEY=$TEST_KEY_BASE-err
setup
init_meta <<__META_CONFIG__
[namelist:values_nl1=my_array]
length=:
pattern = ^(\d*)$

[namelist:values_nl1=my_char]
pattern = ^'.*"$

[namelist:values_nl1=my_date]
pattern = ^\d\d/\d\d/41\s\d\d:\d\d:\d\d$

[namelist:values_nl1=my_int]
pattern = ^\d+e\d+$

[namelist:values_nl1=my_nocase]
pattern = ^camelcase$

[namelist:values_nl1=my_raw]
pattern = ^Because\s[\w\s,]+\.$

[namelist:values_nl1=my_raw_ends]
pattern = green$
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 7
    namelist:values_nl1=my_array=1,2,4,6
        Value 1,2,4,6 does not contain the pattern: ^(\d*)$
    namelist:values_nl1=my_char='something'
        Value 'something' does not contain the pattern: ^'.*"$
    namelist:values_nl1=my_date=07/06/12 14:28:13
        Value 07/06/12 14:28:13 does not contain the pattern: ^\d\d/\d\d/41\s\d\d:\d\d:\d\d$
    namelist:values_nl1=my_int=56
        Value 56 does not contain the pattern: ^\d+e\d+$
    namelist:values_nl1=my_nocase=CamelCase
        Value CamelCase does not contain the pattern: ^camelcase$
    namelist:values_nl1=my_raw=This is some kind of sentence.
        Value This is some kind of sentence. does not contain the pattern: ^Because\s[\w\s,]+\.$
    namelist:values_nl1=my_raw_ends=This ends with orange
        Value This ends with orange does not contain the pattern: green$
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
