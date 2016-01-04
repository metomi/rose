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
# Test "rose macro" for optional configuration validating.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
setup
init <<'__CONFIG__'
[car]
budget=1000
paint_job=standard
__CONFIG__
init_meta <<'__META_CONFIG__'
[car=paint_job]
fail-if=this != 'standard' and car=budget < 1500
__META_CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ok-no-opts
run_pass "$TEST_KEY" rose macro --config=../config -V
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
init_opt colour <<'__OPT_CONFIG__'
[car]
paint_job=sparkly
__OPT_CONFIG__
TEST_KEY=$TEST_KEY_BASE-bad-single-opt
run_fail "$TEST_KEY" rose macro --config=../config -V 
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 1
    (opts=colour)car=paint_job=sparkly
        failed because: this != 'standard' and car=budget < 1500
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-opt-incl
init <<'__CONFIG__'
opts=colour

[car]
budget=1000
paint_job=standard
wheels=4
__CONFIG__
run_fail "$TEST_KEY" rose macro --config=../config -V
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 1
    (opts=colour)car=paint_job=sparkly
        failed because: this != 'standard' and car=budget < 1500
__ERR__
#-------------------------------------------------------------------------------
init_opt deluxe <<'__OPT_CONFIG__'
[car]
paint_job=invisible
__OPT_CONFIG__
TEST_KEY=$TEST_KEY_BASE-bad-two-opts
run_fail "$TEST_KEY" rose macro --config=../config -V
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 2
    (opts=colour)car=paint_job=sparkly
        failed because: this != 'standard' and car=budget < 1500
    (opts=deluxe)car=paint_job=invisible
        failed because: this != 'standard' and car=budget < 1500
__ERR__
#-------------------------------------------------------------------------------
init_meta <<'__META_CONFIG__'
[car=paint_job]
warn-if=this != 'standard' and car=budget < 1500
__META_CONFIG__
TEST_KEY=$TEST_KEY_BASE-warn-bad-opt
run_fail "$TEST_KEY" rose macro --config=../config -V
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 0
[V] rose.macros.DefaultValidators: warnings: 2
    (opts=colour)car=paint_job=sparkly
        warn because: this != 'standard' and car=budget < 1500
    (opts=deluxe)car=paint_job=invisible
        warn because: this != 'standard' and car=budget < 1500
__ERR__
teardown
#-------------------------------------------------------------------------------
exit
