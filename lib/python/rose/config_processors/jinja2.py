# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
#-----------------------------------------------------------------------------
"""Process a section in a rose.config.ConfigNode into a Jinja2 template."""

from rose.config_processor import ConfigProcessorBase


class ConfigProcessorForJinja2(ConfigProcessorBase):

    KEY = "jinja2"

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Return a Jinja2 template string for a section in "config"."""
        ret = ""
        section = config.get([item], no_ignore=True)
        if section is not None:
            for key, node in sorted(section.value.items()):
                if not node.is_ignored():
                    ret += "{%% set %s=%s %%}\n" % (key, node.value)
        return ret
