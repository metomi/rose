#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# -----------------------------------------------------------------------------
"""Class to check if a URL is valid."""

import http.client

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
                        connection = http.client.HTTPConnection(value, 80)
                        connection.request("HEAD", "")
                    except IOError as exc:
                        self._flag_problem(section, option, value, exc)
                    connection.close()
        return self.reports

    def _flag_problem(self, sect, opt, val, exc):
        """Add a setting to the list of problems."""
        info = self.BAD_URL.format(val, exc)
        self.add_report(sect, opt, val, info)
