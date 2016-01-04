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
# Test "rose metadata-gen" in basic metadata output mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<__CONFIG__
[namelist:testnl1]
my_char = 'Character string'
my_char_array = 'a', 'b', 'c'
my_int = 1
my_int_array_long = 1, 2, 3, 4, 5, 6
my_raw = Raw string
my_real = 1.0
my_real_array = 1.0, 2.0, 3.0
my_logical = .false.
my_logical_array = .false., .true., .false.
my_derived = 'String', 1.0, 2, .false.
my_derived_array = 'String1', 1.0, 2, .false., 'String2', 3.0, 4, .true.

[namelist:testnl2(1)]
my_int = -3000

[namelist:testnl3{mod1}]
my_real = 2.0

[namelist:testnl4{mod1}(1)]
my_logical = .false.
__CONFIG__
#-------------------------------------------------------------------------------
tests 8
#-------------------------------------------------------------------------------
# No properties to be set.
TEST_KEY=$TEST_KEY_BASE-no-props
setup
run_pass "$TEST_KEY" rose metadata-gen --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.conf" ../config/meta/rose-meta.conf - <<'__CONTENT__'
[namelist:testnl1]

[namelist:testnl1=my_char]

[namelist:testnl1=my_char_array]

[namelist:testnl1=my_derived]

[namelist:testnl1=my_derived_array]

[namelist:testnl1=my_int]

[namelist:testnl1=my_int_array_long]

[namelist:testnl1=my_logical]

[namelist:testnl1=my_logical_array]

[namelist:testnl1=my_raw]

[namelist:testnl1=my_real]

[namelist:testnl1=my_real_array]

[namelist:testnl2]

[namelist:testnl2=my_int]

[namelist:testnl3]

[namelist:testnl3=my_real]

[namelist:testnl4]

[namelist:testnl4=my_logical]
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# No properties to be set, use different output directory.
TEST_KEY=$TEST_KEY_BASE-no-props-output
setup
run_pass "$TEST_KEY" \
   rose metadata-gen --config=../config --output=../config/something
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.conf" ../config/something/rose-meta.conf - <<'__CONTENT__'
[namelist:testnl1]

[namelist:testnl1=my_char]

[namelist:testnl1=my_char_array]

[namelist:testnl1=my_derived]

[namelist:testnl1=my_derived_array]

[namelist:testnl1=my_int]

[namelist:testnl1=my_int_array_long]

[namelist:testnl1=my_logical]

[namelist:testnl1=my_logical_array]

[namelist:testnl1=my_raw]

[namelist:testnl1=my_real]

[namelist:testnl1=my_real_array]

[namelist:testnl2]

[namelist:testnl2=my_int]

[namelist:testnl3]

[namelist:testnl3=my_real]

[namelist:testnl4]

[namelist:testnl4=my_logical]
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
