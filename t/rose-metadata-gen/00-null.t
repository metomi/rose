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
# Test "rose metadata-gen" in the absence of a rose-app.conf.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
rm config/rose-app.conf
#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
# Normal mode.
TEST_KEY=$TEST_KEY_BASE-base
setup
run_fail "$TEST_KEY" rose metadata-gen
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Usage: rose metadata-gen [OPTIONS] [PROPERTY=VALUE ...]

__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Normal mode, --config-dir.
TEST_KEY=$TEST_KEY_BASE--config-dir
setup
run_fail "$TEST_KEY" rose metadata-gen --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Usage: rose metadata-gen [OPTIONS] [PROPERTY=VALUE ...]

__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown option.
TEST_KEY=$TEST_KEY_BASE-unknown-option
setup
run_fail "$TEST_KEY" rose metadata-gen --unknown-option
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Usage: rose metadata-gen [OPTIONS] [PROPERTY=VALUE ...]

rose metadata-gen: error: no such option: --unknown-option
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
