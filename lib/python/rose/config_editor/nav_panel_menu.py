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

import os
import time
import webbrowser

import pygtk
pygtk.require('2.0')
import gtk

import rose.config
import rose.config_editor.util
import rose.gtk.dialog


class NavPanelHandler(object):

    """Handles the navigation panel menu."""

    def __init__(self, data, util, reporter, mainwindow,
                 undo_stack, redo_stack, add_config_func,
                 group_ops_inst, section_ops_inst, variable_ops_inst,
                 kill_page_func, reload_ns_tree_func, transform_default_func,
                 graph_ns_func):
        self.data = data
        self.util = util
        self.reporter = reporter
        self.mainwindow = mainwindow
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.group_ops = group_ops_inst
        self.sect_ops = section_ops_inst
        self.var_ops = variable_ops_inst
        self._add_config = add_config_func
        self.kill_page_func = kill_page_func
        self.reload_ns_tree_func = reload_ns_tree_func
        self._transform_default_func = transform_default_func
        self._graph_ns_func = graph_ns_func

    def add_dialog(self, base_ns):
        """Handle an add section dialog and request."""
        if base_ns is not None and '/' in base_ns:
            config_name, subsp = self.util.split_full_ns(self.data, base_ns)
            config_data = self.data.config[config_name]
            if config_name == base_ns:
                help_str = ''
            else:
                sections = self.data.helper.get_sections_from_namespace(
                                                              base_ns)
                if sections == []:
                    help_str = subsp.replace('/', ':')
                else:
                    help_str = sections[0]
                help_str = help_str.split(':', 1)[0]
                for config_section in (config_data.sections.now.keys() +
                                       config_data.sections.latent.keys()):
                    if config_section.startswith(help_str + ":"):
                        help_str = help_str + ":"
        else:
            help_str = None
            config_name = None
        choices_help = self.data.helper.get_missing_sections(config_name)

        config_names = [n for n in self.data.config if not self.ask_is_preview(n)]
        config_names.sort(lambda x, y: (y == config_name) -(x == config_name))
        config_name, section = self.mainwindow.launch_add_dialog(
                                    config_names, choices_help, help_str)
        if config_name in self.data.config and section is not None:
            self.sect_ops.add_section(config_name, section, page_launch=True)

    def ask_is_preview(self, base_ns):
        namespace = "/" + base_ns.lstrip("/")
        try:
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            config_data = self.data.config[config_name]
            return config_data.is_preview
        except KeyError:
            print config_name
            return False

    def copy_request(self, base_ns, new_section=None, skip_update=False):
        """Handle a copy request for a section and its options."""
        namespace = "/" + base_ns.lstrip("/")
        sections = self.data.helper.get_sections_from_namespace(namespace)
        if len(sections) != 1:
            return False
        section = sections.pop()
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        return self.group_ops.copy_section(config_name, section,
                                           skip_update=skip_update)

    def create_request(self):
        """Handle a create configuration request."""
        if not any([v.config_type == rose.TOP_CONFIG_NAME
                    for v in self.data.config.values()]):
            text = rose.config_editor.WARNING_APP_CONFIG_CREATE
            title = rose.config_editor.WARNING_APP_CONFIG_CREATE_TITLE
            rose.gtk.dialog.run_dialog(rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                       text, title)
            return False
        # Need an application configuration to be created.
        root = os.path.join(self.data.top_level_directory,
                            rose.SUB_CONFIGS_DIR)
        name, meta = self.mainwindow.launch_new_config_dialog(root)
        if name is None:
            return False
        config_name = "/" + name
        self._add_config(config_name, meta)

    def ignore_request(self, base_ns, is_ignored):
        """Handle an ignore or enable section request."""
        config_names = self.data.config.keys()
        if base_ns is not None and '/' in base_ns:
            config_name, subsp = self.util.split_full_ns(self.data, base_ns)
            prefer_name_sections = {
                  config_name: self.data.helper.get_sections_from_namespace(
                                                                  base_ns)}
        else:
            prefer_name_sections = {}
        config_sect_dict = {}
        sorter = rose.config.sort_settings
        for config_name in config_names:
            config_data = self.data.config[config_name]
            config_sect_dict[config_name] = []
            sect_and_data = list(config_data.sections.now.items())
            for v_sect in config_data.vars.now:
                sect_data = config_data.sections.now[v_sect]
                sect_and_data.append((v_sect, sect_data))
            for section, sect_data in sect_and_data:
                if section not in config_sect_dict[config_name]:
                    if sect_data.ignored_reason:
                        if is_ignored:
                            continue
                    if not is_ignored:
                        co = sect_data.metadata.get(rose.META_PROP_COMPULSORY)
                        if (not sect_data.ignored_reason or
                            co == rose.META_PROP_VALUE_TRUE):
                            continue
                    config_sect_dict[config_name].append(section)
            config_sect_dict[config_name].sort(
                             rose.config.sort_settings)
            if config_name in prefer_name_sections:
                prefer_name_sections[config_name].sort(
                            rose.config.sort_settings)
        config_name, section = self.mainwindow.launch_ignore_dialog(
                                               config_sect_dict,
                                               prefer_name_sections,
                                               is_ignored)
        if config_name in self.data.config and section is not None:
            self.sect_ops.ignore_section(config_name, section, is_ignored)

    def edit_request(self, base_ns):
        """Handle a request for editing section comments."""
        if base_ns is None:
            return False
        base_ns = "/" + base_ns.lstrip("/")
        config_name, subsp = self.util.split_full_ns(self.data, base_ns)
        config_data = self.data.config[config_name]
        sections = self.data.helper.get_sections_from_namespace(base_ns)
        for section in list(sections):
            if section not in config_data.sections.now:
                sections.remove(section)
        if not sections:
            return False
        if len(sections) > 1:
            section = rose.gtk.dialog.run_choices_dialog(
                          rose.config_editor.DIALOG_LABEL_CHOOSE_SECTION_EDIT,
                          sections,
                          rose.config_editor.DIALOG_TITLE_CHOOSE_SECTION)
        else:
            section = sections[0]
        if section is None:
            return False
        title = rose.config_editor.DIALOG_TITLE_EDIT_COMMENTS.format(section)
        text = "\n".join(config_data.sections.now[section].comments)
        finish = lambda t: self.sect_ops.set_section_comments(
                                     config_name, section,t.splitlines())
        rose.gtk.dialog.run_edit_dialog(text, finish_hook=finish, title=title)

    def fix_request(self, base_ns):
        """Handle a request to auto-fix a configuration."""
        if base_ns is None:
            return False
        base_ns = "/" + base_ns.lstrip("/")
        config_name, subsp = self.util.split_full_ns(self.data, base_ns)
        self._transform_default_func(only_this_config=config_name)

    def get_ns_metadata_and_comments(self, namespace):
        """Return metadata dict and comments list."""
        namespace = "/" + namespace.lstrip("/")
        metadata = {}
        comments = ""
        if namespace is None:
            return metadata, comments
        metadata = self.data.namespace_meta_lookup.get(namespace, {})
        comments = self.data.helper.get_ns_comment_string(namespace)
        return metadata, comments

    def info_request(self, namespace):
        """Handle a request for namespace info."""
        if namespace is None:
            return False
        config_name, subsp = self.util.split_full_ns(self.data, namespace)
        config_data = self.data.config[config_name]
        sections = self.data.helper.get_sections_from_namespace(namespace)
        search_function = lambda i: self.search_request(namespace, i)
        for section in sections:
            sect_data = config_data.sections.now.get(section)
            if sect_data is not None:
                rose.config_editor.util.launch_node_info_dialog(
                            sect_data, "", search_function)

    def graph_request(self, namespace):
        """Handle a graph request for namespace info."""
        self._graph_ns_func(namespace)

    def remove_request(self, base_ns):
        """Handle a delete section request."""
        config_names = self.data.config.keys()
        if base_ns is not None and '/' in base_ns:
            config_name, subsp = self.util.split_full_ns(self.data, base_ns)
            prefer_name_sections = {
                  config_name: self.data.helper.get_sections_from_namespace(
                                                                  base_ns)}
        else:
            prefer_name_sections = {}
        config_sect_dict = {}
        sorter = rose.config.sort_settings
        for config_name in config_names:
            config_data = self.data.config[config_name]
            config_sect_dict[config_name] = config_data.sections.now.keys()
            config_sect_dict[config_name].sort(
                             rose.config.sort_settings)
            if config_name in prefer_name_sections:
                prefer_name_sections[config_name].sort(
                            rose.config.sort_settings)
        config_name, section = self.mainwindow.launch_remove_dialog(
                                               config_sect_dict,
                                               prefer_name_sections)
        if config_name in self.data.config and section is not None:
            start_stack_index = len(self.undo_stack)
            group = rose.config_editor.STACK_GROUP_DELETE + "-" + str(
                                                                 time.time())
            config_data = self.data.config[config_name]
            sect_data = config_data.sections.now[section]
            ns = sect_data.metadata["full_ns"]
            variable_sorter = lambda v, w: rose.config.sort_settings(
                                                        v.metadata['id'],
                                                        w.metadata['id'])
            variables = list(config_data.vars.now.get(section, []))
            variables.sort(variable_sorter)
            variables.reverse()
            for variable in variables:
                self.var_ops.remove_var(variable)
            self.sect_ops.remove_section(config_name, section)
            for stack_item in self.undo_stack[start_stack_index:]:
                stack_item.group = group

    def search_request(self, namespace, setting_id):
        """Handle a search for an id (hyperlink)."""
        config_name, subsp = self.util.split_full_ns(self.data, namespace)
        self.var_ops.search_for_var(config_name, setting_id)

    def popup_panel_menu(self, base_ns, event):
        """Popup a page menu on the navigation panel."""
        if base_ns is None:
            namespace = None
        else:
            namespace = "/" + base_ns.lstrip("/")

        ui_config_string = """<ui> <popup name='Popup'>"""
        actions = [('New', gtk.STOCK_NEW,
                    rose.config_editor.TREE_PANEL_NEW_CONFIG),
                   ('Add', gtk.STOCK_ADD,
                    rose.config_editor.TREE_PANEL_ADD_GENERIC),
                   ('Add section', gtk.STOCK_ADD,
                    rose.config_editor.TREE_PANEL_ADD_SECTION),
                   ('Autofix', gtk.STOCK_CONVERT,
                    rose.config_editor.TREE_PANEL_AUTOFIX_CONFIG),
                   ('Clone', gtk.STOCK_COPY,
                    rose.config_editor.TREE_PANEL_CLONE_SECTION),
                   ('Edit', gtk.STOCK_EDIT,
                    rose.config_editor.TREE_PANEL_EDIT_SECTION),
                   ('Enable', gtk.STOCK_YES,
                    rose.config_editor.TREE_PANEL_ENABLE_GENERIC),
                   ('Enable section', gtk.STOCK_YES,
                    rose.config_editor.TREE_PANEL_ENABLE_SECTION),
                   ('Graph', gtk.STOCK_SORT_ASCENDING,
                    rose.config_editor.TREE_PANEL_GRAPH_SECTION),
                   ('Ignore', gtk.STOCK_NO,
                    rose.config_editor.TREE_PANEL_IGNORE_GENERIC),
                   ('Ignore section', gtk.STOCK_NO,
                    rose.config_editor.TREE_PANEL_IGNORE_SECTION),
                   ('Info', gtk.STOCK_INFO,
                    rose.config_editor.TREE_PANEL_INFO_SECTION),
                   ('Help', gtk.STOCK_HELP,
                    rose.config_editor.TREE_PANEL_HELP_SECTION),
                   ('URL', gtk.STOCK_HOME,
                    rose.config_editor.TREE_PANEL_URL_SECTION),
                   ('Remove', gtk.STOCK_DELETE,
                    rose.config_editor.TREE_PANEL_REMOVE_GENERIC),
                   ('Remove section', gtk.STOCK_DELETE,
                    rose.config_editor.TREE_PANEL_REMOVE_SECTION)]
        url = None
        help = None
        is_empty = (not self.data.config)
        if namespace is not None:
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            if self.data.config[config_name].is_preview:
                return False
            cloneable = self.is_ns_duplicate(namespace)
            is_top = (namespace in self.data.config.keys())
            is_fixable = bool(self.get_ns_errors(namespace))
            has_content = self.data.helper.is_ns_content(namespace)
            is_unsaved = self.data.helper.get_config_has_unsaved_changes(
                config_name)
            ignored_sections = self.data.helper.get_ignored_sections(
                                                namespace)
            enabled_sections = self.data.helper.get_ignored_sections(
                                                namespace, get_enabled=True)
            is_latent = self.data.helper.get_ns_latent_status(namespace)
            latent_sections = self.data.helper.get_latent_sections(
                                                   namespace)
            metadata, comments = self.get_ns_metadata_and_comments(namespace)
            if is_latent:
                for i, section in enumerate(latent_sections):
                    action_name = "Add {0}".format(i)
                    ui_config_string += '<menuitem action="{0}"/>'.format(
                        action_name)
                    actions.append(
                        (action_name, gtk.STOCK_ADD,
                         rose.config_editor.TREE_PANEL_ADD_SECTION.format(
                             section.replace("_", "__")))
                    )
                ui_config_string += '<separator name="addlatentsep"/>'
            ui_config_string += '<menuitem action="Add"/>'
            if cloneable:
                ui_config_string += '<separator name="clonesep"/>'
                ui_config_string += '<menuitem action="Clone"/>'
            ui_config_string += '<separator name="ignoresep"/>'
            ui_config_string += '<menuitem action="Enable"/>'
            ui_config_string += '<menuitem action="Ignore"/>'
            ui_config_string += '<separator name="infosep"/>'
            if has_content:
                ui_config_string += '<menuitem action="Info"/>'
                ui_config_string += '<menuitem action="Edit"/>'
                ui_config_string += '<separator name="graphsep"/>'
                ui_config_string += '<menuitem action="Graph"/>'
            url = metadata.get(rose.META_PROP_URL)
            help = metadata.get(rose.META_PROP_HELP)
            if url is not None or help is not None:
                ui_config_string += '<separator name="helpsep"/>'
                if url is not None:
                    ui_config_string += '<menuitem action="URL"/>'
                if help is not None:
                    ui_config_string += '<menuitem action="Help"/>'
            if not is_empty:
                ui_config_string += """<separator name="removesep"/>"""
                ui_config_string += """<menuitem action="Remove"/>"""
            if is_fixable:
                ui_config_string += """<separator name="sepauto"/>
                                       <menuitem action="Autofix"/>"""
        else:
            ui_config_string += '<menuitem action="Add"/>'
            ui_config_string += '<separator name="ignoresep"/>'
            ui_config_string += '<menuitem action="Enable"/>'
            ui_config_string += '<menuitem action="Ignore"/>'
        if namespace is None or (is_top or is_empty):
            ui_config_string += """<separator name="newconfigsep"/>
                                   <menuitem action="New"/>"""
        ui_config_string += """</popup> </ui>"""
        uimanager = gtk.UIManager()
        actiongroup = gtk.ActionGroup('Popup')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(ui_config_string)
        if namespace is None or (is_top or is_empty):
            new_item = uimanager.get_widget('/Popup/New')
            new_item.connect("activate",
                             lambda b: self.create_request())
            new_item.set_sensitive(not is_empty)
        add_item = uimanager.get_widget('/Popup/Add')
        add_item.connect("activate",
                         lambda b: self.add_dialog(namespace))
        add_item.set_sensitive(not is_empty)
        enable_item = uimanager.get_widget('/Popup/Enable')
        enable_item.connect(
                    "activate",
                    lambda b: self.ignore_request(namespace, False))
        enable_item.set_sensitive(not is_empty)
        ignore_item = uimanager.get_widget('/Popup/Ignore')
        ignore_item.connect(
                    "activate",
                    lambda b: self.ignore_request(namespace, True))
        ignore_item.set_sensitive(not is_empty)
        if namespace is not None:
            if is_latent:
                for i, section in enumerate(latent_sections):
                    action_name = "Add {0}".format(i)
                    add_item = uimanager.get_widget("/Popup/" + action_name)
                    add_item._section = section
                    add_item.connect("activate",
                                     lambda b: self.sect_ops.add_section(
                                                    config_name, b._section))
            if cloneable:
                clone_item = uimanager.get_widget('/Popup/Clone')
                clone_item.connect("activate",
                                   lambda b: self.copy_request(namespace))
            if has_content:
                edit_item = uimanager.get_widget('/Popup/Edit')
                edit_item.connect("activate",
                                    lambda b: self.edit_request(namespace))
                info_item = uimanager.get_widget('/Popup/Info')
                info_item.connect("activate",
                                    lambda b: self.info_request(namespace))
                graph_item = uimanager.get_widget("/Popup/Graph")
                graph_item.connect("activate",
                                   lambda b: self.graph_request(namespace))
                if is_unsaved:
                    graph_item.set_sensitive(False)
            if help is not None:
                help_item = uimanager.get_widget('/Popup/Help')
                help_title = namespace.split('/')[1:]
                help_title = rose.config_editor.DIALOG_HELP_TITLE.format(
                                                                  help_title)
                search_function = lambda i: self.search_request(namespace, i)
                help_item.connect(
                          "activate",
                          lambda b: rose.gtk.dialog.run_hyperlink_dialog(
                                         gtk.STOCK_DIALOG_INFO,
                                         help, help_title,
                                         search_function))
            if url is not None:
                url_item = uimanager.get_widget('/Popup/URL')
                url_item.connect(
                            "activate",
                            lambda b: webbrowser.open(url))
            if is_fixable:
                autofix_item = uimanager.get_widget('/Popup/Autofix')
                autofix_item.connect("activate",
                                     lambda b: self.fix_request(namespace))
            remove_section_item = uimanager.get_widget('/Popup/Remove')
            remove_section_item.connect(
                           "activate",
                           lambda b: self.remove_request(namespace))
        menu = uimanager.get_widget('/Popup')
        menu.popup(None, None, None, event.button, event.time)
        return False

    def is_ns_duplicate(self, namespace):
        """Lookup whether a page can be cloned, via the metadata."""
        sections = self.data.helper.get_sections_from_namespace(namespace)
        if len(sections) != 1:
            return False
        section = sections.pop()
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        sect_data = self.data.config[config_name].sections.now.get(section)
        if sect_data is None:
            return False
        return (sect_data.metadata.get(rose.META_PROP_DUPLICATE) ==
                rose.META_PROP_VALUE_TRUE)

    def get_ns_errors(self, namespace):
        """Count the number of errors in a namespace."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        sections = self.data.helper.get_sections_from_namespace(namespace)
        errors = 0
        for section in sections:
            errors += len(config_data.sections.get_sect(section).error)
        real_data, latent_data = self.data.helper.get_data_for_namespace(
                                                               namespace)
        errors += sum([len(v.error) for v in real_data + latent_data])
        return errors

    def get_ns_ignored(self, base_ns):
        """Lookup the ignored status of a namespace's data."""
        namespace = "/" + base_ns.lstrip("/")
        return self.data.helper.get_ns_ignored_status(namespace)

    def get_can_show_page(self, latent_status, ignored_status, has_error):
        """Lookup whether to display a page based on the data status."""
        if has_error or (not ignored_status and not latent_status):
            # Always show this.
            return True
        show_ignored = self.data.page_ns_show_modes[
                                      rose.config_editor.SHOW_MODE_IGNORED]
        show_user_ignored = self.data.page_ns_show_modes[
                                 rose.config_editor.SHOW_MODE_USER_IGNORED]
        show_latent = self.data.page_ns_show_modes[
                                rose.config_editor.SHOW_MODE_LATENT]
        if latent_status:
            if not show_latent:
                # Latent page, no latent pages allowed.
                return False
            # Latent page, latent pages allowed (but may be ignored...).
        if ignored_status:
            if ignored_status == rose.config.ConfigNode.STATE_USER_IGNORED:
                if show_ignored or show_user_ignored:
                    # This is an allowed user-ignored page.
                    return True
                # This is a user-ignored page that isn't allowed.
                return False
            # This is a trigger-ignored page that may be allowed.
            return show_ignored
        # This is a latent page that isn't ignored, latent pages allowed.
        return True
