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
# Test "rose app-run", file installation will not fail if a broken
# symlink is contained in a repository or directory.
# See https://github.com/metomi/rose/issues/2946

. "$(dirname "$0")/test_header"

tests 4

test_init <<__CONFIG__
[command]
default=true

[file:destination]
source=${TEST_DIR}/source
__CONFIG__

# Create a broken symlink dir
mkdir -p ${TEST_DIR}/source/
touch ${TEST_DIR}/source/missing
ln -s ${TEST_DIR}/source/missing ${TEST_DIR}/source/link
rm ${TEST_DIR}/source/missing

test_setup

# It doesn't fail when rsync installs broken symlink dirs:
run_pass "${TEST_KEY_BASE}-rsync" rose app-run --config=../config
file_grep_fail "${TEST_KEY_BASE}-rsync.err" \
    "No such file" \
    "${TEST_KEY_BASE}-rsync.err"

# Turn the source file into a Git repo and try to use the git file-handler:
git -C ${TEST_DIR}/source init
git -C ${TEST_DIR}/source add .
git -C ${TEST_DIR}/source commit -a -m "my_commit"
sed -i 'sXsource=.*Xsource=git:../source::./::HEADX' ../config/rose-app.conf

# It doesn't fail when git installs broken symlink dirs:
run_pass "${TEST_KEY_BASE}-git" rose app-run --config=../config
file_grep_fail "${TEST_KEY_BASE}-git.err" \
    "No such file" \
    "${TEST_KEY_BASE}-git.err"
