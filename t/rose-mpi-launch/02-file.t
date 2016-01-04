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
# Test "rose mpi-launch" command file mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# No argument, rose-mpi-launch.rc exists.
TEST_KEY=$TEST_KEY_BASE-null
touch rose-mpi-launch.rc
run_pass "$TEST_KEY" rose mpi-launch
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -file $PWD/rose-mpi-launch.rc
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# No configuration, rose-mpi-launch.rc exists.
TEST_KEY=$TEST_KEY_BASE-no-config
touch rose-mpi-launch.rc
ROSE_CONF_PATH= run_fail "$TEST_KEY" rose mpi-launch
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] ROSE_LAUNCHER not defined, command file not supported.
[FAIL] exit 1
__ERR__
#-------------------------------------------------------------------------------
# No argument, rose-mpi-launch.rc exists, modified ROSE_LAUNCHER_FILEOPTS.
TEST_KEY=$TEST_KEY_BASE-null-env
touch rose-mpi-launch.rc
ROSE_LAUNCHER_FILEOPTS='-foo -file $ROSE_COMMAND_FILE -bar' \
    run_pass "$TEST_KEY" rose mpi-launch -- -baz
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -foo -file $PWD/rose-mpi-launch.rc -bar -baz
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# -f FILE.
TEST_KEY=$TEST_KEY_BASE-f
touch my-command-file
run_pass "$TEST_KEY" rose mpi-launch -f my-command-file
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[my-launcher] -file my-command-file
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# -f FILE, alternate launcher.
TEST_KEY=$TEST_KEY_BASE-f-alt
touch my-command-file
ROSE_LAUNCHER=our-launcher \
    run_pass "$TEST_KEY" rose mpi-launch -f my-command-file foo bar baz
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[our-launcher] -f my-command-file foo bar baz
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
exit
