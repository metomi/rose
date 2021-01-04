#!/usr/bin/env python3
# Copyright (C) British Crown (Met Office) & Contributors.
# -----------------------------------------------------------------------------

import metomi.rose.macro


class NullChecker(metomi.rose.macro.MacroBase):

    """Class to report errors for missing or null settings."""

    REPORTS_INFO = [
        (None, None, None, "Warning for null section, null option"),
        ("made", "up", None, "Warning for non-data & non-metadata setting")]

    def validate(self, config, meta_config):
        """Validate meaningless settings."""
        self.reports = []
        for section, option, value, message in self.REPORTS_INFO:
            self.add_report(section, option, value, message, is_warning=True)
        return self.reports
