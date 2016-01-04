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
# Test "rose namelist-dump" with null input.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 14
#-------------------------------------------------------------------------------
# Null standard input, standard output.
TEST_KEY=$TEST_KEY_BASE
setup
run_pass "$TEST_KEY" rose namelist-dump </dev/null
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[file:STDIN]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Null standard input, file output.
TEST_KEY=$TEST_KEY_BASE-o
setup
run_pass "$TEST_KEY" rose namelist-dump -o "$TEST_KEY.file" </dev/null
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" "$TEST_KEY.file" <<'__CONTENT__'
[file:STDIN]
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Null file input, file output.
TEST_KEY=$TEST_KEY_BASE-o-file
setup
cat </dev/null >"$TEST_KEY.nl"
run_pass "$TEST_KEY" rose namelist-dump -o "$TEST_KEY.file" "$TEST_KEY.nl"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" "$TEST_KEY.file" <<__CONTENT__
[file:$TEST_KEY.nl]
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Null file input and null standard input, standard output.
TEST_KEY=$TEST_KEY_BASE-o-file-stdin
setup
cat </dev/null >"$TEST_KEY.nl"
run_pass "$TEST_KEY" rose namelist-dump - "$TEST_KEY.nl" </dev/null
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[file:$TEST_KEY.nl]

[file:STDIN]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
