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
my_char_array = 'red', 'green'
my_num_array = 3, 56, 35
my_raw_array = red, green, red
my_fixed_array = red, red, red, red, red
my_char = 'orange'
my_num = 56
my_raw = something"(")\,
my_location = 'Exeter, England'

[namelist:values_nl2{mod1}]
my_num = 4

[namelist:values_nl2{mod2}]
my_num = 5
__CONFIG__
#-------------------------------------------------------------------------------
tests 17
#-------------------------------------------------------------------------------
# Check single values checking.
TEST_KEY=$TEST_KEY_BASE-single-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_fixed_array]
length=:
values = red

[namelist:values_nl1=my_char]
values = 'orange'

[namelist:values_nl1=my_num]
values = 56

[namelist:values_nl1=my_raw]
values = something"(")\\\,

[namelist:values_nl2]
duplicate = true

[namelist:values_nl2=my_num]
values = 5

[namelist:values_nl2{mod1}=my_num]
values = 4
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check single values checking errs.
TEST_KEY=$TEST_KEY_BASE-single-err
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_fixed_array]
length=:
values = 'purple'

[namelist:values_nl1=my_char]
values = 'maroon'

[namelist:values_nl1=my_num]
values = 5

[namelist:values_nl1=my_raw]
values = other

[namelist:values_nl2]
duplicate = true

[namelist:values_nl2=my_num]
values = 4

[namelist:values_nl2{mod1}=my_num]
values = 5
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_char='orange'
        Value 'orange' should be 'maroon'
    namelist:values_nl1=my_fixed_array=red,red,red,red,red
        Value red should be 'purple'
    namelist:values_nl1=my_num=56
        Value 56 should be 5
    namelist:values_nl1=my_raw=something"(")\,
        Value something"(")\, should be other
    namelist:values_nl2{mod1}=my_num=4
        Value 4 should be 5
    namelist:values_nl2{mod2}=my_num=5
        Value 5 should be 4
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check multiple values checking.
TEST_KEY=$TEST_KEY_BASE-multiple-ok
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_char_array]
length=:
values = 'red', 'green', 'orange', 'purple'

[namelist:values_nl1=my_raw_array]
length=:
values = red, green, brown

[namelist:values_nl1=my_num_array]
length=:
values = 3, 56, 35, 567, 2, -54

[namelist:values_nl1=my_fixed_array]
length=:
values = red, green

[namelist:values_nl1=my_char]
values = 'red', 'green', 'orange'

[namelist:values_nl1=my_num]
values = 56, 5, 1

[namelist:values_nl1=my_raw]
values = something"(")\\\,, something_else

[namelist:values_nl2]
duplicate = true
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check multiple values checking errs.
TEST_KEY=$TEST_KEY_BASE-multiple-err
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_char_array]
length=:
values = 'orange', 'purple'

[namelist:values_nl1=my_raw_array]
length=:
values = blue, yellow

[namelist:values_nl1=my_num_array]
length=:
values = 3, 35, 567, 2, -54

[namelist:values_nl1=my_fixed_array]
length=:
values = 'green', 'yellow'

[namelist:values_nl1=my_char]
values = 'maroon', 'turquoise'

[namelist:values_nl=my_num]
values = 4.67, -345

[namelist:values_nl1=my_raw]
values = x, y, z

[namelist:values_nl2]
duplicate = true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:values_nl1=my_char='orange'
        Value 'orange' not in allowed values ["'maroon'", "'turquoise'"]
    namelist:values_nl1=my_char_array='red','green'
        Value 'red' not in allowed values ["'orange'", "'purple'"]
    namelist:values_nl1=my_fixed_array=red,red,red,red,red
        Value red not in allowed values ["'green'", "'yellow'"]
    namelist:values_nl1=my_num_array=3,56,35
        Value 56 not in allowed values ['3', '35', '567', '2', '-54']
    namelist:values_nl1=my_raw=something"(")\,
        Value something"(")\, not in allowed values ['x', 'y', 'z']
    namelist:values_nl1=my_raw_array=red,green,red
        Value red not in allowed values ['blue', 'yellow']
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check comma escape in "values"
TEST_KEY="${TEST_KEY_BASE}-comma-esc-1"
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_location]
values = 'Exeter\, England'
__META_CONFIG__
run_pass "${TEST_KEY}" rose macro -V --config='../config'
teardown

TEST_KEY="${TEST_KEY_BASE}-comma-esc-1-comma"
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_location]
values = 'Exeter\, England',
__META_CONFIG__
run_pass "${TEST_KEY}" rose macro -V --config='../config'
teardown

TEST_KEY="${TEST_KEY_BASE}-comma-esc-2"
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_location]
values = 'Exeter\, England', 'Aberdeen\, Scotland'
__META_CONFIG__
run_pass "${TEST_KEY}" rose macro -V --config='../config'
teardown

TEST_KEY="${TEST_KEY_BASE}-comma-esc-bad"
setup
init_meta <<'__META_CONFIG__'
[namelist:values_nl1=my_location]
values = 'Manchester\, England', 'Glasgow\, Scotland'
__META_CONFIG__
run_fail "${TEST_KEY}" rose macro -V --config='../config'
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 1
    namelist:values_nl1=my_location='Exeter, England'
        Value 'Exeter, England' not in allowed values ["'Manchester, England'", "'Glasgow, Scotland'"]
__ERR__
teardown
#-------------------------------------------------------------------------------
exit
