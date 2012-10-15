#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
# Test "rose macro" in built-in compulsory checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:compulsory_nl1]
my_var1 = 235

[namelist:compulsory_nl2]
my_var2 = 235

[namelist:compulsory_nl3]

[namelist:compulsory_nl4(1)]
my_var3(1) = .true.
my_var4 = .true.

[namelist:compulsory_nl5]
my_var5(1) = .true.

[namelist:compulsory_nl6{modifier}(1)]
my_var6(2) = .true.
my_var7 = .true.

[namelist:compulsory_nl7{modifier}]
my_var8(2) = .true.
my_var9 = .true.
__CONFIG__
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check compulsory checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init_meta <<__META_CONFIG__
[namelist:compulsory_nl1=my_var1]
compulsory = true

[namelist:compulsory_nl2]
compulsory = true

[namelist:compulsory_nl2=my_var2]
compulsory = true

[namelist:compulsory_nl3]
compulsory = true

[namelist:compulsory_nl4]
compulsory = true
duplicate = true

[namelist:compulsory_nl4=my_var3]
compulsory = true

[namelist:compulsory_nl4=my_var4]
compulsory = true

[namelist:compulsory_nl5=my_var5]
compulsory = true

[namelist:compulsory_nl6]
compulsory = true
duplicate = true

[namelist:compulsory_nl6=my_var6]
compulsory = true

[namelist:compulsory_nl6=my_var7]
compulsory = true

[namelist:compulsory_nl7]
duplicate = true

[namelist:compulsory_nl7=my_var8]
compulsory = true

[namelist:compulsory_nl7=my_var9]
compulsory = true
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check compulsory checking.
TEST_KEY=$TEST_KEY_BASE-err
setup
init <<__CONFIG__
[namelist:compulsory_nl4]

[namelist:compulsory_nl5]
!my_var5 = true
__CONFIG__
init_meta <<__META_CONFIG__
[namelist:compulsory_nl1=my_var1]
compulsory = true

[namelist:compulsory_nl2]
compulsory = true

[namelist:compulsory_nl2=my_var2]
compulsory = true

[namelist:compulsory_nl3]
compulsory = true

[namelist:compulsory_nl4=my_var4]
compulsory = true

[namelist:compulsory_nl5=my_var5]
compulsory = true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 6
    namelist:compulsory_nl1=my_var1=None
        Variable set as compulsory, but not in configuration.
    namelist:compulsory_nl2=None=None
        Section set as compulsory, but not in configuration.
    namelist:compulsory_nl2=my_var2=None
        Variable set as compulsory, but not in configuration.
    namelist:compulsory_nl3=None=None
        Section set as compulsory, but not in configuration.
    namelist:compulsory_nl4=my_var4=None
        Variable set as compulsory, but not in configuration.
    namelist:compulsory_nl5=my_var5=true
        Compulsory settings should not be user-ignored.
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
