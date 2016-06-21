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
# Test "rose macro" in the absence of a rose configuration.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 2
#-------------------------------------------------------------------------------
# Test that only relevant prompts are provided
init <<'__CONFIG__'
[env]
ANSWER=42
__CONFIG__

setup
init_meta <<'__META_CONFIG__'
[env=ANSWER]
macro=prompt.Test
__META_CONFIG__

init_opt baseeight <<'__OPT_CONFIG__'
[env]
ANSWER=52
__OPT_CONFIG__

init_macro prompt.py < $TEST_SOURCE_DIR/lib/custom_macro_prompt.py
TEST_KEY="$TEST_KEY_BASE"
rose macro --config='../config' -V <<<'' >>'temp'
grep_count_ok "$TEST_KEY"-1 'Value for answer (default 42)' 'temp' 1
grep_count_ok "$TEST_KEY"-2 'Value for optional_config_name' 'temp' 0

rm temp
teardown
#-------------------------------------------------------------------------------
exit
