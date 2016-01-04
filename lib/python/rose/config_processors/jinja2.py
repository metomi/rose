# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
"""Process a section in a rose.config.ConfigNode into a Jinja2 template."""

import filecmp
from rose.config_processor import ConfigProcessError, ConfigProcessorBase
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.fs_util import FileSystemEvent
import os
from tempfile import NamedTemporaryFile


class ConfigProcessorForJinja2(ConfigProcessorBase):

    """Processor for [jinja2:FILE] sections in a runtime configuration."""

    SCHEME = "jinja2"
    MSG_DONE = "{# Rose Configuration Insertion: Done #}\n"
    MSG_INIT = "{# Rose Configuration Insertion: Init #}\n"

    def process(self, conf_tree, item, orig_keys=None, orig_value=None, **_):
        """Process [jinja2:*] in "conf_tree.node"."""
        for s_key, s_node in sorted(conf_tree.node.value.items()):
            if (s_node.is_ignored() or
                    not s_key.startswith(self.PREFIX) or
                    not s_node.value):
                continue
            target = s_key[len(self.PREFIX):]
            source = os.path.join(conf_tree.files[target], target)
            if not os.access(source, os.F_OK | os.R_OK):
                continue
            tmp_file = NamedTemporaryFile()
            tmp_file.write("#!" + self.SCHEME + "\n")
            tmp_file.write(self.MSG_INIT)
            for key, node in sorted(s_node.value.items()):
                if node.is_ignored():
                    continue
                try:
                    value = env_var_process(node.value)
                except UnboundEnvironmentVariableError as exc:
                    raise ConfigProcessError([s_key, key], node.value, exc)
                tmp_file.write("{%% set %s=%s %%}\n" % (key, value))
            tmp_file.write(self.MSG_DONE)
            line_n = 0
            is_in_old_insert = False
            for line in open(source):
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
                tmp_file.write(line)
            tmp_file.seek(0)
            if os.access(target, os.F_OK | os.R_OK):
                if filecmp.cmp(target, tmp_file.name):  # identical
                    tmp_file.close()
                    continue
                else:
                    self.manager.fs_util.delete(target)
            # Write content to target
            target_file = open(target, "w")
            for line in tmp_file:
                target_file.write(line)
            event = FileSystemEvent(FileSystemEvent.INSTALL, target)
            self.manager.handle_event(event)
            tmp_file.close()
