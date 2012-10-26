#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import rose.macro


class Upgrade272to273(rose.macro.MacroUpgrade):

    """Upgrade from 27.2 to 27.3."""

    BEFORE_TAG = "27.2"
    AFTER_TAG = "27.3"

    def transform(self, config, meta_config=None, downgrade=False):
        changes = []
        if downgrade:
            self.remove_setting(changes, config, "env", "C")
            self.remove_setting(changes, config, "env", "D")
            self.add_setting(changes, config, "env", "A", "0")
            self.add_setting(changes, config, "env", "B", "1")
        else:
            self.add_setting(changes, config, "env", "C", "0")
            self.add_setting(changes, config, "env", "D", "1")
            self.remove_setting(changes, config, "env", "A")
            self.remove_setting(changes, config, "env", "B")
        return config, changes


class Upgrade273to281(rose.macro.MacroUpgrade):

    """Upgrade from 27.3 to 28.1."""

    BEFORE_TAG = "27.3"
    AFTER_TAG = "28.1"

    def transform(self, config, meta_config=None, downgrade=False):
        changes = []
        if downgrade:
            self.add_setting(changes, config, "namelist:test_nl",
                             "X", "0")
        else:
            self.remove_setting(changes, config, "namelist:test_nl",
                                "X", info="Remove for #2020")
        return config, changes


class Upgrade281to291(rose.macro.MacroUpgrade):

    """Upgrade from 28.1 to 29.1."""

    BEFORE_TAG = "28.1"
    AFTER_TAG = "29.1"

    def transform(self, config, meta_config=None, downgrade=False):
        changes = []
        if downgrade:
            self.add_setting(changes, config, "namelist:test_nl",
                             "C", "0")
        else:
            self.remove_setting(changes, config, "namelist:test_nl",
                                "C", info="Remove for #1668")
        return config, changes


class Upgrade291to292(rose.macro.MacroUpgrade):

    """Upgrade from 29.1 to 29.2."""

    BEFORE_TAG = "29.1"
    AFTER_TAG = "29.2"

    def transform(self, config, meta_config=None, downgrade=False):
        changes = []
        print "call act from files..."
        self.act_from_files(changes, config, downgrade)
        return config, changes
