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
# Test "rose macro" in built-in compulsory checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:compulsory_nl1]
my_var1=235

[namelist:compulsory_nl2]
my_var2=235

[namelist:compulsory_nl3]

[namelist:compulsory_nl4(1)]
my_var3(1)=.true.
my_var4=.true.

[namelist:compulsory_nl4(2)]
my_var3(1)=.true.
my_var4=.true.

[namelist:compulsory_nl5]
my_var5(1)=.true.
!my_var5.5=.true.

[namelist:compulsory_nl6{modifier}(1)]
my_var6(2)=.true.
my_var7=.true.

[namelist:compulsory_nl7{modifier}]
my_var8(2)=.true.
my_var9=.true.
__CONFIG__
#-------------------------------------------------------------------------------
tests 18
#-------------------------------------------------------------------------------
# Check compulsory checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init_meta <<__META_CONFIG__
[namelist:compulsory_nl1=my_var1]
compulsory=true

[namelist:compulsory_nl2]
compulsory=true

[namelist:compulsory_nl2=my_var2]
compulsory=true

[namelist:compulsory_nl3]
compulsory=true

[namelist:compulsory_nl4]
compulsory=true
duplicate=true

[namelist:compulsory_nl4=my_var3]
compulsory=true

[namelist:compulsory_nl4=my_var4]
compulsory=true

[namelist:compulsory_nl5=my_var5]
compulsory=true

[namelist:compulsory_nl5=my_var5.5]

[namelist:compulsory_nl6]
compulsory=true
duplicate=true

[namelist:compulsory_nl6{modifier}]
duplicate=true

[namelist:compulsory_nl6=my_var6]
compulsory=true

[namelist:compulsory_nl6=my_var7]
compulsory=true

[namelist:compulsory_nl7]
duplicate=true

[namelist:compulsory_nl7=my_var8]
compulsory=true

[namelist:compulsory_nl7=my_var9]
compulsory=true
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check user-ignored checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<'__CONFIG__'
[namelist:compulsory_nl1]
my_var1=235

[namelist:compulsory_nl2]
!my_var2=235

[namelist:compulsory_nl3]

[namelist:compulsory_nl4(1)]
my_var3(1)=.true.
!my_var4=.true.

[namelist:compulsory_nl4(2)]
my_var3(1)=.true.
my_var4=.true.

[namelist:compulsory_nl4(3)]
my_var3(1)=.true.
!my_var4=.true.

[namelist:compulsory_nl5]
my_var5(1)=.true.
!my_var5.5=.true.

[namelist:compulsory_nl6{modifier}(1)]
!my_var6(2)=.true.
my_var7=.true.

[namelist:compulsory_nl6{modifier}(2)]
!my_var6(2)=.true.
my_var7=.true.

[namelist:compulsory_nl7{modifier}]
my_var8(2)=.true.
my_var9=.true.
__CONFIG__
init_meta <<__META_CONFIG__
[namelist:compulsory_nl1=my_var1]
compulsory=true

[namelist:compulsory_nl2]
compulsory=true

[namelist:compulsory_nl2=my_var2]
compulsory=true

[namelist:compulsory_nl3]
compulsory=true

[namelist:compulsory_nl4]
compulsory=true
duplicate=true

[namelist:compulsory_nl4=my_var3]
compulsory=true

[namelist:compulsory_nl4=my_var4]
compulsory=true

[namelist:compulsory_nl5=my_var5]
compulsory=true

[namelist:compulsory_nl6]
compulsory=true
duplicate=true

[namelist:compulsory_nl6{modifier}]
duplicate=true

[namelist:compulsory_nl6=my_var6]
compulsory=true

[namelist:compulsory_nl6=my_var7]
compulsory=true

[namelist:compulsory_nl7]
duplicate=true

[namelist:compulsory_nl7=my_var8]
compulsory=true

[namelist:compulsory_nl7=my_var9]
compulsory=true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 5
    namelist:compulsory_nl2=my_var2=235
        Compulsory settings should not be user-ignored.
    namelist:compulsory_nl4(1)=my_var4=.true.
        Compulsory settings should not be user-ignored.
    namelist:compulsory_nl4(3)=my_var4=.true.
        Compulsory settings should not be user-ignored.
    namelist:compulsory_nl6{modifier}(1)=my_var6(2)=.true.
        Compulsory settings should not be user-ignored.
    namelist:compulsory_nl6{modifier}(2)=my_var6(2)=.true.
        Compulsory settings should not be user-ignored.
