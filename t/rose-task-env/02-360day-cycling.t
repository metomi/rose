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
# Test "rose task-env" in 360day calendar mode.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

export ROSE_CONF_PATH=

tests 3

get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --workflow-name="${FLOW}" \
        --no-run-name
run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "${FLOW}" \
        --host='localhost' \
        --no-detach \
        --debug
for CYCLE in \
    '20200227T0000Z' \
    '20200228T0000Z' \
    '20200229T0000Z' \
    '20200230T0000Z' \
    '20200301T0000Z' \
    '20200302T0000Z'
do
    echo "${CYCLE}:"
    sed "s?^${FLOW_RUN_DIR}??" "${FLOW_RUN_DIR}/work/${CYCLE}/foo/my-datac.txt"
done >'expected-my-datac.txt'

file_cmp "${TEST_KEY_BASE}-my-datac" 'expected-my-datac.txt' <<'__TXT__'
20200227T0000Z:
/share/cycle/20200226T0000Z
/share/cycle/20200227T0000Z
/share/cycle/20200228T0000Z
20200228T0000Z:
/share/cycle/20200227T0000Z
/share/cycle/20200228T0000Z
/share/cycle/20200229T0000Z
20200229T0000Z:
/share/cycle/20200228T0000Z
/share/cycle/20200229T0000Z
/share/cycle/20200230T0000Z
20200230T0000Z:
/share/cycle/20200229T0000Z
/share/cycle/20200230T0000Z
/share/cycle/20200301T0000Z
20200301T0000Z:
/share/cycle/20200230T0000Z
/share/cycle/20200301T0000Z
/share/cycle/20200302T0000Z
20200302T0000Z:
/share/cycle/20200301T0000Z
/share/cycle/20200302T0000Z
/share/cycle/20200303T0000Z
__TXT__

purge
exit 0
