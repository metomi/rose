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
# Test "rose app-run", file installation, source=(SOURCE) syntax.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=14
tests $N_TESTS
#-------------------------------------------------------------------------------
test_init <<__CONFIG__
[command]
default=true

# (Missing)
[file:hello0.nl]
source=(namelist:hello0)

# (Missing) (Exist)
[file:hello01.nl]
source=(namelist:hello0) (namelist:hello1)

# (Missing) Exist
[file:hello02.nl]
source=(namelist:hello0) namelist:hello2

# (Exist)
[file:hello1.nl]
source=(namelist:hello1)

# Exist (Exist)
[file:hello21.nl]
source=namelist:hello2 (namelist:hello1)

# (FS-Missing)
[file:foo0.txt]
source=($TEST_DIR/foolish.txt)

# (FS-Exist)
[file:foo1.txt]
source=($TEST_DIR/foot.txt)

# (FS-Missing) (FS-Exist)
[file:foo01.txt]
source=($TEST_DIR/foolish.txt) ($TEST_DIR/foot.txt)

# FS-Exist (FS-Exist)
[file:foo21.txt]
source=$TEST_DIR/food.txt ($TEST_DIR/foot.txt)

# (SVN-Missing)
[file:sub0.txt]
source=(file://$TEST_DIR/repos/submerged.txt)

# (SVN-Exist)
[file:sub1.txt]
source=(file://$TEST_DIR/repos/submarine.txt)

[namelist:hello1]
world='Earth'

[namelist:hello2]
world='Mars'
__CONFIG__

echo 'Food cupboard is full.' >food.txt
echo 'Oh my foot!' >foot.txt
svnadmin create $TEST_DIR/repos
echo 'I can see the periscope.' >submarine.txt
svn import -q -m 'submarine.txt: new file' submarine.txt \
    file://$TEST_DIR/repos/submarine.txt
rm submarine.txt
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY-hello0.nl" "hello0.nl" </dev/null
file_cmp "$TEST_KEY-hello01.nl" "hello01.nl" <<'__NL__'
&hello1
world='Earth',
/
__NL__
file_cmp "$TEST_KEY-hello02.nl" "hello02.nl" <<'__NL__'
&hello2
world='Mars',
/
__NL__
file_cmp "$TEST_KEY-hello1.nl" "hello1.nl" <<'__NL__'
&hello1
world='Earth',
/
__NL__
file_cmp "$TEST_KEY-hello21.nl" "hello21.nl" <<'__NL__'
&hello2
world='Mars',
/
&hello1
world='Earth',
/
__NL__
file_cmp "$TEST_KEY-foo0.txt" "foo0.txt" </dev/null
file_cmp "$TEST_KEY-foo01.txt" "foo01.txt" <<'__TXT__'
Oh my foot!
__TXT__
file_cmp "$TEST_KEY-foo1.txt" "foo1.txt" <<'__TXT__'
Oh my foot!
__TXT__
file_cmp "$TEST_KEY-foo21.txt" "foo21.txt" <<'__TXT__'
Food cupboard is full.
Oh my foot!
__TXT__
file_cmp "$TEST_KEY-sub0.txt" "sub0.txt" </dev/null
file_cmp "$TEST_KEY-sub1.txt" "sub1.txt" <<'__TXT__'
I can see the periscope.
__TXT__
ls -l hello*.nl foo*.txt sub*.txt | LANG=C sort >"$TEST_KEY-ls-l-before"
run_pass "$TEST_KEY" rose app-run --config=../config -q
ls -l hello*.nl foo*.txt sub*.txt | LANG=C sort >"$TEST_KEY-ls-l-after"
file_cmp "$TEST_KEY-ls-l" "$TEST_KEY-ls-l-before" "$TEST_KEY-ls-l-after"
test_teardown
#-------------------------------------------------------------------------------
exit
