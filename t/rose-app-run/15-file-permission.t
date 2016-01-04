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
# Test "rose app-run", file installation, invalid permissions.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=12
tests $N_TESTS
#-------------------------------------------------------------------------------
test_init <<__CONFIG__
[command]
default=true

[file:read_only_dest/foo.nl]
source=namelist:foo

[namelist:foo]
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-read-only-dest
test_setup
mkdir read_only_dest
chmod u-w read_only_dest
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] [Errno 13] Permission denied: 'read_only_dest/foo.nl'
[FAIL] install: read_only_dest/foo.nl
[FAIL]     source: namelist:foo
__ERR__
chmod u+w read_only_dest
#-------------------------------------------------------------------------------
test_init <<__CONFIG__
[command]
default=true

[file:bar]
source=$TEST_DIR/no_read_target
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-read-target-file
touch $TEST_DIR/no_read_target
chmod u-r $TEST_DIR/no_read_target
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] [Errno 13] Permission denied: '$TEST_DIR/no_read_target'
__ERR__
chmod u+r $TEST_DIR/no_read_target
rm $TEST_DIR/no_read_target
#-------------------------------------------------------------------------------
test_init <<__CONFIG__
[command]
default=true

[file:baz]
source=$TEST_DIR/no_read_target_dir/
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-read-target-dir
mkdir $TEST_DIR/no_read_target_dir
chmod u-r $TEST_DIR/no_read_target_dir
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
__OUT__
file_grep "$TEST_KEY.err" "Permission denied" "$TEST_KEY.err"
chmod u+r $TEST_DIR/no_read_target_dir
rmdir $TEST_DIR/no_read_target_dir
#-------------------------------------------------------------------------------
test_init <<__CONFIG__
[command]
default=true

[file:qux]
source=$TEST_DIR/no_read_target_dir/qux
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-no-read-target-dir-file
mkdir $TEST_DIR/no_read_target_dir
touch $TEST_DIR/no_read_target_dir/qux
chmod u-x $TEST_DIR/no_read_target_dir
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] file:qux=source=$TEST_DIR/no_read_target_dir/qux: bad or missing value
__ERR__
chmod u+x $TEST_DIR/no_read_target_dir
rm $TEST_DIR/no_read_target_dir/qux
rmdir $TEST_DIR/no_read_target_dir
test_teardown
#-------------------------------------------------------------------------------
exit
