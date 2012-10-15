#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import rose.macro


class NamelistIgnorer(rose.macro.MacroBase):

    """Test class to ignore and enable a section."""

    WARNING_ENABLED = "Enabled {0}"
    WARNING_IGNORED = "User-ignored {0}"

    def transform(self, config, meta_config=None):
        """Perform the transform operation on the section."""
        change_list = []
        section = "namelist:ignore_nl"
        node = config.get([section])
        if node is not None:
            if node.state:
                node.state = rose.config.ConfigNode.STATE_NORMAL
                info = self.WARNING_ENABLED.format(section)
            else:
                node.state = rose.config.ConfigNode.STATE_USER_IGNORED
                info = self.WARNING_IGNORED.format(section)
        self.add_report(change_list, section, None, None, info)
        return config, change_list
