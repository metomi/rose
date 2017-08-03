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

if ! eslint --version 1>'/dev/null' 2>&1; then
    skip_all '"eslint" command not available'
fi

tests 3

TEST_KEY="${TEST_KEY_BASE}-docs"
run_pass "${TEST_KEY}" eslint --env browser --env jquery --env es6 \
    --parser-options=ecmaVersion:6 sphinx/_static/
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <'/dev/null'
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'

exit
