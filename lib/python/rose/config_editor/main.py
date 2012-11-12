# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
"""
This module contains the core processing of the config editor.

Classes:
    MainController - driver for loading, and handles updates.

"""

import copy
import itertools
import os
import re
import shutil
import sre_constants
import sys
import warnings

# Ignore add menu related warnings for now, but remove this later.
warnings.filterwarnings('ignore',
                        'instance of invalid non-instantiatable type',
                        Warning)
warnings.filterwarnings('ignore',
                        'g_signal_handlers_disconnect_matched',
                        Warning)
warnings.filterwarnings('ignore',
                        'use set_markup',
                        Warning)
warnings.filterwarnings('ignore',
                        'Unable to show',
                        Warning)
warnings.filterwarnings('ignore',
                        'gdk',
                        Warning)

import pygtk
pygtk.require('2.0')
import gtk  # Only used to run the main gtk loop.

import rose.config
import rose.config_editor
import rose.config_editor.loader
import rose.config_editor.menu
import rose.config_editor.page
import rose.config_editor.panel
import rose.config_editor.stack
import rose.config_editor.util
import rose.config_editor.variable
import rose.config_editor.window
import rose.gtk.util
import rose.macro
import rose.opt_parse
import rose.resource
import rose.macros


RESOURCER = rose.resource.ResourceLocator(paths=sys.path)


class MainController(object):

    """The main controller class.
    
    Call with a configuration directory and/or a dict of
    configuration names and objects.
    
    If pluggable is True, return containers for plugging into other
    GTK applications.
    If pluggable is False, launch the standalone application.
    
    """

    RE_ARRAY_ELEMENT = re.compile('\([\d:, ]+\)$')

    def __init__(self, config_directory=None, config_objs=None,
                 pluggable=False,
                 loader_update=rose.config_editor.false_function):
        if config_objs is None:
            config_objs = {}
        self.pluggable = pluggable
        self.tab_windows = []  # No child windows yet
        self.orphan_pages = []
        self.undo_stack = [] # Nothing to undo yet
        self.redo_stack = [] # Nothing to redo yet
        self.find_hist = {'regex': '', 'ids': []}
        self.util = rose.config_editor.util.Lookup()
        self.macros = {
             rose.META_PROP_COMPULSORY:
             rose.macros.compulsory.CompulsoryChecker,
             rose.META_PROP_TYPE:
             rose.macros.value.ValueChecker}
        self.metadata_off = False

        # Load the top configuration directory
        self.data = rose.config_editor.loader.ConfigDataManager(
                                self.util,
                                config_directory,
                                config_objs,
                                self.tree_trigger_update,
                                loader_update)
        self.trigger = self.data.trigger

        loader_update(rose.config_editor.LOAD_STATUSES,
                      self.data.top_level_name)

        self.mainwindow = rose.config_editor.window.MainWindow()

        self.section_ops = rose.config_editor.stack.SectionOperations(
                                   self.data, self.util,
                                   self.undo_stack, self.redo_stack,
                                   self.check_cannot_enable_setting,
                                   self.update_namespace,
                                   self.update_ns_info,
                                   self.update_ns_comments,
                                   view_page_func=self.view_page,
                                   kill_page_func=self.kill_page)

        self.variable_ops = rose.config_editor.stack.VariableOperations(
                                   self.data, self.util, 
                                   self.undo_stack, self.redo_stack,
                                   self.check_cannot_enable_setting,
                                   self.update_namespace,
                                   search_id_func=self.perform_find_by_id)

        # Add in the general 'menu' event handler.
        # Eventually it might be a good idea to package up the undo stuff.
        self.handle = rose.config_editor.menu.Handler(
                             self.data, self.util, self.mainwindow,
                             self.undo_stack, self.redo_stack,
                             self.perform_undo,
                             self.apply_macro_transform,
                             self.apply_macro_validation,
                             self._add_config,
                             self.check_cannot_enable_setting,
                             self.section_ops,
                             self.variable_ops,
                             self.kill_page, self.update_status,
                             self.update_namespace, self.view_page,
                             self.perform_find_by_ns_id)

        if not self.pluggable:
            self.generate_toolbar()
            self.generate_menubar()
            self.generate_hyper_panel()
            # Create notebook (tabbed container) and connect signals.
            self.notebook = rose.gtk.util.Notebook()

        # Set page 'verbosity' defaults.
        self.page_show_modes = {
             rose.config_editor.SHOW_MODE_FIXED:
             rose.config_editor.SHOULD_SHOW_FIXED,
             rose.config_editor.SHOW_MODE_FLAG_OPTIONAL:
             rose.config_editor.SHOULD_SHOW_FLAG_OPTIONAL,
             rose.config_editor.SHOW_MODE_FLAG_NO_META:
             rose.config_editor.SHOULD_SHOW_FLAG_NO_META,
             rose.config_editor.SHOW_MODE_IGNORED:
             rose.config_editor.SHOULD_SHOW_IGNORED,
             rose.config_editor.SHOW_MODE_USER_IGNORED:
             rose.config_editor.SHOULD_SHOW_USER_IGNORED,
             rose.config_editor.SHOW_MODE_LATENT:
             rose.config_editor.SHOULD_SHOW_LATENT,
             rose.config_editor.SHOW_MODE_NO_TITLE:
             rose.config_editor.SHOULD_SHOW_NO_TITLE}

        # Create the main panel with the menu, toolbar, tree panel, notebook.
        if not self.pluggable:
            self.mainwindow.load(name=self.data.top_level_name,
                                 menu=self.top_menu,
                                 accelerators=self.menubar.accelerators,
                                 toolbar=self.toolbar,
                                 hyper_panel=self.hyper_panel,
                                 notebook=self.notebook,
                                 page_change_func=self.handle_page_change,
                                 save_func=self.save_to_file,)
            self.mainwindow.window.connect('destroy', self.handle.destroy)
            self.mainwindow.window.connect('delete-event',
                                           self.handle.destroy)
            self.mainwindow.window.connect_after('grab_focus',
                                                 self.handle_page_change)
            self.mainwindow.window.connect_after('focus-in-event',
                                                 self.handle_page_change)
        self.update_all()
        loader_update(rose.config_editor.LOAD_DONE, self.data.top_level_name)
        self.perform_startup_check()
        if (self.data.top_level_directory is None and not self.data.config):
            self.load_from_file()

