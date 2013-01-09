# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
import os
from tempfile import TemporaryFile


class ConfigProcessorForJinja2(ConfigProcessorBase):

    SCHEME = "jinja2"

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        """Process jinja2:* sections in "config"."""
        for key, node in sorted(config.value.items()):
            if (node.is_ignored() or
                not key.startswith(self.PREFIX) or
                not node.value):
                continue
            target = key[len(self.PREFIX):]
            if not os.access(target, os.F_OK | os.R_OK | os.W_OK):
                continue
            f = TemporaryFile()
            f.write("#!" + self.SCHEME + "\n")
            for k, n in sorted(node.value.items()):
                if not n.is_ignored():
                    f.write("{%% set %s=%s %%}\n" % (k, n.value))
            for line in open(target):
                if line.rstrip().lower() != ("#!" + self.SCHEME):
                    f.write(line)
            f.seek(0)
            open(target, "w").write(f.read())
            f.close()
