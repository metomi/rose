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
# Check compulsory syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
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
run_pass "$TEST_KEY" rose metadata-check -v -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] Configurations OK
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check compulsory syntax checking (fail).
TEST_KEY=$TEST_KEY_BASE-bad
setup
init <<__META_CONFIG__
[namelist:compulsory_nl1=my_var1]
compulsory=.true.

[namelist:compulsory_nl2]
compulsory=false

[namelist:compulsory_nl6=my_var6]
compulsory=duplicate

[namelist:compulsory_nl6=my_var7]
compulsory=1

[namelist:compulsory_nl7=my_var8]
compulsory=?
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 4
    namelist:compulsory_nl1=my_var1=compulsory=.true.
        Invalid syntax: .true.
    namelist:compulsory_nl6=my_var6=compulsory=duplicate
        Invalid syntax: duplicate
    namelist:compulsory_nl6=my_var7=compulsory=1
        Invalid syntax: 1
    namelist:compulsory_nl7=my_var8=compulsory=?
        Invalid syntax: ?
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
