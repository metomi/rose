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
# Test "rose namelist-dump" with empty namelist input.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# Empty namelist standard input, standard output.
TEST_KEY=$TEST_KEY_BASE
setup
run_pass "$TEST_KEY" rose namelist-dump <<'__CONTENT__'
&name /
__CONTENT__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[file:STDIN]
source=namelist:name

[namelist:name]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty namelist standard input, standard output, -u.
TEST_KEY=$TEST_KEY_BASE-u
setup
run_pass "$TEST_KEY" rose namelist-dump -u <<'__CONTENT__'
&name /
__CONTENT__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[file:STDIN]
source=namelist:NAME

[namelist:NAME]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty namelist standard input, standard output, -l.
TEST_KEY=$TEST_KEY_BASE-l
setup
run_pass "$TEST_KEY" rose namelist-dump -l <<'__CONTENT__'
&Name /
__CONTENT__
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[file:STDIN]
source=namelist:name

[namelist:name]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty namelists (x10) standard input, standard output.
TEST_KEY=$TEST_KEY_BASE-namelists
setup
run_pass "$TEST_KEY" rose namelist-dump -l <<'__CONTENT__'
&Name / &Name / &Name / &Name / &Name / &Name / &Name / &Name / &Name / &Name /
__CONTENT__
CONTENT=
SPACE=
for i in $(seq 1 10); do
    CONTENT="${CONTENT}${SPACE}namelist:name($i)"
    SPACE=' '
done
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[file:STDIN]
source=$CONTENT

[namelist:name(1)]

[namelist:name(2)]

[namelist:name(3)]

[namelist:name(4)]

[namelist:name(5)]

[namelist:name(6)]

[namelist:name(7)]

[namelist:name(8)]

[namelist:name(9)]

[namelist:name(10)]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Empty namelists in multiple files, standard output.
TEST_KEY=$TEST_KEY_BASE-multi
setup
cat >file1 <<'__CONTENT__'
&name1 /
&name1 /
&name2 /
&name3 /
&name4 /
__CONTENT__
cat >file2 <<'__CONTENT__'
&name2 /
&name3 /
&name2 /
__CONTENT__
run_pass "$TEST_KEY" rose namelist-dump file1 file2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__CONTENT__
[file:file1]
source=namelist:name1(1) namelist:name1(2) namelist:name2(1) namelist:name3(1) namelist:name4

[file:file2]
source=namelist:name2(2) namelist:name3(2) namelist:name2(3)

[namelist:name1(1)]

[namelist:name1(2)]

[namelist:name2(1)]

[namelist:name2(2)]

[namelist:name2(3)]

[namelist:name3(1)]

[namelist:name3(2)]

[namelist:name4]
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
