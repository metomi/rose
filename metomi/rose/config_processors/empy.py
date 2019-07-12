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
"""Process a section in a metomi.rose.config.ConfigNode into a EmPy template.
"""


from metomi.rose.config_processors.jinja2 import ConfigProcessorForJinja2


class ConfigProcessorForEmPy(ConfigProcessorForJinja2):

    """Processor for [empy:FILE] sections in a runtime configuration."""

    SCHEME = "empy"
    ASSIGN_TEMPL = "@{%s=%s}@\n"
    COMMENT_TEMPL = "@# %s\n"


del ConfigProcessorForJinja2  # avoid loading it more than once