#------------------ Setting up main component functions ----------------------

    def generate_toolbar(self):
        """Link in the toolbar functionality."""
        self.toolbar = rose.gtk.util.ToolBar(
                widgets=[
                   (rose.config_editor.TOOLBAR_OPEN, 'gtk.STOCK_OPEN'),
                   (rose.config_editor.TOOLBAR_SAVE, 'gtk.STOCK_SAVE'),
                   (rose.config_editor.TOOLBAR_BROWSE, 'gtk.STOCK_DIRECTORY'),
                   (rose.config_editor.TOOLBAR_UNDO, 'gtk.STOCK_UNDO'),
                   (rose.config_editor.TOOLBAR_REDO, 'gtk.STOCK_REDO'),
                   (rose.config_editor.TOOLBAR_ADD, 'gtk.STOCK_ADD'),
                   (rose.config_editor.TOOLBAR_REVERT,
                    'gtk.STOCK_REVERT_TO_SAVED'),
                   (rose.config_editor.TOOLBAR_FIND, 'gtk.Entry'),
                   (rose.config_editor.TOOLBAR_FIND_NEXT, 'gtk.STOCK_FIND'),
                   (rose.config_editor.TOOLBAR_VALIDATE,
                    'gtk.STOCK_DIALOG_QUESTION')],
                sep_on_name=[rose.config_editor.TOOLBAR_SAVE,
                             rose.config_editor.TOOLBAR_BROWSE,
                             rose.config_editor.TOOLBAR_REDO,
                             rose.config_editor.TOOLBAR_REVERT,
                             rose.config_editor.TOOLBAR_FIND_NEXT,
                             rose.config_editor.TOOLBAR_VALIDATE])
        assign = self.toolbar.set_widget_function
        assign(rose.config_editor.TOOLBAR_OPEN, self.load_from_file)
        assign(rose.config_editor.TOOLBAR_SAVE, self.save_to_file)
        assign(rose.config_editor.TOOLBAR_BROWSE, self.handle.launch_browser)
        assign(rose.config_editor.TOOLBAR_UNDO, self.perform_undo)
        assign(rose.config_editor.TOOLBAR_REDO, self.perform_undo, [True])
        assign(rose.config_editor.TOOLBAR_REVERT, self.revert_to_saved_data)
        assign(rose.config_editor.TOOLBAR_FIND_NEXT, self._launch_find)
        assign(rose.config_editor.TOOLBAR_VALIDATE,
               self.handle.check_all_extra)
        self.find_entry = self.toolbar.item_dict.get(
                               rose.config_editor.TOOLBAR_FIND)['widget']
        self.find_entry.connect("activate", self._launch_find)
        self.find_entry.connect("changed", self._clear_find)
        add_icon = self.toolbar.item_dict.get(
                        rose.config_editor.TOOLBAR_ADD)['widget']
        add_icon.connect('button_press_event', self.add_page_variable)
        self.toolbar.set_widget_function(rose.config_editor.TOOLBAR_REVERT,
                                         self.revert_to_saved_data)
        custom_text = rose.config_editor.TOOLBAR_SUITE_RUN_MENU
        run_button = rose.gtk.util.CustomMenuButton(
                          stock_id=gtk.STOCK_MEDIA_PLAY,
                          menu_items=[(custom_text, gtk.STOCK_MEDIA_PLAY)],
                          menu_funcs=[self.handle.get_run_suite_args],
                          tip_text=rose.config_editor.TOOLBAR_SUITE_RUN)
        run_button.connect("clicked", self.handle.run_suite)
        run_button.set_sensitive(
              any([c.is_top_level for c in self.data.config.values()]))
        self.toolbar.insert(run_button, -1)

    def generate_menubar(self):
        """Link in the menu functionality and accelerators."""
        self.menubar = rose.config_editor.menu.MenuBar()
        self.menu_widgets = {}
        menu_list = [('/TopMenuBar/File/Open...', self.load_from_file),
                     ('/TopMenuBar/File/Save', lambda m: self.save_to_file()),
                     ('/TopMenuBar/File/Quit', self.handle.destroy),
                     ('/TopMenuBar/Edit/Undo', 
                      lambda m: self.perform_undo()),
                     ('/TopMenuBar/Edit/Redo', 
                      lambda m: self.perform_undo(redo_mode_on=True)),
                     ('/TopMenuBar/Edit/Find', self._launch_find),
                     ('/TopMenuBar/Edit/Find Next',
                      lambda m: self.perform_find(self.find_hist['regex'])),
                     ('/TopMenuBar/Edit/Preferences', self.handle.prefs),
                     ('/TopMenuBar/Edit/Stack', self.handle.view_stack),
                     ('/TopMenuBar/View/View fixed',
                      lambda m: self._set_page_show_modes(
                                     rose.config_editor.SHOW_MODE_FIXED,
                                     m.get_active())),
                     ('/TopMenuBar/View/View ignored',
                      lambda m: self._set_page_show_modes(
                                  rose.config_editor.SHOW_MODE_IGNORED,
                                  m.get_active())),
                     ('/TopMenuBar/View/View user-ignored',
                      lambda m: self._set_page_show_modes(
                                   rose.config_editor.SHOW_MODE_USER_IGNORED,
                                   m.get_active())),
                     ('/TopMenuBar/View/View latent',
                      lambda m: self._set_page_show_modes(
                                     rose.config_editor.SHOW_MODE_LATENT,
                                     m.get_active())),
                     ('/TopMenuBar/View/View without titles',
                      lambda m: self._set_page_show_modes(
                                     rose.config_editor.SHOW_MODE_NO_TITLE,
                                     m.get_active())),
                     ('/TopMenuBar/View/Flag no-metadata',
                      lambda m: self._set_page_show_modes(
                                   rose.config_editor.SHOW_MODE_FLAG_NO_META,
                                   m.get_active())),
                     ('/TopMenuBar/View/Flag optional',
                      lambda m: self._set_page_show_modes(
                                  rose.config_editor.SHOW_MODE_FLAG_OPTIONAL,
                                  m.get_active())),
                     ('/TopMenuBar/Metadata/All V',
                      lambda m: self.handle.run_custom_macro(
                                     method_name=rose.macro.VALIDATE_METHOD)),
                     ('/TopMenuBar/Metadata/Extra checks',
                      lambda m: self.handle.check_fail_rules()),
                     ('/TopMenuBar/Metadata/Switch off metadata',
                      lambda m: self.refresh_metadata(m.get_active())),
                     ('/TopMenuBar/Tools/Run Suite/Run Suite default',
                      self.handle.run_suite),
                     ('/TopMenuBar/Tools/Run Suite/Run Suite custom',
                      self.handle.get_run_suite_args),
                     ('/TopMenuBar/Tools/Browser',
                      lambda m: self.handle.launch_browser()),
                     ('/TopMenuBar/Tools/Terminal',
                      lambda m: self.handle.launch_terminal()),
                     ('/TopMenuBar/Page/Revert',
                      lambda m: self.revert_to_saved_data()),
                     ('/TopMenuBar/Page/Page Info',
                      lambda m: self.handle.info_request(
                                     self._get_current_page().namespace)),
                     ('/TopMenuBar/Page/Page Help',
                      lambda m: self._get_current_page().launch_help()),
                     ('/TopMenuBar/Page/Page Web Help',
                      lambda m: self._get_current_page().launch_url()),
                     ('/TopMenuBar/Help/GUI Help', self.handle.help),
                     ('/TopMenuBar/Help/About', self.handle.about_dialog)]
        is_toggled = dict([('/TopMenuBar/View/View fixed',
                            rose.config_editor.SHOULD_SHOW_FIXED),
                           ('/TopMenuBar/View/View ignored',
                            rose.config_editor.SHOULD_SHOW_IGNORED),
                           ('/TopMenuBar/View/View user-ignored',
                            rose.config_editor.SHOULD_SHOW_USER_IGNORED),
                           ('/TopMenuBar/View/View latent',
                            rose.config_editor.SHOULD_SHOW_LATENT),
                           ('/TopMenuBar/View/View without titles',
                            rose.config_editor.SHOULD_SHOW_NO_TITLE),
                           ('/TopMenuBar/View/Flag optional',
                            rose.config_editor.SHOULD_SHOW_FLAG_OPTIONAL),
                           ('/TopMenuBar/View/Flag no-metadata',
                            rose.config_editor.SHOULD_SHOW_FLAG_NO_META)])
        for (address, action) in menu_list:
            widget = self.menubar.uimanager.get_widget(address)
            self.menu_widgets.update({address: widget})
            if address in is_toggled:
                widget.set_active(is_toggled[address])
                if (address.endswith("View user-ignored") and
                    rose.config_editor.SHOULD_SHOW_IGNORED):
                    widget.set_sensitive(False)
            widget.connect('activate', action)
        page_menu = self.menubar.uimanager.get_widget("/TopMenuBar/Page")
        add_menuitem = self.menubar.uimanager.get_widget(
                                              "/TopMenuBar/Page/Add variable")
        page_menu.connect("activate",
                          lambda m: self.handle.load_page_menu(
                                                self.menubar,
                                                add_menuitem,
                                                self._get_current_page()))
        page_menu.get_submenu().connect(
                          "deactivate",
                          lambda m: self.handle.clear_page_menu(
                                                      self.menubar,
                                                      add_menuitem))
        self.handle.load_macro_menu(self.menubar)
        if not any([c.is_top_level for c in self.data.config.values()]):
            self.menubar.uimanager.get_widget(
                         "/TopMenuBar/Tools/Run Suite").set_sensitive(False)
        self.alter_bar_sensitivity()
        self.top_menu = self.menubar.uimanager.get_widget('/TopMenuBar')
        # Load the keyboard accelerators.
        accel = {
            rose.config_editor.ACCEL_UNDO:
                        lambda: self.perform_undo(),
            rose.config_editor.ACCEL_REDO:
                        lambda: self.perform_undo(redo_mode_on=True),
            rose.config_editor.ACCEL_FIND:
                        lambda: self.find_entry.grab_focus(),
            rose.config_editor.ACCEL_FIND_NEXT:
                        lambda: self.perform_find(self.find_hist['regex']),
            rose.config_editor.ACCEL_HELP_GUI:
                        lambda: self.handle.help(),
            rose.config_editor.ACCEL_OPEN:
                        lambda: self.load_from_file(),
            rose.config_editor.ACCEL_SAVE:
                        lambda: self.save_to_file(),
            rose.config_editor.ACCEL_QUIT:
                        lambda: self.handle.destroy(),
            rose.config_editor.ACCEL_SUITE_RUN:
                        lambda: self.handle.run_suite(),
            rose.config_editor.ACCEL_BROWSER:
                        lambda: self.handle.launch_browser(),
            rose.config_editor.ACCEL_TERMINAL:
                        lambda: self.handle.launch_terminal()}
        self.menubar.set_accelerators(accel)

    def generate_hyper_panel(self):
        """"Create tree panel and link functions."""
        self.hyper_panel = rose.config_editor.panel.HyperLinkTreePanel(
                                              self.data.namespace_tree)
        self.hyper_panel.send_create_request = self.handle.create_request
        self.hyper_panel.send_launch_request = self.handle_launch_request
        self.hyper_panel.send_add_dialog_request = self.handle.add_dialog
        self.hyper_panel.ask_can_clone = self.handle.ask_can_clone
        self.hyper_panel.ask_is_top = (
                   lambda n: "/" + n in self.data.config.keys())
        self.hyper_panel.ask_has_content = (
                   lambda n: self.data.is_ns_content("/" + n))
        self.hyper_panel.send_clone_request = self.handle.clone_request
        self.hyper_panel.send_delete_request = self.handle.delete_request
        self.hyper_panel.send_edit_request = self.handle.edit_request
        self.hyper_panel.send_ignore_request = self.handle.ignore_request
        self.hyper_panel.send_info_request = self.handle.info_request
        self.hyper_panel.send_search_request = self.perform_find_by_ns_id

