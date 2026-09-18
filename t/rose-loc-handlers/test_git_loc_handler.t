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

. $(dirname $0)/test_header

tests 1

# Setup a local git repository to test with.
SOURCE_REPO="${TEST_DIR}/repo"
mkdir -p "${SOURCE_REPO}"
git -C "${SOURCE_REPO}" init --quiet --initial-branch=main
touch "${SOURCE_REPO}/foo"
touch "${SOURCE_REPO}/bar"
git -C "${SOURCE_REPO}" add .
git -C "${SOURCE_REPO}" commit -q -m "initial import"
git -C "${SOURCE_REPO}" config uploadpack.allowAnySHA1InWant true
git -C "${SOURCE_REPO}" config uploadpack.allowFilter true

# Run the script on a blob:
TEST_KEY="${TEST_KEY_BASE} local filtered clone"
cat >rose-app.conf <<__APP__
[command]
# Check that foo has been cloned and installed but not bar.
default=test -f foo -a ! -f bar

[file:foo]
source=git:$SOURCE_REPO::foo::main
__APP__
run_pass "${TEST_KEY}" rose app-run
