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
"""Process namelist: sections in a rose.config.ConfigNode matching a name."""


from hashlib import md5
import os
import re
import rose.config
from rose.config_processor import ConfigProcessError
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.reporter import Event


RE_NAMELIST_GROUP = re.compile(r"\Anamelist:(\w+).*\Z")


class NamelistEvent(Event):

    LEVEL = Event.VV


class NamelistLocHandler(object):
    """Handler of namelists."""

    SCHEME = "namelist"

    def __init__(self, manager):
        self.manager = manager

    def can_pull(self, loc):
        return loc.name.startswith(self.SCHEME + ":")

    def parse(self, loc, config):
        """Set loc.scheme, loc.loc_type."""
        loc.scheme = self.SCHEME
        loc.loc_type = loc.TYPE_BLOB

    def pull(self, loc, config, work_dir):
        """If loc is in the file system, sets loc.cache to loc.name.

        Otherwise, raise an OSError.

        """
        if not loc.loc_type:
            self.parse(loc, config)
        m = md5()
        m.update(loc.name)
        base_name = m.hexdigest()
        loc.cache = os.path.join(work_dir, base_name)
        f = open(loc.cache, "wb")

        if loc.name.endswith("(:)"):
            name = loc.name[0:-2]
            sections = [k for k in config.value.keys() if k.startswith(name)]
        else:
            sections = [k for k in config.value.keys() if k == loc.name]
        if not sections:
            raise ValueError(loc.name)
        if loc.name.endswith("(:)"):
            sections.sort(rose.config.sort_settings)
        for section in sections:
            section_node = config.get([section], no_ignore=True)
            if section_node.state:
                continue
            group = RE_NAMELIST_GROUP.match(section).group(1)
            nlg = "&" + group + "\n"
            for key, node in sorted(section_node.value.items()):
                if node.state:
                    continue
                try:
                    value = env_var_process(node.value)
                except UnboundEnvironmentVariableError as e:
                    raise ConfigProcessError([section, key], node.value, e)
                nlg += "%s=%s,\n" % (key, value)
            nlg += "/" + "\n"
            f.write(nlg)
            self.manager.handle_event(NamelistEvent(nlg))

        f.close()
