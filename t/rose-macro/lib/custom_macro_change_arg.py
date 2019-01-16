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

from rose.macro import MacroBase


class ArgumentTransformer(MacroBase):

    """Test class to change a setting to a user defined value."""

    def transform(self, config, meta_config=None, myvalue=None):
        """Perform the transform operation on the env switch."""
        keys = ["env", "MY_VALUE"]
        if config.get(keys) is not None:
            value = config.get(keys).value
            if value != myvalue:
                config.set(keys, myvalue)
                self.add_report(
                    "env", "MY_VALUE", value, '%s -> %s' % (value, myvalue))
        return config, self.reports