__ERR__
teardown
#-------------------------------------------------------------------------------
# Check compulsory checking.
TEST_KEY=$TEST_KEY_BASE-err
setup
init <<__CONFIG__
[namelist:compulsory_nl4(1)]

[namelist:compulsory_nl4(2)]

[namelist:compulsory_nl5]
!my_var5=true
__CONFIG__
init_meta <<__META_CONFIG__
[namelist:compulsory_nl1=my_var1]
compulsory=true

[namelist:compulsory_nl2]
compulsory=true

[namelist:compulsory_nl2=my_var2]
compulsory=true

[namelist:compulsory_nl3]
compulsory=true

[namelist:compulsory_nl4]
duplicate=true

[namelist:compulsory_nl4=my_var4]
compulsory=true

[namelist:compulsory_nl5=my_var5]
compulsory=true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 5
    namelist:compulsory_nl2=None=None
        Section set as compulsory, but not in configuration.
    namelist:compulsory_nl3=None=None
        Section set as compulsory, but not in configuration.
    namelist:compulsory_nl4(1)=my_var4=None
        Variable set as compulsory, but not in configuration.
    namelist:compulsory_nl4(2)=my_var4=None
        Variable set as compulsory, but not in configuration.
    namelist:compulsory_nl5=my_var5=true
        Compulsory settings should not be user-ignored.
__ERR__
teardown
#-------------------------------------------------------------------------------
# Check compulsory fixing.
TEST_KEY=$TEST_KEY_BASE-fixing-check
setup
init <<__CONFIG__
[compulsory_section]
compulsory_present_and_ok=true
optional_present_and_ok=true

[compulsory_section_dups(1)]
compulsory_present_and_ok=true
optional_present_and_ok=true

[compulsory_section_dups(2)]
compulsory_present_and_ok=true
optional_present_and_ok=true

[compulsory_section_dups{bar}]
compulsory_present_and_ok=true
optional_present_and_ok=true

[compulsory_section_dups{foo}(1)]
compulsory_present_and_ok=true
optional_present_and_ok=true

[env]
compulsory_present_and_ok=true
optional_present_and_ok=true

[optional_section_dups(1)]
__CONFIG__
init_meta <<__META_CONFIG__
[compulsory_duplicate_section_missing]
compulsory=true
duplicate=true

[compulsory_duplicate_section_missing=compulsory_missing_and_err]
compulsory=true
type=boolean

[compulsory_duplicate_section_missing=compulsory_present_and_ok]
compulsory=true
type=boolean

[compulsory_duplicate_section_missing=optional_missing_and_ok]
type=boolean

[compulsory_duplicate_section_missing=optional_present_and_ok]
type=boolean

[compulsory_duplicate_section_missing_empty]
compulsory=true
duplicate=true

[compulsory_section]
compulsory=true

[compulsory_section=compulsory_missing_and_err_1]
compulsory=true
type=boolean

[compulsory_section=compulsory_missing_and_err_2]
compulsory=true
type=boolean

[compulsory_section=compulsory_present_and_ok]
compulsory=true
trigger=compulsory_section=compulsory_triggered_ignored_missing_and_err: false;
type=boolean

[compulsory_section=compulsory_triggered_ignored_missing_and_err]
compulsory=true
type=boolean

[compulsory_section=optional_missing_and_ok]
type=boolean

[compulsory_section=optional_present_and_ok]
type=boolean

[compulsory_section_dups]
compulsory=true
duplicate=true

[compulsory_section_dups=compulsory_missing_and_err_1]
compulsory=true
type=boolean

[compulsory_section_dups=compulsory_missing_and_err_2]
compulsory=true
type=boolean

[compulsory_section_dups=compulsory_present_and_ok]
compulsory=true
type=boolean

[compulsory_section_dups=optional_missing_and_ok]
type=boolean

[compulsory_section_dups=optional_present_and_ok]
type=boolean

[compulsory_section_dups{foo}]
duplicate=true

[compulsory_section_missing]
compulsory=true

[compulsory_section_missing=compulsory_missing_and_err]
compulsory=true
type=boolean

[compulsory_section_missing=compulsory_present_and_ok]
compulsory=true
type=boolean

[compulsory_section_missing=optional_missing_and_ok]
type=boolean

[compulsory_section_missing=optional_present_and_ok]
type=boolean

[compulsory_section_missing_empty]
compulsory=true

[env]
compulsory=true

[env=compulsory_missing_and_err]
compulsory=true
type=boolean

[env=compulsory_present_and_ok]
compulsory=true
type=boolean

