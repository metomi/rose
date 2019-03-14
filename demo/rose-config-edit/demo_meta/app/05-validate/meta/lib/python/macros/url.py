#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
# -----------------------------------------------------------------------------

import http.client

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
                        connection = http.client.HTTPConnection(value, 80)
                        connection.request("HEAD", "")
                    except IOError as exc:
                        self.add_report(section, option, value, str(exc))
                    connection.close()
        return self.reports
