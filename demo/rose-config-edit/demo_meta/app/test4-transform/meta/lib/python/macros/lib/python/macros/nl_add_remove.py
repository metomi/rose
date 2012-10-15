#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) Crown copyright Met Office. All rights reserved.
#-----------------------------------------------------------------------------

import rose.macro


class NamelistAdderRemover(rose.macro.MacroBase):

    """Test class to add and remove a section."""

    WARNING_ADDED = "Added {0}"
    WARNING_REMOVED = "Removed {0}"

    def transform(self, config, meta_config=None):
        """Perform the transform operation on the env switch."""
        change_list = []
        section = "namelist:add_remove_nl"
        if config.get([section]) is not None:
            config.value.pop(section)
            info = self.WARNING_REMOVED.format(section)
        else:
            config.set([section])
            info = self.WARNING_ADDED.format(section)
        self.add_report(change_list, section, None, None,
                        info)
        return config, change_list
