# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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

import copy
import os

import rose.config
import rose.config_tree
import rose.env
import rose.macro
import rose.macros.rule
import rose.resource


class TriggerMacro(rose.macro.MacroBaseRoseEdit):

    """Class to load and check trigger dependencies."""

    ERROR_BAD_EXPR = "Invalid trigger expression: {0}"
    ERROR_BAD_STATE = "State should be {0}"
    ERROR_CYCLIC = 'Cyclic dependency detected: {0} to {1}'
    ERROR_DUPL_TRIG = "Badly defined trigger - {0} is 'duplicate'"
    ERROR_MISSING_METADATA = 'No metadata entry found'
    WARNING_STATE_CHANGED = '{0} -> {1}'
    IGNORED_STATUS_PARENT = 'from state of parent: {0}'
    IGNORED_STATUS_VALUE = ('from parent value: {0} '
                            'is not {2} ({1})')
    IGNORED_STATUS_VALUES = ('from parent value: {0} with {1} '
                             'is not in the allowed values: {2}')
    PARENT_VALUE = 'value {0}'
    _evaluated_rule_checks = {}
    MAX_STORED_RULE_CHECKS = 10000

    def _setup_triggers(self, meta_config):
        self.trigger_family_lookup = {}
        self._id_is_duplicate = {}  # Speedup dictionary.
        self.enabled_dict = {}
        self.evaluator = rose.macros.rule.RuleEvaluator()
        self.rec_rule = rose.macros.rule.REC_EXPR_IS_THIS_RULE
        for setting_id, sect_node in meta_config.value.items():
            if sect_node.is_ignored():
                continue
            opt_node = sect_node.get([rose.META_PROP_TRIGGER], no_ignore=True)
            if opt_node is not None:
                expr = opt_node.value
                id_value_dict = rose.variable.parse_trigger_expression(expr)
                for trig_id, values in id_value_dict.items():
                    if values == []:
                        id_value_dict.update({trig_id: [None]})
                self.trigger_family_lookup.update({setting_id: id_value_dict})
        self._trigger_involved_ids = self.get_all_ids()

    def transform(self, config, meta_config=None):
        """Apply metadata trigger expressions to variables."""
        self.reports = []
        meta_config = self._load_meta_config(config, meta_config)
        self._setup_triggers(meta_config)
        self.enabled_dict = {}
        self.ignored_dict = {}
        enabled = rose.config.ConfigNode.STATE_NORMAL
        trig_ignored = rose.config.ConfigNode.STATE_SYST_IGNORED
        user_ignored = rose.config.ConfigNode.STATE_USER_IGNORED
        state_map = {enabled: 'enabled     ',
                     trig_ignored: 'trig-ignored',
                     user_ignored: 'user-ignored'}
        change_list = []
        id_list = []
        prev_ignoreds = {trig_ignored: [], user_ignored: []}
        for keylist, node in config.walk():
            if len(keylist) == 1:
                n_id = keylist[0]
            else:
                n_id = self._get_id_from_section_option(*keylist)
            id_list.append(n_id)
            if node.state in prev_ignoreds:
                prev_ignoreds[node.state].append(n_id)
        for var_id in self.trigger_family_lookup:
            self.update(var_id, config, meta_config)
        for var_id in id_list:
            section, option = self._get_section_option_from_id(var_id)
            node = config.get([section, option])
            old, new = None, None
            if var_id in self.ignored_dict:
                node.state = trig_ignored
                if not any([var_id in v for k, v in prev_ignoreds.items()]):
                    old, new = state_map[enabled], state_map[trig_ignored]
            elif var_id in prev_ignoreds[trig_ignored]:
                node.state = enabled
                old, new = state_map[trig_ignored], state_map[enabled]
            elif (var_id in prev_ignoreds[user_ignored] and
                  var_id in self._trigger_involved_ids):
                node.state = enabled
                old, new = state_map[user_ignored], state_map[enabled]
            if old != new:
                info = self.WARNING_STATE_CHANGED.format(old, new)
                if option is None:
                    value = None
                else:
                    value = node.value
                self.add_report(section, option, value, info)
        return config, self.reports

    def update(self, var_id, config_data, meta_config):
        """Update enabled and ignored ids starting with var_id.

        var_id - a setting id to start the triggering update at.
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
        has_ignored_parent = True
        config_sections = self._get_config_sections(config_data)
        config_sections_duplicate_map = self._get_duplicate_config_sections(
            config_data, config_sections=config_sections)
        start_ids = [var_id]
        alt_ids = self._get_id_duplicates(
            var_id, config_data, meta_config,
            config_sections_duplicate_map=config_sections_duplicate_map
        )
        if alt_ids:
            start_ids = alt_ids
        id_stack = []
        for start_id in start_ids:
            if (start_id in self.enabled_dict and
                    start_id not in self.ignored_dict):
                has_ignored_parent = False
            if not sum([start_id in v for v in
                        self.trigger_family_lookup.values()]):
                has_ignored_parent = False
            section, option = self._get_section_option_from_id(start_id)
            is_node_present = self._get_config_has_id(config_data, start_id)
            if section in self.ignored_dict and option is not None:
                has_ignored_parent = True
            has_ignored_parent = has_ignored_parent or not is_node_present
            id_stack.append((start_id, has_ignored_parent))
        update_id_list = []
        while id_stack:
            this_id, has_ignored_parent = id_stack[0]
            alt_ids = self._get_id_duplicates(
                this_id, config_data, meta_config,
                config_sections_duplicate_map=config_sections_duplicate_map
            )
            if alt_ids:
                this_id = alt_ids.pop(0)
            for alt_id in alt_ids:
                id_stack.insert(1, (alt_id, has_ignored_parent))
            is_duplicate = self._check_is_id_dupl(this_id, meta_config)
            # Triggered sections need their options to trigger sub children.
            if this_id in config_sections:
                options = []
                for option in self._get_config_section_options(config_data,
                                                               this_id):
                    skip_id = self._get_id_from_section_option(
                        this_id, option)
                    if skip_id in self.trigger_family_lookup:
                        id_stack.insert(1, (skip_id, has_ignored_parent))
            update_id_list.append(this_id)
            if not self.check_is_id_trigger(this_id, meta_config):
                id_stack.pop(0)
                continue
            if not has_ignored_parent:
                section, option = self._get_section_option_from_id(this_id)
                is_node_present = self._get_config_has_id(
                    config_data, this_id)
                value = self._get_config_id_value(
                    config_data, this_id)
                if option is None and is_node_present:
                    value = True
            # Check the children of this id
            id_val_map = self._get_family_dict(
                this_id, config_data, meta_config)
            for child_id, vals in id_val_map.items():
                if has_ignored_parent or value is None:
                    help_text = self.IGNORED_STATUS_PARENT.format(this_id)
                    self.ignored_dict.setdefault(child_id, {})
                    self.ignored_dict[child_id].update({this_id: help_text})
                    if child_id in self.enabled_dict:
                        child_list = self.enabled_dict[child_id]
                        if this_id in child_list:
                            child_list.remove(this_id)
                        if not child_list:
                            self.enabled_dict.pop(child_id)
                    id_stack.insert(1, (child_id, True))
                else:  # Enabled parent
                    if vals == [None]:
                        # Enabled parent with a value, don't care what it is.
                        self.enabled_dict.setdefault(child_id, [])
                        if this_id not in self.enabled_dict[child_id]:
                            self.enabled_dict[child_id].append(this_id)
                        if this_id in self.ignored_dict.get(child_id, {}):
                            self.ignored_dict[child_id].pop(this_id)
                        if (child_id in self.ignored_dict and
                                self.ignored_dict[child_id] == {}):
                            self.ignored_dict.pop(child_id)
                        id_stack.insert(1, (child_id, False))
                    elif not self._check_values_ok(value, this_id, vals):
                        # Enabled parent, with the wrong values.
                        repr_value = self.PARENT_VALUE.format(value)
                        if len(vals) == 1:
                            help_text = self.IGNORED_STATUS_VALUE.format(
                                this_id, repr_value, repr(vals[0]))
                        else:
                            help_text = self.IGNORED_STATUS_VALUES.format(
                                this_id, repr_value, repr(vals))
                        self.ignored_dict.setdefault(child_id, {})
                        self.ignored_dict[child_id].update(
                            {this_id: help_text})
                        if child_id in self.enabled_dict:
                            child_list = self.enabled_dict[child_id]
                            if this_id in child_list:
                                child_list.remove(this_id)
                            if not child_list:
                                self.enabled_dict.pop(child_id)
                        id_stack.insert(1, (child_id, True))
                    else:
                        # Enabled parent, value is ok.
                        self.enabled_dict.setdefault(child_id, [])
                        if this_id not in self.enabled_dict[child_id]:
                            self.enabled_dict[child_id].append(this_id)
                        if this_id in self.ignored_dict.get(child_id, {}):
                            self.ignored_dict[child_id].pop(this_id)
                        if (child_id in self.ignored_dict and
                                self.ignored_dict[child_id] == {}):
                            self.ignored_dict.pop(child_id)
                        id_stack.insert(1, (child_id, False))
            id_stack.pop(0)
        return update_id_list

    def validate(self, config, meta_config=None):
        self.reports = []
        if meta_config is None:
            meta_config = rose.config.ConfigNode()
        if not hasattr(self, 'trigger_family_lookup'):
            self._setup_triggers(meta_config)
        enabled = rose.config.ConfigNode.STATE_NORMAL
        trig_ignored = rose.config.ConfigNode.STATE_SYST_IGNORED
        user_ignored = rose.config.ConfigNode.STATE_USER_IGNORED
        state_map = {enabled: 'enabled     ',
                     trig_ignored: 'trig-ignored',
                     user_ignored: 'user-ignored'}

        invalid_trigger_reports = self.validate_dependencies(config,
                                                             meta_config)
        if invalid_trigger_reports:
            return invalid_trigger_reports
        macro_config = copy.deepcopy(config)
        trig_config, reports = self.transform(macro_config, meta_config)
        transform_reports = copy.deepcopy(reports)
        del self.reports[:]
        for report in transform_reports:
            config_node = config.get([report.section, report.option])
            trig_config_node = trig_config.get([report.section, report.option])
            if report.option is None:
                value = None
            else:
                value = trig_config_node.value
            after_state_string = state_map[trig_config_node.state].strip()
            info = self.ERROR_BAD_STATE.format(after_state_string)
            self.add_report(report.section, report.option,
                            value, info)
        return self.reports

    def validate_dependencies(self, config, meta_config):
        """Validate the trigger setup - e.g. check for cyclic dependencies."""
        self.reports = []
        if meta_config is None:
            meta_config = rose.config.ConfigNode()
        if not hasattr(self, 'trigger_family_lookup'):
            self._setup_triggers(meta_config)
        config_sections = config.value.keys()
        meta_settings = [k for k in meta_config.value.keys()
                         if not meta_config.value[k].is_ignored()]
        allowed_repetitions = {}
        trigger_ids = self.trigger_family_lookup.keys()
        trigger_ids.sort()
        for var_id in trigger_ids:
            allowed_repetitions[var_id] = 0
        for id_value_dict in self.trigger_family_lookup.values():
            for var_id in id_value_dict:
                allowed_repetitions.setdefault(var_id, 0)
                allowed_repetitions[var_id] += 1
        for start_id in trigger_ids:
            id_value_dict = self._get_family_dict(start_id, config,
                                                  meta_config)
            triggered_ids = id_value_dict.keys()
            triggered_ids.sort()
            if self._check_is_id_dupl(start_id, meta_config):
                st_sect, st_opt = self._get_section_option_from_id(start_id)
                for tr_id in triggered_ids:
                    tr_sect, tr_opt = self._get_section_option_from_id(tr_id)
                    if tr_sect != st_sect:
                        return self._get_error_report_for_id(
                            start_id, config,
                            self.ERROR_DUPL_TRIG.format(st_sect))
            for value_list in id_value_dict.values():
                for string in [s for s in value_list if s is not None]:
                    if self.rec_rule.search(string):
                        try:
                            self.evaluate_trig_rule(string, start_id, '')
                        except rose.macros.rule.RuleValueError:
                            continue
                        except Exception:
                            return self._get_error_report_for_id(
                                start_id, config,
                                self.ERROR_BAD_EXPR.format(string))
            stack = [(start_id, triggered_ids)]
            id_list = []
            while stack:
                var_id, child_ids = stack[0]
                base_id = self._get_stripped_id(var_id, meta_config)
                if base_id not in meta_settings:
                    return self._get_error_report_for_id(
                        var_id, config, self.ERROR_MISSING_METADATA)
                id_list.append(var_id)
                child_ids.sort()
                if var_id in config_sections:
                    child_ids += config.get([var_id]).value.keys()
                for child_id in child_ids:
                    base_id = self._get_stripped_id(child_id, meta_config)
                    if base_id not in meta_settings:
                        return self._get_error_report_for_id(
                            child_id, config, self.ERROR_MISSING_METADATA)
                    if child_id in self.trigger_family_lookup:
                        grandchildren = (
                            self.trigger_family_lookup[child_id].keys())
                        grandchildren.sort()
                        stack.insert(1, (child_id, grandchildren))
                        if (id_list.count(child_id) + 1 >
                                allowed_repetitions[child_id] and
                                id_list.count(child_id) >= 2):
                            # Then it may be looping cyclically.
                            duplicate_seq = self._get_dup_sequence(id_list,
                                                                   child_id)
                            if duplicate_seq:
                                return self._get_error_report_for_id(
                                    var_id, config,
                                    self.ERROR_CYCLIC.format(child_id, var_id))
                stack.pop(0)
        return []

    def _get_duplicate_config_sections(self, config_data,
                                       config_sections=None):
        if config_sections is None:
            config_sections = self._get_config_sections(config_data)
        config_sections_duplicate_map = {}
        for section in config_sections:
            if "(" in section:
                base_section = section.split("(")[0]
                config_sections_duplicate_map.setdefault(base_section, [])
                config_sections_duplicate_map[base_section].append(section)
        return config_sections_duplicate_map

    def _get_family_dict(self, setting_id, config_data, meta_config):
        if self._check_is_id_dupl(setting_id, meta_config):
            sect, opt = self._get_section_option_from_id(setting_id)
            base_sect = rose.macro.REC_ID_STRIP.sub("", sect)
            trig_id = self._get_id_from_section_option(base_sect, opt)
            items = self.trigger_family_lookup.get(trig_id, {}).items()
            for i, (child_id, vals) in enumerate(items):
                ch_sect, ch_opt = self._get_section_option_from_id(child_id)
                if rose.macro.REC_ID_STRIP.sub("", ch_sect) == base_sect:
                    new_id = self._get_id_from_section_option(sect, ch_opt)
                    items[i] = (new_id, vals)
            return dict(items)
        items = self.trigger_family_lookup.get(setting_id, {}).items()
        dupl_adjusted_items = []
        while items:
            child_id, vals = items.pop(0)
            alt_ids = self._get_id_duplicates(
                child_id, config_data, meta_config)
            if alt_ids:
                for alt_id in alt_ids:
                    dupl_adjusted_items.append((alt_id, vals))
            else:
                dupl_adjusted_items.append((child_id, vals))
        return dict(dupl_adjusted_items)

    def _get_id_duplicates(self, setting_id, config_data, meta_config,
                           config_sections_duplicate_map=None):
        dupl_ids = []
        if self._check_is_id_dupl(setting_id, meta_config):
            sect, opt = self._get_section_option_from_id(setting_id)
            if config_sections_duplicate_map is None:
                config_sections_duplicate_map = (
                    self._get_duplicate_config_sections(config_data))
            for section in config_sections_duplicate_map.get(sect, []):
                new_id = self._get_id_from_section_option(section, opt)
                dupl_ids.append(new_id)
        return dupl_ids

    def _check_is_id_dupl(self, setting_id, meta_config):
        if setting_id not in self._id_is_duplicate:
            sect, opt = self._get_section_option_from_id(setting_id)
            # Note: when modifier metadata ticket goes in, change the regex.
            sect = rose.macro.REC_ID_STRIP.sub("", sect)
            node = meta_config.get([sect, rose.META_PROP_DUPLICATE])
            self._id_is_duplicate[setting_id] = (
                node is not None and node.value == rose.META_PROP_VALUE_TRUE)
        return self._id_is_duplicate[setting_id]

    def _get_stripped_id(self, setting_id, meta_config):
        if self._check_is_id_dupl(setting_id, meta_config):
            sect, opt = self._get_section_option_from_id(setting_id)
            base_sect = rose.macro.REC_ID_STRIP.sub("", sect)
            return self._get_id_from_section_option(base_sect, opt)
        return setting_id

    def check_is_id_trigger(self, setting_id, meta_config):
        return (self._get_stripped_id(setting_id, meta_config) in
                self.trigger_family_lookup)

    def _get_error_report_for_id(self, variable_id, config, error_string):
        section, option = self._get_section_option_from_id(variable_id)
        node = config.get([section, option])
        value = None if node is None else node.value
        self.add_report(section, option, value, error_string)
        return self.reports

    def _get_dup_sequence(self, id_list, child_id):
        """Check that the last two sequences for child_id are not equal."""
        id_copy_list = [i for i in id_list]
        id_copy_list.reverse()
        index_1 = id_copy_list.index(child_id)
        if index_1 == 0:
            return id_copy_list
        index_2 = id_copy_list.index(child_id, index_1 + 1)
        if (id_copy_list[:index_1] == id_copy_list[index_1 + 1: index_2]):
            return [i for i in reversed(id_copy_list[:index_2])]
        return []

    def _check_values_ok(self, value, setting_id, allowed_values):
        """Check whether a value of setting_id matches any allowed values."""
        for string in allowed_values:
            if value is not None and self.rec_rule.search(string):
                if self.evaluate_trig_rule(string, setting_id, value):
                    return True
            else:
                if string == value:
                    return True
        return rose.env.contains_env_var(value)

    def evaluate_trig_rule(self, rule, setting_id, value):
        """Launch an evaluation of a custom trigger expression."""
        try:
            return self._evaluated_rule_checks[(rule, value)]
        except KeyError:
            section, option = self._get_section_option_from_id(setting_id)
            tiny_config = rose.config.ConfigNode()
            tiny_config.set([section, option], value)
            tiny_meta_config = rose.config.ConfigNode()
            check_failed = self.evaluator.evaluate_rule(
                rule, setting_id, tiny_config, tiny_meta_config)
            if len(self._evaluated_rule_checks) > self.MAX_STORED_RULE_CHECKS:
                self._evaluated_rule_checks.popitem()
            self._evaluated_rule_checks[(rule, value)] = check_failed
            return check_failed

    def get_all_ids(self):
        """Return all setting ids involved in the triggers."""
        ids = []
        for trigger_id in self.trigger_family_lookup.keys():
            ids.append(trigger_id)
        for id_value_dict in self.trigger_family_lookup.values():
            for triggered_id in id_value_dict:
                if triggered_id not in ids:
                    ids.append(triggered_id)
        return ids
