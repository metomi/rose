#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rose.macro


class Test(rose.macro.MacroBase):

    def validate(self, config, meta_config=None, answer=42,
                 optional_config_name=None):
        print('optional_config_name', optional_config_name, \
               config['env']['ANSWER'].get_value())
        return self.reports
