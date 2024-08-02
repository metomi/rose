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
"""This module deals with variable actions.

The methods of VariableOperations are the only ways that variable data
objects should be interacted with (adding, removing, changing value,
etc). There are also some utility methods.

"""
import copy
import time
import webbrowser

import rose.variable
import rose.config_editor
import rose.config_editor.stack


class VariableOperations(object):

    """A class to hold functions that act on variables and their storage."""

    def __init__(self, data, util, reporter, undo_stack, redo_stack,
                 add_section_func,
                 check_cannot_enable_func=rose.config_editor.false_function,
                 update_ns_func=rose.config_editor.false_function,
                 ignore_update_func=rose.config_editor.false_function,
                 search_id_func=rose.config_editor.false_function):
        self.__data = data
        self.__util = util
        self.__reporter = reporter
        self.__undo_stack = undo_stack
        self.__redo_stack = redo_stack
        self.__add_section_func = add_section_func
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

    def add_var(self, variable, skip_update=False, skip_undo=False):
        """Add a variable to the internal list."""
        namespace = variable.metadata.get('full_ns')
        var_id = variable.metadata['id']
        sect, opt = self.__util.get_section_option_from_id(var_id)
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        old_metadata = copy.deepcopy(variable.metadata)
        flags = self.__data.load_option_flags(config_name, sect, opt)
        variable.flags.update(flags)
        metadata = self.__data.helper.get_metadata_for_config_id(var_id,
                                                                 config_name)
        variable.process_metadata(metadata)
        variable.metadata.update(old_metadata)
        variables = config_data.vars.now.get(sect, [])
        copy_var = variable.copy()
        v_id = variable.metadata.get('id')
        if v_id in [v.metadata.get('id') for v in variables]:
            # This is the case of adding a blank variable and
            # renaming it to an existing variable's name.
            # At the moment, assume this should just be skipped.
            pass
        else:
            group = None
            if sect not in config_data.sections.now:
                start_stack_index = len(self.__undo_stack)
                group = (rose.config_editor.STACK_GROUP_ADD + "-" +
                         str(time.time()))
                self.__add_section_func(config_name, sect)
                for item in self.__undo_stack[start_stack_index:]:
                    item.group = group
            latent_variables = config_data.vars.latent.get(sect, [])
            for latent_var in list(latent_variables):
                if latent_var.metadata["id"] == v_id:
                    latent_variables.remove(latent_var)
            config_data.vars.now.setdefault(sect, [])
            config_data.vars.now[sect].append(variable)
            if not skip_undo:
                self.__undo_stack.append(
                    rose.config_editor.stack.StackItem(
                        variable.metadata['full_ns'],
                        rose.config_editor.STACK_ACTION_ADDED,
                        copy_var,
                        self.remove_var,
                        [copy_var, skip_update],
                        group=group)
                )
                del self.__redo_stack[:]
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])
        return variable.metadata['full_ns']

    def remove_var(self, variable, skip_update=False, skip_undo=False):
        """Remove the variable entry from the internal lists."""
        variable = self._get_proper_variable(variable)
        variable.error = {}  # Kill any metadata errors before removing.
        namespace = variable.metadata.get('full_ns')
        var_id = variable.metadata['id']
        sect = self.__util.get_section_option_from_id(var_id)[0]
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        config_data = self.__data.config[config_name]
        variables = config_data.vars.now.get(sect, [])
        latent_variables = config_data.vars.latent.get(sect, [])
        if variable in latent_variables:
            latent_variables.remove(variable)
            if not config_data.vars.latent[sect]:
                config_data.vars.latent.pop(sect)
            return None
        if variable in variables:
            variables.remove(variable)
            if not config_data.vars.now[sect]:
                config_data.vars.now.pop(sect)
            if variable.name:
                config_data.vars.latent.setdefault(sect, [])
                config_data.vars.latent[sect].append(variable)
        if not skip_undo:
            copy_var = variable.copy()
            self.__undo_stack.append(
                rose.config_editor.stack.StackItem(
                    variable.metadata['full_ns'],
                    rose.config_editor.STACK_ACTION_REMOVED,
                    copy_var,
                    self.add_var,
                    [copy_var, skip_update]))
            del self.__redo_stack[:]
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])
        return variable.metadata['full_ns']

    def fix_var_ignored(self, variable):
        """Fix any variable ignore state errors."""
        ignored_reasons = list(variable.ignored_reason.keys())
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

    def set_var_ignored(self, variable, new_reason_dict=None, override=False,
                        skip_update=False, skip_undo=False):
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
            return None
        # Protect against user-enabling of triggered ignored.
        if (not override and
                rose.variable.IGNORED_BY_SYSTEM in old_reason and
                rose.variable.IGNORED_BY_SYSTEM not in new_reason_dict):
            if rose.config_editor.WARNING_TYPE_NOT_TRIGGER in variable.error:
                variable.error.pop(
                    rose.config_editor.WARNING_TYPE_NOT_TRIGGER)
        my_ignored_keys = list(variable.ignored_reason.keys())
        if rose.variable.IGNORED_BY_SECTION in my_ignored_keys:
            my_ignored_keys.remove(rose.variable.IGNORED_BY_SECTION)
        old_ignored_keys = list(old_reason.keys())
        if rose.variable.IGNORED_BY_SECTION in old_ignored_keys:
            old_ignored_keys.remove(rose.variable.IGNORED_BY_SECTION)
        if len(my_ignored_keys) > len(old_ignored_keys):
            action_text = rose.config_editor.STACK_ACTION_IGNORED
            if (not old_ignored_keys and
                    rose.config_editor.WARNING_TYPE_ENABLED in variable.error):
                variable.error.pop(rose.config_editor.WARNING_TYPE_ENABLED)
        else:
            action_text = rose.config_editor.STACK_ACTION_ENABLED
            if not my_ignored_keys:
                for err_type in rose.config_editor.WARNING_TYPES_IGNORE:
                    if err_type in variable.error:
                        variable.error.pop(err_type)
        if not skip_undo:
            copy_var = variable.copy()
            self.__undo_stack.append(
                rose.config_editor.stack.StackItem(
                    variable.metadata['full_ns'],
                    action_text,
                    copy_var,
                    self.set_var_ignored,
                    [copy_var, old_reason, True])
            )
            del self.__redo_stack[:]
        self.trigger_ignored_update(variable)
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])
        return variable.metadata['full_ns']

    def set_var_value(self, variable, new_value, skip_update=False,
                      skip_undo=False):
        """Set the value of the variable."""
        variable = self._get_proper_variable(variable)
        if variable.value == new_value:
            # A bad valuewidget setter.
            return None
        variable.old_value = variable.value
        variable.value = new_value
        if not skip_undo:
            copy_var = variable.copy()
            self.__undo_stack.append(
                rose.config_editor.stack.StackItem(
                    variable.metadata['full_ns'],
                    rose.config_editor.STACK_ACTION_CHANGED,
                    copy_var,
                    self.set_var_value,
                    [copy_var, copy_var.old_value])
            )
            del self.__redo_stack[:]
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])
        return variable.metadata['full_ns']

    def set_var_comments(self, variable, comments,
                         skip_update=False, skip_undo=False):
        """Set the comments field for the variable."""
        variable = self._get_proper_variable(variable)
        copy_variable = variable.copy()
        old_comments = copy_variable.comments
        variable.comments = comments
        if not skip_undo:
            self.__undo_stack.append(
                rose.config_editor.stack.StackItem(
                    variable.metadata['full_ns'],
                    rose.config_editor.STACK_ACTION_CHANGED_COMMENTS,
                    copy_variable,
                    self.set_var_comments,
                    [copy_variable, old_comments])
            )
            del self.__redo_stack[:]
        if not skip_update:
            self.trigger_update(variable.metadata['full_ns'])
        return variable.metadata['full_ns']

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
            if (rose.variable.IGNORED_BY_SYSTEM in variable.ignored_reason and
                    rose.variable.IGNORED_BY_SYSTEM not in old_ignore):
                return rose.config_editor.KEY_TIP_TRIGGER_IGNORED
            if (rose.variable.IGNORED_BY_USER in variable.ignored_reason and
                    rose.variable.IGNORED_BY_USER not in old_ignore):
                return rose.config_editor.KEY_TIP_USER_IGNORED
            if (rose.variable.IGNORED_BY_SECTION in variable.ignored_reason and
                    rose.variable.IGNORED_BY_SECTION not in old_ignore):
                return rose.config_editor.KEY_TIP_SECTION_IGNORED
            return rose.config_editor.KEY_TIP_ENABLED
        return ''

    def launch_url(self, variable):
        """Determine and launch the variable help URL in a web browser."""
        if rose.META_PROP_URL not in variable.metadata:
            return
        url = variable.metadata[rose.META_PROP_URL]
        if rose.variable.REC_FULL_URL.match(url):
            # It is a proper URL by itself - launch it.
            return self._launch_url(url)
        # Must be a partial URL (e.g. '#foo') - try to prefix a parent URL.
        ns_url = self.__data.helper.get_ns_url_for_variable(variable)
        if ns_url:
            return self._launch_url(ns_url + url)
        return self._launch_url(url)

    def _launch_url(self, url):
        """Actually launch a URL."""
        try:
            webbrowser.open(url)
        except webbrowser.Error as exc:
            rose.gtk.dialog.run_exception_dialog(exc)

    def search_for_var(self, config_name_or_namespace, setting_id):
        """Launch a search for a setting or variable id."""
        config_name = self.__util.split_full_ns(
            self.__data, config_name_or_namespace)[0]
        self.search_id_func(config_name, setting_id)

    def get_ns_metadata_files(self, namespace):
        """Retrieve filenames within the metadata for this namespace."""
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        return self.__data.config[config_name].meta_files

    def get_sections(self, namespace):
        """Retrieve all real sections (empty or not) for this ns's config."""
        config_name = self.__util.split_full_ns(self.__data, namespace)[0]
        section_objects = self.__data.config[config_name].sections.get_all(
            skip_latent=True)
        return [_.name for _ in section_objects]
