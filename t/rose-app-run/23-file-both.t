#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
# Test "rose app-run" file install, with both [file:NAME] and "file/NAME".
# The [file:NAME]source=SOURCE should override.
. $(dirname $0)/test_header

test_init <<__CONFIG__
[command]
default=true

[file:whatever.txt]
source=${TEST_DIR}/etc/whatever.txt
__CONFIG__

mkdir "${TEST_DIR}/config/file" "${TEST_DIR}/etc"
echo "I don't care!" >"${TEST_DIR}/config/file/whatever.txt"
echo 'Whatever!' >"${TEST_DIR}/etc/whatever.txt"

#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
test_setup
run_pass "${TEST_KEY}" rose app-run --config='../config'
sed -n '/\[INFO\] \(install\|    source\)/p;' "${TEST_KEY}.out" \
    >"${TEST_KEY}.out.edited"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out.edited" <<__OUT__
[INFO] install: whatever.txt
[INFO]     source: ${TEST_DIR}/etc/whatever.txt
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
file_cmp "${TEST_KEY}-whatever.txt" 'whatever.txt' <<<'Whatever!'
test_teardown
#-------------------------------------------------------------------------------
exit
