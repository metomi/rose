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
# Test "rose date" usage 2, print durations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Positive duration
TEST_KEY=$TEST_KEY_BASE-pos
run_pass "$TEST_KEY" rose date 20130101T12 20130301
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<'P58DT12H'
#-------------------------------------------------------------------------------
# Negative duration
TEST_KEY=$TEST_KEY_BASE-neg
run_pass "$TEST_KEY" rose date 20150101T12 20130301
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<'-P671DT12H'
#-------------------------------------------------------------------------------
# Print format for duration
TEST_KEY=$TEST_KEY_BASE-formatting
run_pass "$TEST_KEY" rose date 20130101T12 20130301 -f "y,m,d,h,M,s"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<'0,0,58,12,0,0'
#-------------------------------------------------------------------------------
# Offset 1, task cycle time mode
TEST_KEY=$TEST_KEY_BASE-offset1
ROSE_TASK_CYCLE_TIME=20150106 \
    run_pass "$TEST_KEY" rose date -c -1 P11M24D 20140101 ref
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<'P12D'
#-------------------------------------------------------------------------------
# Offset 2
TEST_KEY=$TEST_KEY_BASE-offset2
run_pass "$TEST_KEY" rose date 20100101T00 20100201T00 -2 P1D
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<'P32D'
#-------------------------------------------------------------------------------
# Offset 3
TEST_KEY=$TEST_KEY_BASE-offset3
run_pass "$TEST_KEY" rose date 0000 0000 -s=-PT2M -f y,m,d,h,M,s
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<<'0,0,0,0,2,0'
#-------------------------------------------------------------------------------
exit 0
