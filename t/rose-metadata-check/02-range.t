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
# Check range syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_int]
range=5

[namelist:values_nl1=my_int_neg]
range=-2

[namelist:values_nl1=my_real]
range=678.3

[namelist:values_nl1=my_real_neg]
range=-345.1

[namelist:values_nl1=my_int]
range=this % 5 == 3

[namelist:values_nl1=my_int_neg]
range=-1,-2,-3

[namelist:values_nl1=my_real]
range=4.0e2, 678.3

[namelist:values_nl1=my_real_neg]
range=456, -345.1

[namelist:values_nl1=my_real_sci_notation_neg]
range=-3.546e-2, -100

[namelist:values_nl1=my_real_sci_notation_pos]
range=-2.3, 56.0e+67, 56, 5, 1, -2

[namelist:values_nl1=my_real_complex_rule]
range=this * 4 != 2 and 2 + 3 + this < 67
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check range syntax checking (fail).
TEST_KEY=$TEST_KEY_BASE-bad
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_int]
range=5foo

[namelist:values_nl1=my_int_neg]
range=-2:x

[namelist:values_nl1=my_real]
range=678.3, y, 56.0

[namelist:values_nl1=my_real_neg]
range=-345.1

[namelist:values_nl1=my_int_dot]
range=this != .

[namelist:values_nl1=my_int_neg_div_0]
range=this/0 = 2

[namelist:values_nl1=my_real_million]
range=2 * this < 1 million dollars

[namelist:values_nl1=my_real_neg]
range=namelist:foo=bar * this < 0

[namelist:values_nl1=my_real_sci_notation_neg]
range=-3.546e-2-100

[namelist:values_nl1=my_real_sci_notation_pos]
range=-2.3, 56.0e+67, 56, 5, 1, -2, sqrt(4)
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^ *Invalid syntax:/d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 9
    namelist:values_nl1=my_int=range=5foo
    namelist:values_nl1=my_int_dot=range=this != .
    namelist:values_nl1=my_int_neg=range=-2:x
    namelist:values_nl1=my_int_neg_div_0=range=this/0 = 2
    namelist:values_nl1=my_real=range=678.3, y, 56.0
    namelist:values_nl1=my_real_million=range=2 * this < 1 million dollars
    namelist:values_nl1=my_real_neg=range=namelist:foo=bar * this < 0
        Inter-variable comparison not allowed in range.
    namelist:values_nl1=my_real_sci_notation_neg=range=-3.546e-2-100
    namelist:values_nl1=my_real_sci_notation_pos=range=-2.3, 56.0e+67, 56, 5, 1, -2, sqrt(4)
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
