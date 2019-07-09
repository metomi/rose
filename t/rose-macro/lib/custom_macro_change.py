#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
#
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

import metomi.rose.macro


class LogicalTransformer(metomi.rose.macro.MacroBase):

    """Test class to change the value of a boolean environment variable."""

    WARNING_CHANGED_VALUE = "{0} -> {1}"

    def transform(self, config, meta_config=None):
        """Perform the transform operation on the env switch."""
        self.reports = []
        if config.get(["env", "TRANSFORM_SWITCH"]) is not None:
            value = config.get(["env", "TRANSFORM_SWITCH"]).value
            if value == metomi.rose.TYPE_BOOLEAN_VALUE_FALSE:
                new_value = metomi.rose.TYPE_BOOLEAN_VALUE_TRUE
            else:
                new_value = metomi.rose.TYPE_BOOLEAN_VALUE_FALSE
            config.set(["env", "TRANSFORM_SWITCH"], new_value)
            info = self.WARNING_CHANGED_VALUE.format(value, new_value)
            self.add_report("env", "TRANSFORM_SWITCH", value, info)
        return config, self.reports
