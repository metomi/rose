#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


import rose.upgrade


class UpgradeAppletoFig(rose.upgrade.MacroUpgrade):

    """Upgrade from Apple to Fig."""

    BEFORE_TAG = "apple"
    AFTER_TAG = "fig"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:add_sect_only"])
        print("Current directory:", os.getcwd())
        return config, self.reports
