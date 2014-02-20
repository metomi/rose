# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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

import re

import rose.config
import rose.macro
import rose.variable


class CompulsoryChecker(rose.macro.MacroBaseRoseEdit):

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

    def validate(self, config_data, meta_config):
        """Return a list of compulsory-related errors, if any.

        config_data - a rose.config.ConfigNode or a dictionary that
        looks like this:
        {"sections":
            {"namelist:foo": rose.section.Section instance,
             "env": rose.section.Section instance},
         "variables":
            {"namelist:foo": [rose.variable.Variable instance,
                              rose.variable.Variable instance],
             "env": [rose.variable.Variable instance]
            }
        }
        meta_config - a rose.config.ConfigNode.

        """
        return self.validate_settings(config_data, meta_config)

    def validate_settings(self, config_data, meta_config,
                          only_these_sections=None):
        """Return a list of compulsory-related errors, if any.

        config_data - a rose.config.ConfigNode or a dictionary that
        looks like this:
        {"sections":
            {"namelist:foo": rose.section.Section instance,
             "env": rose.section.Section instance},
         "variables":
            {"namelist:foo": [rose.variable.Variable instance,
                              rose.variable.Variable instance],
             "env": [rose.variable.Variable instance]
            }
        }
        meta_config - a rose.config.ConfigNode.
        only_these_sections (default None) - a list of sections to
        examine. If specified, checking for other sections will be
        skipped.

        """
        self.reports = []
        if not hasattr(self, 'section_to_basic_map'):
            self.section_to_basic_map = {}
            self.section_from_basic_map = {}
        for section in self._get_config_sections(config_data):
            if section not in self.section_to_basic_map:
                basic_section = rose.macro.REC_ID_STRIP.sub('', section)
                self.section_to_basic_map.update({section: basic_section})
                self.section_from_basic_map.setdefault(basic_section, [])
                self.section_from_basic_map[basic_section].append(section)
        if self.stored_compulsory_ids is None:
            # Build a cache of basic ids known to be compulsory.
            self.stored_compulsory_ids = []
            for setting_id, sect_node in meta_config.value.items():
                if sect_node.is_ignored() or isinstance(sect_node.value, str):
                    continue
                for prop_opt, opt_node in sect_node.value.items():
                    if (prop_opt == rose.META_PROP_COMPULSORY and
                        not opt_node.is_ignored() and
                        opt_node.value == rose.META_PROP_VALUE_TRUE):
                        self.stored_compulsory_ids.append(setting_id)
        check_user_ignored_ids = []
        for setting_id in self.stored_compulsory_ids:
            section, option = self._get_section_option_from_id(setting_id)
            if (only_these_sections is not None and
                    section not in only_these_sections):
                continue
            is_node_present = self._get_config_has_id(config_data, setting_id)
            if is_node_present:
                # It is present in the basic form - no duplicates/modifiers.
                check_user_ignored_ids.append(setting_id)
                continue
            # Look for duplicates/modifiers - e.g. for foo(1) instead of foo.
            found_the_section = False
            for sect in self.section_from_basic_map.get(section, []):
                # Loop through all known duplicate/modifiers for section.
                # This includes the section itself.
                sect_exists = self._get_config_has_id(config_data, sect)
                if sect_exists:
                    # A duplicate section exists - e.g. foo(1) for foo.
                    found_the_section = True
                    if option is None:
                        # The compulsory condition for section is OK.
                        check_user_ignored_ids.append(sect)
                        break
                    # We're looking for an option - look within the section.
                    found_the_option = False
                    for opt in self._get_config_section_options(
                            config_data, sect):
                        if (opt == option or
                            opt.startswith(option + "(")):
                            # The option is present or in duplicate form.
                            found_the_option = True
                            var_id = self._get_id_from_section_option(
                                sect, opt)
                            check_user_ignored_ids.append(var_id)
                    if not found_the_option:
                        # This section is missing our compulsory option.
                        self.add_report(
                            sect, option, None,
                            self.WARNING_COMPULSORY_OPT_MISSING
                        )
            if not found_the_section:
                if option is None:
                    # No valid duplicate sections found.
                    self.add_report(
                        section, None, None,
                        self.WARNING_COMPULSORY_SECT_MISSING
                    )
                else:
                    # No valid parent duplicate sections were found.
                    self.add_report(
                        section, option, None,
                        self.WARNING_COMPULSORY_OPT_MISSING
                    )
        for setting_id in check_user_ignored_ids:
            # These ids need checking to make sure they're not user-ignored.
            if (self._get_config_id_state(config_data, setting_id) ==
                    rose.config.ConfigNode.STATE_USER_IGNORED):
                value = self._get_config_id_value(config_data, setting_id)
                section, option = self._get_section_option_from_id(setting_id)
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
    ADD_MISSING_SECT = ('Added section for compulsory option')

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
            if config.get([sect]) is None:
                config.set([sect])
                self.add_report(sect, None, None,
                                self.ADD_MISSING_SECT)
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
