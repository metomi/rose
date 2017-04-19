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
# Test Sphinx documentation building and validate urls in "doc/*.html".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 8
#-------------------------------------------------------------------------------
# Build Sphinx documentation and run doctests.
TEST_KEY="${TEST_KEY_BASE}-doctest"
# export SPHINX_DEV_MODE=true  # For development, don't rebuild the virtualenv.
run_pass "${TEST_KEY}" make -C "${ROSE_HOME}/doc"
file_grep "${TEST_KEY}-build" "build succeeded." "${TEST_KEY}.out"
file_grep "${TEST_KEY}-tests-setup" "0 failures in setup code" \
    "${TEST_KEY}.out"
file_grep "${TEST_KEY}-tests-run" "0 failures in tests" \
    "${TEST_KEY}.out"
file_grep "${TEST_KEY}-tests-clean" "0 failures in cleanup code" \
    "${TEST_KEY}.out"
# Make sure that the virtual environment is removed (if created).
ls -l "${ROSE_HOME}" > "${TEST_DIR}/ls"
file_grep_fail "${TEST_KEY}-clean" "venv" "${TEST_DIR}/ls"
#-------------------------------------------------------------------------------
# Test rose documentation for broken links.
TEST_KEY="${TEST_KEY_BASE}-urls"
run_pass "${TEST_KEY}" python $TEST_SOURCE_DIR/lib/python/urlvalidator.py \
    "${ROSE_HOME}/doc/"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
#-------------------------------------------------------------------------------

exit
