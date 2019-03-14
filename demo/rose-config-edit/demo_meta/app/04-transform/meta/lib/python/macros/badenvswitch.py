#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
# -----------------------------------------------------------------------------

import rose.macro


class InvalidValueTransformer(rose.macro.MacroBase):

    """Test class to return an invalid value."""

    WARNING_CHANGED_VALUE = "{0} -> {1} (invalid value)"

    def transform(self, config, meta_config=None):
        """Return an invalid node value."""
        self.reports = []
        node = config.get(["env", "TRANSFORM_SWITCH"])
        config.set(["env", "TRANSFORM_SWITCH"], 0)
        info = self.WARNING_CHANGED_VALUE.format(node.value, "0")
        self.add_report("env", "TRANSFORM_SWITCH", "0", info)
        return config, self.reports
