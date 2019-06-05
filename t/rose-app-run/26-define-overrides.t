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
# Test "rose app-run", command line define of opts and import keys.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
test_init <<'__CONFIG__'
opts=foo
import=non-existing-config
[command]
default = rose config -f rose-app-run.conf env
[env]
FOO = foo
__CONFIG__
mkdir -p config/opt
cat >config/opt/rose-app-foo.conf <<'__CONFIG__'
[env]
FOO = foolish fool
__CONFIG__
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Undefine in-place import.
TEST_KEY=$TEST_KEY_BASE-control
test_setup
run_pass "$TEST_KEY" rose app-run --config=../config --define='!import' -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
FOO=foolish fool
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
test_teardown
#-------------------------------------------------------------------------------
# Redefine import and undefine in-place optional configuration.
TEST_KEY=$TEST_KEY_BASE-define-no-opts
test_setup
mkdir -p ../config2/opt ../config3
cat >../config2/rose-app.conf <<'__CONFIG__'
opts = bar
[command]
default = true
[env]
FOO = foo fighter
BAR = bar
__CONFIG__
cat >../config2/opt/rose-app-bar.conf <<'__CONFIG__'
import = config3
[env]
BAR = barman
__CONFIG__
cat >../config3/rose-app.conf <<'__CONFIG__'
[env]
BAZ = buzzing
__CONFIG__
run_pass "$TEST_KEY" rose app-run --config=../config \
    --define='!opts' --define='import=config2' -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
BAR=barman
BAZ=buzzing
FOO=foo
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
rm -r ../config2 ../config3
test_teardown
#-------------------------------------------------------------------------------
exit
