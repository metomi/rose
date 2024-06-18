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
# Test Rose file installation under "cylc install"
# * Rose file installation is tested under "rose app-run" / "rose task-run",
#   however, the way the async code is called is different when file
#   installation is performed under "cylc install".
# * See https://github.com/metomi/rose/issues/2784
#-------------------------------------------------------------------------------
ROSE_REPO="$(realpath "$PWD/$(dirname $0)/../../")" >&2
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3

# install a file from the Rose github repository
cat >rose-suite.conf <<__CONF__
[file:README.md]
source=git:${ROSE_REPO}::README.md::HEAD
__CONF__

touch flow.cylc
get_reg

# install the workflow
TEST_KEY="${TEST_KEY_BASE}-install"
run_pass "$TEST_KEY" \
    cylc install \
        --workflow-name="${FLOW}" \
        --no-run-name \
        .

# ensure no error was produced during file installation
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

# check the README file was produced
run_pass "${TEST_KEY_BASE}-foo" stat $HOME/cylc-run/$FLOW/README.md

purge
exit 0
