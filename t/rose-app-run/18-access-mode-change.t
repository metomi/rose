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
# Test "rose app-run", file installation, access mode change.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
test_init <<__CONFIG__
[command]
default=./bin/egg.sh

[file:bin/egg.sh]
source=$PWD/bin/egg.sh
__CONFIG__

mkdir "$TEST_DIR/bin"
cat >"$TEST_DIR/bin/egg.sh" <<'__BASH__'
#!/bin/bash
echo 'Bash it, crack it, bin it.'
__BASH__

#-------------------------------------------------------------------------------
test_setup

# Forgot to add executable permission
TEST_KEY="$TEST_KEY_BASE-0"
run_fail "$TEST_KEY" rose app-run --config=../config -q
run_fail "$TEST_KEY.egg.sh" test -x ./bin/egg.sh

chmod +x "$TEST_DIR/bin/egg.sh"
TEST_KEY="$TEST_KEY_BASE-1"
run_pass "$TEST_KEY" rose app-run --config=../config -q
run_pass "$TEST_KEY.egg.sh" test -x ./bin/egg.sh
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
Bash it, crack it, bin it.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

test_teardown
#-------------------------------------------------------------------------------
exit
