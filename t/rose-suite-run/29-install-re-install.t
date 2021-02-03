#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
mkdir -p "${HOME}/cylc-run"
RUND="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${RUND}")"
export TEST_SOURCE_DIR="${TEST_SOURCE_DIR}"

# Run rose-suite-run install using source file 1:
run_pass "${TEST_KEY}-install-src1" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --install-only --verbose -O one

file_cmp "${TEST_KEY_BASE}-check-src1" "${RUND}/MyTargetFile" <<__HERE__
source 1 file
__HERE__

# Run rose-suite-run install using source file 2:
run_pass "${TEST_KEY}-install-src2" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --install-only --verbose -O two

file_cmp "${TEST_KEY_BASE}-check-src2" "${RUND}/MyTargetFile" <<__HERE__
source 2 file
__HERE__

# Run rose-suite-run install using source file 1:
run_pass "${TEST_KEY}-install-src1-again" \
    rose suite-run -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" --name="${NAME}" \
    --no-gcontrol --install-only --verbose -O one

file_cmp "${TEST_KEY_BASE}-check-src1-again" "${RUND}/MyTargetFile" <<__HERE__
source 1 file
__HERE__

rose suite-clean -q -y "${NAME}"
exit 0
