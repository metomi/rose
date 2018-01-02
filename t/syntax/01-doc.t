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
. "$(dirname "$0")/test_header"

if ! tidy -version 1>'/dev/null' 2>&1; then
    skip_all '"tidy" command not available'
fi

tests 1

# IMPORTANT: this test has been written to work with a 2007 version of tidy
# in order for html5 documents to pass tests warnings are removed from the stderr
# file.

# cannot use run-pass as tidy will fail for valid html
touch "${TEST_KEY_BASE}.err"
tidy --new-blocklevel-tags nav -q "${ROSE_HOME}/doc/"*".html" 2> "${TEST_KEY_BASE}.err" 1>/dev/null
# ignore html5 <nav> element
sed -i '/Warning: <nav> is not approved by W3C/d' "${TEST_KEY_BASE}.err"
# ignore html5 doctype <!DOCTYPE html>
sed -i '/Warning: discarding malformed <\!DOCTYPE>/d' "${TEST_KEY_BASE}.err"
file_cmp "${TEST_KEY_BASE}.err" "${TEST_KEY_BASE}.err" <'/dev/null'

exit
