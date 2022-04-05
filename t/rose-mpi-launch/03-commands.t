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
# Test "rose mpi-launch" with multiple commands; e.g.
#   $ export ROSE_LAUNCHER="time mpiexec"
#   $ rose mpi-launch -v true
#
# Should work through each command.
#
# Response to bug @https://github.com/metomi/rose/issues/2573
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 4
#-------------------------------------------------------------------------------
true_path=$(which true)
ls_path=$(which ls)
time_path=$(which time)

# Control - test that having one command in "ROSE_LAUNCHER" still works.
TEST_NAME="${TEST_KEY_BASE}-check-single-path"
export ROSE_LAUNCHER="ls"
run_pass "${TEST_NAME}" rose mpi-launch -v true
file_grep \
    "${TEST_NAME}-output" \
    "exec ${ls_path} ${true_path}"\
    "${TEST_NAME}.out"

# Test - test having multiple commands in "ROSE_LAUNCHER".
TEST_NAME="${TEST_KEY_BASE}-check-multiple-paths"
export ROSE_LAUNCHER="time ls"
run_pass "${TEST_NAME}" rose mpi-launch -v true

file_grep \
    "${TEST_NAME}-output" \
    "exec ${time_path} ${ls_path} ${true_path}"\
    "${TEST_NAME}.out"