#------------------ Page manipulation functions ------------------------------


    def handle_launch_request(self, namespace_name, as_new=False):
        """Handle a request to create a page.

        It normally returns a page containing all variables associated with
        the namespace namespace_name, but it won't create a page if it is
        already open. It will overwrite the existing current page, if any,
        in the internal notebook, unless as_new is True.

        """
        if not namespace_name.startswith('/'):
            namespace_name = '/' + namespace_name
        if namespace_name in self.notebook.get_page_ids():
            index = self.notebook.get_page_ids().index(namespace_name)
            self.notebook.set_current_page(index)
            return False
        for tab_window in self.tab_windows:
            if tab_window.get_child().namespace == namespace_name:
                tab_window.present()
                return False
        page = self.make_page(namespace_name)
        if page is None:
            return False
        if as_new:
            self.notebook.append_page(page, page.labelwidget)
            self.notebook.set_current_page(-1)
        else:
            n = self.notebook.get_current_page()
            self.notebook.insert_page(page, page.labelwidget, n)
            if n != -1:
                self.notebook.remove_page(n + 1)
            self.notebook.set_current_page(n)
        self.notebook.set_tab_label_packing(page)

    def make_page(self, namespace_name):
        """Look up page data and attributes and call a page constructor."""
        config_name, subspace = self.util.split_full_ns(self.data,
                                                        namespace_name)
        data, latent_data = self.data.get_data_for_namespace(
                                                   namespace_name)
        config_data = self.data.config[config_name]
        meta_config = config_data.meta
        ns_metadata = self.data.namespace_meta_lookup.get(namespace_name, {})
        description = ns_metadata.get(rose.META_PROP_DESCRIPTION, '')
        duplicate = ns_metadata.get(rose.META_PROP_DUPLICATE)
        help = ns_metadata.get(rose.META_PROP_HELP)
        url = ns_metadata.get(rose.META_PROP_URL)
        custom_widget = ns_metadata.get(rose.META_PROP_WIDGET)
        if custom_widget is not None:
            module, cls = re.match('([.\w]*)\.(\w+)$', custom_widget).groups()
            custom_widget = None
        label = ns_metadata.get(rose.META_PROP_TITLE)
        if label is None:
            label = subspace.split('/')[-1]
        if label.isdigit() and duplicate == rose.META_PROP_VALUE_TRUE:
            label = "(".join(subspace.split('/')[-2:]) + ")"
        sections = [s for s in ns_metadata.get('sections', [])]
        has_sub_data = self.data.is_ns_sub_data(namespace_name)
        section_data_objects = []
        for section in sections:
            sect_data = config_data.sections.now.get(section)
            if sect_data is not None:
                section_data_objects.append(sect_data)
        # Related pages
        see_also = ''
        for section_name in [s for s in sections if s.startswith('namelist')]:
            last_part = section_name.split(':')[-1]
            search_name = section_name
            while re.search('\([\d:, ]+\)$', search_name):
                search_name = re.sub('\([\d:, ]+\)$', '', search_name)
            for section, variables in config_data.vars.now.items():
                if not section.startswith(rose.SUB_CONFIG_FILE_DIR):
                    continue
                for variable in variables:
                    if variable.name != rose.FILE_VAR_CONTENT:
                        continue
                    if (variable.value in [search_name, last_part] or
                        search_name in variable.value):
                        var_id = variable.metadata['id']
                        sect = self.util.get_section_option_from_id(var_id)[0]
                        see_also += ", " + var_id
        see_also = see_also.replace(", ", "", 1)
        # Icon
        icon_path = self.data.get_icon_path_for_config(config_name)
        is_default = self.get_ns_is_default(namespace_name)
        sub_data = None
        if has_sub_data:
            sub_data = self.data.get_sub_data_for_namespace(namespace_name)
        page_metadata = {'namespace': namespace_name,
                         'ns_is_default': is_default,
                         'label': label,
                         'description': description,
                         'duplicate': duplicate,
                         'help': help,
                         'url': url,
                         'widget': custom_widget,
                         'see_also': see_also,
                         'config_name': config_name,
                         'show_modes': self.page_show_modes,
                         'icon': icon_path}
        if len(sections) == 1:
            page_metadata.update({'id': sections.pop()})
        variable_ops = rose.config_editor.stack.VariableOperations(
                                   self.data, self.util, 
                                   self.undo_stack, self.redo_stack,
                                   self.check_cannot_enable_setting,
                                   self.update_namespace,
                                   search_id_func=self.perform_find_by_id)
        directory = None
        if namespace_name == config_name:
            directory = config_data.directory
        launch_info = lambda: self.handle.info_request(namespace_name)
        launch_edit = lambda: self.handle.edit_request(namespace_name)
        page = rose.config_editor.page.ConfigPage(
                                  page_metadata,
                                  data,
                                  latent_data,
                                  variable_ops,
                                  section_data_objects,
                                  self.data.get_format_sections,
                                  directory,
                                  sub_data=sub_data,
                                  launch_info_func=launch_info,
                                  launch_edit_func=launch_edit)
        #FIXME: These three should go.
        page.trigger_tab_detach = lambda b: self._handle_detach_request(page)
        variable_ops.trigger_ignored_update = lambda v: page.update_ignored()
        page.trigger_update_status = lambda: self.update_status(page)
        return page

    def get_orphan_page(self, namespace):
        page = self.make_page(namespace)
        orphan_container = self.handle.get_orphan_container(page)
        self.orphan_pages.append(page)
        return orphan_container

    def get_ns_is_default(self, namespace):
        """Sets if this namespace is the default for a section. Slow!"""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        meta_config = config_data.meta
        allowed_sections = self.data.get_sections_from_namespace(namespace)
        empty = True
        for section in allowed_sections:
            for variable in config_data.vars.now.get(section, []):
                if variable.metadata['full_ns'] == namespace:
                    empty = False
                    if rose.META_PROP_NS not in variable.metadata:
                        return True
            for variable in config_data.vars.latent.get(section, []):
                if variable.metadata['full_ns'] == namespace:
                    empty = False
                    if rose.META_PROP_NS not in variable.metadata:
                        return True
        if empty:
            # An added, non-metadata section with no variables.
            return True
        return False

    def _handle_detach_request(self, page, old_window=None):
        """Open tab (or 'page') in a window and manage close page events."""
        if old_window is None:
            tab_window = gtk.Window()
            tab_window.set_icon(self.mainwindow.window.get_icon())
            tab_window.add_accel_group(self.menubar.accelerators)
            tab_window.set_default_size(*rose.config_editor.SIZE_PAGE_DETACH)
            tab_window.connect('destroy-event', lambda w, e:
                               self.tab_windows.remove(w) and False)
            tab_window.connect('delete-event', lambda w, e:
                               self.tab_windows.remove(w) and False)
        else:
            tab_window = old_window
        notebook_index = None
        for n, notebook_page in enumerate(self.notebook.get_pages()):
            if notebook_page == page:
                notebook_index = n
                break
        add_button = rose.gtk.util.CustomButton(
                              stock_id=gtk.STOCK_ADD,
                              tip_text=rose.config_editor.TIP_ADD_TO_PAGE,
                              size=gtk.ICON_SIZE_LARGE_TOOLBAR,
                              as_tool=True)
        revert_button = rose.gtk.util.CustomButton(
                                 stock_id=gtk.STOCK_REVERT_TO_SAVED,
                                 tip_text=rose.config_editor.TIP_REVERT_PAGE,
                                 size=gtk.ICON_SIZE_LARGE_TOOLBAR,
                                 as_tool=True)
        add_button.connect('button_press_event', self.add_page_variable)
        revert_button.connect('clicked',
                              lambda b: self.revert_to_saved_data())
        if old_window is None:
            parent = self.notebook
        else:
            parent = old_window
        page.reshuffle_for_detached(add_button, revert_button, parent)
        tab_window.set_title(' - '.join([page.label, self.data.top_level_name,
                                         rose.config_editor.PROGRAM_NAME]))
        tab_window.add(page)
        tab_window.connect_after('focus-in-event', self.handle_page_change)
        if old_window is None:
            self.tab_windows.append(tab_window)
        tab_window.show()
        tab_window.present()
        self.set_current_page_indicator(page.namespace)
        return False

    def handle_page_change(self, *args):
        """Handle a page change and select the correct tree row."""
        current_page = self._get_current_page()
        self.alter_page_menubar_toolbar_sensitivity(current_page)
        if current_page is None:
            self.hyper_panel.select_row(None)
            return False
        self.set_current_page_indicator(current_page.namespace)
        return False

    def alter_page_menubar_toolbar_sensitivity(self, current_page):
        if not hasattr(self, 'toolbar') or not hasattr(self, 'menubar'):
            return False
        page_icons = ['Add to page...', 'Revert page to saved']
        get_widget = self.menubar.uimanager.get_widget
        page_menu = get_widget('/TopMenuBar/Page')
        page_menuitems = page_menu.get_submenu().get_children()
        if current_page is None or not self.notebook.get_n_pages():
            for name in page_icons:
                self.toolbar.set_widget_sensitive(name, False)
            for menuitem in page_menuitems:
                menuitem.set_sensitive(False)
        else:
            for name in page_icons:
                self.toolbar.set_widget_sensitive(name, True)
            for menuitem in page_menuitems:
                menuitem.set_sensitive(True)
            ns = current_page.namespace
            metadata = self.data.namespace_meta_lookup.get(ns, {})
            get_widget("/TopMenuBar/Page/Page Help").set_sensitive(
                                         rose.META_PROP_HELP in metadata)
            get_widget("/TopMenuBar/Page/Page Web Help").set_sensitive(
                                         rose.META_PROP_URL in metadata)

    def set_current_page_indicator(self, namespace):
        if hasattr(self, 'hyper_panel'):
            self.hyper_panel.select_row(namespace.lstrip('/').split('/'))

    def add_page_variable(self, widget, event):
        """Launch an add menu based on page content."""
        page = self._get_current_page()
        if page is None:
            return False
        page.launch_add_menu(event.button, event.time)

    def revert_to_saved_data(self):
        """Reload the page data from saved configuration information."""
        page = self._get_current_page()
        if page is None:
            return
        namespace = page.namespace
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        self.data.load_variable_namespaces(config_name, from_saved=True)
        config_data, ghost_data = self.data.get_data_for_namespace(
                                            namespace, from_saved=True)
        page.reload_from_data(config_data, ghost_data)
        self.data.load_variable_namespaces(config_name)
        self.update_status(page)

    def _generate_pagelist(self):
        """Load an attribute self.pagelist with a list of open pages."""
        self.pagelist = []
        if hasattr(self, 'notebook'):
            for n in range(self.notebook.get_n_pages()):
                if hasattr(self.notebook.get_nth_page(n), 'panel_data'):
                    self.pagelist.append(self.notebook.get_nth_page(n))
        if hasattr(self, 'tab_windows'):
            for window in self.tab_windows:
                if hasattr(window.get_child(), 'panel_data'):
                    self.pagelist.append(window.get_child())
        self.pagelist.extend(self.orphan_pages)

    def _get_current_page(self):
        self._generate_pagelist()
        if not self.pagelist:
            return None
        for window in self.tab_windows:
            if window.has_toplevel_focus():
                return window.get_child()
        for page in self.orphan_pages:
            if page.get_toplevel().is_active():
                return page
        if hasattr(self, "notebook"):
            n = self.notebook.get_current_page()
            return self.notebook.get_nth_page(n)
        return None

    def _set_page_show_modes(self, key, is_key_allowed):
        self.page_show_modes[key] = is_key_allowed
        self._generate_pagelist()
        for page in self.pagelist:
            page.react_to_show_modes(key, is_key_allowed)
        if (hasattr(self, "menubar") and 
            key == rose.config_editor.SHOW_MODE_IGNORED):
            user_ign_item = self.menubar.uimanager.get_widget(
                                         "/TopMenuBar/View/View user-ignored")
            user_ign_item.set_sensitive(not is_key_allowed)

    def kill_page(self, namespace):
        """Destroy a page if it has the same namespace as the argument."""
        self._generate_pagelist()
        for page in self.pagelist:
            if page.namespace == namespace:
                if page.namespace in self.notebook.get_page_ids():
                    self.notebook.delete_by_id(page.namespace)
                else:
                    tab_pages = [w.get_child() for w in self.tab_windows]
                    if page in tab_pages:
                        page_window = self.tab_windows[tab_pages.index(page)]
                        page_window.destroy()
                        self.tab_windows.remove(page_window)
                    else:
                        self.orphan_pages.remove(page)

