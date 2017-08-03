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
. "$(dirname "$0")/test_header"

if ! pep8 --version 1>'/dev/null' 2>&1; then
    skip_all '"pep8" command not available'
fi

tests 3

run_pass "${TEST_KEY_BASE}" \
    pep8 --ignore=E402,E731 \
    "${ROSE_HOME}/lib/python/isodatetime" \
    "${ROSE_HOME}/lib/python/rose" \
    "${ROSE_HOME}/lib/python/rosie" \
    "${ROSE_HOME}/sphinx/ext"
file_cmp "${TEST_KEY_BASE}.out" "${TEST_KEY_BASE}.out" <'/dev/null'
file_cmp "${TEST_KEY_BASE}.err" "${TEST_KEY_BASE}.err" <'/dev/null'

exit
