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
import inspect
import itertools
import os
import re
import shlex
import subprocess
import sys
import time
import urllib
import webbrowser

import pygtk
pygtk.require('2.0')
import gtk

import rose.config
import rose.config_editor.util
import rose.external
import rose.gtk.run
import rose.gtk.util
import rose.macro
import rose.macros
from rose.suite_control import SuiteControl
from rose.suite_log_view import SuiteLogViewGenerator


class MenuBar(object):

    """Generate the menu bar, using the GTK UIManager.

    Parses the settings in 'ui_config_string'. Connection of buttons is done
    at a higher level.

    """

    ui_config_string = """<ui>
    <menubar name="TopMenuBar">
      <menu action="File">
        <menuitem action="Open..."/>
        <menuitem action="Save"/>
        <separator name="sep_save"/>
        <menuitem action="Quit"/>
      </menu>
      <menu action="Edit">
        <menuitem action="Undo"/>
        <menuitem action="Redo"/>
        <menuitem action="Stack"/>
        <separator name="sep_undo_redo"/>
        <menuitem action="Find"/>
        <menuitem action="Find Next"/>
        <separator name="sep_find"/>
        <menuitem action="Preferences"/>
      </menu>
      <menu action="View">
        <menuitem action="View fixed"/>
        <menuitem action="View ignored"/>
        <menuitem action="View user-ignored"/>
        <menuitem action="View latent"/>
        <separator name="sep_view_options"/>
        <menuitem action="View without titles"/>
        <separator name="sep_tweak_views"/>
        <menuitem action="Flag no-metadata"/>
        <menuitem action="Flag optional"/>
      </menu>
      <menu action="Metadata">
      <menuitem action="Reload metadata"/>
      <menuitem action="Switch off metadata"/>
      <separator name="sep_checking"/>
      <menuitem action="Extra checks"/>
      <separator name="sep macro"/>
      <menuitem action="All V"/>
      <menuitem action="Autofix"/>
      </menu>
      <menu action="Tools">
        <menu action="Run Suite">
          <menuitem action="Run Suite default"/>
          <menuitem action="Run Suite custom"/>
        </menu>
        <separator name="sep_run_action"/>
        <menuitem action="Browser"/>
        <menuitem action="Terminal"/>
        <menuitem action="View Output"/>
        <menuitem action="Open Suite GControl"/>
      </menu>
      <menu action="Page">
        <menuitem action="Add variable"/>
        <menuitem action="Revert"/>
        <separator name="info"/>
        <menuitem action="Page Info"/>
        <separator name="help"/>
        <menuitem action="Page Help"/>
        <menuitem action="Page Web Help"/>
      </menu>
      <menu action="Help">
        <menuitem action="GUI Help"/>
        <menuitem action="About"/>
      </menu>
    </menubar>
    </ui>"""

    action_details = [('File', None,
                       rose.config_editor.TOP_MENU_FILE),
                      ('Open...', gtk.STOCK_OPEN,
                       rose.config_editor.TOP_MENU_FILE_OPEN,
                       rose.config_editor.ACCEL_OPEN),
                      ('Save', gtk.STOCK_SAVE,
                       rose.config_editor.TOP_MENU_FILE_SAVE,
                       rose.config_editor.ACCEL_SAVE),
                      ('Quit', gtk.STOCK_QUIT,
                       rose.config_editor.TOP_MENU_FILE_QUIT,
                       rose.config_editor.ACCEL_QUIT),
                      ('Edit', None,
                       rose.config_editor.TOP_MENU_EDIT),
                      ('Undo', gtk.STOCK_UNDO,
                       rose.config_editor.TOP_MENU_EDIT_UNDO,
                       rose.config_editor.ACCEL_UNDO),
                      ('Redo', gtk.STOCK_REDO,
                       rose.config_editor.TOP_MENU_EDIT_REDO,
                       rose.config_editor.ACCEL_REDO),
                      ('Stack', gtk.STOCK_INFO,
                       rose.config_editor.TOP_MENU_EDIT_STACK),
                      ('Find', gtk.STOCK_FIND,
                       rose.config_editor.TOP_MENU_EDIT_FIND,
                       rose.config_editor.ACCEL_FIND),
                      ('Find Next', gtk.STOCK_FIND,
                       rose.config_editor.TOP_MENU_EDIT_FIND_NEXT,
                       rose.config_editor.ACCEL_FIND_NEXT),
                      ('Preferences', gtk.STOCK_PREFERENCES,
                       rose.config_editor.TOP_MENU_EDIT_PREFERENCES),
                      ('View', None,
                       rose.config_editor.TOP_MENU_VIEW),
                      ('Page', None,
                       rose.config_editor.TOP_MENU_PAGE),
                      ('Add variable', gtk.STOCK_ADD,
                       rose.config_editor.TOP_MENU_PAGE_ADD),
                      ('Revert', gtk.STOCK_REVERT_TO_SAVED,
                       rose.config_editor.TOP_MENU_PAGE_REVERT),
                      ('Page Info', gtk.STOCK_INFO,
                       rose.config_editor.TOP_MENU_PAGE_INFO),
                      ('Page Help', gtk.STOCK_HELP,
                       rose.config_editor.TOP_MENU_PAGE_HELP),
                      ('Page Web Help', gtk.STOCK_HOME,
                       rose.config_editor.TOP_MENU_PAGE_WEB_HELP),
                      ('Metadata', None,
                       rose.config_editor.TOP_MENU_METADATA),
                      ('Reload metadata', gtk.STOCK_REFRESH,
                       rose.config_editor.TOP_MENU_METADATA_REFRESH,
                       rose.config_editor.ACCEL_METADATA_REFRESH),
                      ('All V', gtk.STOCK_DIALOG_QUESTION,
                       rose.config_editor.TOP_MENU_METADATA_MACRO_ALL_V),
                      ('Autofix', gtk.STOCK_CONVERT,
                       rose.config_editor.TOP_MENU_METADATA_MACRO_AUTOFIX),
                      ('Extra checks', gtk.STOCK_DIALOG_QUESTION,
                       rose.config_editor.TOP_MENU_METADATA_CHECK),
                      ('Tools', None,
                       rose.config_editor.TOP_MENU_TOOLS),
                      ('Run Suite', gtk.STOCK_MEDIA_PLAY,
                       rose.config_editor.TOP_MENU_TOOLS_SUITE_RUN),
                      ('Run Suite default', gtk.STOCK_MEDIA_PLAY,
                       rose.config_editor.TOP_MENU_TOOLS_SUITE_RUN_DEFAULT,
                       rose.config_editor.ACCEL_SUITE_RUN),
                      ('Run Suite custom', gtk.STOCK_EDIT,
                       rose.config_editor.TOP_MENU_TOOLS_SUITE_RUN_CUSTOM),
                      ('Browser', gtk.STOCK_DIRECTORY,
                       rose.config_editor.TOP_MENU_TOOLS_BROWSER,
                       rose.config_editor.ACCEL_BROWSER),
                      ('Terminal', gtk.STOCK_EXECUTE,
                       rose.config_editor.TOP_MENU_TOOLS_TERMINAL,
                       rose.config_editor.ACCEL_TERMINAL),
                      ('View Output', gtk.STOCK_DIRECTORY,
                       rose.config_editor.TOP_MENU_TOOLS_VIEW_OUTPUT),
                      ('Open Suite GControl', "rose-gtk-scheduler",
                       rose.config_editor.TOP_MENU_TOOLS_OPEN_SUITE_GCONTROL),
                      ('Help', None,
                       rose.config_editor.TOP_MENU_HELP),
                      ('GUI Help', gtk.STOCK_HELP,
                       rose.config_editor.TOP_MENU_HELP_GUI,
                       rose.config_editor.ACCEL_HELP_GUI),
                      ('About', gtk.STOCK_DIALOG_INFO,
                       rose.config_editor.TOP_MENU_HELP_ABOUT)]

    toggle_action_details = [
                      ('View latent', None,
                       rose.config_editor.TOP_MENU_VIEW_LATENT),
                      ('View fixed', None,
                       rose.config_editor.TOP_MENU_VIEW_FIXED),
                      ('View ignored', None,
                       rose.config_editor.TOP_MENU_VIEW_IGNORED),
                      ('View user-ignored', None,
                       rose.config_editor.TOP_MENU_VIEW_USER_IGNORED),
                      ('View without titles', None,
                       rose.config_editor.TOP_MENU_VIEW_WITHOUT_TITLES),
                      ('Flag optional', None,
                       rose.config_editor.TOP_MENU_VIEW_FLAG_OPTIONAL),
                      ('Flag no-metadata', None,
                       rose.config_editor.TOP_MENU_VIEW_FLAG_NO_METADATA),
                      ('Switch off metadata', None,
                       rose.config_editor.TOP_MENU_METADATA_SWITCH_OFF)]

    def __init__(self):
        self.uimanager = gtk.UIManager()
        self.actiongroup = gtk.ActionGroup('MenuBar')
        self.actiongroup.add_actions(self.action_details)
        self.actiongroup.add_toggle_actions(self.toggle_action_details)
        self.uimanager.insert_action_group(self.actiongroup, pos=0)
        self.uimanager.add_ui_from_string(self.ui_config_string)
        self.macro_ids = []

    def set_accelerators(self, accel_dict):
        """Add the keyboard accelerators."""
        self.accelerators = gtk.AccelGroup()
        self.accelerators.lookup = {}  # Unfortunately, this is necessary.
        key_list = []
        mod_list = []
        action_list = []
        for key_press, accel_func in accel_dict.items():
            key, mod = gtk.accelerator_parse(key_press)
            self.accelerators.lookup[str(key) + str(mod)] = accel_func
            self.accelerators.connect_group(
                              key, mod,
                              gtk.ACCEL_VISIBLE,
                              lambda a, c, k, m:
                                self.accelerators.lookup[str(k) + str(m)]())

    def clear_macros(self):
        """Reset menu to original configuration and clear macros."""
        for merge_id in self.macro_ids:
            self.uimanager.remove_ui(merge_id)
        self.macro_ids = []
        all_v_item = self.uimanager.get_widget("/TopMenuBar/Metadata/All V")
        all_v_item.set_sensitive(False)

    def add_macro(self, config_name, modulename, classname, methodname,
                  help, image_path, run_macro):
        """Add a macro to the macro menu."""
        macro_address = '/TopMenuBar/Metadata'
        macro_menu = self.uimanager.get_widget(macro_address).get_submenu()
        if methodname == rose.macro.VALIDATE_METHOD:
            all_v_item = self.uimanager.get_widget(macro_address + "/All V")
            all_v_item.set_sensitive(True)
        config_menu_name = config_name.replace('/', ':').replace('_', '__')
        config_label_name = config_name.split('/')[-1].replace('_', '__')
        label = rose.config_editor.TOP_MENU_METADATA_MACRO_CONFIG.format(
                                                     config_label_name)
        config_address = macro_address + '/' + config_menu_name
        config_item = self.uimanager.get_widget(config_address)
        if config_item is None:
            actiongroup = self.uimanager.get_action_groups()[0]
            if actiongroup.get_action(config_menu_name) is None:
                actiongroup.add_action(gtk.Action(config_menu_name,
                                                  label,
                                                  None, None))
            new_ui = """<ui><menubar name="TopMenuBar">
                        <menu action="Metadata">
                        <menuitem action="{0}"/></menu></menubar>
                        </ui>""".format(config_menu_name)
            self.macro_ids.append(self.uimanager.add_ui_from_string(new_ui))
            config_item = self.uimanager.get_widget(config_address)
            if image_path is not None:
                image = gtk.image_new_from_file(image_path)
                config_item.set_image(image)
        if config_item.get_submenu() is None:
            config_item.set_submenu(gtk.Menu())
        macro_fullname = ".".join([modulename, classname, methodname])
        macro_fullname = macro_fullname.replace("_", "__")
        if methodname == rose.macro.VALIDATE_METHOD:
            stock_id = gtk.STOCK_DIALOG_QUESTION
        else:
            stock_id = gtk.STOCK_CONVERT
        macro_item = gtk.ImageMenuItem(stock_id=stock_id)
        macro_item.set_label(macro_fullname)
        macro_item.set_tooltip_text(help)
        macro_item.show()
        macro_item._run_data = [config_name, modulename, classname,
                                methodname]
        macro_item.connect("activate",
                           lambda i: run_macro(*i._run_data))
        config_item.get_submenu().append(macro_item)
        if (methodname == rose.macro.VALIDATE_METHOD):
            for item in config_item.get_submenu().get_children():
                if hasattr(item, "_rose_all_validators"):
                    return False
            all_item = gtk.ImageMenuItem(gtk.STOCK_DIALOG_QUESTION)
            all_item._rose_all_validators = True
            all_item.set_label(rose.config_editor.MACRO_MENU_ALL_VALIDATORS)
            all_item.set_tooltip_text(
                     rose.config_editor.MACRO_MENU_ALL_VALIDATORS_TIP)
            all_item.show()
            all_item._run_data = [config_name, None, None, methodname]
            all_item.connect("activate",
                             lambda i: run_macro(*i._run_data))
            config_item.get_submenu().prepend(all_item)


