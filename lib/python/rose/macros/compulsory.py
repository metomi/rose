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


class CompulsoryChecker(rose.macro.MacroBase):

    """Returns sections and options that are compulsory but missing.
    
    It also returns sections or options that are compulsory but
    user-ignored.
    
    """

    stored_compulsory_ids = None  # Speedup.
    WARNING_COMPULSORY_SECT_MISSING = ('Section set as compulsory, but '
                                       'not in configuration.')
    WARNING_COMPULSORY_OPT_MISSING = ('Variable set as compulsory, but '
                                      'not in configuration.')
    WARNING_COMPULSORY_USER_IGNORED = ('Compulsory settings should not be '
                                       'user-ignored.')

    def validate(self, config, meta_config=None):
        """Return a list of errors, if any."""
        self.reports = []
        meta_config = self._load_meta_config(config, meta_config)
        if not hasattr(self, 'section_to_basic_map'):
            self.section_to_basic_map = {}
            self.section_from_basic_map = {}
        for section, node in config.value.items():
            if not isinstance(node.value, dict):
                section = ""
            if section not in self.section_to_basic_map:
                basic_section = rose.macro.REC_ID_STRIP.sub('', section)
                self.section_to_basic_map.update({section: basic_section})
                self.section_from_basic_map.setdefault(basic_section, [])
                self.section_from_basic_map[basic_section].append(section)
        if self.stored_compulsory_ids is None:
            self.stored_compulsory_ids = []
            for setting_id, sect_node in meta_config.value.items():
                if sect_node.is_ignored():
                    continue
                for prop_opt, opt_node in sect_node.value.items():
                    if (prop_opt == rose.META_PROP_COMPULSORY and
                        not opt_node.is_ignored() and
                        opt_node.value == rose.META_PROP_VALUE_TRUE):
                        self.stored_compulsory_ids.append(setting_id)
        for setting_id in self.stored_compulsory_ids:
            section, option = self._get_section_option_from_id(setting_id)
            node = config.get([section, option])
            if node is None:
                for sect in self.section_from_basic_map.get(section, []):
                    if sect in config.value:
                        node = config.get([sect])
                        section = sect
                        break
                if node is None:
                    if option is None:
                        self.add_report(section, option, None,
                                        self.WARNING_COMPULSORY_SECT_MISSING)
                    else:
                        self.add_report(section, option, None,
                                        self.WARNING_COMPULSORY_OPT_MISSING)
                elif option is not None:
                    for opt, opt_node in node.value.items():
                        if (opt == option or
                            opt.startswith(option + "(")):
                            node = opt_node
                            option = opt
                            break
                    else:
                        self.add_report(section, option, None,
                                        self.WARNING_COMPULSORY_OPT_MISSING)
            if node is not None and node.state == node.STATE_USER_IGNORED:
                value = node.value
                if not isinstance(value, basestring):
                    value = None
                self.add_report(section, option, value,
                                self.WARNING_COMPULSORY_USER_IGNORED)
        return self.reports


class CompulsoryChanger(rose.macro.MacroBase):

    """Add sections and options that are compulsory but missing.

    Do not add sections or options that are compulsory but
    user-ignored.

    """

    ADD_COMPULSORY_SECT = ('Added compulsory section')
    ADD_COMPULSORY_OPT = ('Added compulsory option')

    def transform(self, config, meta_config=None):
        """Return a config and a list of changes, if any."""
        checker = CompulsoryChecker()
        problem_list = checker.validate(config, meta_config)
        missing_sect_opts = []
        for report in problem_list:
            if report.info != checker.WARNING_COMPULSORY_USER_IGNORED:
                missing_sect_opts.append((report.section, report.option))
        missing_sect_opts.sort()
        missing_sect_opts.sort(lambda x, y: cmp(x[1], y[1]))
        for sect, opt in missing_sect_opts:
            if opt is None:
                config.set([sect])
                self.add_report(sect, opt, None,
                                self.ADD_COMPULSORY_SECT)
                continue
            var_id = self._get_id_from_section_option(sect, opt)
            metadata = {}
            for key, node in meta_config.get([var_id]).value.items():
                if node.is_ignored():
                    continue
                metadata.update({key: node.value})
            value = rose.variable.get_value_from_metadata(metadata)
            config.set([sect, opt], value)
            self.add_report(sect, opt, value,
                            self.ADD_COMPULSORY_OPT)
        return config, self.reports
