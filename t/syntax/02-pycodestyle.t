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
. "$(dirname "$0")/test_header"

if ! pycodestyle --version 1>'/dev/null' 2>&1; then
    skip_all '"pycodestyle" command not available'
fi

tests 3

# Ignores:
# E402 module level import not at top of file:
# - To allow import on demand for expensive modules.
# E731 do not assign a lambda expression, use a def
# - There are too many in the logic at the moment.
# - Most are in the GUI logic, which is due for replacement soon.
# W503 line break before binary operator
# W504 line break after binary operator
# - PEP8 allows both, line break before binary preferred for new code.
run_pass "${TEST_KEY_BASE}" \
    pycodestyle --ignore=E402,E731,W503,W504 \
    "${ROSE_HOME}/lib/python/isodatetime" \
    "${ROSE_HOME}/lib/python/rose" \
    "${ROSE_HOME}/lib/python/rosie" \
    "${ROSE_HOME}/sphinx/ext" \
    "${ROSE_HOME}/sphinx/conf.py"
file_cmp "${TEST_KEY_BASE}.out" "${TEST_KEY_BASE}.out" <'/dev/null'
file_cmp "${TEST_KEY_BASE}.err" "${TEST_KEY_BASE}.err" <'/dev/null'

exit
