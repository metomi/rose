#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose metadata-graph" in the absence of a rose configuration.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

python -c "import pygraphviz" 2>/dev/null || \
    skip_all 'pygraphviz not installed'

init </dev/null
rm config/rose-app.conf
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# Normal mode.
TEST_KEY=$TEST_KEY_BASE-base
setup
run_fail "$TEST_KEY" rose metadata-graph --debug
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[FAIL] Could not load metadata 
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Normal mode, -C.
TEST_KEY=$TEST_KEY_BASE-C
setup
run_fail "$TEST_KEY" rose metadata-graph --debug -C ../config
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Could not load metadata 
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown option.
TEST_KEY=$TEST_KEY_BASE-unknown-option
setup
run_fail "$TEST_KEY" rose metadata-graph --unknown-option
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Usage: rose metadata-graph [OPTIONS] [SECTION ...]

rose metadata-graph: error: no such option: --unknown-option
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# No metadata.
init </dev/null
TEST_KEY=$TEST_KEY_BASE-no-metadata
setup
run_fail "$TEST_KEY" rose metadata-graph --debug -C ../config
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] Could not load metadata 
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Null metadata.
init </dev/null
init_meta </dev/null
TEST_KEY=$TEST_KEY_BASE-null-metadata
setup
run_fail "$TEST_KEY" rose metadata-graph --debug -C ../config
file_xxdiff "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_xxdiff "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] Could not load metadata 
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
