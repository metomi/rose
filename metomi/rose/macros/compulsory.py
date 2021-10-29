# Copyright (C) British Crown (Met Office) & Contributors.
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


import metomi.rose.config
import metomi.rose.macro
import metomi.rose.variable

_OPTIONS_KEY = "options"
_REPORTED_SECTION_KEY = "reported config sect"
_SECTION_IS_COMPULSORY_KEY = "section is compulsory"


class CompulsoryChecker(metomi.rose.macro.MacroBaseRoseEdit):

    """Returns sections and options that are compulsory but missing.

    It also returns sections or options that are compulsory but
    user-ignored.

    """

    WARNING_COMPULSORY_SECT_MISSING = (
        'Section set as compulsory, but ' 'not in configuration.'
    )
    WARNING_COMPULSORY_OPT_MISSING = (
        'Variable set as compulsory, but ' 'not in configuration.'
    )
    WARNING_COMPULSORY_USER_IGNORED = (
        'Compulsory settings should not be ' 'user-ignored.'
    )

    def __init__(self, *args, **kwargs):
        self.basic_section_aliases = {}
        self.alias_section_to_basics = {}
        self.duplicate_section_default = {}
        self.compulsory_data = None
        super(CompulsoryChecker, self).__init__(*args, **kwargs)

    def get_compulsory_data(self, meta_config):
        """Return a list of compulsory=true basic (no duplicate info) ids."""
        compulsory_data = {}
        for setting_id, sect_node in meta_config.value.items():
            if sect_node.is_ignored() or isinstance(sect_node.value, str):
                continue
            if (
                sect_node.get_value([metomi.rose.META_PROP_COMPULSORY])
                == metomi.rose.META_PROP_VALUE_TRUE
            ):
                config_sect, config_opt = self._get_section_option_from_id(
                    setting_id
                )
                compulsory_data.setdefault(
                    config_sect,
                    {
                        _SECTION_IS_COMPULSORY_KEY: False,
                        _REPORTED_SECTION_KEY: config_sect,
                        _OPTIONS_KEY: [],
                    },
                )
                if config_opt is None:
                    compulsory_data[config_sect][
                        _SECTION_IS_COMPULSORY_KEY
                    ] = True
                else:
                    compulsory_data[config_sect][_OPTIONS_KEY].append(
                        config_opt
                    )
                if (
                    sect_node.get_value([metomi.rose.META_PROP_DUPLICATE])
                    == metomi.rose.META_PROP_VALUE_TRUE
                ):
                    compulsory_data[config_sect][
                        _REPORTED_SECTION_KEY
                    ] = config_sect + "({0})".format(
                        metomi.rose.CONFIG_SETTING_INDEX_DEFAULT
                    )
        return compulsory_data

    def validate(self, config_data, meta_config):
        """Return a list of compulsory-related errors, if any.

        config_data - a metomi.rose.config.ConfigNode or a dictionary that
        looks like this:
        {"sections":
            {"namelist:foo": metomi.rose.section.Section instance,
             "env": metomi.rose.section.Section instance},
         "variables":
            {"namelist:foo": [metomi.rose.variable.Variable instance,
                              metomi.rose.variable.Variable instance],
             "env": [metomi.rose.variable.Variable instance]
            }
        }
        meta_config - a metomi.rose.config.ConfigNode.

        """
        return self.validate_settings(config_data, meta_config)

    def validate_settings(
        self, config_data, meta_config, only_these_sections=None
    ):
        """Return a list of compulsory-related errors, if any.

        config_data - a metomi.rose.config.ConfigNode or a dictionary that
        looks like this:
        {"sections":
            {"namelist:foo": metomi.rose.section.Section instance,
             "env": metomi.rose.section.Section instance},
         "variables":
            {"namelist:foo": [metomi.rose.variable.Variable instance,
                              metomi.rose.variable.Variable instance],
             "env": [metomi.rose.variable.Variable instance]
            }
        }
        meta_config - a metomi.rose.config.ConfigNode.
        only_these_sections (default None) - a list of sections to
        examine. If specified, checking for other sections will be
        skipped.

        """
        self.reports = []
        if self.compulsory_data is None:
            self.compulsory_data = self.get_compulsory_data(meta_config)
        self._generate_aliases_for_sections(config_data)
        if only_these_sections is None:
            basic_sections_to_check = self.compulsory_data.keys()
        else:
            basic_sections_to_check = []
            alias_sections_to_check = []
            for section in list(only_these_sections):
                basic_sections_to_check.extend(
                    self.alias_section_to_basics.get(section, [section])
                )
                alias_sections_to_check.extend(
                    self.basic_section_aliases.get(section, [section])
                )
        check_user_ignored_ids = []
        for basic_section in basic_sections_to_check:
            section_data = self.compulsory_data.get(basic_section)
            if section_data is None:
                # This happens when an only_these_section is not compulsory.
                continue

            # Find all sections in config_data that belong to basic_section.
            present_section_aliases = []
            for alias_section in self.basic_section_aliases.get(
                basic_section, []
            ):
                if self._get_config_has_id(config_data, alias_section):
                    present_section_aliases.append(alias_section)
                    if section_data[_SECTION_IS_COMPULSORY_KEY]:
                        check_user_ignored_ids.append(alias_section)

            if not present_section_aliases:
                # No sections in config_data that belong to basic_section.
                if section_data[_SECTION_IS_COMPULSORY_KEY]:
                    self.add_report(
                        section_data[_REPORTED_SECTION_KEY],
                        None,
                        None,
                        self.WARNING_COMPULSORY_SECT_MISSING,
                    )
                continue

            if not section_data[_OPTIONS_KEY]:
                # There are no compulsory options set for basic_section.
                continue

            # Check for compulsory options in the present sections.
            for alias_section in present_section_aliases:
                if (
                    only_these_sections is not None
                    and alias_section not in alias_sections_to_check
                ):
                    continue
                for option in section_data[_OPTIONS_KEY]:
                    present_option_aliases = []
                    for alias_option in self._get_config_section_options(
                        config_data, alias_section
                    ):
                        if option == alias_option or (
                            alias_option.startswith(option)
                            and metomi.rose.macro.REC_ID_STRIP_DUPL.sub(
                                "", alias_option
                            )
                            == option
                        ):
                            setting_id = self._get_id_from_section_option(
                                alias_section, alias_option
                            )
                            check_user_ignored_ids.append(setting_id)
                            present_option_aliases.append(alias_option)
                    if not present_option_aliases:
                        self.add_report(
                            alias_section,
                            option,
                            None,
                            self.WARNING_COMPULSORY_OPT_MISSING,
                        )
        # Check that ids that we have found are not user-ignored.
        for setting_id in check_user_ignored_ids:
            if (
                self._get_config_id_state(config_data, setting_id)
                == metomi.rose.config.ConfigNode.STATE_USER_IGNORED
            ):
                value = self._get_config_id_value(config_data, setting_id)
                section, option = self._get_section_option_from_id(setting_id)
                self.add_report(
                    section,
                    option,
                    value,
                    self.WARNING_COMPULSORY_USER_IGNORED,
                )
        return self.reports

    def _generate_aliases_for_sections(self, config_data):
        """Generate maps of duplicate-vs-basic sections in config_data."""
        for section in self._get_config_sections(config_data):
            if section not in self.alias_section_to_basics:
                basic_section_no_modifier = metomi.rose.macro.REC_ID_STRIP.sub(
                    '', section
                )
                basic_section_keep_modifier = (
                    metomi.rose.macro.REC_ID_STRIP_DUPL.sub('', section)
                )
                basic_sections = set(
                    [basic_section_no_modifier, basic_section_keep_modifier]
                )
                for basic_section in basic_sections:
                    self.alias_section_to_basics.setdefault(section, [])
                    self.alias_section_to_basics[section].append(basic_section)
                    self.basic_section_aliases.setdefault(basic_section, [])
                    self.basic_section_aliases[basic_section].append(section)


