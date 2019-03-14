#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# Check pattern syntax checking.
TEST_KEY=$TEST_KEY_BASE-ok
setup
init <<__META_CONFIG__
[namelist:values_nl1=my_array]
length=:
pattern = ^(\d*,\s*)*\d*$

[namelist:values_nl1=my_char]
pattern =^'.*'(?#Anything in quotes is acceptable)$

[namelist:values_nl1=my_date]
pattern =^\d\d/\d\d/\d\d\s\d\d:\d\d:\d\d$

[namelist:values_nl1=my_int]
pattern =^\d+$

[namelist:values_nl1=my_nocase]
pattern= (?i)^camelcase$

[namelist:values_nl1=my_raw]
pattern = ^[A-Z][\w\s,]+\.$

[namelist:values_nl1=my_raw_ends]
pattern = orange$
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
[namelist:values_nl1=my_array]
length=:
pattern = (?} oo){1,-9}(\d*,{\s*)*\d*$

[namelist:values_nl1=my_char]
pattern =+'.*'$

[namelist:values_nl1=my_int]
pattern =^\d+(?& \e)

[namelist:values_nl1=my_nocase]
pattern= (?i see a silhouette)^camelcase$

[namelist:values_nl1=my_raw]
pattern = ^[A->>Z\][\w\s,]+\.$
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 5
    namelist:values_nl1=my_array=pattern=(?} oo){1,-9}(\d*,{\s*)*\d*$
        Invalid syntax: error: unknown extension ?} at position 1
    namelist:values_nl1=my_char=pattern=+'.*'$
        Invalid syntax: error: nothing to repeat at position 0
    namelist:values_nl1=my_int=pattern=^\d+(?& \e)
        Invalid syntax: error: unknown extension ?& at position 5
    namelist:values_nl1=my_nocase=pattern=(?i see a silhouette)^camelcase$
        Invalid syntax: error: missing -, : or ) at position 3
    namelist:values_nl1=my_raw=pattern=^[A->>Z\][\w\s,]+\.$
        Invalid syntax: error: bad character range A-> at position 2
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
