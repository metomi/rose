# Copyright (C) British Crown (Met Office) & Contributors.
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
"""Process an env section in node of a metomi.rose.config_tree.ConfigTree."""

import os

from metomi.rose.config_processor import (
    ConfigProcessError,
    ConfigProcessorBase,
)
from metomi.rose.env import (
    UnboundEnvironmentVariableError,
    env_export,
    env_var_process,
)


class ConfigProcessorForEnv(ConfigProcessorBase):

    SCHEME = "env"

    def process(
        self, conf_tree, item, orig_keys=None, orig_value=None, **kwargs
    ):
        """Export environment variables in an [env] in "conf_tree.node"."""
        env_node = conf_tree.node.get([item], no_ignore=True)
        if env_node is None:
            return
        if "UNDEF" in os.environ:
            os.environ.pop("UNDEF")
        environ = {}
        if env_node and not env_node.state:
            for key, node in env_node.value.items():
                if node.state:
                    continue
                try:
                    environ[key] = env_var_process(node.value)
                except UnboundEnvironmentVariableError as exc:
                    raise ConfigProcessError([item, key], node.value, exc)
                environ[key] = os.path.expanduser(environ[key])  # ~ expansion
        for key, value in sorted(environ.items()):
            env_export(key, value, self.manager.event_handler)
        return environ
