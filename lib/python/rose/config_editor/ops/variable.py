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
        return self.__data.helper.get_ns_variable(var_id, config_name)

    def add_var(self, variable, skip_update=False):
        """Add a variable to the internal list."""
        existing_variable = self._get_proper_variable(variable)
        namespace = variable.metadata.get('full_ns')
        var_id = variable.metadata['id']
        sect, opt = self.__util.get_section_option_from_id(var_id)
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        old_metadata = copy.deepcopy(variable.metadata)
        metadata = self.__data.helper.get_metadata_for_config_id(var_id,
                                                                 config_name)
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
                                        [copy_var, skip_update]))
            del self.__redo_stack[:]
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])

    def remove_var(self, variable, skip_update=False):
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
                                    [copy_var, skip_update]))
        del self.__redo_stack[:]
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])

    def fix_var_ignored(self, variable):
        """Fix any variable ignore state errors."""
        ignored_reasons = variable.ignored_reason.keys()
        new_reason_dict = {}  # Enable, by default.
        old_reason = variable.ignored_reason.copy()
        if rose.variable.IGNORED_BY_SECTION in old_reason:
            # Preserve section-ignored status.
            new_reason_dict.setdefault(
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
        save_var = self.__data.helper.get_variable_by_id(var_id, config_name,
                                                         save=True)
        if save_var is None:
            return None
        return save_var.comments

    def get_var_original_ignore(self, variable):
        """Get the original value, if any."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        save_var = self.__data.helper.get_variable_by_id(var_id, config_name,
                                                         save=True)
        if save_var is None:
            return None
        return save_var.ignored_reason
  
    def get_var_original_value(self, variable):
        """Get the original value, if any."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        save_variable = self.__data.helper.get_variable_by_id(
                                    var_id, config_name, save=True)
        if save_variable is None:
            return None
        return save_variable.value

    def is_var_modified(self, variable):
        """Check against the last saved variable reference."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        this_variable = self.__data.helper.get_variable_by_id(var_id,
                                                              config_name)
        save_variable = self.__data.helper.get_variable_by_id(var_id,
                                                              config_name,
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
        save_variable = self.__data.helper.get_variable_by_id(var_id,
                                                              config_name,
                                                              save=True)
        return save_variable is None

    def is_var_ghost(self, variable):
        """Check if the variable is a latent variable."""
        var_id = variable.metadata['id']
        namespace = variable.metadata['full_ns']
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        this_variable = self.__data.helper.get_variable_by_id(var_id,
                                                              config_name)
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
