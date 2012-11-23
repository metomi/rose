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
"""Process an env section in a rose.config.ConfigNode."""

import os
import re
from rose.env \
    import env_export, env_var_process, UnboundEnvironmentVariableError
from rose.reporter import Event
from rose.config_processor import ConfigProcessError, ConfigProcessorBase


class ConfigProcessorForEnv(ConfigProcessorBase):

    SCHEME = "env"

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Export environment variables in an env section in "config"."""
        env_node = config.get([item], no_ignore=True)
        if env_node is None:
            return
        if os.environ.has_key("UNDEF"):
            os.environ.pop("UNDEF")
        environ = {}
        if env_node and not env_node.state:
            for key, node in env_node.value.iteritems():
                if node.state:
                    continue
                try:
                    environ[key] = env_var_process(node.value)
                except UnboundEnvironmentVariableError as e:
                    raise ConfigProcessError([item, key], node.value, e)
                environ[key] = os.path.expanduser(environ[key]) # ~ expansion
        for key, value in sorted(environ.items()):
            env_export(key, value, self.manager.event_handler)
        return environ
