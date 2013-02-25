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

import copy
import os
import re
import time

import pygtk
pygtk.require('2.0')
import gtk

import rose.gtk.util
import rose.resource


class StackItem(object):

    """A dictionary containing stack information."""

    def __init__(self, page_label, action_text, node,
                       undo_function, undo_args=None,
                       group=None):
        self.page_label = page_label
        self.action = action_text
        self.node = node
        self.name = self.node.name
        self.group = group
        if hasattr(self.node, "value"):
            self.value = self.node.value
            self.old_value = self.node.old_value
        else:
            self.value = ""
            self.old_value = ""
        self.undo_func = undo_function
        if undo_args is None:
            undo_args = []
        self.undo_args = undo_args

    def __repr__(self):
        return (self.action[0].lower() + self.action[1:] + ' ' + self.name +
                ", ".join([str(u) for u in self.undo_args]))


class SectionOperations(object):

    """A class to hold functions that act on sections and their storage."""

    def __init__(self, data, util, undo_stack, redo_stack,
                 check_cannot_enable_func=rose.config_editor.false_function, 
                 update_ns_func=rose.config_editor.false_function,
                 update_info_func=rose.config_editor.false_function,
                 update_comments_func=rose.config_editor.false_function,
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
        self.trigger_comments_update = update_comments_func
        self.search_id_func = search_id_func
        self.view_page_func = view_page_func
        self.kill_page_func = kill_page_func

    def add_section(self, config_name, section, no_update=False):
        """Add a section to this configuration."""
        config_data = self.__data.config[config_name]
        new_section_data = None
        was_latent = False
        if section in config_data.sections.latent:
            new_section_data = config_data.sections.latent.pop(section)
            was_latent = True
        else:
            metadata = self.__data.get_metadata_for_config_id(section,
                                                              config_name)
            new_section_data = rose.section.Section(section, [], metadata)
        config_data.sections.now.update({section: new_section_data})
        self.__data.add_section_to_config(section, config_name)
        self.__data.load_file_metadata(config_name, section)
        self.__data.load_vars_from_config(config_name,
                                          just_this_section=section,
                                          update=True)
        self.__data.load_variable_namespaces(config_name,
                                             just_this_section=section)
        metadata = self.__data.get_metadata_for_config_id(section,
                                                          config_name)
        new_section_data.metadata = metadata
        ns = self.__data.get_default_namespace_for_section(section, 
                                                           config_name)
        if not no_update:
            self.__data.reload_namespace_tree()  # This will update everything.
        copy_section_data = new_section_data.copy()
        stack_item = rose.config_editor.stack.StackItem(
                          ns,
                          rose.config_editor.STACK_ACTION_ADDED,
                          copy_section_data,
                          self.remove_section,
                          (config_name, section, no_update))
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        if not no_update:
            self.view_page_func(ns)
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
        ns = self.__data.get_default_namespace_for_section(section,
                                                           config_name)
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

    def remove_section(self, config_name, section, no_update=False):
        """Remove a section from this configuration."""
        config_data = self.__data.config[config_name]
        old_section_data = config_data.sections.now.pop(section)
        config_data.sections.latent.update(
                             {section: old_section_data})
        if section in config_data.vars.now:
            config_data.vars.now.pop(section)
        namespace = self.__data.get_default_namespace_for_section(
                                                      section, config_name)
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
                          (config_name, section, no_update))
        for ns in ns_list:
            self.kill_page_func(ns)
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        if not no_update:
            self.__data.reload_namespace_tree()  # This will update everything.

    def set_section_comments(self, config_name, section, comments):
        """Change the comments field for the section object."""
        config_data = self.__data.config[config_name]
        sect_data = config_data.sections.now[section]
        old_sect_data = sect_data.copy()
        last_comments = old_sect_data.comments
        sect_data.comments = comments
        ns = self.__data.get_default_namespace_for_section(
                                                   section, config_name)
        stack_item = rose.config_editor.stack.StackItem(
                             ns,
                             rose.config_editor.STACK_ACTION_CHANGED_COMMENTS,
                             old_sect_data,
                             self.set_section_comments,
                             (config_name, section, last_comments))
        self.__undo_stack.append(stack_item)
        del self.__redo_stack[:]
        self.trigger_update(ns)
        self.trigger_comments_update(ns)

    def get_ns_metadata_files(self, namespace):
        """Retrieve filenames within the metadata for this namespace."""
        config_name = self.__util.split_full_ns(
                             self.__data, namespace)[0]
        return self.__data.config[config_name].meta_files


