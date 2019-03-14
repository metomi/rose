#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
# -----------------------------------------------------------------------------

import rose.macro


class LogicalTransformer(rose.macro.MacroBase):

    """Test class to change the value of a boolean environment variable."""

    WARNING_CHANGED_VALUE = "{0} -> {1}"

    def transform(self, config, meta_config=None):
        """Perform the transform operation on the env switch."""
        if config.get(["env", "TRANSFORM_SWITCH"]) is not None:
            value = config.get(["env", "TRANSFORM_SWITCH"]).value
            if value == rose.TYPE_BOOLEAN_VALUE_FALSE:
                new_value = rose.TYPE_BOOLEAN_VALUE_TRUE
            else:
                new_value = rose.TYPE_BOOLEAN_VALUE_FALSE
            config.set(["env", "TRANSFORM_SWITCH"], new_value)
            info = self.WARNING_CHANGED_VALUE.format(value, new_value)
            self.add_report("env", "TRANSFORM_SWITCH", value, info)
        return config, self.reports
