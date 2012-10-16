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


import re
import rose.config
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.reporter import Event
from rose.config_processor \
     import ConfigProcessError, ConfigProcessorBase, UnknownContentError


RE_NAMELIST_GROUP = re.compile(r"\Anamelist:(\w+).*\Z")


class ConfigProcessNamelistEvent(Event):

    LEVEL = Event.VV


class ConfigProcessorForNamelist(ConfigProcessorBase):

    KEY = "namelist"

    def process(self, config, item, orig_keys=None, orig_value=None, **kwargs):
        if item.endswith("(:)"):
            name = item[0:-2]
            sections = filter(lambda key: key.startswith(name),
                                          config.value.keys())
        else:
            sections = filter(lambda key: key == item, config.value.keys())
        if not sections:
            e = UnknownContentError(item)
            raise ConfigProcessError(orig_keys, orig_value, e)
        if item.endswith("(:)"):
            sections.sort(rose.config.sort_settings)
        ret = ""
        for section in sections:
            section_node = config.get([section], no_ignore=True)
            if section_node.state:
                continue
            group = RE_NAMELIST_GROUP.match(section).group(1)
            nlg = "&" + group + "\n"
            for key, node in sorted(section_node.value.items()):
                try:
                    value = env_var_process(node.value)
                except UnboundEnvironmentVariableError as e:
                    raise ConfigProcessError([section, key], node.value, e)
                else:
                    nlg += "%s=%s,\n" % (key, value)
            nlg += "/" + "\n"
            self.manager.event_handler(ConfigProcessNamelistEvent(nlg))
            ret += nlg
        return ret
