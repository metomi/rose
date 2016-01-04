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
# Test "rose app-run", generation of files in incremental mode (1).
# Switch off symlink mode in a target.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
mkdir -p $TEST_DIR/man/man{1,2,3}
SOURCE1=$TEST_DIR/man/man1/burger.1
echo "yummy" >$SOURCE1
DIR2=$TEST_DIR/man/man2
DIR3=$TEST_DIR/man/man3
echo "cook a yummy burger" >$DIR2/burger_cook.2
echo "cook a yummy chilli burger" >$DIR3/burger_cook_f.3
test_init <<__CONFIG__
[command]
default=true

[file:man/man1/burger.1]
source=$SOURCE1
mode=symlink

[file:man/man2]
source=$DIR2
mode=symlink

[file:man/man3]
source=$DIR3
mode=symlink
__CONFIG__
#-------------------------------------------------------------------------------
tests 7
#-------------------------------------------------------------------------------
# Remove symlink mode
TEST_KEY=$TEST_KEY_BASE-mode-symlink-to-auto
test_setup
rose app-run --config=../config -q || exit 1
sed -i '/mode=symlink/d; s/source=.*3$/mode=mkdir/' ../config/rose-app.conf
run_pass "$TEST_KEY" rose app-run --config=../config -q
if [[ -L man/man1/burger.1 ]]; then
    fail "$TEST_KEY.1.type"
else
    pass "$TEST_KEY.1.type"
fi
file_cmp "$TEST_KEY.1.content" man/man1/burger.1 <<<'yummy'
if [[ -L man/man2 ]]; then
    fail "$TEST_KEY.2.type"
else
    pass "$TEST_KEY.2.type"
fi
ls man/man2 >"$TEST_KEY.2.content.out" 2>/dev/null
file_cmp "$TEST_KEY.2.file-content" "$TEST_KEY.2.content.out" <<'__OUT__'
burger_cook.2
__OUT__
if [[ -L man/man3 ]]; then
    fail "$TEST_KEY.3.type"
else
    pass "$TEST_KEY.3.type"
fi
ls man/man3 >"$TEST_KEY.3.content.out" 2>/dev/null
file_cmp "$TEST_KEY.3.file-content" "$TEST_KEY.3.content.out" </dev/null
test_teardown
#-------------------------------------------------------------------------------
exit
