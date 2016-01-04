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
tests 12
#-------------------------------------------------------------------------------
# Check values syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_fixed_array]
length=:
values=red, blue

[namelist:values_nl1=my_char]
values = 'orange'

[namelist:values_nl1=my_num]
values=56

[namelist:values_nl1=my_raw]
values = something"(")\,

[namelist:values_nl2]
duplicate = true

[namelist:values_nl2=my_num]
values = 5

[namelist:values_nl2{mod1}=my_num]
values = 4
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check values syntax checking (fail).
TEST_KEY=$TEST_KEY_BASE-bad
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_fixed_var]
values=
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:values_nl1=my_fixed_var=values=
        Invalid syntax: 
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check value-titles syntax checking.
TEST_KEY=$TEST_KEY_BASE-titles-ok
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_fixed_array]
length=:
values=red, blue
value-titles=Red Colour, Blue Colour

[namelist:values_nl1=my_char]
values = 'orange'
value-titles=Orange

[namelist:values_nl1=my_num]
values=56
value-titles=fifty-six

[namelist:values_nl1=my_raw]
values = something"(")\,
value-titles=Piece of random stuff

[namelist:values_nl2]
duplicate = true

[namelist:values_nl2=my_num]
values = 5
value-titles=Five

[namelist:values_nl2{mod1}=my_num]
values=4
value-titles=Four
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check value-titles syntax checking (fail).
TEST_KEY=$TEST_KEY_BASE-titles-bad
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_fixed_array]
length=:
values=red, blue
value-titles=Red Colour

[namelist:values_nl1=my_char]
values = 'orange'
value-titles=Orange, and Purple, and Pink, and Green

[namelist:values_nl1=my_num]
value-titles=Something
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 3
    namelist:values_nl1=my_char=value-titles=Orange, and Purple, and Pink, and Green
        Incompatible with values
    namelist:values_nl1=my_fixed_array=value-titles=Red Colour
        Incompatible with values
    namelist:values_nl1=my_num=value-titles=Something
        Incompatible with values
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
