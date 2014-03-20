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

import rose.config_editor


class Updater(object):

    """This handles the updating of various statuses and displays."""

    def __init__(self, data, util, reporter, mainwindow, main_handle,
                 nav_controller, get_pagelist_func,
                 update_bar_widgets_func,
                 refresh_metadata_func,
                 is_pluggable=False):
        self.data = data
        self.util = util
        self.reporter = reporter
        self.mainwindow = mainwindow
        self.main_handle = main_handle
        self.nav_controller = nav_controller
        self.get_pagelist_func = get_pagelist_func
        self.pagelist = []  # This is the current list of pages open.
        self.load_errors = 0
        self.update_bar_widgets_func = update_bar_widgets_func
        self.refresh_metadata_func = refresh_metadata_func
        self.is_pluggable = is_pluggable
        self.nav_panel = None  # This may be set later.

    def namespace_data_is_modified(self, namespace):
        """Return a string for namespace modifications or null string.""" 
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        if config_name is None:
            return ""
        config_data = self.data.config[config_name]
        config_sections = config_data.sections
        if config_name == namespace:
            # This is the top-level.
            if config_name not in self.data.saved_config_names:
                return rose.config_editor.TREE_PANEL_TIP_ADDED_CONFIG
            section_hashes = []
            for sect, sect_data in config_sections.now.items():
                section_hashes.append(sect_data.to_hashable())
            old_section_hashes = []
            for sect, sect_data in config_sections.save.items():
                old_section_hashes.append(sect_data.to_hashable())
            if set(section_hashes) ^ set(old_section_hashes):
                return rose.config_editor.TREE_PANEL_TIP_CHANGED_CONFIG
        allowed_sections = self.data.helper.get_sections_from_namespace(
                                                              namespace)
        save_var_map = {}
        for section in allowed_sections:
            for var in config_data.vars.save.get(section, []):
                if var.metadata['full_ns'] == namespace:
                    save_var_map.update({var.metadata['id']: var})
            for var in config_data.vars.now.get(section, []):
                if var.metadata['full_ns'] == namespace:
                    var_id = var.metadata['id']
                    save_var = save_var_map.get(var_id)
                    if save_var is None:
                        return rose.config_editor.TREE_PANEL_TIP_ADDED_VARS
                    if save_var.to_hashable() != var.to_hashable():
                        # Variable has changed in some form.
                        return rose.config_editor.TREE_PANEL_TIP_CHANGED_VARS
                    save_var_map.pop(var_id)
        if save_var_map:
            # Some variables are now absent.
            return rose.config_editor.TREE_PANEL_TIP_REMOVED_VARS
        if self.data.helper.get_ns_is_default(namespace):
            sections = self.data.helper.get_sections_from_namespace(namespace)
            for section in sections:
                sect_data = config_sections.now.get(section)
                save_sect_data = config_sections.save.get(section)
                if (sect_data is None) != (save_sect_data is None):
                    return rose.config_editor.TREE_PANEL_TIP_DIFF_SECTIONS
                if sect_data is not None and save_sect_data is not None:
                    if sect_data.to_hashable() != save_sect_data.to_hashable():
                        return rose.config_editor.TREE_PANEL_TIP_CHANGED_SECTIONS
        return ""

    def update_ns_tree_states(self, namespace):
        """Refresh the tree panel states for a single row (namespace)."""
        if self.nav_panel is not None:
            latent_status = self.data.helper.get_ns_latent_status(namespace)
            ignored_status = self.data.helper.get_ns_ignored_status(namespace)
            ns_names = namespace.lstrip("/").split("/")
            self.nav_panel.update_statuses(ns_names, latent_status,
                                           ignored_status)

    def tree_trigger_update(self, only_this_config=None,
                            only_this_namespace=None):
        """Reload the tree panel, and perform an update.

        If only_this_config is not None, perform an update only on the
        particular configuration namespaces.

        If only_this_namespace is not None, perform a selective update
        to save time.

        """
        if self.nav_panel is not None:
            self.nav_panel.load_tree(None,
                                     self.nav_controller.namespace_tree)
            if only_this_namespace is None:
                self.update_all(only_this_config=only_this_config)
            else:
                self.update_all(skip_checking=True, skip_sub_data_update=True)
                spaces = only_this_namespace.lstrip("/").split("/")
                for i in range(len(spaces), 0, -1):
                    update_ns = "/" + "/".join(spaces[:i])
                    self.update_namespace(update_ns,
                                          skip_sub_data_update=True)
                self.update_ns_sub_data(only_this_namespace)

    def refresh_ids(self, config_name, setting_ids, is_loading=False,
                    are_errors_done=False):
        """Refresh and redraw settings if needed."""
        self.pagelist = self.get_pagelist_func()
        nses_to_do = []
        for changed_id in setting_ids:
            sect, opt = self.util.get_section_option_from_id(changed_id)
            if opt is None:
                ns = self.data.helper.get_default_namespace_for_section(
                                          sect, config_name)
                if ns in [p.namespace for p in self.pagelist]:
                    index = [p.namespace for p in self.pagelist].index(ns)
                    page = self.pagelist[index]
                    page.refresh()
            else:
                var = self.data.helper.get_ns_variable(changed_id,
                                                       config_name)
                if var is None:
                    continue
                ns = var.metadata['full_ns']
                if ns in [p.namespace for p in self.pagelist]:
                    index = [p.namespace for p in self.pagelist].index(ns)
                    page = self.pagelist[index]
                    page.refresh(changed_id)
            if ns not in nses_to_do and not are_errors_done:
                nses_to_do.append(ns)
        for ns in nses_to_do:
            self.update_namespace(ns, is_loading=is_loading)

    def update_all(self, only_this_config=None, is_loading=False,
                   skip_checking=False, skip_sub_data_update=False):
        """Loop over all namespaces and update."""
        unique_namespaces = self.data.helper.get_all_namespaces(
                                                     only_this_config)
        if only_this_config is None:
            configs = self.data.config.keys()
        else:
            configs = [only_this_config]
        for config_name in configs:
            self.update_config(config_name)
        self.pagelist = self.get_pagelist_func()

        if not skip_checking:
            for ns in unique_namespaces:
                if ns in [p.namespace for p in self.pagelist]:
                    index = [p.namespace for p in self.pagelist].index(ns)
                    page = self.pagelist[index]
                    self.sync_page_var_lists(page)
                self.update_ignored_statuses(ns)
                self.update_ns_tree_states(ns)
            self.perform_error_check(is_loading=is_loading)

        for ns in unique_namespaces:
            if ns in [p.namespace for p in self.pagelist]:
                index = [p.namespace for p in self.pagelist].index(ns)
                page = self.pagelist[index]
                self.update_tree_status(page)  # Faster.
            else:
                self.update_tree_status(ns)
        self.update_bar_widgets_func()
        self.update_stack_viewer_if_open()
        for config_name in configs:
            self.update_metadata_id(config_name)
        if not skip_sub_data_update:
            self.update_ns_sub_data()

    def update_namespace(self, namespace, are_errors_done=False,
                         is_loading=False,
                         skip_sub_data_update=False):
        """Update driver function. Updates the page if open."""
        self.pagelist = self.get_pagelist_func()
        if namespace in [p.namespace for p in self.pagelist]:
            index = [p.namespace for p in self.pagelist].index(namespace)
            page = self.pagelist[index]
            self.update_status(page, are_errors_done=are_errors_done,
                               skip_sub_data_update=skip_sub_data_update)
        else:
            self.update_sections(namespace)
            self.update_ignored_statuses(namespace)
            if not are_errors_done and not is_loading:
                self.perform_error_check(namespace)
            self.update_tree_status(namespace)
            if not is_loading:
                self.update_bar_widgets_func()
            self.update_stack_viewer_if_open()
            self.update_ns_tree_states(namespace)
            if namespace in self.data.config.keys():
                self.update_metadata_id(namespace)
            if not skip_sub_data_update:
                self.update_ns_sub_data(namespace)

    def update_status(self, page, are_errors_done=False,
                      skip_sub_data_update=False):
        """Update ignored statuses and update the tree statuses."""
        self.pagelist = self.get_pagelist_func()
        self.sync_page_var_lists(page)
        self.update_sections(page.namespace)
        self.update_ignored_statuses(page.namespace)
        if not are_errors_done:
            self.perform_error_check(page.namespace)
        self.update_tree_status(page)
        self.update_bar_widgets_func()
        self.update_stack_viewer_if_open()
        page.update_info()
        self.update_ns_tree_states(page.namespace)
        if page.namespace in self.data.config.keys():
            self.update_metadata_id(page.namespace)
        if not skip_sub_data_update:
            self.update_ns_sub_data(page.namespace)

    def update_ns_sub_data(self, namespace=None):
        """Update any relevant summary data on another page."""
        for page in self.pagelist:
            if (namespace is not None and
                 not namespace.startswith(page.namespace) and
                 namespace != page.namespace):
                continue
            page.sub_data = self.data.helper.get_sub_data_for_namespace(
                                                     page.namespace)
            page.update_sub_data()

    def update_ns_info(self, namespace):
        if namespace in [p.namespace for p in self.pagelist]:
            index = [p.namespace for p in self.pagelist].index(namespace)
            page = self.pagelist[index]
            page.update_ignored()
            page.update_info()

    def sync_page_var_lists(self, page):
        """Make sure the list of page variables has the right members."""
        config_name = self.util.split_full_ns(self.data, page.namespace)[0]
        real, miss = self.data.helper.get_data_for_namespace(
                                                   page.namespace)
        page_real, page_miss = page.panel_data, page.ghost_data
        refresh_vars = []
        action_vsets = [(page_real.remove, set(page_real) - set(real)),
                        (page_real.append, set(real) - set(page_real)),
                        (page_miss.remove, set(page_miss) - set(miss)),
                        (page_miss.append, set(miss) - set(page_miss))]

        for action, v_set in action_vsets:
            for var in v_set:
                if var not in refresh_vars:
                    refresh_vars.append(var)
            for var in v_set:
                action(var)
        for var in refresh_vars:
            page.refresh(var.metadata['id'])

    def update_config(self, namespace):
        """Update the config object for the macros."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config = self.data.dump_to_internal_config(config_name)
        self.data.config[config_name].config = config

    def update_sections(self, namespace):
        """Update the list of sections that are empty."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        ns_sections = self.data.helper.get_sections_from_namespace(namespace)
        for section in ns_sections:
            sect_data = config_data.sections.now.get(section)
            if sect_data is None:
                continue
            variables = config_data.vars.now.get(section, [])
            sect_data.options = []
            if not variables:
                if section in config_data.vars.now:
                    config_data.vars.now.pop(section)
            for variable in variables:
                var_id = variable.metadata['id']
                option = self.util.get_section_option_from_id(var_id)[1]
                sect_data.options.append(option)

    def update_ignored_statuses(self, namespace):
        """Refresh the list of ignored variables and update relevant pages."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        # Check for triggering variables that have changed values
        self.data.trigger_id_value_lookup.setdefault(config_name, {})
        trig_id_val_dict = self.data.trigger_id_value_lookup[config_name]
        trigger = self.data.trigger[config_name]
        allowed_sections = self.data.helper.get_sections_from_namespace(
                                                              namespace)
        updated_ids = []

        this_ns_triggers = []
        ns_vars, ns_l_vars = self.data.helper.get_data_for_namespace(
                                                           namespace)
        for var in ns_vars + ns_l_vars:
            var_id = var.metadata['id']
            if not trigger.check_is_id_trigger(var_id, config_data.meta):
                continue
            if var in ns_l_vars:
                new_val = None
            else:
                new_val = var.value
            old_val = trig_id_val_dict.get(var_id)
            if old_val != new_val:  # new_val or old_val can be None
                this_ns_triggers.append(var_id)
                updated_ids += self.update_ignoreds(config_name,
                                                    var_id)

        if not this_ns_triggers:
            # No reason to update anything.
            return False

        var_id_map = {}
        for var in config_data.vars.get_all(skip_latent=True):
            var_id = var.metadata['id']
            var_id_map.update({var_id: var})

        update_nses = []
        update_section_nses = []
        for setting_id in updated_ids:
            sect, opt = self.util.get_section_option_from_id(setting_id)
            if opt is None:
                sect_vars = config_data.vars.now.get(sect, [])
                ns = self.data.helper.get_default_namespace_for_section(
                                          sect, config_name)
                if ns not in update_section_nses:
                    update_section_nses.append(ns)
            else:
                sect_vars = list(config_data.vars.now.get(sect, []))
                sect_vars += list(config_data.vars.latent.get(sect, []))
                for var in list(sect_vars):
                    if var.metadata['id'] != setting_id:
                        sect_vars.remove(var)
            for var in sect_vars:
                var_ns = var.metadata['full_ns']
                var_id = var.metadata['id']
                vsect = self.util.get_section_option_from_id(var_id)[0]
                if var_ns not in update_nses:
                    update_nses.append(var_ns)
                if (vsect in updated_ids and
                    var_ns not in update_section_nses):
                    update_section_nses.append(var_ns)
        for page in self.pagelist:
            if page.namespace in update_nses:
                page.update_ignored()  # Redraw affected widgets.
            if page.namespace in update_section_nses:
                page.update_info()
        for ns in update_nses:
            if ns != namespace:
                # We don't need another update of namespace.
                self.update_ns_tree_states(ns)
        for var_id in trig_id_val_dict.keys() + updated_ids:
            var = var_id_map.get(var_id)
            if var is None:
                if var_id in trig_id_val_dict:
                    trig_id_val_dict.pop(var_id)
            else:
                trig_id_val_dict.update(
                                    {var_id: var.value})

    def update_ignoreds(self, config_name, var_id):
        """Update the variable ignored flags ('reasons')."""
        config_data = self.data.config[config_name]
        trigger = self.data.trigger[config_name]

        config = config_data.config
        meta_config = config_data.meta
        config_sections = config_data.sections
        config_data_for_trigger = {"sections": config_sections.now,
                                   "variables": config_data.vars.now}
        update_ids = trigger.update(var_id, config_data_for_trigger,
                                    meta_config)
        update_vars = []
        update_sections = []
        for setting_id in update_ids:
            section, option = self.util.get_section_option_from_id(setting_id)
            if option is None:
                update_sections.append(section)
            else:
                for var in config_data.vars.now.get(section, []):
                    if var.metadata['id'] == setting_id:
                        update_vars.append(var)
                        break
                else:
                    for var in config_data.vars.latent.get(section, []):
                        if var.metadata['id'] == setting_id:
                            update_vars.append(var)
                            break
        triggered_ns_list = []
        this_id = var_id
        nses = []
        for namespace, metadata in self.data.namespace_meta_lookup.items():
            this_name = self.util.split_full_ns(self.data, namespace)
            if this_name != config_name:
                continue
            for section in update_sections:
                if section in metadata['sections']:
                    triggered_ns_list.append(namespace)

        # Update the sections.
        enabled_sections = [s for s in update_sections
                            if s in trigger.enabled_dict and
                            s not in trigger.ignored_dict]
        for section in update_sections:
            # Clear pre-existing errors.
            sect_vars = (config_data.vars.now.get(section, []) +
                         config_data.vars.latent.get(section, []))
            sect_data = config_sections.now.get(section)
            if sect_data is None:
                sect_data = config_sections.latent[section]
            for attribute in rose.config_editor.WARNING_TYPES_IGNORE:
                if attribute in sect_data.error:
                    sect_data.error.pop(attribute)
            reason = sect_data.ignored_reason
            if section in enabled_sections:
                # Trigger-enabled sections
                if (rose.variable.IGNORED_BY_USER in reason):
                    # User-ignored but trigger-enabled
                    if (meta_config.get(
                            [section, rose.META_PROP_COMPULSORY]).value
                        == rose.META_PROP_VALUE_TRUE):
                        # Doc table: I_u -> E -> compulsory
                        sect_data.error.update(
                              {rose.config_editor.WARNING_TYPE_USER_IGNORED:
                               rose.config_editor.WARNING_NOT_USER_IGNORABLE})
                elif (rose.variable.IGNORED_BY_SYSTEM in reason):
                    # Normal trigger-enabled sections
                    reason.pop(rose.variable.IGNORED_BY_SYSTEM)
                    for var in sect_vars:
                        ns = var.metadata['full_ns']
                        if ns not in triggered_ns_list:
                            triggered_ns_list.append(ns)
                        var.ignored_reason.pop(
                                    rose.variable.IGNORED_BY_SECTION)
            elif section in trigger.ignored_dict:
                # Trigger-ignored sections
                parents = trigger.ignored_dict.get(section, {})
                if parents:
                    help_text = "; ".join(parents.values())
                else:
                    help_text = rose.config_editor.IGNORED_STATUS_DEFAULT
                reason.update({rose.variable.IGNORED_BY_SYSTEM: help_text})
                for var in sect_vars:
                    ns = var.metadata['full_ns']
                    if ns not in triggered_ns_list:
                        triggered_ns_list.append(ns)
                    var.ignored_reason.update(
                                {rose.variable.IGNORED_BY_SECTION: help_text})
        # Update the variables.
        for var in update_vars:
            var_id = var.metadata.get('id')
            ns = var.metadata.get('full_ns')
            if ns not in triggered_ns_list:
                triggered_ns_list.append(ns)
            if var_id == this_id:
                continue
            for attribute in rose.config_editor.WARNING_TYPES_IGNORE:
                if attribute in var.error:
                    var.error.pop(attribute)
            if (var_id in trigger.enabled_dict and
                var_id not in trigger.ignored_dict):
                # Trigger-enabled variables
                if (rose.variable.IGNORED_BY_USER in
                    var.ignored_reason):
                    # User-ignored but trigger-enabled
                    # Doc table: I_u -> E
                    if (var.metadata.get(rose.META_PROP_COMPULSORY) ==
                        rose.META_PROP_VALUE_TRUE):
                        # Doc table: I_u -> E -> compulsory
                        var.error.update(
                              {rose.config_editor.WARNING_TYPE_USER_IGNORED:
                               rose.config_editor.WARNING_NOT_USER_IGNORABLE})
                elif (rose.variable.IGNORED_BY_SYSTEM in
                      var.ignored_reason):
                    # Normal trigger-enabled variables
                    var.ignored_reason.pop(rose.variable.IGNORED_BY_SYSTEM)
            elif var_id in trigger.ignored_dict:
                # Trigger-ignored variables
                parents = trigger.ignored_dict.get(var_id, {})
                if parents:
                    help_text = "; ".join(parents.values())
                else:
                    help_text = rose.config_editor.IGNORED_STATUS_DEFAULT
                var.ignored_reason.update(
                            {rose.variable.IGNORED_BY_SYSTEM: help_text})
        for namespace in triggered_ns_list:
            self.update_tree_status(namespace)
        return update_ids

    def update_tree_status(self, page_or_ns, icon_bool=None, icon_type=None):
        """Update the tree statuses."""
        if self.nav_panel is None:
            return
        if isinstance(page_or_ns, basestring):
            namespace = page_or_ns
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            errors = []
            ns_vars, ns_l_vars = self.data.helper.get_data_for_namespace(
                                                               namespace)
            for var in ns_vars + ns_l_vars:
                errors += var.error.items()
        else:
            namespace = page_or_ns.namespace
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            errors = page_or_ns.validate_errors()
        # Add section errors.
        config_data = self.data.config[config_name]
        ns_sections = self.data.helper.get_sections_from_namespace(namespace)
        for section in ns_sections:
            if section in config_data.sections.now:
                errors += config_data.sections.now[section].error.items()
            elif section in config_data.sections.latent:
                errors += config_data.sections.latent[section].error.items()
                
        # Set icons.
        name_tree = namespace.lstrip('/').split('/')
        if icon_bool is None:
            if icon_type == 'changed' or icon_type is None:
                change = self.namespace_data_is_modified(namespace)
                self.nav_panel.update_change(name_tree, change)
                self.nav_panel.set_row_icon(name_tree, bool(change),
                                            ind_type='changed')
            if icon_type == 'error' or icon_type is None:
                self.nav_panel.set_row_icon(name_tree, len(errors),
                                            ind_type='error')
        else:
            self.nav_panel.set_row_icon(name_tree, icon_bool,
                                        ind_type=icon_type)

    def update_stack_viewer_if_open(self):
        """Update the information in the stack viewer, if open."""
        if self.is_pluggable:
            return False
        if isinstance(self.mainwindow.log_window,
                      rose.config_editor.stack.StackViewer):
            self.mainwindow.log_window.update()

    def focus_sub_page_if_open(self, namespace, node_id):
        """Focus the sub (summary) page for a namespace and id."""
        if "/" not in namespace:
            return False
        summary_namespace = namespace.rsplit("/", 1)[0]
        self.pagelist = self.get_pagelist_func()
        page_namespaces = [p.namespace for p in self.pagelist]
        if summary_namespace not in page_namespaces:
            return False
        page = self.pagelist[page_namespaces.index(summary_namespace)]
        page.set_sub_focus(node_id)

    def update_metadata_id(self, config_name):
        """Update the metadata if the id has changed."""
        config_data = self.data.config[config_name]
        new_meta_id = self.data.helper.get_config_meta_flag(
                                                  config_data.config)
        if config_data.meta_id != new_meta_id:
            config_data.meta_id = new_meta_id
            self.refresh_metadata_func(config_name=config_name)

    def perform_startup_check(self):
        """Fix any relevant type errors."""
        for config_name in self.data.config:
            macro_config = self.data.dump_to_internal_config(config_name)
            meta_config = self.data.config[config_name].meta
            # Duplicate checking
            dupl_checker = rose.macros.duplicate.DuplicateChecker()
            problem_list = dupl_checker.validate(macro_config, meta_config)
            if problem_list:
                self.main_handle.handle_macro_validation(
                          config_name,
                          'duplicate.DuplicateChecker.validate',
                          macro_config, problem_list, no_display=True)
            format_checker = rose.macros.format.FormatChecker()
            problem_list = format_checker.validate(macro_config, meta_config)
            if problem_list:
                self.main_handle.handle_macro_validation(
                          config_name, 'format.FormatChecker.validate',
                          macro_config, problem_list)

    def perform_error_check(self, namespace=None, is_loading=False):
        """Loop through system macros and sum errors."""
        configs = self.data.config.keys()
        if namespace is not None:
            config_name = self.util.split_full_ns(self.data,
                                                  namespace)[0]
            configs = [config_name]
        # Compulsory checking.
        for config_name in configs:
            config_data = self.data.config[config_name]
            meta = config_data.meta
            checker = (
                self.data.builtin_macros[config_name][
                    rose.META_PROP_COMPULSORY])
            only_these_sections = None
            if namespace is not None:
                only_these_sections = (
                    self.data.helper.get_sections_from_namespace(namespace))
            config_data_for_compulsory = {
                "sections": config_data.sections.now,
                "variables": config_data.vars.now
            }
            bad_list = checker.validate_settings(
                config_data_for_compulsory, config_data.meta,
                only_these_sections=only_these_sections
            )
            self.apply_macro_validation(config_name,
                                        rose.META_PROP_COMPULSORY, bad_list,
                                        namespace, is_loading=is_loading,
                                        is_macro_dynamic=True)
        # Value checking.
        for config_name in configs:
            config_data = self.data.config[config_name]
            meta = config_data.meta
            checker = (
                self.data.builtin_macros[config_name][rose.META_PROP_TYPE])
            if namespace is None:
                real_variables = config_data.vars.get_all(skip_latent=True)
            else:
                real_variables, latent_variables = (
                    self.data.helper.get_data_for_namespace(namespace))
            bad_list = checker.validate_variables(real_variables, meta)
            self.apply_macro_validation(config_name, rose.META_PROP_TYPE,
                                        bad_list,
                                        namespace, is_loading=is_loading,
                                        is_macro_dynamic=True)

    def apply_macro_validation(self, config_name, macro_type, bad_list=None,
                               namespace=None, is_loading=False,
                               is_macro_dynamic=False):
        """Display error icons if a variable is in the wrong state."""
        if bad_list is None:
            bad_list = []
        config_data = self.data.config[config_name]
        config = config_data.config  # This should be up to date.
        meta = config_data.meta
        config_sections = config_data.sections
        variables = config_data.vars.get_all()
        id_error_dict = {}
        id_warn_dict = {}
        if namespace is None:
            ok_sections = (config_sections.now.keys() +
                           config_sections.latent.keys())
            ok_variables = variables
        else:
            ok_sections = self.data.helper.get_sections_from_namespace(
                                                             namespace)
            ok_variables = [v for v in variables
                            if v.metadata.get('full_ns') == namespace]
        for section in ok_sections:
            sect_data = config_sections.now.get(section)
            if sect_data is None:
                sect_data = config_sections.latent.get(section)
                if sect_data is None:
                    continue
            if macro_type in sect_data.error:
                this_error = sect_data.error.pop(macro_type)
                id_error_dict.update({section: this_error})
            if macro_type in sect_data.warning:
                this_warning = sect_data.warning.pop(macro_type)
                id_warn_dict.update({section: this_warning})
        for var in ok_variables:
            if macro_type in var.error:
                this_error = var.error.pop(macro_type)
                id_error_dict.update({var.metadata['id']: this_error})
            if macro_type in var.warning:
                this_warning = var.warning.pop(macro_type)
                id_warn_dict.update({var.metadata['id']: this_warning})
        if not bad_list:
            self.refresh_ids(config_name,
                             id_error_dict.keys() + id_warn_dict.keys(),
                             is_loading, are_errors_done=is_macro_dynamic)
            return
        for bad_report in bad_list:
            section = bad_report.section
            key = bad_report.option
            info = bad_report.info
            if key is None:
                setting_id = section
                if (namespace is not None and section not in
                    self.data.helper.get_sections_from_namespace(namespace)):
                    continue
                sect_data = config_sections.now.get(section)
                if sect_data is None:
                    sect_data = config_sections.latent.get(section)
                if sect_data is None:
                    continue
                if bad_report.is_warning:
                    sect_data.warning.setdefault(macro_type, info)
                else:
                    sect_data.error.setdefault(macro_type, info)
            else:
                setting_id = self.util.get_id_from_section_option(
                                                    section, key)
                var = self.data.helper.get_variable_by_id(setting_id,
                                                          config_name)
                if var is None:
                    var = self.data.helper.get_variable_by_id(setting_id,
                                                              config_name,
                                                              latent=True)
                if var is None:
                    continue
                if (namespace is not None and
                    var.metadata['full_ns'] != namespace):
                    continue
                if bad_report.is_warning:
                    var.warning.setdefault(macro_type, info)
                else:
                    var.error.setdefault(macro_type, info)
            if bad_report.is_warning:
                map_ = id_warn_dict
            else:
                map_ = id_error_dict
                if is_loading:
                    self.load_errors += 1
                    update_text = rose.config_editor.EVENT_LOAD_ERRORS.format(
                                                     self.data.top_level_name,
                                                     self.load_errors)

                    self.reporter.report_load_event(update_text,
                                                    no_progress=True)
            if setting_id in map_:
                # No need for further update, already had warning/error.
                map_.pop(setting_id)
            else:
                # New warning or error.
                map_.update({setting_id: info})
        self.refresh_ids(config_name,
                         id_error_dict.keys() + id_warn_dict.keys(),
                         is_loading,
                         are_errors_done=is_macro_dynamic)

    def apply_macro_transform(self, config_name, macro_type, changed_ids):
        """Refresh pages with changes."""
        self.refresh_ids(config_name, changed_ids)
