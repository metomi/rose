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
# Test "rose suite-log" on an uninstalled suite.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

tests 3
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
NAME="$(uuidgen)"  # Very unlikely to have a suite of this name installed
run_fail "${TEST_KEY}" rose suite-log "--name=${NAME}"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] ${NAME}: suite log not found
__ERR__
#-------------------------------------------------------------------------------
exit 0