class CompulsoryChanger(metomi.rose.macro.MacroBase):

    """Add sections and options that are compulsory but missing.

    Do not add sections or options that are compulsory but
    user-ignored.

    """

    ADD_COMPULSORY_SECT = 'Added compulsory section'
    ADD_COMPULSORY_OPT = 'Added compulsory option'
    ADD_MISSING_SECT = 'Added section for compulsory option'

    def transform(self, config, meta_config=None):
        """Return a config and a list of changes, if any."""
        checker = CompulsoryChecker()
        problem_list = checker.validate(config, meta_config)
        missing_sect_opts = []
        for report in problem_list:
            if report.info != checker.WARNING_COMPULSORY_USER_IGNORED:
                missing_sect_opts.append((report.section, report.option))
        missing_sect_opts.sort()
        missing_sect_opts.sort(key=lambda x: str(x[1]))
        for sect, opt in missing_sect_opts:
            if opt is None:
                config.set([sect])
                self.add_report(sect, opt, None, self.ADD_COMPULSORY_SECT)
        problem_list = checker.validate(config, meta_config)
        missing_sect_opts = []
        for report in problem_list:
            if report.info != checker.WARNING_COMPULSORY_USER_IGNORED:
                missing_sect_opts.append((report.section, report.option))
        missing_sect_opts.sort()
        missing_sect_opts.sort(key=lambda x: x[1])
        for sect, opt in missing_sect_opts:
            if opt is None:
                continue
            var_id = self._get_id_from_section_option(sect, opt)
            metadata = metomi.rose.macro.get_metadata_for_config_id(
                var_id, meta_config
            )
            value = metomi.rose.variable.get_value_from_metadata(metadata)
            config.set([sect, opt], value)
            self.add_report(sect, opt, value, self.ADD_COMPULSORY_OPT)
        return config, self.reports
