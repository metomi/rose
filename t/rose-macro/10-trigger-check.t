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
# Test "rose macro" in built-in trigger checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[namelist:near_cyclic_namelist]
switch = .false.
!!a = 2
!!b = 2
!!c = 2
!!d = 2
!!e = 2
!!f = 2

[namelist:dupl_nl(1)]
a = .true.

[namelist:subject_nl]
atrig = 2
btrig = 3
__CONFIG__
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Check trigger checking - this is nearly cyclic but should be fine.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init_meta <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger = namelist:near_cyclic_namelist=b;
          namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger = namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger = namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger = namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger = namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=f]

[namelist:dupl_nl]
duplicate = true
__META_CONFIG__
run_pass "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - missing trigger in metadata.
TEST_KEY=$TEST_KEY_BASE-value-trigger-err-cyclic
setup
init_meta <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger = namelist:near_cyclic_namelist=b;
          namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger = namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger = namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger = namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger = namelist:near_cyclic_namelist=f

[namelist:dupl_nl]
duplicate = true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 1
    namelist:near_cyclic_namelist=f=2
        No metadata entry found
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - cyclic dependency.
TEST_KEY=$TEST_KEY_BASE-err-cyclic
setup
init_meta <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type = logical
trigger = namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger = namelist:near_cyclic_namelist=b;
          namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger = namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger = namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger = namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger = namelist:near_cyclic_namelist=f; namelist:near_cyclic_namelist=switch

[namelist:near_cyclic_namelist=f]

[namelist:dupl_nl]
duplicate = true
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 1
    namelist:near_cyclic_namelist=switch=.false.
        Cyclic dependency detected: namelist:near_cyclic_namelist=a to namelist:near_cyclic_namelist=switch
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - duplicate namelist external triggers.
TEST_KEY=$TEST_KEY_BASE-err-dupl-external
setup
init_meta <<__META_CONFIG__
[namelist:dupl_nl]
duplicate = true

[namelist:dupl_nl=a]
trigger = namelist:subject_nl=atrig: .true.
__META_CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[V] rose.macros.DefaultValidators: issues: 1
    namelist:dupl_nl=a=None
        Badly defined trigger - namelist:dupl_nl is 'duplicate'
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
