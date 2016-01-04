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
tests 18
#-------------------------------------------------------------------------------
# Check trigger syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
[namelist:near_cyclic_namelist=switch]
type=logical
trigger=namelist:near_cyclic_namelist=a: this == ".true."

[namelist:near_cyclic_namelist=a]
trigger=namelist:near_cyclic_namelist=b;
        namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger=namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger=namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger=namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger=namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=f]

[namelist:dupl_nl]
duplicate=true
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - missing trigger in metadata.
TEST_KEY=$TEST_KEY_BASE-err-missing
setup
init <<'__META_CONFIG__'
[namelist:near_cyclic_namelist=switch]
type=logical
trigger=namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger=namelist:near_cyclic_namelist=b;
        namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger=namelist:near_cyclic_namelist=c;
          namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger=namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger=namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger=namelist:near_cyclic_namelist=f

[namelist:dupl_nl]
duplicate=true
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:near_cyclic_namelist=f=None=None
        No metadata entry found
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - cyclic dependency.
TEST_KEY=$TEST_KEY_BASE-err-cyclic
setup
init <<'__META_CONFIG__'
[namelist:near_cyclic_namelist=switch]
type=logical
trigger=namelist:near_cyclic_namelist=a: .true.

[namelist:near_cyclic_namelist=a]
trigger=namelist:near_cyclic_namelist=b;
        namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger=namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger=namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
trigger=namelist:near_cyclic_namelist=e; namelist:near_cyclic_namelist=f

[namelist:near_cyclic_namelist=e]
trigger=namelist:near_cyclic_namelist=f; namelist:near_cyclic_namelist=switch

[namelist:near_cyclic_namelist=f]

[namelist:dupl_nl]
duplicate=true
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:near_cyclic_namelist=switch=trigger=namelist:near_cyclic_namelist=a: .true.
        Cyclic dependency detected: namelist:near_cyclic_namelist=a to namelist:near_cyclic_namelist=switch
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check trigger checking - duplicate namelist external triggers.
TEST_KEY=$TEST_KEY_BASE-err-dupl-external
setup
init <<'__META_CONFIG__'
[namelist:dupl_nl]
duplicate=true

[namelist:dupl_nl=a]
trigger=namelist:subject_nl=atrig: .true.
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:dupl_nl=a=trigger=namelist:subject_nl=atrig: .true.
        Badly defined trigger - namelist:dupl_nl is 'duplicate'
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check trigger syntax checking.
TEST_KEY=$TEST_KEY_BASE-err-syntax-1
setup
init <<__META_CONFIG__
[namelist:near_cyclic_namelist=a]
trigger=namelist:near_cyclic_namelist=b something;
        namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger=namelist:near_cyclic_namelist=c
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger=namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:near_cyclic_namelist=b something=None=None
        No metadata entry found
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check trigger syntax checking.
TEST_KEY=$TEST_KEY_BASE-err-syntax-2
setup
init <<__META_CONFIG__
[namelist:near_cyclic_namelist=a]
trigger=namelist:near_cyclic_namelist=b;
        namelist:near_cyclic_namelist=c;
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=b]
trigger=namelist:near_cyclic_namelist=c
        namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=c]
trigger=;namelist:near_cyclic_namelist=d

[namelist:near_cyclic_namelist=d]
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    =trigger=None
        No metadata entry found
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
