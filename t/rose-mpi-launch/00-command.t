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
# Test "rose mpi-launch" command mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------
# No argument.
TEST_KEY=$TEST_KEY_BASE-null
run_fail "$TEST_KEY" rose mpi-launch
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
usage: 1. rose mpi-launch -f FILE
usage: 2. rose mpi-launch
usage: 3. rose mpi-launch COMMAND [ARGS ...]
__ERR__
#-------------------------------------------------------------------------------
# Basic.
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose mpi-launch true to your heart
TRUE=$(which true)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -n 1 $ROSE_HOME/bin/rose-mpi-launch --inner $TRUE to your heart
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Basic, NPROC
TEST_KEY=$TEST_KEY_BASE-nproc
NPROC=$RANDOM
NPROC=$NPROC \
    run_pass "$TEST_KEY" rose mpi-launch true to your heart
TRUE=$(which true)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -n $NPROC $ROSE_HOME/bin/rose-mpi-launch --inner $TRUE to your heart
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Basic, no inner
TEST_KEY=$TEST_KEY_BASE-no-inner
ROSE_LAUNCH_INNER= \
    run_pass "$TEST_KEY" rose mpi-launch true to your heart
TRUE=$(which true)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -n 1 $TRUE to your heart
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Basic, launcher fail.
TEST_KEY=$TEST_KEY_BASE-fail
ROSE_TEST_RC=1 \
    run_fail "$TEST_KEY" rose mpi-launch true to your heart
TRUE=$(which true)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -n 1 $ROSE_HOME/bin/rose-mpi-launch --inner $TRUE to your heart
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Basic, altenate launcher.
TEST_KEY=$TEST_KEY_BASE-alt
ROSE_LAUNCHER=our-launcher \
    run_pass "$TEST_KEY" rose mpi-launch true to your heart
TRUE=$(which true)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[our-launcher] $ROSE_HOME/bin/rose-mpi-launch --inner $TRUE -n 1 to your heart
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Basic, altenate launcher 2.
TEST_KEY=$TEST_KEY_BASE-alt-2
PATH=$(dirname $0)/bin2:$PATH \
    run_pass "$TEST_KEY" rose mpi-launch true to your heart
TRUE=$(which true)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[test-launcher] $ROSE_HOME/bin/rose-mpi-launch --inner $TRUE to your heart
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
exit
