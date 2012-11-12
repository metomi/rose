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

import re

import rose.macro


class DuplicateChecker(rose.macro.MacroBase):

    """Returns settings whose duplicate status does not match their name."""

    WARNING_DUPL_SECT_NO_NUM = ('Section is "duplicate", but '
                                'has no index or modifier.')
    WARNING_NUM_SECT_NO_DUPL = ('Section has an an index or modifier, but '
                                'is not "duplicate"')

    def validate(self, config, meta_config=None):
        """Return a list of errors, if any."""
        meta_config = self._load_meta_config(config, meta_config)
        self.reports = []
        sections_with_duplicate = []
        for setting_id, sect_node in meta_config.value.items():
            if sect_node.is_ignored():
                continue
            section, option = self._get_section_option_from_id(setting_id)
            if option is not None:
                continue
            for prop_opt, opt_node in sect_node.value.items():
                if (prop_opt == rose.META_PROP_DUPLICATE and
                    not opt_node.is_ignored() and
                    opt_node.value == rose.META_PROP_VALUE_TRUE):
                    sections_with_duplicate.append(setting_id)
        basic_sections_with_errors = []
        config_sections = config.value.keys()
        config_sections.sort(rose.config.sort_settings)
        for section in config_sections:
            node = config.get([section])
            if not isinstance(node.value, dict):
                continue
            basic_section = rose.macro.REC_ID_STRIP.sub('', section)
            if basic_section in sections_with_duplicate:
                if basic_section == section:
                    self.add_report(section, None, None,
                                    self.WARNING_DUPL_SECT_NO_NUM)
            elif section != basic_section:
                if basic_section not in basic_sections_with_errors:
                    basic_sections_with_errors.append(basic_section)
                    self.add_report(section, None, None,
                                    self.WARNING_NUM_SECT_NO_DUPL)
        return self.reports
