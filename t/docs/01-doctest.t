#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
# Run doctests in sphinx extensions.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! rose check-software-docs; then
    skip_all "Software dependencies for documentation not met."
fi
#-------------------------------------------------------------------------------
FILES=($(find "${ROSE_HOME}/sphinx/ext" -name "*.py"))
tests $(( ${#FILES[@]} * 2 ))
#-------------------------------------------------------------------------------
TERM=  # Nasty solution to prevent control chars being printed in python output.
for file in ${FILES[@]}; do
    TEST_KEY="${TEST_KEY_BASE}-$(basename ${file})"
    run_pass "${TEST_KEY}" python -m doctest "${file}"
    file_cmp "${TEST_KEY}-err" "${TEST_KEY}.out" /dev/null
done
#-------------------------------------------------------------------------------
exit
