#!/usr/bin/env python3

import metomi.rose.macro


class Test(metomi.rose.macro.MacroBase):

    def validate(self, config, meta_config=None, answer=42,
                 optional_config_name=None):
        print('optional_config_name', optional_config_name,
              config['env']['ANSWER'].get_value())
        return self.reports
