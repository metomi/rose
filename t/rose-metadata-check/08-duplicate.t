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
# Check duplicate syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
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
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check duplicate syntax checking (fail).
TEST_KEY=$TEST_KEY_BASE-bad
setup
init <<__META_CONFIG__
[namelist:duplicate_nl1=my_var1]
duplicate=.true.

[namelist:duplicate_nl2]
duplicate=false

[namelist:duplicate_nl6=my_var6]
duplicate=duplicate

[namelist:duplicate_nl6=my_var7]
duplicate=1

[namelist:duplicate_nl7=my_var8]
duplicate=?
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 4
    namelist:duplicate_nl1=my_var1=duplicate=.true.
        Invalid syntax: .true.
    namelist:duplicate_nl6=my_var6=duplicate=duplicate
        Invalid syntax: duplicate
    namelist:duplicate_nl6=my_var7=duplicate=1
        Invalid syntax: 1
    namelist:duplicate_nl7=my_var8=duplicate=?
        Invalid syntax: ?
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
