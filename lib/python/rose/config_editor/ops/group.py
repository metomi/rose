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
"""This module handles grouped operations.

These are supersets of section and variable operations, such as adding
a section together with some variables, mass removal of sections,
copying sections with their variables, and so on.

"""

import re
import time

import rose.config
import rose.config_editor


class GroupOperations(object):

    """Class to perform actions on groups of sections and/or options."""

    def __init__(self, data, util, reporter, undo_stack, redo_stack,
                 section_ops_inst,
                 variable_ops_inst,
                 view_page_func, reload_ns_tree_func):
        self.data = data
        self.util = util
        self.reporter = reporter
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.sect_ops = section_ops_inst
        self.var_ops = variable_ops_inst
        self.view_page_func = view_page_func
        self.reload_ns_tree_func = reload_ns_tree_func

    def add_section_with_options(self, config_name, new_section_name,
                                 opt_map=None):
        """Add a section and any compulsory options.
        
        Any option-value pairs in the opt_map dict will also be added.
        
        """
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_ADD + "-" + str(time.time())
        self.sect_ops.add_section(config_name, new_section_name)
        namespace = self.data.helper.get_default_namespace_for_section(
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
        for opt_name, value in opt_map.items():
            var_id = self.util.get_id_from_section_option(
                                           new_section_name, opt_name)
            metadata = self.data.helper.get_metadata_for_config_id(
                                            var_id, config_name)
            metadata['full_ns'] = namespace
            flags = self.data.load_option_flags(config_name, section, option)
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
        section_base = re.sub('(.*)\(\w+\)$', r"\1", section)
        existing_sections = []
        clone_vars = []
        existing_sections = config_data.vars.now.keys()
        existing_sections.extend(config_data.sections.now.keys())
        for variable in config_data.vars.now.get(section, []):
            clone_vars.append(variable.copy())
        if new_section is None:
            i = 1
            new_section = section_base + "(" + str(i) + ")"
            while new_section in existing_sections:
                i += 1
                new_section = section_base + "(" + str(i) + ")"
        self.sect_ops.add_section(config_name, new_section,
                                  skip_update=skip_update)
        new_namespace = self.data.helper.get_default_namespace_for_section(
                                  new_section, config_name)
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

    def remove_sections(self, config_name, sections, skip_update=False):
        """Implement a mass removal of sections."""
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_DELETE + "-" + str(time.time())
        nses = []
        for section in sections:
            ns = self.data.helper.get_default_namespace_for_section(
                                              section, config_name)
            if ns not in nses:
                nses.append(ns)
            self.remove_section(config_name, section, skip_update=True)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        if not skip_update:
            for ns in nses:
                self.reload_ns_tree_func(ns)

    def get_sub_ops_for_namespace(self, namespace):
        """Return data functions for summary (sub) data panels."""
        if not namespace.startswith("/"):
            namespace = "/" + namespace
        config_name, subsp = self.util.split_full_ns(self.data, namespace)
        return SubDataOperations(
                    config_name,
                    self.add_section_with_options,
                    self.copy_section,
                    self.sect_ops.ignore_section,
                    self.remove_section,
                    self.remove_sections,
                    get_var_id_values_func=(
                            self.data.helper.get_sub_data_var_id_value_map))


class SubDataOperations(object):

    """Class to hold a selected set of functions."""

    def __init__(self, config_name,
                 add_section_func, clone_section_func,
                 ignore_section_func, remove_section_func,
                 remove_sections_func,
                 get_var_id_values_func):
        self.config_name = config_name
        self._add_section_func = add_section_func
        self._clone_section_func = clone_section_func
        self._ignore_section_func = ignore_section_func
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
