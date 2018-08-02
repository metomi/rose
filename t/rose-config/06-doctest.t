#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-8 Met Office.
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
tests 4
#-------------------------------------------------------------------------------
# Run doctests for the `rose.config` module.
# NOTE: Doctests of code included in the sphinx documentation are automatically
#       run by `rose make-docs doctest`.
# TODO: In the long run we should auto-detect and run doctests and unittests
#       rather than explicitly running them in this manner.
#-------------------------------------------------------------------------------
# Python 2
if ! which python2 2>/dev/null; then
    skip 2
else
    TEST_KEY="${TEST_KEY_BASE}-python2"
    run_pass "$TEST_KEY" python2 "${ROSE_HOME}/lib/python/rose/config.py"
    sed -i /1034h/d "${TEST_KEY}.out"  # Remove nasty unicode output.
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
fi
#-------------------------------------------------------------------------------
# Python 3
if ! which python3 2>/dev/null; then
    skip 2
else
    TEST_KEY="${TEST_KEY_BASE}-python3"
    run_pass "$TEST_KEY" python3 "${ROSE_HOME}/lib/python/rose/config.py"
    sed -i /1034h/d "${TEST_KEY}.out"  # Remove nasty unicode output.
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
fi
