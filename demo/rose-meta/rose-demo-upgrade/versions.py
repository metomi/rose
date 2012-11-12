#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import rose.upgrade


class Upgrade272to273(rose.upgrade.MacroUpgrade):

    """Upgrade from 27.2 to 27.3."""

    BEFORE_TAG = "27.2"
    AFTER_TAG = "27.3"

    def downgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "C"])
        self.remove_setting(config, ["env", "D"])
        self.add_setting(config, ["env", "A"], "0")
        self.add_setting(config, ["env", "B"], "1")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "C"], "0")
        self.add_setting(config, ["env", "D"], "1")
        self.remove_setting(config, ["env", "A"])
        self.remove_setting(config, ["env", "B"])
        return config, self.reports


class Upgrade273to281(rose.upgrade.MacroUpgrade):

    """Upgrade from 27.3 to 28.1."""

    BEFORE_TAG = "27.3"
    AFTER_TAG = "28.1"

    def downgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:test_nl", "X"], "0")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["namelist:test_nl", "X"],
                            info="Remove for #2020")
        return config, self.reports


class Upgrade281to291(rose.upgrade.MacroUpgrade):

    """Upgrade from 28.1 to 29.1."""

    BEFORE_TAG = "28.1"
    AFTER_TAG = "29.1"

    def downgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:test_nl", "C"], "0")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["namelist:test_nl", "C"],
                            info="Remove for #1668")
        return config, self.reports


class Upgrade291to292(rose.upgrade.MacroUpgrade):

    """Upgrade from 29.1 to 29.2."""

    BEFORE_TAG = "29.1"
    AFTER_TAG = "29.2"

    def downgrade(self, config, meta_config=None):
        self.act_from_files(config, downgrade=True)
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.act_from_files(config, downgrade=False)
        return config, self.reports
