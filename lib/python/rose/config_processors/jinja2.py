# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
#-----------------------------------------------------------------------------
"""Process a section in a rose.config.ConfigNode into a Jinja2 template."""

from rose.config_processor import ConfigProcessError, ConfigProcessorBase
from rose.env import env_var_process, UnboundEnvironmentVariableError
import os
from tempfile import TemporaryFile


class ConfigProcessorForJinja2(ConfigProcessorBase):

    SCHEME = "jinja2"
    MSG_DONE = "{# Rose Configuration Insertion: Done #}\n"
    MSG_INIT = "{# Rose Configuration Insertion: Init #}\n"

    def process(self, conf_tree, item, orig_keys=None, orig_value=None,
                **kwargs):
        """Process [jinja2:*] in "conf_tree.node"."""
        for key, node in sorted(conf_tree.node.value.items()):
            if (node.is_ignored() or
                not key.startswith(self.PREFIX) or
                not node.value):
                continue
            target = key[len(self.PREFIX):]
            if not os.access(target, os.F_OK | os.R_OK | os.W_OK):
                continue
            f = TemporaryFile()
            f.write("#!" + self.SCHEME + "\n")
            f.write(self.MSG_INIT)
            for k, n in sorted(node.value.items()):
                if n.is_ignored():
                    continue
                try:
                    value = env_var_process(n.value)
                except UnboundEnvironmentVariableError as e:
                    raise ConfigProcessError([key, k], n.value, e)
                f.write("{%% set %s=%s %%}\n" % (k, value))
            f.write(self.MSG_DONE)
            line_n = 0
            is_in_old_insert = False
            for line in open(target):
                line_n += 1
                if line_n == 1 and line.rstrip().lower() == "#!" + self.SCHEME:
                    continue
                elif line_n == 2 and line == self.MSG_INIT:
                    is_in_old_insert = True
                    continue
                elif is_in_old_insert and line == self.MSG_DONE:
                    is_in_old_insert = False
                    continue
                elif is_in_old_insert:
                    continue
                f.write(line)
            f.seek(0)
            open(target, "w").write(f.read())
            f.close()
