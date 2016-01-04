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
# Test "rose_prune" built-in application:
# Prune items with glob with "%(cycle)s" substitution.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 2

export ROSE_CONF_PATH=
mkdir -p "${HOME}/cylc-run"
SUITE_RUN_DIR=$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')
NAME="$(basename "${SUITE_RUN_DIR}")"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --host='localhost' --debug -- --debug

TEST_KEY="${TEST_KEY_BASE}-prune.log"
sed '/^\[INFO\] export ROSE_TASK_CYCLE_TIME=/p;/^\[INFO\] delete: /!d' \
    "${SUITE_RUN_DIR}/prune.log" >'edited-prune.log'
file_cmp "${TEST_KEY}" 'edited-prune.log' <<__LOG__
[INFO] export ROSE_TASK_CYCLE_TIME=19700101T0000Z
[INFO] export ROSE_TASK_CYCLE_TIME=19900101T0000Z
[INFO] delete: share/hello-earth-in-1970.txt
[INFO] delete: share/hello-mars-in-1970.txt
[INFO] delete: share/hello-venus-in-1970.txt
__LOG__
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit 0
