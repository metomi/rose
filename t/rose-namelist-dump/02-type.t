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
# Test "rose namelist-dump", namelist of different Fortran literals.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
# Namelist standard input, standard output.
TEST_KEY=$TEST_KEY_BASE
setup
run_pass "$TEST_KEY" rose namelist-dump <<'__CONTENT__'
&name
int=1234, int_zero_prefix_1=01234, int_zero_prefix_2=001234,
negative_int=-1234, negative_int_zero_prefix=-01234,
float=12.5, negative_float=-0.123, negative_float_zero_prefix=-00.123,
dot_float=.246,
sci_float=6.02E23, sci_float_2=-7.8D-29, sci_float_3=0.462E+128,
sci_float_4=4.E+01, sci_float_5=5.0E-01,
sci_float_zero_padded_1=006.02D23, sci_float_zero_padded_2=-00.0789E-23,
sci_float_zero_padded_3=006.02D023, sci_float_zero_padded_4=-0.0789E-0023,
pi=3.14e+0,
cmplx=(-1.23,4.56E-9),
struct=1,1.0E-5,(3.14,2.72), ! some comment
awful%struct(-10:-6,8)%more=-10,-20,2537,43486,19374,
bool=.true., bool_2=.false.,
char='hello world', char2='It''s nice!', char_3="I love namelist.",
char0='',
null=3* ! some comment
null1=,
repeat=50*"ring a ring a roses", "ring a ring a roses",
array_zero_prefix=02, 03, -04, -100, 0, -345, 0001000, 10
array_element(1)=1,
array_element(:)=1,
array_element(0:)=1,
array_element(:10)=1,
array_element(1,1)=1,
array_element(-1)=1,
array_element(-2:)=1,
array_element(:-10)=1,
array_element(0,0)=1,
array_element(-1,0)=1,
array_element(-10,-2)=1,
array_element(-100:-10,-2:10,6:720)=1,
/
__CONTENT__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[file:STDIN]
source=namelist:name

[namelist:name]
array_element(-1)=1
array_element(-1,0)=1
array_element(-10,-2)=1
array_element(-100:-10,-2:10,6:720)=1
array_element(-2:)=1
array_element(0,0)=1
array_element(0:)=1
array_element(1)=1
array_element(1,1)=1
array_element(:)=1
array_element(:-10)=1
array_element(:10)=1
array_zero_prefix=2,3,-4,-100,0,-345,1000,10
awful%struct(-10:-6,8)%more=-10,-20,2537,43486,19374
bool=.true.
bool_2=.false.
char='hello world'
char0=''
char2='It''s nice!'
char_3='I love namelist.'
cmplx=(-1.23,4.56e-9)
dot_float=0.246
float=12.5
int=1234
int_zero_prefix_1=1234
int_zero_prefix_2=1234
negative_float=-0.123
negative_float_zero_prefix=-0.123
negative_int=-1234
negative_int_zero_prefix=-1234
null=,,
null1=
pi=3.14
repeat=51*'ring a ring a roses'
sci_float=6.02e23
sci_float_2=-7.8e-29
sci_float_3=0.462e+128
sci_float_4=4.0e+1
sci_float_5=5.0e-1
sci_float_zero_padded_1=6.02e23
sci_float_zero_padded_2=-0.0789e-23
sci_float_zero_padded_3=6.02e23
sci_float_zero_padded_4=-0.0789e-23
struct=1,1.0e-5,(3.14,2.72)
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
