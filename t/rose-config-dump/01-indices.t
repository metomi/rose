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
# Test "rose config-dump".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
# Mixed string-integer section indices.
TEST_KEY=$TEST_KEY_BASE-sort-indices
setup
cat > f1 <<'__CONF__'
[namelist:foo(1)]
baz=1

[namelist:foo(5)]
baz=5

[namelist:foo(10)]
baz=10

[namelist:foo(50)]
baz=50

[namelist:foo(10abc)]
baz=10abc

[namelist:foo(1abc)]
baz=1abc

[namelist:foo(5abc)]
baz=5abc

[namelist:foo(5xyz)]
baz=5xyz

[namelist:foo(abc)]
baz=abc

[namelist:foo(abcd)]
baz=abcd

[namelist:foo(xyz)]
baz=xyz

[namelist:spam(1)]

[namelist:spam(5)]

[namelist:spam(6)]

[namelist:spam(10)]

[namelist:spam(50)]

[namelist:spam(51)]
__CONF__
cp f1 rose-app.conf
run_pass "$TEST_KEY" rose config-dump
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.f1" f1 rose-app.conf
teardown
#-------------------------------------------------------------------------------
exit 0
