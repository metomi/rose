#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


import rose.macro


class PrintCwd(rose.macro.MacroBase):

    """Upgrade from Apple to Fig."""

    def validate(self, config, meta_config=None):
        self.reports = []
        print("Current directory:", os.getcwd())
        return self.reports
