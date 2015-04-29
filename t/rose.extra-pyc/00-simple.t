#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Check for remaining *.pyc files.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 1
#-------------------------------------------------------------------------------
# No .pyc files without a corresponding .py file.
TEST_KEY="$TEST_KEY_BASE"
set -eu
for pyc_file in $(find "$ROSE_HOME/lib/python" -type f -name "*.pyc"); do
    py_file="${pyc_file%c}"
    if [[ ! -f "$py_file" ]]; then
        echo '.pyc file exists without .py file: '$pyc_file >&2
        fail "$TEST_KEY"
        exit 0
    fi
done
pass "$TEST_KEY"