class Handler(object):

    """Handles signals from the menu bar and tree panel menu."""

    def __init__(self, data, util, mainwindow, undo_stack, redo_stack,
                 undo_func, apply_macro_transform_func,
                 apply_macro_validation_func,
                 add_config_func,
                 check_cannot_enable_func,
                 section_ops_inst,
                 variable_ops_inst,
                 kill_page_func, update_func,
                 update_ns_func, view_page_func,
                 find_ns_id_func):
        self.util = util
        self.data = data
        self.mainwindow = mainwindow
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.perform_undo = undo_func
        self.apply_macro_transform = apply_macro_transform_func
        self.apply_macro_validation = apply_macro_validation_func
        self.sect_ops = section_ops_inst
        self.var_ops = variable_ops_inst
        self._add_config = add_config_func
        self.kill_page_func = kill_page_func
        self.update_func = update_func
        self.update_ns_func = update_ns_func
        self.view_page_func = view_page_func
        self.find_ns_id_func = find_ns_id_func

    def about_dialog(self, args):
        self.mainwindow.launch_about_dialog()

    def is_ns_duplicate(self, base_ns):
        """Lookup whether a page can be cloned, via the metadata."""
        namespace = "/" + base_ns.lstrip("/")
        sections = self.data.get_sections_from_namespace(namespace)
        if len(sections) != 1:
            return False
        section = sections.pop()
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        sect_data = self.data.config[config_name].sections.now.get(section)
        if sect_data is None:
            return False
        return (sect_data.metadata.get(rose.META_PROP_DUPLICATE) ==
                rose.META_PROP_VALUE_TRUE)

    def add_dialog(self, base_ns):
        """Handle an add section dialog and request."""
        if base_ns is not None and '/' in base_ns:
            config_name, subsp = self.util.split_full_ns(self.data, base_ns)
            if config_name == base_ns:
                help_str = ''
            else:
                sections = self.data.get_sections_from_namespace(base_ns)
                if sections == []:
                    help_str = subsp.replace('/', ':')
                else:
                    help_str = sections[0]
                help_str = help_str + ':'
                if help_str.count(':') > 1:
                    help_str = help_str.split(':', 1)[0] + ':'
        else:
            help_str = None
            config_name = None
        choices_help = self.data.get_missing_sections(config_name)
        config_names = [n for n in self.data.config]
        config_names.sort(lambda x, y: (y == config_name) -(x == config_name))
        config_name, section = self.mainwindow.launch_add_dialog(
                                    config_names, choices_help, help_str)
        if config_name in self.data.config and section is not None:
            self.sect_ops.add_section(config_name, section, page_launch=True)

    def add_section_with_options(self, config_name, new_section_name, opt_map=None):
        """Add a section and any compulsory options.
        
        Any option-value pairs in the opt_map dict will also be added.
        
        """
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_ADD + "-" + str(time.time())
        self.sect_ops.add_section(config_name, new_section_name)
        namespace = self.data.get_default_namespace_for_section(
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
            metadata = self.data.get_metadata_for_config_id(var_id, config_name)
            metadata['full_ns'] = namespace
            ignored_reason = {}  # This may not be safe.
            var = rose.variable.Variable(opt_name, value,
                                         metadata, ignored_reason,
                                         error={})
            self.var_ops.add_var(var, skip_update=True)
        self.data.reload_namespace_tree(namespace)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        return new_section_name
        
    def copy_request(self, base_ns, new_section=None, skip_update=False):
        """Handle a copy request for a section and its options."""
        namespace = "/" + base_ns.lstrip("/")
        sections = self.data.get_sections_from_namespace(namespace)
        if len(sections) != 1:
            return False
        section = sections.pop()
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        return self.copy_section(config_name, section, skip_update=skip_update)

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
        new_namespace = self.data.get_default_namespace_for_section(
                                  new_section, config_name)
        for var in clone_vars:
            var_id = self.util.get_id_from_section_option(
                                           new_section, var.name)
            metadata = self.data.get_metadata_for_config_id(var_id,
                                                            config_name)
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

    def create_request(self):
        """Handle a create configuration request."""
        if not any([v.is_top_level for v in self.data.config.values()]):
            text = rose.config_editor.WARNING_APP_CONFIG_CREATE
            title = rose.config_editor.WARNING_APP_CONFIG_CREATE_TITLE
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR, 
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

    def delete_request(self, namespace_list, skip_update=False):
        """Handle a delete namespace request (more complicated than add)."""
        namespace_list.sort(rose.config.sort_settings)
        namespace_list.reverse()
        for ns in [n for n in namespace_list]:
            if not ns.startswith('/'):
                ns = '/' + ns
            config_name = self.util.split_full_ns(self.data, ns)[0]
            if config_name == ns:
                short_config_name = config_name.split('/')[-1]
                text = rose.config_editor.WARNING_CONFIG_DELETE.format(
                                                         short_config_name)
                title = rose.config_editor.WARNING_CONFIG_DELETE_TITLE
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR, 
                                         text, title)
                return False
        ns_done = []
        for namespace in namespace_list:
            self.kill_page_func(namespace)
        ns_var_sections = {}
        element_sort = rose.config.sort_settings
        variable_sorter = lambda v, w: element_sort(v.metadata['id'],
                                                    w.metadata['id']) 
        duplicate_nses = []
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_DELETE + "-" + str(time.time())
        for ns in list(namespace_list):
            if ns in ns_done:
                continue
            config_name = self.util.split_full_ns(self.data, ns)[0]
            config_data = self.data.config[config_name]
            real_sections = config_data.sections.now.keys()
            ns_done.append(ns)
            real_data, ghost_data = self.data.get_data_for_namespace(ns)
            var_list = list(real_data)
            var_list.sort(variable_sorter)
            var_list.reverse()
            for variable in var_list:
                self.var_ops.remove_var(variable, skip_update=True)
                var_id = variable.metadata['id']
                sect, opt = self.util.get_section_option_from_id(var_id)
                ns_var_sections.setdefault(ns, {})
                ns_var_sections[ns].update({sect: True})
            config_name = self.util.split_full_ns(self.data, ns)[0]
            for section in self.data.get_sections_from_namespace(ns):
                # Interlinked (in metadata) empty sections may cause problems.
                if (section not in config_data.vars.now and
                    (section in ns_var_sections.get(ns, []) or
                     section in real_sections)):
                    self.sect_ops.remove_section(config_name, section,
                                                 skip_update=True)
            ns_meta = self.data.namespace_meta_lookup[ns]
            if (ns_meta.get(rose.META_PROP_DUPLICATE) ==
                rose.META_PROP_VALUE_TRUE):
                duplicate_nses.append(ns)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        if not skip_update:
            for namespace in namespace_list:
                self.data.reload_namespace_tree(namespace)  # Update everything as well.

    def ignore_request(self, base_ns, is_ignored):
        """Handle an ignore or enable section request."""
        config_names = self.data.config.keys()
        if base_ns is not None and '/' in base_ns:
            config_name, subsp = self.util.split_full_ns(self.data, base_ns)
            prefer_name_sections = {
                  config_name: self.data.get_sections_from_namespace(base_ns)}
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
        sections = self.data.get_sections_from_namespace(base_ns)
        for section in list(sections):
            if section not in config_data.sections.now:
                sections.remove(section)
        if not sections:
            return False
        if len(sections) > 1:
            section = rose.gtk.util.run_choices_dialog(
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
        rose.gtk.util.run_edit_dialog(text, finish_hook=finish, title=title)

    def fix_request(self, base_ns):
        """Handle a request to auto-fix a configuration."""
        if base_ns is None:
            return False
        base_ns = "/" + base_ns.lstrip("/")
        config_name, subsp = self.util.split_full_ns(self.data, base_ns)
        self.transform_default(only_this_config_name=config_name)

    def get_metadata_and_comments(self, base_ns):
        """Return metadata dict and comments list."""
        metadata = {}
        comments = ""
        if base_ns is None:
            return metadata, comments
        base_ns = "/" + base_ns.lstrip("/")
        metadata = self.data.namespace_meta_lookup.get(base_ns, {})
        comments = self.data.get_ns_comment_string(base_ns)
        return metadata, comments

    def info_request(self, base_ns):
        """Handle a request for namespace info."""
        if base_ns is None:
            return False
        base_ns = "/" + base_ns.lstrip("/")
        config_name, subsp = self.util.split_full_ns(self.data, base_ns)
        config_data = self.data.config[config_name]
        sections = self.data.get_sections_from_namespace(base_ns)
        search_function = lambda i: self.search_request(base_ns, i)
        for section in sections:
            sect_data = config_data.sections.now.get(section)
            if sect_data is not None:
                rose.config_editor.util.launch_node_info_dialog(
                            sect_data, "", search_function)

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
            ns = self.data.get_default_namespace_for_section(
                                           section, config_name)
            if ns not in nses:
                nses.append(ns)
            self.remove_section(config_name, section, skip_update=True)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        if not skip_update:
            for ns in nses:
                self.data.reload_namespace_tree(ns)

    def rename_request(self, base_ns, new_section, skip_update=False):
        """Implement a rename (delete + add)."""
        namespace = "/" + base_ns.lstrip("/")
        sections = self.data.get_sections_from_namespace(namespace)
        if len(sections) != 1:
            return False
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_RENAME + "-" + str(time.time())
        self.copy_request(namespace, new_section, skip_update=skip_update)
        self.delete_request([namespace], skip_update=skip_update)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group

    def search_request(self, base_ns, setting_id):
        """Handle a search for an id (hyperlink)."""
        if not base_ns.startswith("/"):
            base_ns = "/" + base_ns
        config_name, subsp = self.util.split_full_ns(self.data, base_ns)
        self.var_ops.search_for_var(config_name, setting_id)

    def reorder_duplicate_namespaces(self, namespaces=None):
        """Make sure duplicate sections have the correct indices."""
        if namespaces is None:
            namespaces = []
            for ns_key, meta_dict in self.data.namespace_meta_lookup.items():
                if (meta_dict.get(rose.META_PROP_DUPLICATE) ==
                    rose.META_PROP_VALUE_TRUE):
                    namespaces.append(ns_key)
        reorder_ns_bases = {}
        for ns in namespaces:
            config_name, subsp = self.util.split_full_ns(self.data, ns)
            reorder_ns_bases.setdefault(config_name, [])
            for sect in self.data.get_sections_from_namespace(ns):
                base_sect = rose.macro.REC_ID_STRIP_DUPL.sub("", sect)
                if base_sect not in reorder_ns_bases[config_name]:
                    reorder_ns_bases[config_name].append(base_sect)
        sorter = rose.config.sort_settings
        id_formatter = rose.macro.ID_ELEMENT_FORMAT.format
        start_stack_index = len(self.undo_stack)
        group = rose.config_editor.STACK_GROUP_REORDER + "-" + str(time.time())
        for config_name, base_sections in reorder_ns_bases.items():
            sections_done = []
            dupl_sect_dict = {}
            for sect in self.data.config[config_name].sections.now:
                base_sect = rose.macro.REC_ID_STRIP_DUPL.sub("", sect)
                if base_sect not in base_sections or base_sect == sect:
                    continue
                element_search = rose.macro.REC_ID_ELEMENT.search(sect)
                if element_search is None:
                    continue
                element = element_search.groups()[0]
                dupl_sect_dict.setdefault(base_sect, {})
                dupl_sect_dict[base_sect].update({sect: element})
            for base_sect, sect_element_dict in dupl_sect_dict.items():
                sections = sect_element_dict.keys()
                sections.sort(sorter)
                for i, sect in enumerate(sections):
                    element = sect_element_dict[sect]
                    if int(element) != i + 1:
                        new_sect_name = id_formatter(base_sect, i + 1)
                        ns = self.data.get_default_namespace_for_section(
                                           sect, config_name)
                        self.rename_request(ns, new_sect_name, skip_update=True)
        for stack_item in self.undo_stack[start_stack_index:]:
            stack_item.group = group
        self.data.reload_namespace_tree()

    def get_sub_ops_for_namespace(self, namespace):
        """Return data functions for summary (sub) data panels."""
        if not namespace.startswith("/"):
            namespace = "/" + namespace
        config_name, subsp = self.util.split_full_ns(self.data, namespace)
        return rose.config_editor.stack.SubDataOperations(
                config_name,
                self.add_section_with_options,
                self.copy_section,
                self.sect_ops.ignore_section,
                self.remove_section,
                self.remove_sections,
                get_var_id_values_func=(
                        self.data.get_sub_data_var_id_value_map))

    def get_orphan_container(self, page):
        """Return a container with the page object inside."""
        box = gtk.VBox()
        box.pack_start(page, expand=True, fill=True)
        box.show()
        return box

    def view_stack(self, args):
        """Handle a View Stack request."""
        self.mainwindow.launch_view_stack(self.undo_stack, self.redo_stack,
                                          self.perform_undo)

    def destroy(self, *args):
        """Handle a destroy main program request."""
        for name in self.data.config:
            config_data = self.data.config[name]
            variables = config_data.vars.get_all(no_latent=True)
            save_vars = config_data.vars.get_all(save=True, no_latent=True)
            sections = config_data.sections.get_all(no_latent=True)
            save_sections = config_data.sections.get_all(save=True,
                                                         no_latent=True)
            now_set = set([v.to_hashable() for v in variables])
            save_set = set([v.to_hashable() for v in save_vars])
            now_sect_set = set([s.to_hashable() for s in sections])
            save_sect_set = set([s.to_hashable() for s in save_sections])
            if (name not in self.data.saved_config_names or
                now_set ^ save_set or
                now_sect_set ^ save_sect_set):
                # There are differences in state between now and then.
                self.mainwindow.launch_exit_warning_dialog()
                return True
        gtk.main_quit()

    def check_all_extra(self):
        """Check fail-if, warn-if, and run all validator macros."""
        self.check_fail_rules()
        self.run_custom_macro(method_name=rose.macro.VALIDATE_METHOD)

    def check_fail_rules(self):
        """Check the fail-if and warn-if conditions of the configurations."""
        macro = rose.macros.rule.FailureRuleChecker()
        macro_fullname = "rule.FailureRuleChecker.validate"
        for config_name, config_data in self.data.config.items():
            config = config_data.config
            meta = config_data.meta
            try:
                return_value = macro.validate(config, meta)
            except Exception as e:
                rose.gtk.util.run_dialog(
                              rose.gtk.util.DIALOG_TYPE_ERROR,
                              str(e),
                              rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                           macro_fullname))
                continue
            sorter = rose.config.sort_settings
            to_id = lambda s: self.util.get_id_from_section_option(
                                                s.section, s.option)
            return_value.sort(lambda x, y: sorter(to_id(x), to_id(y)))
            self.handle_macro_validation(config_name, macro_fullname,
                                         config, return_value,
                                         no_display=(not return_value))

    def clear_page_menu(self, menubar, add_menuitem):
        """Clear all page add variable items."""
        add_menuitem.remove_submenu()

    def load_page_menu(self, menubar, add_menuitem, current_page):
        """Load the page add variable items, if any."""
        if current_page is None:
            return False
        add_var_menu = current_page.get_add_menu()
        if add_var_menu is None or not add_var_menu.get_children():
            add_menuitem.set_sensitive(False)
            return False
        add_menuitem.set_sensitive(True)
        add_menuitem.set_submenu(add_var_menu)

    def load_macro_menu(self, menubar):
        """Refresh the menu dealing with custom macro launches."""
        menubar.clear_macros()
        config_keys = self.data.config.keys()
        config_keys.sort()
        tuple_sorter = lambda x, y: cmp(x[0], y[0])
        for config_name in config_keys:
            config_image = self.data.get_icon_path_for_config(config_name)
            macros = self.data.config[config_name].macros
            macro_tuples = rose.macro.get_macro_class_methods(macros)
            macro_tuples.sort(tuple_sorter)
            for macro_mod, macro_cls, macro_func, help in macro_tuples:
                menubar.add_macro(config_name, macro_mod, macro_cls,
                                  macro_func, help, config_image,
                                  self.run_custom_macro)

    def run_custom_macro(self, config_name=None, module_name=None,
                         class_name=None, method_name=None):
        """Run the custom macro method and launch a dialog."""
        macro_data = []
        if config_name is None:
            configs = self.data.config.keys()
        else:
            configs = [config_name]
        for config_name in configs:
            config_data = self.data.config[config_name]
            for module in config_data.macros:
                if module_name is not None and module.__name__ != module_name:
                    continue
                for obj_name, obj in inspect.getmembers(module):
                    if (not hasattr(obj, method_name) or
                        obj_name.startswith("_") or
                        not issubclass(obj, rose.macro.MacroBase)):
                        continue
                    if class_name is not None and obj_name != class_name:
                        continue
                    try:
                        macro_inst = obj()
                    except Exception as e:
                        rose.gtk.util.run_dialog(
                             rose.gtk.util.DIALOG_TYPE_ERROR,
                             str(e),
                             rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                                macro_fullname))
                        continue
                    if hasattr(macro_inst, method_name):
                        macro_data.append((config_name, macro_inst,
                                           module.__name__, obj_name,
                                           method_name))
        if not macro_data:
            return None
        sorter = rose.config.sort_settings
        to_id = lambda s: self.util.get_id_from_section_option(s.section,
                                                               s.option)
        for config_name, macro_inst, modname, objname, methname in macro_data:
            macro_fullname = '.'.join([modname, objname, methname])
            macro_config = self.data.dump_to_internal_config(config_name)
            meta_config = self.data.config[config_name].meta
            macro_method = getattr(macro_inst, methname)
            try:
                return_value = macro_method(macro_config, meta_config)
            except Exception as e:
                rose.gtk.util.run_dialog(
                              rose.gtk.util.DIALOG_TYPE_ERROR,
                              str(e),
                              rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                                 macro_fullname))
                continue
            if method_name == 'transform':
                if (not isinstance(return_value, tuple) or
                    len(return_value) != 2 or
                    not isinstance(return_value[0], rose.config.ConfigNode) or
                    not isinstance(return_value[1], list)):
                    self._handle_bad_macro_return(macro_fullname, return_value)
                    continue
                macro_config, change_list = return_value
                if not change_list:
                    continue
                change_list.sort(lambda x, y: sorter(to_id(x), to_id(y)))
                self.handle_macro_transforms(config_name, macro_fullname,
                                             macro_config, change_list)
                continue
            elif method_name == 'validate':
                if not isinstance(return_value, list):
                    self._handle_bad_macro_return(macro_fullname, return_value)
                    continue
                if return_value:
                    return_value.sort(lambda x, y: sorter(to_id(x), to_id(y)))
                self.handle_macro_validation(config_name, macro_fullname,
                                             macro_config, return_value)
                continue
        return False                          

    def _handle_bad_macro_return(self, macro_fullname, return_value):
        rose.gtk.util.run_dialog(
            rose.gtk.util.DIALOG_TYPE_ERROR,
            rose.config_editor.ERROR_BAD_MACRO_RETURN.format(
                                                return_value),
            rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                macro_fullname))

    def handle_macro_transforms(self, config_name, macro_name,
                                macro_config, change_list, no_display=False,
                                triggers_ok=False):
        """Calculate needed changes and apply them if prompted to.
        
        At the moment trigger-ignore of variables and sections is
        assumed to be the exclusive property of the Rose trigger
        macro and is not allowed for any other macro.
        
        """
        if not change_list:
            return
        macro_type = ".".join(macro_name.split(".")[:-1])
        var_changes = []
        sect_changes = []
        sect_removes = []
        for item in list(change_list):
            if item.option is None:
                sect_changes.append(item)
            else:
                var_changes.append(item)
        search = lambda i: self.find_ns_id_func(config_name, i)
        if not no_display:
            proceed_ok = self.mainwindow.launch_macro_changes_dialog(
                              config_name, macro_type, change_list,
                              search_func=search)
            if not proceed_ok:
                return
        changed_ids = []
        sections = self.data.config[config_name].sections
        for item in sect_changes:
            sect = item.section
            changed_ids.append(sect)
            macro_node = macro_config.get([sect])
            if macro_node is None:
                sect_removes.append(sect)
                continue
            if sect in sections.now:
                sect_data = sections.now[sect]
            else:
                self.sect_ops.add_section(config_name, sect)
                sect_data = sections.now[sect]
            if (rose.variable.IGNORED_BY_USER in sect_data.ignored_reason and
                macro_node.state !=
                rose.config.ConfigNode.STATE_USER_IGNORED):
                # Enable.
                self.sect_ops.ignore_section(config_name, sect, False,
                                             override=True)
            elif (macro_node.state ==
                  rose.config.ConfigNode.STATE_USER_IGNORED and
                  rose.variable.IGNORED_BY_USER not in
                  sect_data.ignored_reason):
                self.sect_ops.ignore_section(config_name, sect, True,
                                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_SYST_IGNORED and
                  rose.variable.IGNORED_BY_SYSTEM not in
                  sect_data.ignored_reason):
                sect_data.error.setdefault(
                          rose.config_editor.WARNING_TYPE_ENABLED,
                          rose.config_editor.IGNORED_STATUS_MACRO)
                self.sect_ops.ignore_section(config_name, sect, True,
                                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_NORMAL and
                  rose.variable.IGNORED_BY_SYSTEM in
                  sect_data.ignored_reason):
                sect_data.error.setdefault(
                          rose.config_editor.WARNING_TYPE_TRIGGER_IGNORED,
                          rose.config_editor.IGNORED_STATUS_MACRO)
                self.sect_ops.ignore_section(config_name, sect, False,
                                             override=True)
        for item in var_changes:
            sect = item.section
            opt = item.option
            val = item.value
            warning = item.info
            var_id = self.util.get_id_from_section_option(sect, opt)
            changed_ids.append(var_id)
            var = self.data.get_variable_by_id(var_id, config_name)
            macro_node = macro_config.get([sect, opt])
            if macro_node is None:
                self.var_ops.remove_var(var)
                continue
            if var is None:
                value = macro_node.value
                metadata = self.data.get_metadata_for_config_id(
                                         var_id, config_name)
                variable = rose.variable.Variable(opt, value, metadata)
                self.data.load_ns_for_node(variable, config_name)
                self.var_ops.add_var(variable)
                var = self.data.get_variable_by_id(var_id, config_name)
                continue
            if var.value != macro_node.value:
                self.var_ops.set_var_value(var, macro_node.value)
            elif (rose.variable.IGNORED_BY_USER in var.ignored_reason and
                  macro_node.state !=
                  rose.config.ConfigNode.STATE_USER_IGNORED):
                # Enable.
                self.var_ops.set_var_ignored(var, {}, override=True)
            elif (macro_node.state ==
                  rose.config.ConfigNode.STATE_USER_IGNORED and
                  rose.variable.IGNORED_BY_USER not in var.ignored_reason):
                self.var_ops.set_var_ignored(
                             var,
                             {rose.variable.IGNORED_BY_USER:
                              rose.config_editor.IGNORED_STATUS_MACRO},
                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_SYST_IGNORED and
                  rose.variable.IGNORED_BY_SYSTEM not in var.ignored_reason):
                self.var_ops.set_var_ignored(
                             var,
                             {rose.variable.IGNORED_BY_SYSTEM:
                              rose.config_editor.IGNORED_STATUS_MACRO},
                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_NORMAL and
                  rose.variable.IGNORED_BY_SYSTEM in var.ignored_reason):
                self.var_ops.set_var_ignored(var, {}, override=True)
        for sect in sect_removes:
            self.sect_ops.remove_section(config_name, sect)
        self.apply_macro_transform(config_name, macro_type, changed_ids)
                
    def handle_macro_validation(self, config_name, macro_name,
                                macro_config, problem_list, no_display=False):
        """Apply errors and give information to the user."""
        macro_type = ".".join(macro_name.split(".")[:-1])
        self.apply_macro_validation(config_name, macro_type, problem_list)
        search = lambda i: self.find_ns_id_func(config_name, i)
        if not no_display:
            self.mainwindow.launch_macro_changes_dialog(
                            config_name, macro_type, problem_list,
                            mode="validate", search_func=search)

    def handle_run_scheduler(self, *args):
        """Run the scheduler for this suite."""
        this_id = str(SuiteId(id_text=self.get_selected_suite_id()))
        return SuiteControl().gcontrol(this_id)
    
    def help(self, *args):
        # Handle a GUI help request.
        self.mainwindow.launch_help_dialog()

    def prefs(self, args):
        # Handle a Preferences view request.
        self.mainwindow.launch_prefs()

    def launch_browser(self):
        rose.external.launch_fs_browser(self.data.top_level_directory)

    def launch_scheduler(self, *args):
        """Run the scheduler for a suite open in config edit."""
        this_id = self.data.top_level_name
        return SuiteControl().gcontrol(this_id)
        
    def launch_terminal(self):
        # Handle a launch terminal request.
        rose.external.launch_terminal()

    def launch_output_viewer(self):
        """View a suite's output, if any."""
        g = SuiteLogViewGenerator()
        url = g.get_suite_log_url(self.data.top_level_name)
        if url is None:
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_INFO,
                                     rose.config_editor.ERROR_NO_OUTPUT.format(
                                     self.data.top_level_name))
        else:
            g.view_suite_log_url(self.data.top_level_name)

    def get_run_suite_args(self, *args):
        """Ask the user for custom arguments to suite run."""
        help_cmds = shlex.split(rose.config_editor.LAUNCH_SUITE_RUN_HELP)
        help_text = subprocess.Popen(help_cmds,
                                     stdout=subprocess.PIPE).communicate()[0]
        rose.gtk.util.run_command_arg_dialog(
                          rose.config_editor.LAUNCH_SUITE_RUN,
                          help_text, self.run_suite_check_args)

    def run_suite_check_args(self, args):
        if args is None:
            return False
        self.run_suite(args)

    def run_suite(self, args=None, **kwargs):
        """Run the suite, if possible."""
        if not any([c.is_top_level for c in self.data.config.values()]):
            rose.gtk.util.run_dialog(
                     rose.gtk.util.DIALOG_TYPE_ERROR,
                     rose.config_editor.ERROR_SUITE_RUN,
                     title=rose.config_editor.DIALOG_TITLE_CRITICAL_ERROR)
            return False
        if not isinstance(args, list):
            args = []
        for key, value in kwargs.items():
            args.extend([key, value])
        rose.gtk.run.run_suite(*args)
        return False

    def transform_default(self, only_this_config_name=None):
        """Run the Rose built-in transformer macros."""
        if (only_this_config_name is not None and
            only_this_config_name in self.data.config.keys()):
            config_keys = [only_this_config_name]
            text = rose.config_editor.DIALOG_LABEL_AUTOFIX
        else:
            config_keys = sorted(self.data.config.keys())
            text = rose.config_editor.DIALOG_LABEL_AUTOFIX_ALL
        proceed = rose.gtk.util.run_dialog(
                                    rose.gtk.util.DIALOG_TYPE_WARNING,
                                    text,
                                    rose.config_editor.DIALOG_TITLE_AUTOFIX,
                                    cancel=True)
        if not proceed:
            return False
        sorter = rose.config.sort_settings
        to_id = lambda s: self.util.get_id_from_section_option(s.section,
                                                               s.option)
        for config_name in config_keys:
            macro_config = self.data.dump_to_internal_config(config_name)
            meta_config = self.data.config[config_name].meta
            macro = rose.macros.DefaultTransforms()
            config, change_list = macro.transform(macro_config, meta_config)
            change_list.sort(lambda x, y: sorter(to_id(x), to_id(y)))
            self.handle_macro_transforms(
                        config_name, "Autofixer.transform",
                        macro_config, change_list, triggers_ok=True)
