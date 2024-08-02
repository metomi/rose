# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2020 British Crown (Met Office) & Contributors.
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
"""This module handles grouped operations.

These are supersets of section and variable operations, such as adding
a section together with some variables, mass removal of sections,
copying sections with their variables, and so on.

"""

import copy
import re
import time

import rose.config
import rose.config_editor


class GroupOperations(object):

    """Class to perform actions on groups of sections and/or options."""

    def __init__(self, data, util, reporter, undo_stack, redo_stack,
                 section_ops_inst,
                 variable_ops_inst,
                 view_page_func, update_ns_sub_data_func,
                 reload_ns_tree_func):
        self.data = data
        self.util = util
        self.reporter = reporter
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.sect_ops = section_ops_inst
        self.var_ops = variable_ops_inst
        self.view_page_func = view_page_func
        self.update_ns_sub_data_func = update_ns_sub_data_func
        self.reload_ns_tree_func = reload_ns_tree_func

    def apply_diff(self, config_name, config_diff, origin_name=None,
                   triggers_ok=False, is_reversed=False):
        """Apply a rose.config.ConfigNodeDiff object to the config."""
        state_reason_dict = {
            rose.config.ConfigNode.STATE_NORMAL: {},
            rose.config.ConfigNode.STATE_USER_IGNORED: {
                rose.variable.IGNORED_BY_USER:
                rose.config_editor.IGNORED_STATUS_MACRO
            },
            rose.config.ConfigNode.STATE_SYST_IGNORED: {
                rose.variable.IGNORED_BY_SYSTEM:
                rose.config_editor.IGNORED_STATUS_MACRO
            }
        }
        nses = []
        ids = []
        # Handle added sections.
        for keys, data in sorted(config_diff.get_added(),
                                 key=lambda _: len(_[0])):
            value, state, comments = data
            reason = state_reason_dict[state]
            if len(keys) == 1:
                # Section.
                sect = keys[0]
                ids.append(sect)
                nses.append(
                    self.sect_ops.add_section(config_name, sect,
                                              comments=comments,
                                              ignored_reason=reason,
                                              skip_update=True,
                                              skip_undo=True)
                )
            else:
                sect, opt = keys
                var_id = self.util.get_id_from_section_option(sect, opt)
                ids.append(var_id)
                metadata = self.data.helper.get_metadata_for_config_id(
                    var_id, config_name)
                variable = rose.variable.Variable(opt, value, metadata)
                variable.comments = copy.deepcopy(comments)
                variable.ignored_reason = copy.deepcopy(reason)
                self.data.load_ns_for_node(variable, config_name)
                nses.append(
                    self.var_ops.add_var(variable, skip_update=True,
                                         skip_undo=True)
                )

        # Handle modified settings.
        sections = self.data.config[config_name].sections
        for keys, data in config_diff.get_modified():
            old_value, old_state, old_comments = data[0]
            value, state, comments = data[1]
            comments = copy.deepcopy(comments)
            old_reason = state_reason_dict[old_state]
            reason = copy.deepcopy(state_reason_dict[state])
            sect = keys[0]
            sect_data = sections.now[sect]
            opt = None
            var = None
            if len(keys) > 1:
                opt = keys[1]
                var_id = self.util.get_id_from_section_option(sect, opt)
                ids.append(var_id)
                var = self.data.helper.get_variable_by_id(var_id, config_name)
            else:
                ids.append(sect)
            if comments != old_comments:
                # Change the comments.
                if opt is None:
                    # Section.
                    nses.append(
                        self.sect_ops.set_section_comments(config_name, sect,
                                                           comments,
                                                           skip_update=True,
                                                           skip_undo=True)
                    )
                else:
                    nses.append(
                        self.var_ops.set_var_comments(
                            variable, comments, skip_undo=True,
                            skip_update=True)
                    )

            if opt is not None and value != old_value:
                # Change the value (has to be a variable).
                nses.append(
                    self.var_ops.set_var_value(
                        var, value, skip_undo=True, skip_update=True)
                )

            if opt is None:
                ignored_changed = True
                is_ignored = False
                if (rose.variable.IGNORED_BY_USER in old_reason and
                        rose.variable.IGNORED_BY_USER not in reason):
                    # Enable from user-ignored.
                    is_ignored = False
                elif (rose.variable.IGNORED_BY_USER not in old_reason and
                        rose.variable.IGNORED_BY_USER in reason):
                    # User-ignore from enabled.
                    is_ignored = True
                elif (triggers_ok and
                        rose.variable.IGNORED_BY_SYSTEM not in old_reason and
                        rose.variable.IGNORED_BY_SYSTEM in reason):
                    # Trigger-ignore.
                    sect_data.error.setdefault(
                        rose.config_editor.WARNING_TYPE_ENABLED,
                        rose.config_editor.IGNORED_STATUS_MACRO)
                    is_ignored = True
                elif (triggers_ok and
                        rose.variable.IGNORED_BY_SYSTEM in old_reason and
                        rose.variable.IGNORED_BY_SYSTEM not in reason):
                    # Enabled from trigger-ignore.
                    sect_data.error.setdefault(
                        rose.config_editor.WARNING_TYPE_TRIGGER_IGNORED,
                        rose.config_editor.IGNORED_STATUS_MACRO)
                    is_ignored = False
                else:
                    ignored_changed = False
                if ignored_changed:
                    ignore_nses, ignore_ids = (
                        self.sect_ops.ignore_section(config_name, sect,
                                                     is_ignored,
                                                     override=True,
                                                     skip_update=True,
                                                     skip_undo=True)
                    )
                    nses.extend(ignore_nses)
                    ids.extend(ignore_ids)
            elif set(reason) != set(old_reason):
                nses.append(
                    self.var_ops.set_var_ignored(var, new_reason_dict=reason,
                                                 override=True, skip_undo=True,
                                                 skip_update=True)
                )

        for keys, data in sorted(config_diff.get_removed(),
                                 key=lambda _: -len(_[0])):
            # Sort so that variables are removed first.
            sect = keys[0]
            if len(keys) == 1:
                ids.append(sect)
                nses.extend(
                    self.sect_ops.remove_section(config_name, sect,
                                                 skip_update=True,
                                                 skip_undo=True))
            else:
                sect = keys[0]
                opt = keys[1]
                var_id = self.util.get_id_from_section_option(sect, opt)
                ids.append(var_id)
                var = self.data.helper.get_variable_by_id(var_id, config_name)
                nses.append(
                    self.var_ops.remove_var(
                        var, skip_update=True, skip_undo=True)
                )
        reverse_diff = config_diff.get_reversed()
        if is_reversed:
            action = rose.config_editor.STACK_ACTION_REVERSED
        else:
            action = rose.config_editor.STACK_ACTION_APPLIED
        stack_item = rose.config_editor.stack.StackItem(
            None,
            action,
            reverse_diff,
            self.apply_diff,
            (config_name, reverse_diff, origin_name, triggers_ok,
             not is_reversed),
            custom_name=origin_name
        )
        self.undo_stack.append(stack_item)
        del self.redo_stack[:]
        self.reload_ns_tree_func()
        for ns in set(nses):
            if ns is None:
                # Invalid or zero-change operation, e.g. by a corrupt macro.
                continue
            self.sect_ops.trigger_update(ns, skip_sub_data_update=True)
            self.sect_ops.trigger_info_update(ns)
        self.sect_ops.trigger_update_sub_data()
        self.sect_ops.trigger_update(config_name)
        return ids

    def add_section_with_options(self, config_name, new_section_name,
                                 opt_map=None):
        """Add a section and any compulsory options.

        Any option-value pairs in the opt_map dict will also be added.

        """
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_ADD + "-" + str(time.time())
        self.sect_ops.add_section(config_name, new_section_name,
                                  skip_update=True)
        namespace = self.data.helper.get_default_section_namespace(
            new_section_name, config_name)
        config_data = self.data.config[config_name]
        if opt_map is None:
            opt_map = {}
        for var in list(config_data.vars.latent.get(new_section_name, [])):
            if var.name in opt_map:
                var.value = opt_map.pop(var.name)
            if (var.name in opt_map or
                (var.metadata.get(rose.META_PROP_COMPULSORY) ==
                 rose.META_PROP_VALUE_TRUE)):
                self.var_ops.add_var(var, skip_update=True)
        for opt_name, value in list(opt_map.items()):
            var_id = self.util.get_id_from_section_option(
                new_section_name, opt_name)
            metadata = self.data.helper.get_metadata_for_config_id(
                var_id, config_name)
            metadata['full_ns'] = namespace
            flags = self.data.load_option_flags(config_name,
                                                new_section_name, opt_name)
            ignored_reason = {}  # This may not be safe.
            var = rose.variable.Variable(opt_name, value,
                                         metadata, ignored_reason,
                                         error={},
                                         flags=flags)
            self.var_ops.add_var(var, skip_update=True)
        self.reload_ns_tree_func(namespace)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        return new_section_name

    def copy_section(self, config_name, section, new_section=None,
                     skip_update=False):
        """Copy a section and its options."""
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_COPY + "-" + str(time.time())
        config_data = self.data.config[config_name]
        section_base = re.sub(r'(.*)\(\w+\)$', r"\1", section)
        existing_sections = []
        clone_vars = []
        existing_sections = list(config_data.vars.now.keys())
        existing_sections.extend(list(config_data.sections.now.keys()))
        for variable in config_data.vars.now.get(section, []):
            clone_vars.append(variable.copy())
        if new_section is None:
            i = 1
            new_section = section_base + "(" + str(i) + ")"
            while new_section in existing_sections:
                i += 1
                new_section = section_base + "(" + str(i) + ")"
        new_namespace = self.sect_ops.add_section(config_name, new_section,
                                                  skip_update=skip_update)
        if new_namespace is None:
            # Add failed (section already exists).
            return
        for var in clone_vars:
            var_id = self.util.get_id_from_section_option(
                new_section, var.name)
            metadata = self.data.helper.get_metadata_for_config_id(
                var_id, config_name)
            var.process_metadata(metadata)
            var.metadata['full_ns'] = new_namespace
        sorter = rose.config.sort_settings
        clone_vars.sort(lambda v, w: sorter(v.name, w.name))
        if skip_update:
            for var in clone_vars:
                self.var_ops.add_var(var, skip_update=skip_update)
        else:
            page = self.view_page_func(new_namespace)
            for var in clone_vars:
                page.add_row(var)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        return new_section

    def ignore_sections(self, config_name, sections, is_ignored,
                        skip_update=False, skip_sub_data_update=True):
        """Implement a mass user-ignore or enable of sections."""
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_IGNORE + "-" + str(time.time())
        nses = []
        for section in sections:
            ns = self.data.helper.get_default_section_namespace(
                section, config_name)
            if ns not in nses:
                nses.append(ns)
            skipped_nses = self.sect_ops.ignore_section(
                config_name, section, is_ignored, skip_update=True)[0]
            for ns in skipped_nses:
                if ns not in nses:
                    nses.append(ns)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        if not skip_update:
            for ns in nses:
                self.sect_ops.trigger_update(
                    ns, skip_sub_data_update=skip_sub_data_update)
                self.sect_ops.trigger_info_update(ns)
            self.sect_ops.trigger_update(config_name)
            self.update_ns_sub_data_func(config_name)

    def remove_section(self, config_name, section, skip_update=False):
        """Implement a remove of a section and its options."""
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_DELETE + "-" + str(time.time())
        config_data = self.data.config[config_name]
        variables = config_data.vars.now.get(section, [])
        for variable in list(variables):
            self.var_ops.remove_var(variable, skip_update=True)
        self.sect_ops.remove_section(config_name, section,
                                     skip_update=skip_update)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group

    def rename_section(self, config_name, section, target_section,
                       skip_update=False):
        """Implement a rename of a section and its options."""
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_RENAME + "-" + str(time.time())
        added_section = self.copy_section(config_name, section,
                                          target_section,
                                          skip_update=skip_update)
        if added_section is None:
            # Couldn't add the target section.
            return
        self.remove_section(config_name, section, skip_update=skip_update)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group

    def remove_sections(self, config_name, sections, skip_update=False):
        """Implement a mass removal of sections."""
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_DELETE + "-" + str(time.time())
        nses = []
        for section in sections:
            ns = self.data.helper.get_default_section_namespace(
                section, config_name)
            if ns not in nses:
                nses.append(ns)
            self.remove_section(config_name, section, skip_update=True)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        if not skip_update:
            self.reload_ns_tree_func(only_this_config=config_name)

    def get_sub_ops_for_namespace(self, namespace):
        """Return data functions for summary (sub) data panels."""
        if not namespace.startswith("/"):
            namespace = "/" + namespace
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        return SubDataOperations(
            config_name,
            self.add_section_with_options,
            self.copy_section,
            self.sect_ops.ignore_section,
            self.ignore_sections,
            self.remove_section,
            self.remove_sections,
            get_var_id_values_func=(
                self.data.helper.get_sub_data_var_id_value_map))


