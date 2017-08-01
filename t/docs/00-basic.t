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
# Test Sphinx documentation building.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
# Note that the sphinx makefile returns 0 in the fail case.
#-------------------------------------------------------------------------------
# Test the `strict` build (dummy build which converts warnings into errors).
TEST_KEY="${TEST_KEY_BASE}-build-strict"
run_pass "${TEST_KEY}" rose make-docs --venv --dev clean strict
file_grep "${TEST_KEY}-success" "Dummy build finished." \
    "${TEST_KEY}.out"
#-------------------------------------------------------------------------------
# Test the `linkcheck` build (dummy build which checks external links).
TEST_KEY="${TEST_KEY_BASE}-build-linkcheck"
run_pass "${TEST_KEY}" rose make-docs --venv --dev linkcheck
file_grep_fail "${TEST_KEY}-success" '(line.*) broken' \
    "${TEST_KEY}.out"
#-------------------------------------------------------------------------------
# Test the `doctest` build (dummy build which runs doctests on documented code).
TEST_KEY="${TEST_KEY_BASE}-build-doctest"
run_pass "${TEST_KEY}" rose make-docs --venv doctest
file_grep "${TEST_KEY}-setup" "0 failures in setup code" \
    "${TEST_KEY}.out"
file_grep "${TEST_KEY}-run" "0 failures in tests" \
    "${TEST_KEY}.out"
file_grep "${TEST_KEY}-clean" "0 failures in cleanup code" \
    "${TEST_KEY}.out"
#-------------------------------------------------------------------------------
# Make sure that the virtual environment is removed (if created).
ls -l "${ROSE_HOME}" > "${TEST_DIR}/ls"
file_grep_fail "${TEST_KEY_BASE}-clean" "venv" "${TEST_DIR}/ls"
#-------------------------------------------------------------------------------
exit
