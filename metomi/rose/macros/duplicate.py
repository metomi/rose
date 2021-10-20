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

from functools import cmp_to_key

import metomi.rose.macro


class DuplicateChecker(metomi.rose.macro.MacroBase):

    """Returns settings whose duplicate status does not match their name."""

    WARNING_DUPL_SECT_NO_NUM = 'incorrect "duplicate=true" metadata'
    WARNING_NUM_SECT_NO_DUPL = '{0} requires "duplicate=true" metadata'

    def validate(self, config, meta_config=None):
        """Return a list of errors, if any."""
        self.reports = []
        sect_error_no_dupl = {}
        sect_keys = list(config.value)
        sorter = metomi.rose.config.sort_settings
        sect_keys.sort(key=cmp_to_key(sorter))
        for section in sect_keys:
            node = config.get([section])
            if not isinstance(node.value, dict):
                continue
            metadata = self.get_metadata_for_config_id(section, meta_config)
            duplicate = metadata.get(metomi.rose.META_PROP_DUPLICATE)
            is_duplicate = duplicate == metomi.rose.META_PROP_VALUE_TRUE
            basic_section = metomi.rose.macro.REC_ID_STRIP.sub("", section)
            if is_duplicate:
                if basic_section == section:
                    self.add_report(
                        section, None, None, self.WARNING_DUPL_SECT_NO_NUM
                    )
            elif section != basic_section:
                if basic_section not in sect_error_no_dupl:
                    sect_error_no_dupl.update({basic_section: 1})
                    no_index_section = metomi.rose.macro.REC_ID_STRIP_DUPL.sub(
                        "", section
                    )
                    if no_index_section != section:
                        basic_section = no_index_section
                    warning = self.WARNING_NUM_SECT_NO_DUPL
                    if self._get_has_metadata(
                        metadata, basic_section, meta_config
                    ):
                        self.add_report(
                            section, None, None, warning.format(basic_section)
                        )
        return self.reports

    def _get_has_metadata(self, metadata, basic_section, meta_config):
        if list(metadata) != ["id"]:
            return True
        for meta_keys, meta_node in meta_config.walk(no_ignore=True):
            meta_section = meta_keys[0]
            if len(meta_keys) > 1:
                continue
            if (
                meta_section == basic_section
                or meta_section.startswith(
                    basic_section + metomi.rose.CONFIG_DELIMITER
                )
            ) and isinstance(meta_node.value, dict):
                return True
        return False
