#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# Test "rose date".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 10
#-------------------------------------------------------------------------------
# Test the URL validator script for correct functioning.
run_fail ${TEST_KEY_BASE} python $TEST_SOURCE_DIR/lib/python/urlvalidator.py \
  "$TEST_SOURCE_DIR"
file_grep $TEST_KEY_BASE-link "some-file\.css" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-script "some-file\.js" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-link2 "some-file\.png" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-img "some-file\.jpeg" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-anchor "some-link\.html" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-anchor2 "another-link\.html" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-nested-img "another-file\.jpeg" "${TEST_KEY_BASE}.err"
file_grep $TEST_KEY_BASE-malformed "www.malformed\.html" "${TEST_KEY_BASE}.err"
file_grep_fail $TEST_KEY_BASE-pre "dont-match\.html" "${TEST_KEY_BASE}.err"

exit