[env=optional_missing_and_ok]
type=boolean

[env=optional_present_and_ok]
type=boolean

[optional_section_dups]
duplicate=true

[optional_section_dups{compulsory}]
compulsory=true

[optional_section_dups{compulsory}=compulsory_missing_and_err]
compulsory=true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro -V --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 17
    compulsory_duplicate_section_missing(1)=None=None
        Section set as compulsory, but not in configuration.
    compulsory_duplicate_section_missing_empty(1)=None=None
        Section set as compulsory, but not in configuration.
    compulsory_section=compulsory_missing_and_err_1=None
        Variable set as compulsory, but not in configuration.
    compulsory_section=compulsory_missing_and_err_2=None
        Variable set as compulsory, but not in configuration.
    compulsory_section=compulsory_triggered_ignored_missing_and_err=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups(1)=compulsory_missing_and_err_1=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups(1)=compulsory_missing_and_err_2=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups(2)=compulsory_missing_and_err_1=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups(2)=compulsory_missing_and_err_2=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups{bar}=compulsory_missing_and_err_1=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups{bar}=compulsory_missing_and_err_2=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups{foo}(1)=compulsory_missing_and_err_1=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_dups{foo}(1)=compulsory_missing_and_err_2=None
        Variable set as compulsory, but not in configuration.
    compulsory_section_missing=None=None
        Section set as compulsory, but not in configuration.
    compulsory_section_missing_empty=None=None
        Section set as compulsory, but not in configuration.
    env=compulsory_missing_and_err=None
        Variable set as compulsory, but not in configuration.
    optional_section_dups{compulsory}=None=None
        Section set as compulsory, but not in configuration.
__ERR__
TEST_KEY=$TEST_KEY_BASE-fixing
run_pass "$TEST_KEY" rose macro --fix --config=../config --non-interactive
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] rose.macros.DefaultTransforms: changes: 23
    compulsory_duplicate_section_missing(1)=None=None
        Added compulsory section
    compulsory_duplicate_section_missing(1)=compulsory_missing_and_err=false
        Added compulsory option
    compulsory_duplicate_section_missing(1)=compulsory_present_and_ok=false
        Added compulsory option
    compulsory_duplicate_section_missing_empty(1)=None=None
        Added compulsory section
    compulsory_section=compulsory_missing_and_err_1=false
        Added compulsory option
    compulsory_section=compulsory_missing_and_err_2=false
        Added compulsory option
    compulsory_section=compulsory_triggered_ignored_missing_and_err=false
        Added compulsory option
    compulsory_section_dups(1)=compulsory_missing_and_err_1=false
        Added compulsory option
    compulsory_section_dups(1)=compulsory_missing_and_err_2=false
        Added compulsory option
    compulsory_section_dups(2)=compulsory_missing_and_err_1=false
        Added compulsory option
    compulsory_section_dups(2)=compulsory_missing_and_err_2=false
        Added compulsory option
    compulsory_section_dups{bar}=compulsory_missing_and_err_1=false
        Added compulsory option
    compulsory_section_dups{bar}=compulsory_missing_and_err_2=false
        Added compulsory option
    compulsory_section_dups{foo}(1)=compulsory_missing_and_err_1=false
        Added compulsory option
    compulsory_section_dups{foo}(1)=compulsory_missing_and_err_2=false
        Added compulsory option
    compulsory_section_missing=None=None
        Added compulsory section
    compulsory_section_missing=compulsory_missing_and_err=false
        Added compulsory option
    compulsory_section_missing=compulsory_present_and_ok=false
        Added compulsory option
    compulsory_section_missing_empty=None=None
        Added compulsory section
    env=compulsory_missing_and_err=false
        Added compulsory option
    optional_section_dups{compulsory}=None=None
        Added compulsory section
    optional_section_dups{compulsory}=compulsory_missing_and_err=
        Added compulsory option
    compulsory_section=compulsory_triggered_ignored_missing_and_err=false
        enabled      -> trig-ignored
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-----------------------------------------------------------------------------
init <<'__CONFIG__'
[!namelist:icecream(1)]
sprinkles=true
__CONFIG__
init_meta <<'__META_CONFIG__'
[namelist:icecream]
duplicate=true

[namelist:icecream=sprinkles]
compulsory=true
type=boolean
__META_CONFIG__
TEST_KEY=$TEST_KEY_BASE-user-ignore-duplicate
run_pass "$TEST_KEY" rose macro -V --config=../config --non-interactive
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