class VariableOperations(object):

    """A class to hold functions that act on variables and their storage."""

    def __init__(self, data, util, undo_stack, redo_stack,
                 check_cannot_enable_func=rose.config_editor.false_function, 
                 update_ns_func=rose.config_editor.false_function,
                 ignore_update_func=rose.config_editor.false_function,
                 search_id_func=rose.config_editor.false_function):
        self.__data = data
        self.__util = util
        self.__undo_stack = undo_stack
        self.__redo_stack = redo_stack
        self.check_cannot_enable_setting = check_cannot_enable_func
        self.trigger_update = update_ns_func
        self.trigger_ignored_update = ignore_update_func
        self.search_id_func = search_id_func

    def _get_proper_variable(self, possible_copy_variable):
        # Some variables are just copies, and changes to them
        # won't affect anything. We need to look up the 'real' variable.
        namespace = possible_copy_variable.metadata.get('full_ns')
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        var_id = possible_copy_variable.metadata['id']
        return self.__data.get_ns_variable(var_id, config_name)

    def add_var(self, variable, no_update=False):
        """Add a variable to the internal list."""
        existing_variable = self._get_proper_variable(variable)
        namespace = variable.metadata.get('full_ns')
        var_id = variable.metadata['id']
        sect, opt = self.__util.get_section_option_from_id(var_id)
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        old_metadata = copy.deepcopy(variable.metadata)
        metadata = self.__data.get_metadata_for_config_id(var_id, config_name)
        variable.process_metadata(metadata)
        variable.metadata.update(old_metadata)
        variables = config_data.vars.now.get(sect, [])
        latent_variables = config_data.vars.latent.get(sect, [])
        copy_var = variable.copy()
        v_id = variable.metadata.get('id')
        if existing_variable in latent_variables:
            latent_variables.remove(existing_variable)
        if v_id in [v.metadata.get('id') for v in variables]:
            # This is the case of adding a blank variable and 
            # renaming it to an existing variable's name.
            # At the moment, assume this should just be skipped.
            pass
        else:
            config_data.vars.now.setdefault(sect, [])
            config_data.vars.now[sect].append(variable)
            self.__undo_stack.append(StackItem(
                                        variable.metadata['full_ns'],
                                        rose.config_editor.STACK_ACTION_ADDED,
                                        copy_var,
                                        self.remove_var,
                                        [copy_var, no_update]))
            del self.__redo_stack[:]
        if not no_update:
            self.trigger_update(variable.metadata['full_ns'])

    def remove_var(self, variable, no_update=False):
        """Remove the variable entry from the internal lists."""
        variable = self._get_proper_variable(variable)
        namespace = variable.metadata.get('full_ns')
        var_id = variable.metadata['id']
        sect, opt = self.__util.get_section_option_from_id(var_id)
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        variables = config_data.vars.now.get(sect, [])
        latent_variables = config_data.vars.latent.get(sect, [])
        if variable in latent_variables:
            latent_variables.remove(variable)
            if not config_data.vars.latent[sect]:
                config_data.vars.latent.pop(sect)
            return
        if variable in variables:
            variables.remove(variable)
            if not config_data.vars.now[sect]:
                config_data.vars.now.pop(sect)
            if variable.name:
                config_data.vars.latent.setdefault(sect, [])
                config_data.vars.latent[sect].append(variable)
        copy_var = variable.copy()
        self.__undo_stack.append(StackItem(
                                    variable.metadata['full_ns'],
                                    rose.config_editor.STACK_ACTION_REMOVED,
                                    copy_var,
                                    self.add_var,
                                    [copy_var, no_update]))
        del self.__redo_stack[:]
        if not no_update:
            self.trigger_update(variable.metadata['full_ns'])

    def fix_var_ignored(self, variable):
        """Fix any variable ignore state errors."""
        ignored_reasons = variable.ignored_reason.keys()
        new_reason_dict = {}  # Enable, by default.
        old_reason = variable.ignored_reason.copy()
        if rose.variable.IGNORED_BY_SECTION in old_reason:
            # Preserve section-ignored status.
            new_reason.setdefault(
                            rose.variable.IGNORED_BY_SECTION,
                            old_reason[rose.variable.IGNORED_BY_SECTION])
        if rose.variable.IGNORED_BY_SYSTEM in ignored_reasons:
            # Doc table I_t
            if rose.config_editor.WARNING_TYPE_ENABLED in variable.error:
                # Enable new_reason_dict.
                # Doc table I_t -> E
                pass
            if rose.config_editor.WARNING_TYPE_NOT_TRIGGER in variable.error:
                pass
        elif rose.variable.IGNORED_BY_USER in ignored_reasons:
            # Doc table I_u
            if rose.config_editor.WARNING_TYPE_USER_IGNORED in variable.error:
                # Enable new_reason_dict.
                # Doc table I_u -> I_t -> *,
                #           I_u -> E -> compulsory,
                #           I_u -> not trigger -> compulsory
                pass
        else:
            # Doc table E
            if rose.config_editor.WARNING_TYPE_ENABLED in variable.error:
                # Doc table E -> I_t -> *
                new_reason_dict = {rose.variable.IGNORED_BY_SYSTEM:
                                   rose.config_editor.IGNORED_STATUS_MANUAL}
        self.set_var_ignored(variable, new_reason_dict)
                
    def set_var_ignored(self, variable, new_reason_dict=None, override=False):
        """Set the ignored flag data for the variable.
        
        new_reason_dict replaces the variable.ignored_reason attribute,
        except for the rose.variable.IGNORED_BY_SECTION key.
        
        """
        if new_reason_dict is None:
            new_reason_dict = {}
        variable = self._get_proper_variable(variable)
        old_reason = variable.ignored_reason.copy()
        if rose.variable.IGNORED_BY_SECTION in old_reason:
            new_reason_dict.setdefault(
                            rose.variable.IGNORED_BY_SECTION,
                            old_reason[rose.variable.IGNORED_BY_SECTION])
        if rose.variable.IGNORED_BY_SECTION not in old_reason:
            if rose.variable.IGNORED_BY_SECTION in new_reason_dict:
                new_reason_dict.pop(rose.variable.IGNORED_BY_SECTION)
        variable.ignored_reason = new_reason_dict.copy()
        if not set(old_reason.keys()) ^ set(new_reason_dict.keys()):
            # No practical difference, so don't do anything.
            return
        # Protect against user-enabling of triggered ignored.
        if (not override and
            rose.variable.IGNORED_BY_SYSTEM in old_reason and
            rose.variable.IGNORED_BY_SYSTEM not in new_reason_dict):
            ns = variable.metadata['full_ns']
            config_name = self.__util.split_full_ns(self.__data, ns)[0]
            if rose.config_editor.WARNING_TYPE_NOT_TRIGGER in variable.error:
                variable.error.pop(
                         rose.config_editor.WARNING_TYPE_NOT_TRIGGER)
        if len(variable.ignored_reason.keys()) > len(old_reason.keys()):
            action_text = rose.config_editor.STACK_ACTION_IGNORED
            if (not old_reason and
                rose.config_editor.WARNING_TYPE_ENABLED in variable.error):
                variable.error.pop(rose.config_editor.WARNING_TYPE_ENABLED)
        else:
            action_text = rose.config_editor.STACK_ACTION_ENABLED
            if len(variable.ignored_reason.keys()) == 0:
                for err_type in rose.config_editor.WARNING_TYPES_IGNORE:
                    if err_type in variable.error:
                        variable.error.pop(err_type)
        copy_var = variable.copy()
        self.__undo_stack.append(StackItem(variable.metadata['full_ns'],
                                           action_text,
                                           copy_var,
                                           self.set_var_ignored,
                                           [copy_var, old_reason, True]))
        del self.__redo_stack[:]
        self.trigger_ignored_update(variable)
        self.trigger_update(variable.metadata['full_ns'])

    def set_var_value(self, variable, new_value):
        """Set the value of the variable."""
        variable = self._get_proper_variable(variable)
        if variable.value == new_value:
            # A bad valuewidget setter.
            return False
        variable.old_value = variable.value
        variable.value = new_value
        copy_var = variable.copy()
        self.__undo_stack.append(StackItem(
                                    variable.metadata['full_ns'],
                                    rose.config_editor.STACK_ACTION_CHANGED,
                                    copy_var,
                                    self.set_var_value,
                                    [copy_var, copy_var.old_value]))
        del self.__redo_stack[:]
        self.trigger_update(variable.metadata['full_ns'])

    def set_var_comments(self, variable, comments):
        """Set the comments field for the variable."""
        variable = self._get_proper_variable(variable)
        copy_variable = variable.copy()
        old_comments = copy_variable.comments
        variable.comments = comments
        self.__undo_stack.append(
                    StackItem(
                            variable.metadata['full_ns'],
                            rose.config_editor.STACK_ACTION_CHANGED_COMMENTS,
                            copy_variable,
                            self.set_var_comments,
                            [copy_variable, old_comments]))
        del self.__redo_stack[:]
        self.trigger_update(variable.metadata['full_ns'])

    def get_var_original_comments(self, variable):
        """Get the original comments, if any."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        save_var = self.__data.get_variable_by_id(var_id, config_name,
                                                  save=True)
        if save_var is None:
            return None
        return save_var.comments

    def get_var_original_ignore(self, variable):
        """Get the original value, if any."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        save_var = self.__data.get_variable_by_id(var_id, config_name,
                                                  save=True)
        if save_var is None:
            return None
        return save_var.ignored_reason
  
    def get_var_original_value(self, variable):
        """Get the original value, if any."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        save_variable = self.__data.get_variable_by_id(var_id, config_name,
                                                       save=True)
        if save_variable is None:
            return None
        return save_variable.value

    def is_var_modified(self, variable):
        """Check against the last saved variable reference."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        this_variable = self.__data.get_variable_by_id(var_id, config_name)
        save_variable = self.__data.get_variable_by_id(var_id, config_name,
                                                       save=True)
        if this_variable is None:
            # Ghost variable, check absence from saved list.
            if save_variable is not None:
                return True
        else:
            # Real variable, check value and presence in saved list.
            if save_variable is None:
                return True
            return this_variable.to_hashable() != save_variable.to_hashable()

    def is_var_added(self, variable):
        """Check if missing from the saved variables list."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        save_variable = self.__data.get_variable_by_id(var_id, config_name,
                                                       save=True)
        return save_variable is None

    def is_var_ghost(self, variable):
        """Check if the variable is a latent variable."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        this_variable = self.__data.get_variable_by_id(var_id, config_name)
        return (this_variable is None)

    def get_var_changes(self, variable):
        """Return a description of any changed status the variable has."""
        if self.is_var_modified(variable):
            if self.is_var_added(variable):
                return rose.config_editor.KEY_TIP_ADDED
            if self.is_var_ghost(variable):
                return rose.config_editor.KEY_TIP_MISSING
            old_value = self.get_var_original_value(variable)
            if variable.value != self.get_var_original_value(variable):
                return rose.config_editor.KEY_TIP_CHANGED.format(old_value)
            if self.get_var_original_comments(variable) != variable.comments:
                return rose.config_editor.KEY_TIP_CHANGED_COMMENTS
            if not variable.ignored_reason:
                return rose.config_editor.KEY_TIP_ENABLED
            old_ignore = self.get_var_original_ignore(variable)
            if len(old_ignore) > len(variable.ignored_reason):
                return rose.config_editor.KEY_TIP_ENABLED
            if (rose.variable.IGNORED_BY_SYSTEM in variable.ignored_reason
                and rose.variable.IGNORED_BY_SYSTEM not in old_ignore):
                return rose.config_editor.KEY_TIP_TRIGGER_IGNORED
            if (rose.variable.IGNORED_BY_USER in variable.ignored_reason
                and rose.variable.IGNORED_BY_USER not in old_ignore):
                return rose.config_editor.KEY_TIP_USER_IGNORED
            if (rose.variable.IGNORED_BY_SECTION in variable.ignored_reason
                and rose.variable.IGNORED_BY_SECTION not in old_ignore):
                return rose.config_editor.KEY_TIP_SECTION_IGNORED
            return rose.config_editor.KEY_TIP_ENABLED
        return ''

    def search_for_var(self, config_name_or_namespace, setting_id):
        """Launch a search for a setting or variable id."""
        config_name = self.__util.split_full_ns(
                             self.__data, config_name_or_namespace)[0]
        self.search_id_func(config_name, setting_id)

    def get_ns_metadata_files(self, namespace):
        """Retrieve filenames within the metadata for this namespace."""
        config_name = self.__util.split_full_ns(
                             self.__data, namespace)[0]
        return self.__data.config[config_name].meta_files


