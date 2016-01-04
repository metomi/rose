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
# Test PYTHONPATH in "rose env-cat".
# This is really a test for the "rose" command itself.
# See #1244.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

tests 7
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-null"
PYTHONPATH= rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" \
    grep -q "^${ROSE_HOME}/lib/python\(:[^:]*\)*$" "${TEST_KEY}.out"
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-head-1"
PYTHONPATH="$ROSE_HOME/lib/python" \
    rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" \
    grep -q "^${ROSE_HOME}/lib/python\(:[^:]*\)*$" "${TEST_KEY}.out"
#-------------------------------------------------------------------------------
mkdir -p {foo,bar}/lib/python
EXPECTED="$ROSE_HOME/lib/python:$PWD/foo/lib/python:$PWD/bar/lib/python"
PATTERN="^${ROSE_HOME}/lib/python\(:[^:]*\)*:${PWD}/foo/lib/python:${PWD}/bar/lib/python$"

TEST_KEY="$TEST_KEY_BASE-head-2"
PYTHONPATH="$ROSE_HOME/lib/python:$PWD/foo/lib/python:$PWD/bar/lib/python" \
    rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" grep -q "${PATTERN}" "${TEST_KEY}.out"

TEST_KEY="$TEST_KEY_BASE-tail"
PYTHONPATH="$PWD/foo/lib/python:$PWD/bar/lib/python:$ROSE_HOME/lib/python" \
    rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" grep -q "${PATTERN}" "${TEST_KEY}.out"

TEST_KEY="$TEST_KEY_BASE-body-1"
PYTHONPATH="$PWD/foo/lib/python:$ROSE_HOME/lib/python:$PWD/bar/lib/python" \
    rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" grep -q "${PATTERN}" "${TEST_KEY}.out"

TEST_KEY="$TEST_KEY_BASE-body-2"
PYTHONPATH="$PWD/foo/lib/python:$ROSE_HOME/lib/python:$ROSE_HOME/lib/python:$PWD/bar/lib/python" \
    rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" grep -q "${PATTERN}" "${TEST_KEY}.out"

TEST_KEY="$TEST_KEY_BASE-body-tail"
PYTHONPATH="$PWD/foo/lib/python:$ROSE_HOME/lib/python:$PWD/bar/lib/python:$ROSE_HOME/lib/python" \
    rose env-cat <<<'$PYTHONPATH' >"$TEST_KEY.out"
run_pass "$TEST_KEY.out" grep -q "${PATTERN}" "${TEST_KEY}.out"
#-------------------------------------------------------------------------------
exit
