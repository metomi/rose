# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
import os
from tempfile import NamedTemporaryFile

from rose.config_processor import ConfigProcessError, ConfigProcessorBase
from rose.cylc_templatevars import templatevar_eval
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.fs_util import FileSystemEvent


class ConfigProcessorForJinja2(ConfigProcessorBase):

    """Processor for [jinja2:FILE] sections in a runtime configuration."""

    SCHEME = "jinja2"
    ASSIGN_TEMPL = "{%% set %s=%s %%}\n"
    COMMENT_TEMPL = "{# %s #}\n"
    SCHEME_TEMPL = "#!%s\n"
    MSG_DONE = "Rose Configuration Insertion: Done"
    MSG_INIT = "Rose Configuration Insertion: Init"

    def process(self, conf_tree, item, orig_keys=None, orig_value=None,
                **kwargs):
        """Process [jinja2:*] in "conf_tree.node".

        Arguments:
            conf_tree:
                The relevant rose.config_tree.ConfigTree object with the full
                configuration.
            item: The current configuration item to process.
            orig_keys:
                The keys for locating the originating setting in conf_tree in a
                recursive processing. None implies a top level call.
            orig_value: The value of orig_keys in conf_tree.
            **kwargs:
                environ (dict): suite level environment variables.
        """
        for s_key, s_node in sorted(conf_tree.node.value.items()):
            if (s_node.is_ignored() or
                    not s_key.startswith(self.PREFIX) or
                    not s_node.value):
                continue
            target = s_key[len(self.PREFIX):]
            source = os.path.join(conf_tree.files[target], target)
            if not os.access(source, os.F_OK | os.R_OK):
                continue
            scheme_ln = self.SCHEME_TEMPL % self.SCHEME
            msg_init_ln = self.COMMENT_TEMPL % self.MSG_INIT
            msg_done_ln = self.COMMENT_TEMPL % self.MSG_DONE
            tmp_file = NamedTemporaryFile()
            tmp_file.write(scheme_ln)
            tmp_file.write(msg_init_ln)
            suite_variables = ['{']
            for key, node in sorted(s_node.value.items()):
                if node.is_ignored():
                    continue
                try:
                    value = env_var_process(node.value)
                except UnboundEnvironmentVariableError as exc:
                    raise ConfigProcessError([s_key, key], node.value, exc)
                else:
                    # forewarning of Cylc8 capabilities
                    try:
                        templatevar_eval(value)
                    except Exception as exc:  # purposefully vague
                        self.manager.handle_event(
                            exc,
                            level=1
                        )

                tmp_file.write(self.ASSIGN_TEMPL % (key, value))
                suite_variables.append("    '%s': %s," % (key, key))
            suite_variables.append('}')
            tmp_file.write(self.ASSIGN_TEMPL % ('ROSE_SUITE_VARIABLES',
                                                '\n'.join(suite_variables)))
            environ = kwargs.get("environ")
            if environ:
                tmp_file.write('[cylc]\n')
                tmp_file.write('    [[environment]]\n')
                for key, value in sorted(environ.items()):
                    tmp_file.write('        %s=%s\n' % (key, value))
            tmp_file.write(msg_done_ln)
            line_n = 0
            is_in_old_insert = False
            for line in open(source):
                line_n += 1
                if line_n == 1 and line.strip().lower() == scheme_ln.strip():
                    continue
                elif line_n == 2 and line == msg_init_ln:
                    is_in_old_insert = True
                    continue
                elif is_in_old_insert and line == msg_done_ln:
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
