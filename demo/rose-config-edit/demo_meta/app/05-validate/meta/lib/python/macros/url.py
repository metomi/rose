#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import httplib

import rose.macro


class URLChecker(rose.macro.MacroBase):

    """Class to check if a URL is valid."""

    BAD_RESPONSE = "No response for this url: {0}"

    def validate(self, config, meta_config):
        """Validate a string containing a URL."""
        self.reports = []
        seq = [1, 1]
        problem_list = []
        for section in config.value.keys():
            node = config.get([section])
            if not isinstance(node.value, dict):
                continue
            for option in node.value.keys():
                if "URL" not in option:
                    continue
                value = config.get([section, option]).value
                if (not value.isdigit() and " " not in value and
                    "," not in value):
                    try:
                        connection = httplib.HTTPConnection(value, 80)
                        connection.request("HEAD", "")
                    except Exception as e:
                        self.add_report(section, option, value, str(e))
                    connection.close()
        return self.reports
