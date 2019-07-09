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
# Test "rose mpi-launch --inner" command mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Basic.
TEST_KEY=$TEST_KEY_BASE
ROSE_LAUNCHER_ULIMIT_OPTS='-a' \
    run_pass "$TEST_KEY" rose mpi-launch echo hello world
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -n 1 $ROSE_HOME_BIN/rose-mpi-launch --inner $(which echo) hello world
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Use ROSE_LAUNCHER_ULIMIT_OPTS.
TEST_KEY=$TEST_KEY_BASE-ulimit-good
ULIMIT_FILE_SIZE=$(ulimit -f)
if [[ $ULIMIT_FILE_SIZE == 'unlimited' ]]; then
    ULIMIT_FILE_SIZE_NEW=100000
else
    ULIMIT_FILE_SIZE_NEW=$(($(ulimit -f) / 2))
fi
ROSE_LAUNCHER_ULIMIT_OPTS="-f $ULIMIT_FILE_SIZE_NEW -H" \
    run_pass "$TEST_KEY" rose mpi-launch --inner bash -c 'ulimit -f'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$ULIMIT_FILE_SIZE_NEW
$ULIMIT_FILE_SIZE_NEW
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Use bad ROSE_LAUNCHER_ULIMIT_OPTS.
TEST_KEY=$TEST_KEY_BASE-ulimit-bad-opt
ROSE_LAUNCHER_ULIMIT_OPTS='-Z' run_fail "$TEST_KEY" rose mpi-launch --inner true
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '1d' "$TEST_KEY.err" # bash error string may not be portable
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] ROSE_LAUNCHER_ULIMIT_OPTS=-Z
[FAIL] exit 1
__ERR__
#-------------------------------------------------------------------------------
# Use bad argument in ROSE_LAUNCHER_ULIMIT_OPTS.
TEST_KEY=$TEST_KEY_BASE-ulimit-bad-opt-arg
ROSE_LAUNCHER_ULIMIT_OPTS='-s bad' run_fail "$TEST_KEY" \
    rose mpi-launch --inner true
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '1d' "$TEST_KEY.err" # bash error string may not be portable
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] ROSE_LAUNCHER_ULIMIT_OPTS=-s bad
[FAIL] exit 1
__ERR__
#-------------------------------------------------------------------------------
exit
