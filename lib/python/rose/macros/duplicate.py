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

import re

import rose.macro


class DuplicateChecker(rose.macro.MacroBase):

    """Returns settings whose duplicate status does not match their name."""

    WARNING_DUPL_SECT_NO_NUM = ('incorrect "duplicate=true" metadata')
    WARNING_NUM_SECT_NO_DUPL = ('{0} requires "duplicate=true" metadata')

    def validate(self, config, meta_config=None):
        """Return a list of errors, if any."""
        meta_config = self._load_meta_config(config, meta_config)
        self.reports = []
        sect_error_no_dupl = {}
        sect_keys = config.value.keys()
        sorter = rose.config.sort_settings
        sect_keys.sort(sorter)
        for section in sect_keys:
            node = config.get([section])
            if not isinstance(node.value, dict):
                continue
            metadata = self.get_metadata_for_config_id(section, meta_config)
            duplicate = metadata.get(rose.META_PROP_DUPLICATE)
            is_duplicate = duplicate == rose.META_PROP_VALUE_TRUE
            basic_section = rose.macro.REC_ID_STRIP.sub("", section)
            if is_duplicate:
                if basic_section == section:
                    self.add_report(section, None, None,
                                    self.WARNING_DUPL_SECT_NO_NUM)
            elif section != basic_section:
                if basic_section not in sect_error_no_dupl:
                    sect_error_no_dupl.update({basic_section: 1})
                    no_index_section = rose.macro.REC_ID_STRIP_DUPL.sub(
                                                         "", section)
                    if no_index_section != section:
                        basic_section = no_index_section
                    warning = self.WARNING_NUM_SECT_NO_DUPL
                    self.add_report(section, None, None,
                                    warning.format(basic_section))
        return self.reports
