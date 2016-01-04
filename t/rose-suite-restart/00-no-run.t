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
# Test "rose suite-restart" on suites that don't exist.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
tests 7
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-pwd"
ROSE_CONF_PATH= run_fail "${TEST_KEY}" rose suite-restart
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] ${PWD} - no suite found for this path.
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-name-uuid"
NAME="$(uuidgen)"
ROSE_CONF_PATH= run_fail "${TEST_KEY}" rose suite-restart -n "${NAME}"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] ${HOME}/cylc-run/${NAME} - no suite found for this path.
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-name-uuid-installed"
NAME="$(uuidgen)"
mkdir -p "${HOME}/cylc-run/${NAME}"
ROSE_CONF_PATH= run_fail "${TEST_KEY}" rose suite-restart -n "${NAME}"
# N.B. This relies on output of "cylc restart"
head -1 "${TEST_KEY}.err" >"${TEST_KEY}.err.head"
file_cmp "${TEST_KEY}.err.head" "${TEST_KEY}.err.head" <<__ERR__
[FAIL] cylc restart ${NAME}  # return-code=1, stderr=
__ERR__
file_grep "${TEST_KEY}.err.grep" \
    "'ERROR: Suite not found ${NAME}'" "${TEST_KEY}.err"
rmdir "${HOME}/cylc-run/${NAME}"
#-------------------------------------------------------------------------------
exit
