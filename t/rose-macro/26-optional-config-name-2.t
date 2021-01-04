#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# Test that custom parameter is prompted once for transformer macro.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

tests 2

setup
init <<'__CONFIG__'
[env]
MY_VALUE=who cares
__CONFIG__
init_meta <'/dev/null'
init_opt 'baseeight' <<'__OPT_CONFIG__'
[env]
HELLO=world
__OPT_CONFIG__

init_macro 'custom_macro_change_arg.py' \
    <"${TEST_SOURCE_DIR}/lib/custom_macro_change_arg.py"

TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" \
    rose macro --config='../config' \
    'custom_macro_change_arg.ArgumentTransformer' < <(echo '"whatever"'; yes)
sed -i '$d' "${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
Value for myvalue (default None): [T] custom_macro_change_arg.ArgumentTransformer: changes: 1
    env=MY_VALUE=who cares
        who cares -> whatever
__OUT__
teardown
exit
