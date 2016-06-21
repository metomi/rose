#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rose.macro


class Test(rose.macro.MacroBase):

    def validate(self, config, meta_config=None, answer=42,
                 optional_config_name=None):
        return self.reports
