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

import rose.macro


class InvalidCommentsTransformer(rose.macro.MacroBase):

    """Test class to return invalid comments."""

    WARNING_CHANGED_COMMENTS = "{0} -> {1} (invalid comments)"

    def transform(self, config, meta_config=None):
        """Return invalid node comments."""
        self.reports = []
        node = config.get(["env", "TRANSFORM_SWITCH"])
        old_comments = node.comments
        node.comments = "?"
        info = self.WARNING_CHANGED_COMMENTS.format(old_comments,
                                                    node.comments)
        self.add_report("env", "TRANSFORM_SWITCH", node.value, info)
        return config, self.reports


class InvalidConfigKeysTransformer(rose.macro.MacroBase):

    """Test class to return invalid comments."""

    WARNING_ADDED_CONFIG_KEYS = "added {0}"

    def transform(self, config, meta_config=None):
        """Return invalid config keys."""
        self.reports = []
        config.set([1, 2], "3")
        info = self.WARNING_ADDED_CONFIG_KEYS.format([1, 2])
        self.add_report("1", "2", "3", info)
        return config, self.reports


class InvalidConfigObjectTransformer(rose.macro.MacroBase):

    """Test class to return invalid configs."""

    def transform(self, config, meta_config=None):
        """Return an invalid config object."""
        self.reports = []
        return None, self.reports


class InvalidStateTransformer(rose.macro.MacroBase):

    """Test class to return an invalid state."""

    WARNING_CHANGED_STATE = "{0} -> {1} (invalid state)"

    def transform(self, config, meta_config=None):
        """Return an invalid node state."""
        self.reports = []
        node = config.get(["env", "TRANSFORM_SWITCH"])
        old_state = node.state
        node.state = "dunno"
        info = self.WARNING_CHANGED_STATE.format(old_state, node.state)
        self.add_report("env", "TRANSFORM_SWITCH", node.value, info)
        return config, self.reports


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
