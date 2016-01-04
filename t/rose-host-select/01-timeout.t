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
# Test "rose host-select", subprocesses killed.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
export PATH=$TEST_SOURCE_DIR/$TEST_KEY_BASE/bin:$PATH
export ROSE_CONF_PATH=$TEST_SOURCE_DIR/$TEST_KEY_BASE/etc
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_fail "$TEST_KEY" rose host-select sleepy1 sleepy2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
LANG=C sort "$TEST_KEY.err" -o "$TEST_KEY.sorted.err"
file_cmp "$TEST_KEY.sorted.err" "$TEST_KEY.sorted.err" <<'__ERR__'
[FAIL] No hosts selected.
[WARN] sleepy1: (timed out)
[WARN] sleepy2: (timed out)
__ERR__
cut -f2- mock-ssh.out | LANG=C sort >mock-ssh.out.sorted
# N.B. Tab between 1 and sleepy?
file_cmp "$TEST_KEY.mock-ssh.out" mock-ssh.out.sorted <<'__OUT__'
sleepy1 bash
sleepy2 bash
__OUT__
# Make sure there is no lingering processes
run_fail "$TEST_KEY.ps" ps $(cut -f1 mock-ssh.out)
#-------------------------------------------------------------------------------
exit
