#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
# Test "rose macro" in the absence of a rose configuration.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
rm config/rose-app.conf
#-------------------------------------------------------------------------------
tests 24
#-------------------------------------------------------------------------------
# Normal mode.
TEST_KEY=$TEST_KEY_BASE-base
setup
run_fail "$TEST_KEY" rose app-upgrade
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
$PWD: not an application directory.
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Normal mode, -C.
TEST_KEY=$TEST_KEY_BASE-C
setup
run_fail "$TEST_KEY" rose app-upgrade -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
../config: not an application directory.
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown option.
TEST_KEY=$TEST_KEY_BASE-unknown-option
setup
run_fail "$TEST_KEY" rose app-upgrade --unknown-option
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Usage: rose app-upgrade [OPTIONS] [VERSION]

rose app-upgrade: error: no such option: --unknown-option
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# No meta flag.
init </dev/null
TEST_KEY=$TEST_KEY_BASE-no-metadata
setup
run_fail "$TEST_KEY" rose app-upgrade -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown metadata flag, I
init << '__CONFIG__'
meta=unknown-flag
__CONFIG__
init_meta </dev/null
TEST_KEY=$TEST_KEY_BASE-unknown-flag-i
setup
run_fail "$TEST_KEY" rose app-upgrade -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown metadata flag, II
init << '__CONFIG__'
meta=unknown-flag/10.0
__CONFIG__
init_meta </dev/null
TEST_KEY=$TEST_KEY_BASE-unknown-flag-ii
setup
run_fail "$TEST_KEY" rose app-upgrade -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Malformed metadata flag, I
init << '__CONFIG__'
meta=
__CONFIG__
init_meta </dev/null
TEST_KEY=$TEST_KEY_BASE-malformed-flag-i
setup
run_fail "$TEST_KEY" rose app-upgrade -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Malformed metadata flag, II
init << '__CONFIG__'
meta=flag/
 /45/
 flag'456
__CONFIG__
init_meta </dev/null
TEST_KEY=$TEST_KEY_BASE-malformed-flag-ii
setup
run_fail "$TEST_KEY" rose app-upgrade -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
