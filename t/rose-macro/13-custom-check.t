#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
# Test "rose macro" in custom checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init <<'__CONFIG__'
[env]
BAD_URL=htpp://www.google.co.uk
__CONFIG__
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check macro finding.
TEST_KEY=$TEST_KEY_BASE-discovery
setup
init_meta </dev/null
init_macro url.py <<__MACRO__
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
#-----------------------------------------------------------------------------

import httplib

import rose.macro


class URLChecker(rose.macro.MacroBase):

    """Class to check if a URL is valid."""

    BAD_URL = "{0}: {1}"
    BAD_RESPONSE = "No response for this url"

    def validate(self, config, meta_config):
        """Validate a string containing a URL."""
        seq = [1, 1]
        self.reports = []
        for section in config.value.keys():
            for option in config.get([section]).value.keys():
                if "URL" not in option:
                    continue
                value = config.get([section, option]).value
                if (not value.isdigit() and " " not in value and
                    "," not in value):
                    try:
                        connection = httplib.HTTPConnection(value, 80)
                        connection.request("HEAD", "")
                    except Exception as e:
                        self._flag_problem(section, option, value, e)
                    connection.close()
        return self.reports

    def _flag_problem(self, sect, opt, val, e):
        # Add a setting to the list of problems.
        info = self.BAD_URL.format(val, e)
        self.add_report(sect, opt, val, info)
__MACRO__
run_pass "$TEST_KEY" rose macro --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__CONTENT__'
[V] url.URLChecker
    # Class to check if a URL is valid.
__CONTENT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check changing.
TEST_KEY=$TEST_KEY_BASE-check
setup
init_meta </dev/null
init_macro url.py <<__MACRO__
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
#-----------------------------------------------------------------------------

import httplib

import rose.macro


class URLChecker(rose.macro.MacroBase):

    """Class to check if a URL is valid."""

    BAD_URL = "{0}: {1}"
    BAD_RESPONSE = "No response for this url"

    def validate(self, config, meta_config):
        """Validate a string containing a URL."""
        seq = [1, 1]
        self.reports = []
        for section in config.value.keys():
            for option in config.get([section]).value.keys():
                if "URL" not in option:
                    continue
                value = config.get([section, option]).value
                if (not value.isdigit() and " " not in value and
                    "," not in value):
                    try:
                        connection = httplib.HTTPConnection(value, 80)
                        connection.request("HEAD", "")
                    except Exception as e:
                        self._flag_problem(section, option, value, e)
                    connection.close()
        return self.reports

    def _flag_problem(self, sect, opt, val, e):
        # Add a setting to the list of problems.
        info = self.BAD_URL.format(val, e)
        self.add_report(sect, opt, val, info)
__MACRO__
run_fail "$TEST_KEY" rose macro --config=../config url.URLChecker
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[V] url.URLChecker: issues: 1
    env=BAD_URL=htpp://www.google.co.uk
        htpp://www.google.co.uk: [Errno -2] Name or service not known
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit
