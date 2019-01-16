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
# Test "rose.variable" > "array_split".
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
tests 22

if [[ -n "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="${TEST_SOURCE_DIR}:${PYTHONPATH}"
else
    export PYTHONPATH="${TEST_SOURCE_DIR}"
fi
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-0"
run_pass "${TEST_KEY}" python3 -m 't_array_split' ''
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<'[]'
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-0-space"
run_pass "${TEST_KEY}" python3 -m 't_array_split' '    '
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<'[]'
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-1"
run_pass "${TEST_KEY}" python3 -m 't_array_split' 'foo'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-1-space"
run_pass "${TEST_KEY}" python3 -m 't_array_split' '  foo     '
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-2-null"
run_pass "${TEST_KEY}" python3 -m 't_array_split' 'foo,'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo', '']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-2-escape"
run_pass "${TEST_KEY}" python3 -m 't_array_split' 'foo\,bar, baz'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo\\\\,bar', 'baz']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-2-escape-remove"
run_pass "${TEST_KEY}" python3 -m 't_array_split' 'foo\,bar, baz' ',' 1
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo,bar', 'baz']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-3"
run_pass "${TEST_KEY}" python3 -m 't_array_split' 'foo,bar,baz'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo', 'bar', 'baz']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-3-space"
run_pass "${TEST_KEY}" python3 -m 't_array_split' '  foo, bar, baz'
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo', 'bar', 'baz']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-3-only-delim-is-comma"
run_pass "${TEST_KEY}" python3 -m 't_array_split' 'foo, bar, baz' ','
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<<"['foo', 'bar', 'baz']"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-4-complex"
run_pass "${TEST_KEY}" python3 -m 't_array_split' \
    " \"rose's fault\", \"no, it isn't\", 'yes, it is', whatever"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
['"rose\'s fault"', '"no, it isn\'t"', "'yes, it is'", 'whatever']
__OUT__
#-------------------------------------------------------------------------------
exit
