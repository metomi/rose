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
# Tests behaviour of rose/loc_handlers/rsync_remote_check.py. Ideally this
# should be run against as many versions of Python as possible.
# See: https://github.com/metomi/rose/issues/2609

. $(dirname $0)/test_header

tests 4

# Print the Python version to stderr, just to check.
python --version >&2

# Create a folder containing both files and directories.
mkdir -p foo/baz
echo "HI" > foo/bar
echo "THERE" > foo/baz/qux
chmod 752 foo/baz/qux
chmod 755 foo/bar

# Set name of script to test
SCRIPT="${ROSE_TEST_HOME}/rose/metomi/rose/loc_handlers/rsync_remote_check.py"

# Run the script on a tree:
TEST_KEY="${TEST_KEY_BASE} tree"
run_pass "${TEST_KEY}" python "${SCRIPT}" $PWD/foo 'blob' 'tree'
awk '{print $1, $3, $4}' > cut_test_file < "${TEST_KEY}.out"
file_cmp "${TEST_KEY}-vs-kgo" "cut_test_file" <<__HERE__
tree  
- - $PWD/foo/baz
33261 3 $PWD/foo/bar
33258 6 $PWD/foo/baz/qux
__HERE__

# Run the script on a blob:
TEST_KEY="${TEST_KEY_BASE} blob"
run_pass "${TEST_KEY}" python "${SCRIPT}" $PWD/foo/bar 'blob' 'tree'
awk '{print $1, $3, $4}' > cut_test_file < "${TEST_KEY}.out"
file_cmp "${TEST_KEY}-vs-kgo" cut_test_file <<__HERE__
blob  
33261 3 $PWD/foo/bar
__HERE__