#------------------ Update functions -----------------------------------------

    def _namespace_data_is_modified(self, namespace):
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
        allowed_sections = self.data.get_sections_from_namespace(namespace)
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
                        return rose.config_editor.TREE_PANEL_TIP_CHANGED_VARS
                    save_var_map.pop(var_id)
        if save_var_map:
            # Some variables are now absent.
            return rose.config_editor.TREE_PANEL_TIP_REMOVED_VARS
        if self.get_ns_is_default(namespace):
            sections = self.data.get_sections_from_namespace(namespace)
            for section in sections:
                sect_data = config_sections.now.get(section)
                save_sect_data = config_sections.save.get(section)
                if (sect_data is None) != (save_sect_data is None):
                    return rose.config_editor.TREE_PANEL_TIP_DIFF_SECTIONS
                if sect_data is not None and save_sect_data is not None:
                    if sect_data.to_hashable() != save_sect_data.to_hashable():
                        return rose.config_editor.TREE_PANEL_TIP_CHANGED_SECTIONS
        return ""

    def tree_trigger_update(self):
        if hasattr(self, 'hyper_panel'):
            self.hyper_panel.load_tree(None, self.data.namespace_tree)
            self.update_all()

    def refresh_ids(self, config_name, setting_ids):
        """Refresh and redraw settings if needed."""
        self._generate_pagelist()
        nses_to_do = []
        for changed_id in setting_ids:
            sect, opt = self.util.get_section_option_from_id(changed_id)
            if opt is None:
                ns = self.data.get_default_namespace_for_section(sect,
                                                                 config_name)
                if ns in [p.namespace for p in self.pagelist]:
                    index = [p.namespace for p in self.pagelist].index(ns)
                    page = self.pagelist[index]
                    page.refresh()
            else:
                var = self.data.get_ns_variable(changed_id, config_name)
                if var is None:
                    continue
                ns = var.metadata['full_ns']
                if ns in [p.namespace for p in self.pagelist]:
                    index = [p.namespace for p in self.pagelist].index(ns)
                    page = self.pagelist[index]
                    page.refresh(changed_id)
            if ns not in nses_to_do:
                nses_to_do.append(ns)
        for ns in nses_to_do:
            self.update_namespace(ns)

    def update_all(self, just_this_config=None):
        """Loop over all namespaces and update."""
        unique_namespaces = self.data.get_all_namespaces(just_this_config)
        if just_this_config is None:
            configs = self.data.config.keys()
        else:
            configs = [just_this_config]
        for config_name in configs:
            self.update_config(config_name)
        self._generate_pagelist()
        for ns in unique_namespaces:
            if ns in [p.namespace for p in self.pagelist]:
                index = [p.namespace for p in self.pagelist].index(ns)
                page = self.pagelist[index]
                self.sync_page_var_lists(page)
            self.update_ignored_statuses(ns)
        self.perform_error_check()  # Perform a global error check.
        for ns in unique_namespaces:
            if ns in [p.namespace for p in self.pagelist]:
                index = [p.namespace for p in self.pagelist].index(ns)
                page = self.pagelist[index]
                self.update_tree_status(page)  # Faster.
            else:
                self.update_tree_status(ns)
        self.alter_bar_sensitivity()
        self.update_stack_viewer_if_open()
        for config_name in configs:
            self.update_metadata_id(config_name)
        self.update_ns_sub_data()

    def update_namespace(self, namespace, are_errors_done=False):
        """Update driver function. Updates the page if open."""
        self._generate_pagelist()
        if namespace in [p.namespace for p in self.pagelist]:
            index = [p.namespace for p in self.pagelist].index(namespace)
            page = self.pagelist[index]
            self.update_status(page, are_errors_done)
        else:
            self.update_config(namespace)
            self.update_sections(namespace)
            self.update_ignored_statuses(namespace)
            if not are_errors_done:
                self.perform_error_check(namespace)
            self.update_tree_status(namespace)
            self.alter_bar_sensitivity()
            self.update_stack_viewer_if_open()
            if namespace in self.data.config.keys():
                self.update_metadata_id(namespace)
            self.update_ns_sub_data(namespace)

    def update_status(self, page, are_errors_done=False):
        """Update ignored statuses and update the tree statuses."""
        self._generate_pagelist()
        self.sync_page_var_lists(page)
        self.update_config(page.namespace)
        self.update_sections(page.namespace)
        self.update_ignored_statuses(page.namespace)
        if not are_errors_done:
            self.perform_error_check(page.namespace)
        self.update_tree_status(page)
        self.alter_bar_sensitivity()
        self.update_stack_viewer_if_open()
        if page.namespace in self.data.config.keys():
            self.update_metadata_id(page.namespace)
        self.update_ns_sub_data(page.namespace)

    def update_ns_sub_data(self, namespace=None):
        """Update any relevant summary data on another page."""
        for page in self.pagelist:
            if (page.sub_data is None or
                (namespace is not None and
                 not namespace.startswith(page.namespace))):
                continue
            page.sub_data = self.data.get_sub_data_for_namespace(
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
        real, miss = self.data.get_data_for_namespace(page.namespace)
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

    def update_ns_comments(self, namespace):
        """Update section comments for this namespace."""
        if hasattr(self, "hyper_panel"):
            comment = self.data.get_ns_comment_string(namespace)
            self.hyper_panel.update_comment(namespace.lstrip("/").split("/"),
                                            comment)

    def update_config(self, namespace):
        """Update the config object for the macros. To be removed."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config = self.data.dump_to_internal_config(config_name)
        self.data.config[config_name].config = config

    def update_sections(self, namespace):
        """Update the list of sections that are empty."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        config_data = self.data.config[config_name]
        for section in self.data.get_sections_from_namespace(namespace):
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
        trigger = self.trigger[config_name]
        allowed_sections = self.data.get_sections_from_namespace(namespace)
        updated_ids = []

        this_ns_triggers = []
        ns_vars, ns_l_vars = self.data.get_data_for_namespace(namespace)
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
        for var in config_data.vars.get_all(no_latent=True):
            var_id = var.metadata['id']
            var_id_map.update({var_id: var})

        update_nses = []
        update_section_nses = []
        for setting_id in updated_ids:
            sect, opt = self.util.get_section_option_from_id(setting_id)
            if opt is None:
                sect_vars = config_data.vars.now.get(sect, [])
                ns = self.data.get_default_namespace_for_section(sect,
                                                                 config_name)
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
        trigger = self.trigger[config_name]
        
        config = config_data.config
        meta_config = config_data.meta
        config_sections = config_data.sections
        update_ids = trigger.update(var_id, config, meta_config)
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
            for attribute in [rose.config_editor.WARNING_TYPE_ENABLED,
                              rose.config_editor.WARNING_TYPE_IGNORED]:
                if attribute in sect_data.error:
                    sect_data.error.pop(attribute)
            reason = sect_data.ignored_reason
            if section in enabled_sections:
                # Trigger-enabled sections
                if (rose.variable.IGNORED_BY_USER in reason):
                    # User-ignored but trigger-enabled
                    if (meta.get([section, rose.META_PROP_COMPULSORY]).value
                        == rose.META_PROP_VALUE_TRUE):
                        sect_data.error.update(
                              {rose.config_editor.WARNING_TYPE_IGNORED:
                               rose.config_editor.WARNING_NOT_USER_IGNORABLE})
                elif (rose.variable.IGNORED_BY_SYSTEM in reason):
                    # Normal trigger-enabled sections
                    reason.pop(rose.variable.IGNORED_BY_SYSTEM)
                    for var in sect_vars:
                        ns = var.metadata['full_ns']
                        if ns not in triggered_ns_list:
                            triggered_ns_list.append(ns)
                        var.ignored_reason.pop(
                                    rose.var.IGNORED_BY_SECTION)
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
            for attribute in [rose.config_editor.WARNING_TYPE_ENABLED,
                              rose.config_editor.WARNING_TYPE_IGNORED]:
                if attribute in var.error:
                    var.error.pop(attribute)
            if (var_id in trigger.enabled_dict and
                var_id not in trigger.ignored_dict):
                # Trigger-enabled variables
                if (rose.variable.IGNORED_BY_USER in
                    var.ignored_reason):
                    # User-ignored but trigger-enabled
                    if (var.metadata.get(rose.META_PROP_COMPULSORY) ==
                        rose.META_PROP_VALUE_TRUE):
                        var.error.update(
                              {rose.config_editor.WARNING_TYPE_IGNORED:
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
        if not hasattr(self, 'hyper_panel'):
            return
        if isinstance(page_or_ns, basestring):
            namespace = page_or_ns
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            errors = []
            ns_vars, ns_l_vars = self.data.get_data_for_namespace(namespace)
            for var in ns_vars + ns_l_vars:
                errors += var.error.items()
        else:
            namespace = page_or_ns.namespace
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            errors = page_or_ns.validate_errors()
        # Add section errors.
        config_data = self.data.config[config_name]
        for section in self.data.get_sections_from_namespace(namespace):
            if section in config_data.sections.now:
                errors += config_data.sections.now[section].error.items()
        # Set icons.
        name_tree = namespace.lstrip('/').split('/')
        if icon_bool is None:
            if icon_type == 'changed' or icon_type is None:
                change = self._namespace_data_is_modified(namespace)
                self.hyper_panel.update_change(name_tree, change)
                self.hyper_panel.set_row_icon(name_tree, bool(change),
                                              ind_type='changed')
            if icon_type == 'error' or icon_type is None:
                self.hyper_panel.set_row_icon(name_tree, len(errors),
                                              ind_type='error')
        else:
            self.hyper_panel.set_row_icon(name_tree, icon_bool,
                                          ind_type=icon_type)

    def update_stack_viewer_if_open(self):
        """Update the information in the stack viewer, if open."""
        if self.pluggable:
            return False
        if isinstance(self.mainwindow.log_window,
                      rose.config_editor.stack.StackViewer):
            self.mainwindow.log_window.update()

    def update_metadata_id(self, config_name):
        """Update the metadata if the id has changed."""
        config_data = self.data.config[config_name]
        new_meta_id = self.data.get_config_meta_flag(config_data.config)
        if config_data.meta_id != new_meta_id:
            config_data.meta_id = new_meta_id
            if not self.metadata_off:
                self.refresh_metadata(just_this_config=config_name)
        
        
#------------------ Page viewer function -------------------------------------

    def view_page(self, page_id, var_id=None):
        """Set focus by namespace (page_id), and optionally by var key."""
        page = None
        if page_id is None:
            return None
        current_page = self._get_current_page()
        if current_page is not None and current_page.namespace == page_id:
            current_page.set_main_focus(var_id)
            self.handle_page_change()  # Just to make sure.
            return current_page
        self._generate_pagelist()
        if (page_id not in [p.namespace for p in self.pagelist]):
            self.handle_launch_request(page_id, as_new=True)
            n = self.notebook.get_current_page()
            page = self.notebook.get_nth_page(n)
        if page_id in self.notebook.get_page_ids():
            n = self.notebook.get_page_ids().index(page_id)
            page = self.notebook.get_nth_page(n)
            self.notebook.set_current_page(n)
            if not self.mainwindow.window.is_active():
                self.mainwindow.window.present()
            page.set_main_focus(var_id)
        else:
            for tab_window in self.tab_windows:
                if tab_window.get_child().namespace == page_id:
                    page = tab_window.get_child()
                    if not tab_window.is_active():
                        tab_window.present()
                    page.set_main_focus(var_id)
        self.set_current_page_indicator(page_id)
        return page

#------------------ Primary menu functions -----------------------------------

    def load_from_file(self, somewidget=None):
        """Open a standard dialogue and load a config file, if selected."""
        dirname = self.mainwindow.launch_open_dirname_dialog()
        if dirname is None or not os.path.isdir(dirname):
            return False
        if (self.data.top_level_directory is None and not self.pluggable):
            config_objs = {}
            self.data.load_top_config(dirname)
            self.data.saved_config_names = set(self.data.config.keys())
            self.mainwindow.window.set_title(self.data.top_level_name +
                                             ' - rose-config-editor')
            self.update_all()
            self.perform_startup_check()
        else:
            spawn_subprocess_window(dirname)

    def save_to_file(self, only_config_name=None):
        """Dump the component configurations in memory to disk."""
        if only_config_name is None:
            config_names = self.data.config.keys()
        else:
            config_names = [only_config_name]
        for config_name in config_names:
            config = self.data.dump_to_internal_config(config_name)
            new_saved_config = self.data.dump_to_internal_config(config_name)
            config_data = self.data.config[config_name]
            directory = config_data.directory
            config_vars = config_data.vars
            config_sections = config_data.sections
            # Dump the configuration.
            filename = rose.SUB_CONFIG_NAME
            if directory is None:
                if config_data.is_discovery:
                    filename = rose.INFO_CONFIG_NAME
                    directory = self.data.top_level_directory
            elif (directory.rstrip('/') == 
                self.data.top_level_directory.rstrip('/') and
                rose.TOP_CONFIG_NAME in os.listdir(directory)):
                filename = rose.TOP_CONFIG_NAME
            save_path = os.path.join(directory, filename)
            rose.macro.pretty_format_config(config)
            try:
                rose.config.dump(config, save_path)
            except (OSError, IOError) as e:
                rose.gtk.util.run_dialog(
                              rose.gtk.util.DIALOG_TYPE_ERROR,
                              rose.config_editor.ERROR_SAVE_PATH_FAIL.format(
                                                                 str(e)))
                return False
            # Un-prettify.
            config = self.data.dump_to_internal_config(config_name)
            # Update the last save data.
            config_data.saved_config = new_saved_config
            config_vars.save.clear()
            config_vars.latent_save.clear()
            for section, variables in config_vars.now.items():
                config_vars.save.update({section: []})
                for variable in variables:
                    config_vars.save[section].append(variable.copy())
            for section, variables in config_vars.latent.items():
                config_vars.latent_save.update({section: []})
                for variable in variables:
                    config_vars.latent_save[section].append(variable.copy())
            config_sections.save.clear()
            config_sections.latent_save.clear()
            for section, data in config_sections.now.items():
                config_sections.save.update({section: data.copy()})
            for section, data in config_sections.latent.items():
                config_sections.latent_save.update({section: data.copy()})
        self.data.saved_config_names = set(self.data.config.keys())
        # Update open pages.
        self._generate_pagelist()
        for page in self.pagelist:
            page.refresh_widget_status()
        # Update everything else.
        self.update_all()

    def output_config_objects(self, only_config_name=None):
        """Return a dict of config name - object pairs from this session."""
        if only_config_name is None:
            config_names = self.data.config.keys()
        else:
            config_names = [only_config_name]
        return_dict = {}
        for config_name in config_names:
            config = self.data.dump_to_internal_config(config_name)
            return_dict.update({config_name: config})
        return return_dict

#------------------ Secondary Menu/Dialog handling functions -----------------

    def _add_config(self, config_name, meta=None):
        """Add a configuration, optionally with META=TYPE=meta."""
        config_short_name = config_name.split("/")[-1]
        root = os.path.join(self.data.top_level_directory,
                            rose.SUB_CONFIGS_DIR)
        new_path = os.path.join(root, config_short_name, rose.SUB_CONFIG_NAME)
        new_config = rose.config.ConfigNode()
        if meta is not None:
            new_config.set([rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_META_TYPE],
                           meta)
        try:
            os.mkdir(os.path.dirname(new_path))
            rose.config.dump(new_config, new_path)
        except Exception as e:
            text = rose.config_editor.ERROR_CONFIG_CREATE.format(
                                            new_path, type(e), str(e))
            title = rose.config_editor.ERROR_CONFIG_CREATE_TITLE
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     text, title)
            return False
        self.data.load_config(os.path.dirname(new_path), reload_tree_on=True)
        stack_item = rose.config_editor.stack.StackItem(
                          config_name,
                          rose.config_editor.STACK_ACTION_ADDED,
                          rose.variable.Variable('', '', {}),
                          self._remove_config,
                          (config_name, meta))
        self.undo_stack.append(stack_item)
        while self.redo_stack:
            self.redo_stack.pop()
        self.view_page(config_name)
        self.update_namespace(config_name)

    def _remove_config(self, config_name, meta=None):
        """Remove a configuration, optionally caching a meta id."""
        dirpath = self.data.config[config_name].directory
        nses = self.data.get_all_namespaces(config_name)
        nses.remove(config_name)
        self._generate_pagelist()
        for page in self.pagelist:
            name = self.util.split_full_ns(self.data, page.namespace)[0]
            if name == config_name:
                if name in self.notebook.get_page_ids():
                    self.notebook.delete_by_id(name)
                else:
                    tab_nses = [w.get_child().namespace
                                for w in self.tab_windows]
                    page_window = self.tab_windows[tab_nses.index(name)]
                    page.window.destroy()
        self.handle.delete_request(nses)
        if dirpath is not None:
            try:
                shutil.rmtree(dirpath)
            except Exception as e:
                text = rose.config_editor.ERROR_CONFIG_DELETE.format(
                                                dir_path, type(e), str(e))
                title = rose.config_editor.ERROR_CONFIG_CREATE_TITLE
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                         text, title)
                return False
        self.data.config.pop(config_name)
        self.data.reload_namespace_tree()
        stack_item = rose.config_editor.stack.StackItem(
                          config_name,
                          rose.config_editor.STACK_ACTION_REMOVED,
                          rose.variable.Variable('', '', {}),
                          self._add_config,
                          (config_name, meta))
        self.undo_stack.append(stack_item)
        while self.redo_stack:
            self.redo_stack.pop()

    def _get_menu_widget(self, suffix):
        for address in self.menu_widgets:
            if address.endswith(suffix):
                return self.menu_widgets[address]
        return None

    def alter_bar_sensitivity(self):
        """Update bar functionality like Undo and Redo."""
        if not hasattr(self, 'toolbar'):
            return False
        self.toolbar.set_widget_sensitive('Undo', len(self.undo_stack) > 0)
        self.toolbar.set_widget_sensitive('Redo', len(self.redo_stack) > 0)
        self._get_menu_widget('/Undo').set_sensitive(len(self.undo_stack) > 0)
        self._get_menu_widget('/Redo').set_sensitive(len(self.redo_stack) > 0)
        self._get_menu_widget('/Find Next').set_sensitive(
                                            len(self.find_hist['ids']) > 0)
        for config_name in self.data.config:
            config_data = self.data.config[config_name]
            now_vars = []
            for v in config_data.vars.get_all(no_latent=True):
                now_vars.append(v.to_hashable())
            las_vars = []
            for v in config_data.vars.get_all(no_latent=True, save=True):
                las_vars.append(v.to_hashable())
            if set(now_vars) ^ set(las_vars):
                self.toolbar.set_widget_sensitive('Save', True)
                self._get_menu_widget('/Save').set_sensitive(True)
                break
            if self._namespace_data_is_modified(config_name):
                self.toolbar.set_widget_sensitive('Save', True)
                self._get_menu_widget('/Save').set_sensitive(True)
                break
        else:
            self.toolbar.set_widget_sensitive('Save', False)
            self._get_menu_widget('/Save').set_sensitive(False)

    def refresh_metadata(self, metadata_off=False, just_this_config=None):
        """Switch metadata on/off and reloads namespaces."""
        self.metadata_off = metadata_off
        if just_this_config is None:
            configs = self.data.config.keys()
        else:
            configs = [just_this_config]
        self.data.namespace_meta_lookup = {}
        for config_name in configs:
            config = self.data.dump_to_internal_config(config_name)
            config_data = self.data.config[config_name]
            config_data.config = config
            directory = config_data.directory
            del config_data.macros
            meta_config = config_data.meta
            if metadata_off:
                meta_config = self.data.load_meta_config()
                meta_files = []
                macros = []
            else:
                meta_config = self.data.load_meta_config(config, directory)
                meta_files = self.data.load_meta_files(config, directory)
                macros = rose.macro.load_meta_macro_modules(meta_files)
            config_data.meta = meta_config
            self.data.load_file_metadata(config_name)
            self.data.filter_meta_config(config_name)
            # Load section and variable data into the object.
            sects, l_sects = self.data.load_sections_from_config(config_name)
            s_sects, s_l_sects = self.data.load_sections_from_config(
                                                config_name, save=True)
            config_data.sections = rose.config_editor.loader.SectData(
                        sects, l_sects, s_sects, s_l_sects)
            var, l_var = self.data.load_vars_from_config(config_name)
            s_var, s_l_var = self.data.load_vars_from_config(
                                                 config_name, save=True)
            config_data.vars = rose.config_editor.loader.VarData(
                        var, l_var, s_var, s_l_var)
            config_data.meta_files = meta_files
            config_data.macros = macros
            self.data.load_variable_namespaces(config_name)
            self.data.load_variable_namespaces(config_name, from_saved=True)
            self.data.load_ignored_data(config_name)
            self.data.load_metadata_for_namespaces(config_name)
        self.data.reload_namespace_tree()
        if self.pluggable:
            self.update_all()
        if hasattr(self, 'menubar'):
            self.handle.load_macro_menu(self.menubar)
        namespaces_updated = []
        for config_name in configs:
            config_data = self.data.config[config_name]
            for variable in config_data.vars.get_all(no_latent=True):
                ns = variable.metadata.get('full_ns')
                if ns not in namespaces_updated:
                    self.update_tree_status(ns, icon_type='changed')
                    namespaces_updated.append(ns)
        self._generate_pagelist()
        current_page = self._get_current_page()
        current_namespace = None
        if current_page is not None:
            current_namespace = current_page.namespace

        # Generate replacements for existing pages.
        for page in self.pagelist:
            namespace = page.namespace
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            if config_name not in configs:
                continue
            data, missing_data = self.data.get_data_for_namespace(namespace)
            if len(data + missing_data) > 0:
                new_page = self.make_page(namespace)
                if new_page is None:
                    continue
                if page in [w.get_child() for w in self.tab_windows]:
                     # Insert a new page into the old window.
                    tab_pages = [w.get_child() for w in self.tab_windows]
                    old_window = self.tab_windows[tab_pages.index(page)]
                    old_window.remove(page)
                    self._handle_detach_request(new_page, old_window)
                elif hasattr(self, 'notebook'):
                    # Replace a notebook page.
                    index = self.notebook.get_page_ids().index(namespace)
                    self.notebook.remove_page(index)
                    self.notebook.insert_page(new_page, new_page.labelwidget,
                                              index)
                else:
                    # Replace an orphan page
                    parent = page.get_parent()
                    if parent is not None:
                        parent.remove(page)
                        parent.pack_start(new_page)
                    self.orphan_pages.remove(page)
                    self.orphan_pages.append(new_page)
            else:
                self.kill_page(page.namespace)

        # Preserve the old current page view, if possible.
        if current_namespace is not None:
            config_name = self.util.split_full_ns(self.data,
                                                  current_namespace)[0]
            self._generate_pagelist()
            if config_name in configs:
                if current_namespace in [p.namespace for p in self.pagelist]:
                    self.view_page(current_namespace)

#------------------ Data-intensive menu functions / utilities ----------------

    def _launch_find(self, *args):
        """Get the find expression from a dialog."""
        if not self.find_entry.is_focus():
            self.find_entry.grab_focus()
        expression = self.find_entry.get_text()
        start_page = self._get_current_page()
        if expression is not None and expression != '':
            page = self.perform_find(expression, start_page)
            if page is None:
                text = rose.config_editor.WARNING_NOT_FOUND
                try:  # Needs PyGTK >= 2.16
                    self.find_entry.set_icon_from_stock(
                                    0, gtk.STOCK_DIALOG_WARNING)
                    self.find_entry.set_icon_tooltip_text(0, text)
                except AttributeError:
                    rose.gtk.util.run_dialog(
                                  rose.gtk.util.DIALOG_TYPE_INFO,
                                  text,
                                  rose.config_editor.WARNING_NOT_FOUND_TITLE)
            else:
                self._clear_find()

    def _clear_find(self, *args):
        """Clear any warning icons from the find entry."""
        try:  # Needs PyGTK >= 2.16
            self.find_entry.set_icon_from_stock(0, None)
        except AttributeError:
            pass

    def perform_find(self, expression, start_page=None):
        """Drive the finding of the regex 'expression' within the data."""
        if expression == '':
            return None
        page_id, var_id = self.get_found_page_and_id(expression, start_page)
        return self.view_page(page_id, var_id)

    def perform_find_by_ns_id(self, namespace, setting_id):
        """Drive find by id."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        self.perform_find_by_id(config_name, setting_id)

    def perform_find_by_id(self, config_name, setting_id):
        """Drive the finding of a setting id within the data."""
        config_data = self.data.config[config_name]
        section, option = self.util.get_section_option_from_id(setting_id)
        if option is None:
            page_id = self.data.get_default_namespace_for_section(section,
                                                                  config_name)
            self.view_page(page_id)
        else:
            var = self.data.get_variable_by_id(setting_id, config_name)
            if var is None:
                var = self.data.get_variable_by_id(setting_id, config_name,
                                                   latent=True)
            if var is not None:
                page_id = var.metadata["full_ns"]
                self.view_page(page_id, setting_id)

    def get_found_page_and_id(self, expression, start_page):
        """Using regex expression, return a matching page and variable."""
        try:
            reg_find = re.compile(expression).search
        except sre_constants.error as e:
            rose.gtk.util.run_dialog(
                     rose.gtk.util.DIALOG_TYPE_ERROR,
                     rose.config_editor.ERROR_NOT_REGEX.format(
                                        expression, str(e)))
            return None, None
        if self.find_hist['regex'] != expression:
            self.find_hist['ids'] = []
            self.find_hist['regex'] = expression
        if start_page is None:
            ns_cmp = lambda x, y: 0
            name_cmp = lambda x, y: 0
        else:
            current_ns = start_page.namespace
            current_name = self.util.split_full_ns(self.data, current_ns)[0]
            ns_cmp = lambda x, y: (y == current_ns) - (x == current_ns)
            name_cmp = lambda x, y: (y == current_name) - (x == current_name)
        id_cmp = lambda v, w: cmp(v.metadata['id'], w.metadata['id'])
        config_keys = self.data.config.keys()
        config_keys.sort()
        config_keys.sort(name_cmp)
        for config_name in config_keys:
            config_data = self.data.config[config_name]
            search_vars = config_data.vars.get_all(
                                 no_latent=not self.page_show_modes["latent"])
            found_ns_vars = {}
            for variable in search_vars:
                var_id = variable.metadata.get('id')
                ns = variable.metadata.get('full_ns')
                if (rose.META_PROP_TITLE in variable.metadata and
                    reg_find(variable.metadata[rose.META_PROP_TITLE])):
                    found_ns_vars.setdefault(ns, [])
                    found_ns_vars[ns].append(variable)
                    continue
                if reg_find(variable.name) or reg_find(variable.value):
                    found_ns_vars.setdefault(ns, [])
                    found_ns_vars[ns].append(variable)
            ns_list = found_ns_vars.keys()
            ns_list.sort()
            ns_list.sort(ns_cmp)
            for ns in ns_list:
                variables = found_ns_vars[ns]
                variables.sort(id_cmp)
                for variable in variables:
                    var_id = variable.metadata['id']
                    if (config_name, var_id) not in self.find_hist['ids']:
                        if (not self.page_show_modes['fixed'] and
                            len(variable.metadata.get('values', [])) == 1):
                            continue
                        if (not self.page_show_modes['ignored'] and
                            variable.ignored_reason):
                            continue
                        self.find_hist['ids'].append((config_name, var_id))
                        return ns, var_id
        if self.find_hist['ids']:
            config_name, var_id = self.find_hist['ids'][0]
            config_data = self.data.config[config_name]
            var = self.data.get_variable_by_id(var_id, config_name)
            if var is None:
                var = self.data.get_variable_by_id(var_id, config_name,
                                                   latent=True)
            if var is not None:
                self.find_hist['ids'] = [self.find_hist['ids'][0]]
                return var.metadata['full_ns'], var_id
        return None, None

    def perform_startup_check(self):
        """Fix any relevant type errors."""
        for config_name in self.data.config:
            macro_config = self.data.dump_to_internal_config(config_name)
            meta_config = self.data.config[config_name].meta
            # Duplicate checking
            dupl_checker = rose.macros.duplicate.DuplicateChecker()
            problem_list = dupl_checker.validate(macro_config, meta_config)
            if problem_list:
                self.handle.handle_macro_validation(
                            config_name,
                            'duplicate.DuplicateChecker.validate',
                            macro_config, problem_list, no_display=True)
            # Format fixing and checking
            format_fixer = rose.macros.format.FormatFixer()
            macro_config, changes_list = format_fixer.transform(macro_config,
                                                                meta_config)
            if changes_list:
                self.handle.handle_macro_transforms(
                            config_name, "format.FormatFixer.transform",
                            macro_config, changes_list)
                macro_config = self.data.dump_to_internal_config(config_name)
            format_checker = rose.macros.format.FormatChecker()
            problem_list = format_checker.validate(macro_config, meta_config)
            if problem_list:
                self.handle.handle_macro_validation(
                            config_name, 'format.FormatChecker.validate',
                            macro_config, problem_list)
            # Value fixing
            fixer = rose.macros.value.TypeFixer()
            macro_config, changes_list = fixer.transform(
                                              macro_config, meta_config)
            if changes_list:
                self.handle.handle_macro_transforms(config_name,
                                                    'value.TypeFixer.transform',
                                                    macro_config, changes_list)
                   
    def perform_error_check(self, namespace=None):
        """Loop through system macros and sum errors."""
        for macro_name in self.macros:
            # We may need to speed up trigger for large configs.
            self.perform_macro_validation(macro_name, namespace)

    def perform_macro_validation(self, macro_type, namespace=None):
        """Calculate errors for a given internal macro."""
        configs = self.data.config.keys()
        if namespace is not None:
            config_name = self.util.split_full_ns(self.data,
                                                  namespace)[0]
            configs = [config_name]
        for config_name in configs:
            config = self.data.config[config_name].config
            if (namespace is not None and
                macro_type in [rose.META_PROP_TYPE,
                               rose.META_PROP_COMPULSORY]):
                config = self.data.dump_to_internal_config(config_name,
                                                           namespace)
            meta = self.data.config[config_name].meta
            checker = self.macros[macro_type]()
            bad_list = checker.validate(config, meta)
            self.apply_macro_validation(config_name, macro_type, bad_list,
                                        namespace)

    def apply_macro_validation(self, config_name, macro_type, bad_list=None,
                               namespace=None):
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
            ok_sections = self.data.get_sections_from_namespace(namespace)
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
                             id_error_dict.keys() + id_warn_dict.keys())
            return
        for bad_report in bad_list:
            section = bad_report.section
            key = bad_report.option
            info = bad_report.info
            if key is None:
                setting_id = section
                if (namespace is not None and section not in
                    self.data.get_sections_from_namespace(namespace)):
                    continue
                sect_data = config_sections.now.get(section)
                if sect_data is None:
                    sect_data = config_sections.latent.get(section)
                if bad_report.is_warning:
                    sect_data.warning.setdefault(macro_type, info)
                else:
                    sect_data.error.setdefault(macro_type, info)
            else:
                setting_id = self.util.get_id_from_section_option(
                                                    section, key)
                var = self.data.get_variable_by_id(setting_id,
                                                    config_name)
                if var is None:
                    var = self.data.get_variable_by_id(setting_id,
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
            if setting_id in map_:
                # No need for further update, already had warning/error.
                map_.pop(setting_id)
            else:
                # New warning or error.
                map_.update({setting_id: info})
        self.refresh_ids(config_name,
                         id_error_dict.keys() + id_warn_dict.keys())

    def apply_macro_transform(self, config_name, macro_type, changed_ids):
        """Refresh pages with changes."""
        self.refresh_ids(config_name, changed_ids)

    def check_cannot_enable_setting(self, config_name, setting_id):
        return setting_id in self.trigger[config_name].get_all_ids()

    def perform_undo(self, redo_mode_on=False):
        """Change focus to the correct page and call an undo or redo.

        It grabs the relevant page and widget focus and calls the
        correct 'undo_func' StackItem attribute function.
        It then regenerates the affected container and sets the focus to
        the variable that was last affected by the undo.

        """
        if redo_mode_on:
            stack = self.redo_stack
        else:
            stack = self.undo_stack
        if not stack:
            return False
        self._generate_pagelist()
        do_list = [stack[-1]]  # Undo all list items at once
        # do_list should only contain items for a single page
        focused = False
        new_page = None
        for stack_item in do_list:
            node = stack_item.node
            node_id = node.metadata.get('id')
            # We need to handle namespace and metadata changes
            if node_id is None:
                # Not a variable or section
                namespace = stack_item.page_label
            else:
                # A variable or section
                namespace = node.metadata.get('full_ns')
                if namespace is None:
                    namespace = stack_item.page_label
                config_name = self.util.split_full_ns(
                                        self.data, namespace)[0]
                node.process_metadata(
                     self.data.get_metadata_for_config_id(node_id,
                                                          config_name))
                if isinstance(node, rose.variable.Variable):
                    self.data.load_ns_for_variable(node, config_name)
                    namespace = node.metadata.get('full_ns')
                else:
                    namespace = self.data.get_default_namespace_for_section(
                                                      node_id, config_name)
            if self.data.is_ns_in_tree(namespace):
                page = self.view_page(namespace, node_id)
            redo_items = [x for x in self.redo_stack]
            if stack_item.undo_args:
                args = list(stack_item.undo_args)
                for i, arg_item in enumerate(args):
                    if arg_item == stack_item.page_label:
                        # Then it is a namespace argument & should be changed.
                        args[i] = namespace
                stack_item.undo_func(*args)
            else:
                stack_item.undo_func()
            del self.redo_stack[:]
            for redo_item in redo_items:
                self.redo_stack.append(redo_item)
            just_done_item = self.undo_stack[-1]
            del self.undo_stack[-1]
            del stack[-1]
            if redo_mode_on:
                self.undo_stack.append(just_done_item)
            else:
                self.redo_stack.append(just_done_item)
            if not self.data.is_ns_in_tree(namespace):
                self.data.reload_namespace_tree()
            if self.data.is_ns_in_tree(namespace):
                page = self.view_page(namespace, node_id)
            else:
                page = None
            if page is not None:
                self.sync_page_var_lists(page)
                page.sort_data()
                page.refresh(node_id)
                page.update_ignored()
                page.update_info()
                page.set_main_focus(node_id)
                self.set_current_page_indicator(page.namespace)
                if namespace != stack_item.page_label:
                    # Make sure the right status update is made.
                    self.update_status(page)
            self.alter_bar_sensitivity()
            self.update_stack_viewer_if_open()
        return True

# ----------------------- System functions -----------------------------------

def spawn_window(config_directory_path=None):
    """Create a window and load the configuration into it. Run gtk."""
    RESOURCER = rose.resource.ResourceLocator(paths=sys.path)
    rose.gtk.util.rc_setup(
         RESOURCER.locate('etc/rose-config-edit/.gtkrc-2.0'))
    rose.gtk.util.setup_stock_icons()
    logo = RESOURCER.locate("etc/images/rose-splash-logo.png")
    number_of_events = (get_number_of_configs(config_directory_path) *
                        rose.config_editor.LOAD_NUMBER_OF_EVENTS + 1)
    if config_directory_path is None:
        title = rose.config_editor.UNTITLED_NAME
    else:
        title = config_directory_path.split("/")[-1]
    splash_screen = rose.gtk.util.SplashScreen(logo, title, number_of_events)
    MainController(config_directory_path, loader_update=splash_screen.update)
    gtk.settings_get_default().set_long_property("gtk-button-images",
                                                 True, "main")
    gtk.settings_get_default().set_long_property("gtk-menu-images",
                                                 True, "main")
    gtk.main()


def spawn_subprocess_window(config_directory_path=None):
    """Launch a subprocess for a new config editor. Is it safe?"""
    if config_directory_path is None:
        os.system(rose.config_editor.LAUNCH_COMMAND + ' --new &')
        return
    elif not os.path.isdir(str(config_directory_path)):
        return
    os.system(rose.config_editor.LAUNCH_COMMAND_CONFIG +
              config_directory_path + " &")


def get_number_of_configs(config_directory_path=None):
    """Return the number of configurations that will be loaded."""
    number_to_load = 0
    if config_directory_path is not None:
        number_to_load = 1
        info_file = os.path.join(config_directory_path, rose.INFO_CONFIG_NAME)
        if os.path.exists(info_file):
            number_to_load += 1
        app_dir = os.path.join(config_directory_path, rose.SUB_CONFIGS_DIR)
        if os.path.exists(app_dir):
            for entry in os.listdir(app_dir):
                if (os.path.isdir(os.path.join(app_dir, entry)) and
                    not entry.startswith('.')):
                    number_to_load += 1
    return number_to_load


def load_site_config_path():
    """Load any metadata path specified in a user or site configuration."""
    conf = rose.resource.ResourceLocator.default().get_conf()
    path = conf.get_value([rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_META_PATH])
    if path is not None:
        sys.path.insert(0, path)


if __name__ == '__main__':
    if (gtk.pygtk_version[0] < rose.config_editor.MIN_PYGTK_VERSION[0]
        or gtk.pygtk_version[1] < rose.config_editor.MIN_PYGTK_VERSION[1]):
        this_version = '{0}.{1}.{2}'.format(*gtk.pygtk_version)
        required_version = '{0}.{1}.{2}'.format(
                                        *rose.config_editor.MIN_PYGTK_VERSION)
        rose.gtk.util.run_dialog(
                 rose.gtk.util.DIALOG_TYPE_ERROR,
                 rose.config_editor.ERROR_MIN_PYGTK_VERSION.format(
                                    required_version, this_version),
                 rose.config_editor.ERROR_MIN_PYGTK_VERSION_TITLE)
        sys.exit(1)
    sys.path.append(os.getenv('ROSE_HOME'))
    opt_parser = rose.opt_parse.RoseOptionParser()
    opt_parser.add_my_options("conf_dir", "meta_path", "new_mode")
    opts, args = opt_parser.parse_args()
    if args:
        opt_parser.print_usage(sys.stderr)
        sys.exit(2)
    load_site_config_path()
    if opts.meta_path is not None:
        opts.meta_path.reverse()
        for child_paths in [arg.split(":") for arg in opts.meta_path]:
            child_paths.reverse()
            for path in child_paths:
                sys.path.insert(0, os.path.abspath(path))
    if opts.conf_dir:
        os.chdir(opts.conf_dir)
    path = os.getcwd()
    name_set = set([rose.SUB_CONFIG_NAME, rose.TOP_CONFIG_NAME])
    while True:
        if set(os.listdir(path)) & name_set:
            break
        path = os.path.dirname(path)
        if path == os.path.dirname(path):
            # We don't support suites located at the root!
            break
    if path != os.getcwd() and path != os.path.dirname(path):
        os.chdir(path)
    cwd = os.getcwd()
    if opts.new_mode:
        cwd = None
    rose.gtk.util.set_exception_hook(keep_alive=True)
    spawn_window(cwd)
