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
# Test "rose mpi-launch --inner" command mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Basic.
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose mpi-launch --inner echo hello world
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
hello world
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Use ROSE_LAUNCHER_ULIMIT_OPTS.
TEST_KEY=$TEST_KEY_BASE
ROSE_LAUNCHER_ULIMIT_OPTS='-s unlimited' \
    run_pass "$TEST_KEY" rose mpi-launch --inner bash -c 'ulimit -s'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
unlimited
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
exit