class StackViewer(gtk.Window):

    """Window to dynamically display the internal stack."""

    def __init__(self, undo_stack, redo_stack, undo_func):
        """Load a view of the stack."""
        log_text = ''
        super(StackViewer, self).__init__()
        self.set_title(rose.config_editor.STACK_VIEW_TITLE)
        self.action_colour_map = {
                rose.config_editor.STACK_ACTION_ADDED:
                rose.config_editor.COLOUR_STACK_ADDED,
                rose.config_editor.STACK_ACTION_CHANGED:
                rose.config_editor.COLOUR_STACK_CHANGED,
                rose.config_editor.STACK_ACTION_CHANGED_COMMENTS:
                rose.config_editor.COLOUR_STACK_CHANGED_COMMENTS,
                rose.config_editor.STACK_ACTION_ENABLED:
                rose.config_editor.COLOUR_STACK_ENABLED,
                rose.config_editor.STACK_ACTION_IGNORED:
                rose.config_editor.COLOUR_STACK_IGNORED,
                rose.config_editor.STACK_ACTION_REMOVED:
                rose.config_editor.COLOUR_STACK_REMOVED}
        self.undo_func = undo_func
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.set_border_width(rose.config_editor.SPACING_SUB_PAGE)
        self.main_vbox = gtk.VPaned()
        accelerators = gtk.AccelGroup()
        accel_key, accel_mods = gtk.accelerator_parse("<Ctrl>Z")
        accelerators.connect_group(accel_key, accel_mods, gtk.ACCEL_VISIBLE,
                                   lambda a, b, c, d: self.undo_from_log())
        accel_key, accel_mods = gtk.accelerator_parse("<Ctrl><Shift>Z")
        accelerators.connect_group(accel_key, accel_mods, gtk.ACCEL_VISIBLE,
                                   lambda a, b, c, d:
                                   self.undo_from_log(redo_mode_on=True))
        self.add_accel_group(accelerators)
        self.set_default_size(*rose.config_editor.SIZE_STACK)
        self.undo_view = self.get_stack_view(redo_mode_on=False)
        self.redo_view = self.get_stack_view(redo_mode_on=True)
        undo_vbox = self.get_stack_view_box(self.undo_view,
                                            redo_mode_on=False)
        redo_vbox = self.get_stack_view_box(self.redo_view,
                                            redo_mode_on=True)
        self.main_vbox.pack1(undo_vbox, resize=True, shrink=True)
        self.main_vbox.show()
        self.main_vbox.pack2(redo_vbox, resize=False, shrink=True)
        self.main_vbox.show()
        self.undo_view.connect('size-allocate', self.scroll_view)
        self.redo_view.connect('size-allocate', self.scroll_view)
        self.add(self.main_vbox)
        self.show()

    def get_stack_view_box(self, log_buffer, redo_mode_on=False):
        """Return a frame containing a scrolled text view."""
        text_view = log_buffer
        text_scroller = gtk.ScrolledWindow()
        text_scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        text_scroller.set_shadow_type(gtk.SHADOW_IN)
        text_scroller.add(text_view)
        vadj = text_scroller.get_vadjustment()
        vadj.set_value(vadj.upper - 0.9*vadj.page_size)
        text_scroller.show()
        vbox = gtk.VBox()
        label = gtk.Label()
        if redo_mode_on:
            label.set_text('REDO STACK')
            self.redo_text_view = text_view
        else:
            label.set_text('UNDO STACK')
            self.undo_text_view = text_view
        label.show()
        vbox.set_border_width(rose.config_editor.SPACING_SUB_PAGE)
        vbox.pack_start(label, expand=False, fill=True,
                        padding=rose.config_editor.SPACING_SUB_PAGE)
        vbox.pack_start(text_scroller, expand=True, fill=True)
        vbox.show()
        return vbox

    def undo_from_log(self, redo_mode_on=False):
        """Drive the main program undo function and update."""
        self.undo_func(redo_mode_on)
        self.update()

    def get_stack_view(self, redo_mode_on=False):
        """Return a tree view with information from a stack."""
        stack_model = self.get_stack_model(redo_mode_on, make_new_model=True)
        stack_view = gtk.TreeView(stack_model)
        columns = {}
        cell_text = {}
        for title in [rose.config_editor.STACK_COL_NS,
                      rose.config_editor.STACK_COL_ACT,
                      rose.config_editor.STACK_COL_NAME,
                      rose.config_editor.STACK_COL_VALUE,
                      rose.config_editor.STACK_COL_OLD_VALUE]:
            columns[title] = gtk.TreeViewColumn()
            columns[title].set_title(title)
            cell_text[title] = gtk.CellRendererText()
            columns[title].pack_start(cell_text[title], expand=True)
            columns[title].add_attribute(cell_text[title], attribute='markup',
                                         column=len(columns.keys()) - 1)
            stack_view.append_column(columns[title])
        stack_view.show()
        return stack_view

    def get_stack_model(self, redo_mode_on=False, make_new_model=False):
        """Return a gtk.ListStore generated from a stack."""
        stack = [self.undo_stack, self.redo_stack][redo_mode_on]
        if make_new_model:
            model = gtk.ListStore(str, str, str, str, str, bool)
        else:
            model = [self.undo_view.get_model(),
                     self.redo_view.get_model()][redo_mode_on]
        model.clear()
        for stack_item in stack:
            marked_up_action = stack_item.action
            if stack_item.action in self.action_colour_map:
                colour = self.action_colour_map[stack_item.action]
                marked_up_action = ("<span foreground='" + colour + "'>"
                                     + stack_item.action + "</span>")
            short_label = re.sub('^/[^/]+/', '', stack_item.page_label)
            model.append((short_label, marked_up_action,
                          stack_item.name, repr(stack_item.value),
                          repr(stack_item.old_value), False))
        return model

    def scroll_view(self, tree_view, event=None):
        """Scroll the parent scrolled window to the bottom."""
        vadj = tree_view.get_parent().get_vadjustment()
        if vadj.upper > vadj.lower + vadj.page_size:
            vadj.set_value(vadj.upper - 0.95*vadj.page_size)

    def update(self):
        """Reload text views from the undo and redo stacks."""
        if self.undo_text_view.get_parent() is None:
            return
        self.get_stack_model(redo_mode_on=False)
        self.get_stack_model(redo_mode_on=True)
