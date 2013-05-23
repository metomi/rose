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
"""This module deals with section-specific actions.

The methods of SectionOperations are the only ways that section data
objects should be interacted with. There are also some utility methods.

"""

import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor.stack
import rose.gtk.util


class SectionOperations(object):

    """A class to hold functions that act on sections and their storage."""

    def __init__(self, data, util, undo_stack, redo_stack,
                 check_cannot_enable_func=rose.config_editor.false_function, 
                 update_ns_func=rose.config_editor.false_function,
                 update_info_func=rose.config_editor.false_function,
                 update_comments_func=rose.config_editor.false_function,
                 update_tree_func=rose.config_editor.false_function,
                 search_id_func=rose.config_editor.false_function,
                 view_page_func=rose.config_editor.false_function,
                 kill_page_func=rose.config_editor.false_function):
        self.__data = data
        self.__util = util
        self.__undo_stack = undo_stack
        self.__redo_stack = redo_stack
        self.check_cannot_enable_setting = check_cannot_enable_func
        self.trigger_update = update_ns_func
        self.trigger_info_update = update_info_func
        self.trigger_reload_tree = update_tree_func
        self.search_id_func = search_id_func
        self.view_page_func = view_page_func
        self.kill_page_func = kill_page_func

    def add_section(self, config_name, section, skip_update=False,
                    page_launch=False):
        """Add a section to this configuration."""
        config_data = self.__data.config[config_name]
        new_section_data = None
        was_latent = False
        if section in config_data.sections.latent:
            new_section_data = config_data.sections.latent.pop(section)
            was_latent = True
        else:
            metadata = self.__data.helper.get_metadata_for_config_id(
                                              section, config_name)
            new_section_data = rose.section.Section(section, [], metadata)
        config_data.sections.now.update({section: new_section_data})
        self.__data.add_section_to_config(section, config_name)
        self.__data.load_ns_for_node(new_section_data, config_name)
        self.__data.load_file_metadata(config_name, section)
        self.__data.load_vars_from_config(config_name,
                                          only_this_section=section,
                                          update=True)
        self.__data.load_node_namespaces(config_name,
                                         only_this_section=section)
        metadata = self.__data.helper.get_metadata_for_config_id(section,
                                                                 config_name)
        new_section_data.process_metadata(metadata)
        ns = new_section_data.metadata["full_ns"]
        if not skip_update:
            self.trigger_reload_tree(ns)
        if rose.META_PROP_DUPLICATE in metadata:
            self.__data.load_namespace_has_sub_data(config_name)
        copy_section_data = new_section_data.copy()
        stack_item = rose.config_editor.stack.StackItem(
                          ns,
                          rose.config_editor.STACK_ACTION_ADDED,
                          copy_section_data,
                          self.remove_section,
                          (config_name, section, skip_update))
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        if page_launch and not skip_update:
            self.view_page_func(ns)
        if not skip_update:
            self.trigger_update(ns)

    def ignore_section(self, config_name, section, is_ignored,
                       override=False):
        """Ignore or enable a section for this configuration."""
        config_data = self.__data.config[config_name]
        sect_data = config_data.sections.now[section]
        if is_ignored:
            # User-ignore request for this section.
            # The section must be enabled and optional.
            if (not override and (sect_data.ignored_reason or
                sect_data.metadata.get(rose.META_PROP_COMPULSORY) ==
                rose.META_PROP_VALUE_TRUE)):
                rose.gtk.util.run_dialog(
                        rose.gtk.util.DIALOG_TYPE_ERROR,
                        rose.config_editor.WARNING_CANNOT_USER_IGNORE.format(
                                        section),
                        rose.config_editor.WARNING_CANNOT_IGNORE_TITLE)
                return
            for error in [rose.config_editor.WARNING_TYPE_USER_IGNORED,
                          rose.config_editor.WARNING_TYPE_ENABLED]:
                if error in sect_data.error:
                    sect_data.ignored_reason.update(
                              {rose.variable.IGNORED_BY_SYSTEM:
                               rose.config_editor.IGNORED_STATUS_MANUAL})
                    sect_data.error.pop(error)
                    break
            else:
                sect_data.ignored_reason.update(
                                  {rose.variable.IGNORED_BY_USER:
                                   rose.config_editor.IGNORED_STATUS_MANUAL})
            action = rose.config_editor.STACK_ACTION_IGNORED
        else:
            # Enable request for this section.
            # The section must not be justifiably triggered ignored.
            ign_errors = [e for e in rose.config_editor.WARNING_TYPES_IGNORE
                          if e != rose.config_editor.WARNING_TYPE_ENABLED]
            my_errors = sect_data.error.keys()
            if (not override and
                rose.variable.IGNORED_BY_SYSTEM in sect_data.ignored_reason
                and all([e not in my_errors for e in ign_errors])
                and self.check_cannot_enable_setting(config_name,
                                                     section)):
                rose.gtk.util.run_dialog(
                      rose.gtk.util.DIALOG_TYPE_ERROR,
                      rose.config_editor.WARNING_CANNOT_ENABLE.format(
                                         section),
                      rose.config_editor.WARNING_CANNOT_ENABLE_TITLE)
                return
            sect_data.ignored_reason.clear()
            for error in ign_errors:
                if error in my_errors:
                    sect_data.error.pop(error)
            action = rose.config_editor.STACK_ACTION_ENABLED
        ns = sect_data.metadata["full_ns"]
        copy_sect_data = sect_data.copy()
        stack_item = rose.config_editor.stack.StackItem(
                          ns,
                          action,
                          copy_sect_data,
                          self.ignore_section,
                          (config_name, section, not is_ignored, True))
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        nses_to_do = []
        for var in (config_data.vars.now.get(section, []) +
                    config_data.vars.latent.get(section, [])):
            self.trigger_info_update(var)
            if var.metadata['full_ns'] not in nses_to_do:
                nses_to_do.append(var.metadata['full_ns'])
            if is_ignored:
                var.ignored_reason.update(
                            {rose.variable.IGNORED_BY_SECTION:
                             rose.config_editor.IGNORED_STATUS_MANUAL})
            elif rose.variable.IGNORED_BY_SECTION in var.ignored_reason:
                var.ignored_reason.pop(rose.variable.IGNORED_BY_SECTION)
            else:
                continue
        for ns in nses_to_do:
            self.trigger_update(ns)
            self.trigger_info_update(ns)
            self.trigger_update(config_name)

    def remove_section(self, config_name, section, skip_update=False):
        """Remove a section from this configuration."""
        config_data = self.__data.config[config_name]
        old_section_data = config_data.sections.now.pop(section)
        config_data.sections.latent.update(
                             {section: old_section_data})
        if section in config_data.vars.now:
            config_data.vars.now.pop(section)
        namespace = old_section_data.metadata["full_ns"]
        ns_list = [namespace]
        for ns, values in self.__data.namespace_meta_lookup.items():
            sections = values.get('sections')
            if sections == [section]:
                if ns not in ns_list:
                    ns_list.append(ns)
        stack_item = rose.config_editor.stack.StackItem(
                          namespace,
                          rose.config_editor.STACK_ACTION_REMOVED,
                          old_section_data.copy(),
                          self.add_section,
                          (config_name, section, skip_update))
        for ns in ns_list:
            self.kill_page_func(ns)
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        if not skip_update:
            self.trigger_reload_tree(only_this_namespace=namespace)

    def set_section_comments(self, config_name, section, comments):
        """Change the comments field for the section object."""
        config_data = self.__data.config[config_name]
        sect_data = config_data.sections.now[section]
        old_sect_data = sect_data.copy()
        last_comments = old_sect_data.comments
        sect_data.comments = comments
        ns = sect_data.metadata["full_ns"]
        stack_item = rose.config_editor.stack.StackItem(
                             ns,
                             rose.config_editor.STACK_ACTION_CHANGED_COMMENTS,
                             old_sect_data,
                             self.set_section_comments,
                             (config_name, section, last_comments))
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        self.trigger_update(ns)

    def is_section_modified(self, section_object):
        """Check against the last saved section object reference."""
        section = section_object.metadata["id"]
        namespace = section_object.metadata["full_ns"]
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        this_section = config_data.sections.now.get(section)
        save_section = config_data.sections.save.get(section)
        if this_section is None:
            # Ghost variable, check absence from saved list.
            if save_section is not None:
                return True
        else:
            # Real variable, check value and presence in saved list.
            if save_section is None:
                return True
            return this_section.to_hashable() != this_section.to_hashable()

    def get_section_changes(self, section_object):
        """Return text describing changes since the last save."""
        section = section_object.metadata["id"]
        namespace = section_object.metadata["full_ns"]
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        this_section = config_data.sections.now.get(section)
        save_section = config_data.sections.save.get(section)
        if this_section is None:
            if save_section is not None:
                return rose.config_editor.KEY_TIP_ADDED
            # Ignore both-missing scenarios (no actual diff in output).
            return ""
        if save_section is None:
            return rose.config_editor.KEY_TIP_MISSING
        if this_section.to_hashable() == save_section.to_hashable():
            return ""
        if this_section.comments != save_section.comments:
            return rose.config_editor.KEY_TIP_CHANGED_COMMENTS
        # The difference must now be in the ignored state.
        if rose.variable.IGNORED_BY_SYSTEM in this_section.ignored_reason:
            return rose.config_editor.KEY_TIP_TRIGGER_IGNORED
        if rose.variable.IGNORED_BY_USER in this_section.ignored_reason:
            return rose.config_editor.KEY_TIP_USER_IGNORED
        return rose.config_editor.KEY_TIP_ENABLED       

    def get_ns_metadata_files(self, namespace):
        """Retrieve filenames within the metadata for this namespace."""
        config_name = self.__util.split_full_ns(
                             self.__data, namespace)[0]
        return self.__data.config[config_name].meta_files