class SubDataOperations(object):

    """Class to hold a selected set of functions."""

    def __init__(self, config_name,
                 add_section_func, clone_section_func,
                 ignore_section_func, ignore_sections_func,
                 remove_section_func, remove_sections_func,
                 get_var_id_values_func):
        self.config_name = config_name
        self._add_section_func = add_section_func
        self._clone_section_func = clone_section_func
        self._ignore_section_func = ignore_section_func
        self._ignore_sections_func = ignore_sections_func
        self._remove_section_func = remove_section_func
        self._remove_sections_func = remove_sections_func
        self._get_var_id_values_func = get_var_id_values_func

    def add_section(self, new_section_name, opt_map=None):
        """Add a new section, complete with any compulsory variables."""
        return self._add_section_func(self.config_name, new_section_name,
                                      opt_map=opt_map)

    def clone_section(self, clone_section_name):
        """Copy a (duplicate) section and all its options."""
        return self._clone_section_func(self.config_name, clone_section_name)

    def ignore_section(self, ignore_section_name, is_ignored):
        """User-ignore or enable a section."""
        return self._ignore_section_func(
            self.config_name,
            ignore_section_name,
            is_ignored)

    def ignore_sections(self, ignore_sections_list, is_ignored,
                        skip_sub_data_update=True):
        """User-ignore or enable a list of sections."""
        return self._ignore_sections_func(
            self.config_name,
            ignore_sections_list,
            is_ignored,
            skip_sub_data_update=skip_sub_data_update
        )

    def remove_section(self, remove_section_name):
        """Remove a section and all its options."""
        return self._remove_section_func(self.config_name,
                                         remove_section_name)

    def remove_sections(self, remove_sections_list):
        """Remove a list of sections and all their options."""
        return self._remove_sections_func(self.config_name,
                                          remove_sections_list)

    def get_var_id_values(self):
        """Return a map of all var id values."""
        return self._get_var_id_values_func(self.config_name)
