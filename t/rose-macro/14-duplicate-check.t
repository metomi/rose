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
# Test "rose macro" in built-in duplicate checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:nl1]
my_var1 = 235

[namelist:nl2(1)]
my_var3(1) = .true.
my_var4 = .true.

[namelist:nl3{modifier}]
my_var5(1) = .true.

[namelist:nl4{modifier}(1)]
my_var6(2) = .true.
my_var7 = .true.


__CONFIG__
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check duplicate checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init_meta <<__META_CONFIG__

[namelist:nl2]
duplicate = true

[namelist:nl3]
duplicate = true

[namelist:nl3{modifier}]
duplicate = true

[namelist:nl4]
duplicate = true

[namelist:nl4{modifier}]
duplicate = true
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check duplicate checking.
TEST_KEY=$TEST_KEY_BASE-err
setup
init_meta <<__META_CONFIG__
[namelist:nl1]
duplicate = true

[namelist:nl2]

[namelist:nl3=foo]
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] rose.macros.DefaultValidators: issues: 3
    namelist:nl1=None=None
        incorrect "duplicate=true" metadata
    namelist:nl2(1)=None=None
        namelist:nl2 requires "duplicate=true" metadata
    namelist:nl3{modifier}=None=None
        namelist:nl3 requires "duplicate=true" metadata
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
