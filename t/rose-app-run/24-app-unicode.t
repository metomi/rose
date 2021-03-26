#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# Test dealing with Unicode configuration values.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 2
#-------------------------------------------------------------------------------
test_setup
test_init </dev/null
cp "$TEST_SOURCE_DIR/$TEST_KEY_BASE"/rose-app.conf "$TEST_DIR/config/"
TEST_KEY="$TEST_KEY_BASE"
run_pass "$TEST_KEY" rose app-run --config="$TEST_DIR/config"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] export FLOWER=⚘
[INFO] export PATH=$PATH
[INFO] command: true
__OUT__
test_teardown
#-------------------------------------------------------------------------------
exit 0
