#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# Basic tests for "rose suite-cmp-vc" with "svn".
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

if ! which svn 1>'/dev/null' 2>&1; then
    skip_all '"svn" unavailable'
fi
tests 2
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
svnadmin create 'repos'
svn import -q -m'who cares' --non-interactive --no-auth-cache \
    "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}/" "file://${PWD}/repos"
svn checkout -q --non-interactive --no-auth-cache "file://${PWD}/repos" 'source'
mkdir -p "${HOME}/cylc-run"
RUND="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
NAME="$(basename "${RUND}")"
rose suite-run -C './source' --debug -q --name="${NAME}" -l

TEST_KEY="${TEST_KEY_BASE}-run-pass"
run_pass "${TEST_KEY}" rose suite-cmp-vc "${NAME}"

TEST_KEY="${TEST_KEY_BASE}-run-fail"
sed -i 's/meow/miaow/' './source/suite.rc'
run_fail "${TEST_KEY}" rose suite-cmp-vc "${NAME}"
#-------------------------------------------------------------------------------
rose suite-clean -q -y "${NAME}"
exit
