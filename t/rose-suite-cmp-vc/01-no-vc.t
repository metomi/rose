#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2018 British Crown (Met Office) & Contributors.
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
# Tests for "rose suite-cmp-vc" with VC.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
tests 2
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
cp -pr "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/" 'source'
mkdir -p "${HOME}/cylc-run"
RUND="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${RUND}")"
rose suite-run -C './source' --debug -q --name="${NAME}" -l

TEST_KEY="${TEST_KEY_BASE}"
run_fail "${TEST_KEY}" rose suite-cmp-vc "${NAME}"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<__ERR__
[FAIL] ${NAME}: rose-suite-run.version: VC info not found
__ERR__
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit
