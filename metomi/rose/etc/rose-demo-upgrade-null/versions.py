#!/usr/bin/env python3
# Copyright (C) British Crown (Met Office) & Contributors.
# -----------------------------------------------------------------------------
"""Module containing test upgrade macros"""

import metomi.rose.upgrade


class UpgradeNull01(metomi.rose.upgrade.MacroUpgrade):

    """Upgrade nothing..."""

    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def upgrade(self, config, meta_config=None):
        self.add_report(None, None, None, "nothing...", is_warning=True)
        self.add_report("made", "up", None, "made up option", is_warning=True)
        return config, self.reports
