#!/bin/bash
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
# Test "rose date".
# Test logic triggered by `if "-c" in sys.args`.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# Test -c option where ROSE_TASK_CYCLE_TIME is set
TEST_KEY=$TEST_KEY_BASE-ROSE_TASK_CYCLE_TIME-set
ROSE_TASK_CYCLE_TIME=20121225T0000Z \
    run_pass "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T0000Z
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test --use-task-cycle-time option where ROSE_TASK_CYCLE_TIME is set
TEST_KEY=$TEST_KEY_BASE-ROSE_TASK_CYCLE_TIME-set-use-task-cycle-time
ROSE_TASK_CYCLE_TIME=20121225T0000Z \
    run_pass "$TEST_KEY" rose date --use-task-cycle-time
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T0000Z
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option where ISODATETIMEREF is set
TEST_KEY=$TEST_KEY_BASE-ISODATETIMEREF-set
ISODATETIMEREF=20121225T0000Z \
    run_pass "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121225T0000Z
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option where both of the previous variables are set
TEST_KEY=$TEST_KEY_BASE-both-env-vars-set
ROSE_TASK_CYCLE_TIME=20121225T0000+0100 \
ISODATETIMEREF=20191225T0000Z \
    run_pass "$TEST_KEY" rose date -c --utc
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20121224T2300+0000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Test -c option where neither of the previous variables are set
TEST_KEY=$TEST_KEY_BASE-neither-env-var-set
unset ROSE_TASK_CYCLE_TIME
unset ISODATETIMEREF
run_fail "$TEST_KEY" rose date -c
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] [UNDEFINED ENVIRONMENT VARIABLE] ROSE_TASK_CYCLE_TIME
__ERR__
#-------------------------------------------------------------------------------
exit 0
