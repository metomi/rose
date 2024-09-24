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
"""
This module contains the core processing of the config editor.

Classes:
    MainController - driver for loading and central coordination.

"""
import cProfile
import os
import pstats
import re
import shutil
import sre_constants
import sys
import tempfile
import warnings

from functools import cmp_to_key

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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import metomi.rose.config
import metomi.rose.config_editor
import metomi.rose.config_editor.data
import metomi.rose.config_editor.menu
import metomi.rose.config_editor.nav_controller
import metomi.rose.config_editor.nav_panel
import metomi.rose.config_editor.nav_panel_menu
import metomi.rose.config_editor.ops.group
import metomi.rose.config_editor.ops.section
import metomi.rose.config_editor.ops.variable
import metomi.rose.config_editor.page
import metomi.rose.config_editor.stack
import metomi.rose.config_editor.status
import metomi.rose.config_editor.updater
import metomi.rose.config_editor.util
import metomi.rose.config_editor.variable
import metomi.rose.config_editor.window
import metomi.rose.gtk.dialog
import metomi.rose.gtk.splash
import metomi.rose.gtk.util
import metomi.rose.macro
import metomi.rose.opt_parse
import metomi.rose.resource
import metomi.rose.macros


class MainController(object):

    """The main controller class.

    Call with a configuration directory and/or a dict of
    configuration names and objects.

    pluggable is a boolean that if True, returns containers for
    plugging into other GTK applications. If pluggable is False,
    launch the standalone application.

    load_updater is a metomi.rose.gtk.splash.SplashScreenProcess instance or
    None, in which case it will be set to a
    metomi.rose.gtk.splash.NullSplashScreenProcess.

    load_all_apps is a boolean that overrides the load-on-demand
    automation to always load all sub configurations at start time.

    load_no_apps is a boolean that overrides the load-on-demand
    automation to always skip loading sub configurations at start time.

    metadata_off is a boolean that controls whether the suite or app
    should load with metadata on or off.

    """

    RE_ARRAY_ELEMENT = re.compile(r'\([\d:, ]+\)$')

    def __init__(self, config_directory=None, config_objs=None,
                 config_obj_types=None, pluggable=False, load_updater=None,
                 load_all_apps=False, load_no_apps=False, metadata_off=False,
                 opt_meta_paths=None, no_warn=None):
        if config_objs is None:
            config_objs = {}
        if pluggable:
            metomi.rose.macro.add_meta_paths()
        if load_updater is None:
            load_updater = metomi.rose.gtk.splash.NullSplashScreenProcess()
        self.is_pluggable = pluggable
        self.tab_windows = []  # No child windows yet
        self.orphan_pages = []
        self.undo_stack = []  # Nothing to undo yet
        self.redo_stack = []  # Nothing to redo yet
        self.find_hist = {'regex': '', 'ids': []}
        self.util = metomi.rose.config_editor.util.Lookup()
        self.metadata_off = metadata_off
        if opt_meta_paths is None:
            opt_meta_paths = []

        # Set page variable 'verbosity' defaults.
        self.page_var_show_modes = {
            metomi.rose.config_editor.SHOW_MODE_CUSTOM_DESCRIPTION:
            metomi.rose.config_editor.SHOULD_SHOW_CUSTOM_DESCRIPTION,
            metomi.rose.config_editor.SHOW_MODE_CUSTOM_HELP:
            metomi.rose.config_editor.SHOULD_SHOW_CUSTOM_HELP,
            metomi.rose.config_editor.SHOW_MODE_CUSTOM_TITLE:
            metomi.rose.config_editor.SHOULD_SHOW_CUSTOM_TITLE,
            metomi.rose.config_editor.SHOW_MODE_FIXED:
            metomi.rose.config_editor.SHOULD_SHOW_FIXED_VARS,
            metomi.rose.config_editor.SHOW_MODE_FLAG_OPTIONAL:
            metomi.rose.config_editor.SHOULD_SHOW_FLAG_OPTIONAL_VARS,
            metomi.rose.config_editor.SHOW_MODE_FLAG_OPT_CONF:
            metomi.rose.config_editor.SHOULD_SHOW_FLAG_OPT_CONF_VARS,
            metomi.rose.config_editor.SHOW_MODE_FLAG_NO_META:
            metomi.rose.config_editor.SHOULD_SHOW_FLAG_NO_META_VARS,
            metomi.rose.config_editor.SHOW_MODE_IGNORED:
            metomi.rose.config_editor.SHOULD_SHOW_IGNORED_VARS,
            metomi.rose.config_editor.SHOW_MODE_USER_IGNORED:
            metomi.rose.config_editor.SHOULD_SHOW_USER_IGNORED_VARS,
            metomi.rose.config_editor.SHOW_MODE_LATENT:
            metomi.rose.config_editor.SHOULD_SHOW_LATENT_VARS,
            metomi.rose.config_editor.SHOW_MODE_NO_DESCRIPTION:
            metomi.rose.config_editor.SHOULD_SHOW_NO_DESCRIPTION,
            metomi.rose.config_editor.SHOW_MODE_NO_HELP:
            metomi.rose.config_editor.SHOULD_SHOW_NO_HELP,
            metomi.rose.config_editor.SHOW_MODE_NO_TITLE:
            metomi.rose.config_editor.SHOULD_SHOW_NO_TITLE
        }

        # Set page tree 'verbosity' defaults.
        self.page_ns_show_modes = {
            metomi.rose.config_editor.SHOW_MODE_IGNORED:
            metomi.rose.config_editor.SHOULD_SHOW_IGNORED_PAGES,
            metomi.rose.config_editor.SHOW_MODE_USER_IGNORED:
            metomi.rose.config_editor.SHOULD_SHOW_USER_IGNORED_PAGES,
            metomi.rose.config_editor.SHOW_MODE_LATENT:
            metomi.rose.config_editor.SHOULD_SHOW_LATENT_PAGES,
            metomi.rose.config_editor.SHOW_MODE_NO_TITLE:
            metomi.rose.config_editor.SHOULD_SHOW_NO_TITLE
        }

        self.reporter = metomi.rose.config_editor.status.StatusReporter(
            load_updater,
            self.update_status_text
        )

        # Load the top configuration directory
        self.data = metomi.rose.config_editor.data.ConfigDataManager(
            self.util,
            self.reporter,
            self.page_ns_show_modes,
            self.reload_namespace_tree,
            opt_meta_paths=opt_meta_paths,
            no_warn=no_warn
        )

        self.nav_controller = (
            metomi.rose.config_editor.nav_controller.NavTreeManager(
                self.data,
                self.util,
                self.reporter,
                self.tree_trigger_update
            ))

        self.mainwindow = metomi.rose.config_editor.window.MainWindow()

        self.section_ops = metomi.rose.config_editor.ops.section.SectionOperations(
            self.data, self.util, self.reporter,
            self.undo_stack, self.redo_stack,
            self.check_cannot_enable_setting,
            self.update_namespace,
            self.update_namespace_sub_data,
            self.update_ns_info,
            update_tree_func=self.reload_namespace_tree,
            view_page_func=self.view_page,
            kill_page_func=self.kill_page
        )

        self.variable_ops = (
            metomi.rose.config_editor.ops.variable.VariableOperations(
                self.data, self.util, self.reporter,
                self.undo_stack, self.redo_stack,
                self.section_ops.add_section,
                self.check_cannot_enable_setting,
                self.update_namespace,
                search_id_func=self.perform_find_by_id
            ))

        self.group_ops = metomi.rose.config_editor.ops.group.GroupOperations(
            self.data, self.util, self.reporter,
            self.undo_stack, self.redo_stack,
            self.section_ops,
            self.variable_ops,
            self.view_page,
            self.update_ns_sub_data,
            self.reload_namespace_tree
        )

        # Add in the main menu bar and tool bar handler.
        self.main_handle = metomi.rose.config_editor.menu.MainMenuHandler(
            self.data, self.util, self.reporter,
            self.mainwindow,
            self.undo_stack, self.redo_stack,
            self.perform_undo,
            self.update_config,
            self.apply_macro_transform,
            self.apply_macro_validation,
            self.group_ops,
            self.section_ops,
            self.variable_ops,
            self.perform_find_by_ns_id
        )

        # Add in the navigation panel menu handler.
        self.nav_handle = metomi.rose.config_editor.nav_panel_menu.NavPanelHandler(
            self.data, self.util, self.reporter,
            self.mainwindow,
            self.undo_stack, self.redo_stack,
            self._add_config,
            self.group_ops,
            self.section_ops,
            self.variable_ops,
            self.kill_page,
            self.reload_namespace_tree,
            self.main_handle.transform_default,
            self.main_handle.launch_graph
        )

        self.updater = metomi.rose.config_editor.updater.Updater(
            self.data, self.util, self.reporter,
            self.mainwindow, self.main_handle,
            self.nav_controller,
            self._get_pagelist,
            self.update_bar_widgets,
            self._refresh_metadata_if_on,
            self.is_pluggable
        )

        self.data.load(config_directory, config_objs,
                       config_obj_type_dict=config_obj_types,
                       load_all_apps=load_all_apps,
                       load_no_apps=load_no_apps)
        self.reporter.report_load_event(
            metomi.rose.config_editor.EVENT_LOAD_STATUSES.format(
                self.data.top_level_name)
        )
        if not self.is_pluggable:
            self.generate_toolbar()
            self.generate_menubar()
            self.generate_nav_panel()
            self.generate_status_bar()
            # Create notebook (tabbed container) and connect signals.
            self.notebook = metomi.rose.gtk.util.Notebook()
        self.updater.nav_panel = getattr(self, "nav_panel", None)
        # Create the main panel with the menu, toolbar, tree panel, notebook.
        if not self.is_pluggable:
            self.mainwindow.load(name=self.data.top_level_name,
                                 menu=self.top_menu,
                                 accelerators=self.menubar.accelerators,
                                 toolbar=self.toolbar,
                                 nav_panel=self.nav_panel,
                                 status_bar=self.status_bar,
                                 notebook=self.notebook,
                                 page_change_func=self.handle_page_change,
                                 save_func=self.save_to_file)
            self.mainwindow.window.connect('destroy', self.main_handle.destroy)
            self.mainwindow.window.connect('delete-event',
                                           self.main_handle.destroy)
            self.mainwindow.window.connect_after('grab_focus',
                                                 self.handle_page_change)
            self.mainwindow.window.connect_after('focus-in-event',
                                                 self.handle_page_change)
        self.updater.update_all(is_loading=True)
        self.reporter.report_load_event(
            metomi.rose.config_editor.EVENT_LOAD_ERRORS.format(
                self.data.top_level_name,
                self.updater.load_errors
            ))
        self.updater.perform_startup_check()
        self.reporter.report_load_event(
            metomi.rose.config_editor.EVENT_LOAD_DONE.format(
                self.data.top_level_name
            ))
        if (self.data.top_level_directory is None and not self.data.config):
            self.load_from_file()

        self.update_bar_widgets()

        self.performing_undo = False

# ----------------- Setting up main component functions ----------------------

    def generate_toolbar(self):
        """Link in the toolbar functionality."""
        self.toolbar = metomi.rose.gtk.util.ToolBar(
            widgets=[
                (metomi.rose.config_editor.TOOLBAR_OPEN, 'Gtk.STOCK_OPEN'),
                (metomi.rose.config_editor.TOOLBAR_SAVE, 'Gtk.STOCK_SAVE'),
                (metomi.rose.config_editor.TOOLBAR_CHECK_AND_SAVE,
                 'Gtk.STOCK_SPELL_CHECK'),
                (metomi.rose.config_editor.TOOLBAR_LOAD_APPS, 'Gtk.STOCK_CDROM'),
                (metomi.rose.config_editor.TOOLBAR_BROWSE, 'Gtk.STOCK_DIRECTORY'),
                (metomi.rose.config_editor.TOOLBAR_UNDO, 'Gtk.STOCK_UNDO'),
                (metomi.rose.config_editor.TOOLBAR_REDO, 'Gtk.STOCK_REDO'),
                (metomi.rose.config_editor.TOOLBAR_ADD, 'Gtk.STOCK_ADD'),
                (metomi.rose.config_editor.TOOLBAR_REVERT,
                 'Gtk.STOCK_REVERT_TO_SAVED'),
                (metomi.rose.config_editor.TOOLBAR_FIND, 'Gtk.SearchEntry'),
                (metomi.rose.config_editor.TOOLBAR_FIND_NEXT, 'Gtk.STOCK_FIND'),
                (metomi.rose.config_editor.TOOLBAR_VALIDATE,
                 "dialog-question"),
                (metomi.rose.config_editor.TOOLBAR_TRANSFORM,
                 'Gtk.STOCK_CONVERT'),
            ],
            sep_on_name=[
                metomi.rose.config_editor.TOOLBAR_CHECK_AND_SAVE,
                metomi.rose.config_editor.TOOLBAR_BROWSE,
                metomi.rose.config_editor.TOOLBAR_REDO,
                metomi.rose.config_editor.TOOLBAR_REVERT,
                metomi.rose.config_editor.TOOLBAR_FIND_NEXT,
                metomi.rose.config_editor.TOOLBAR_TRANSFORM
            ]
        )
        assign = self.toolbar.set_widget_function
        assign(metomi.rose.config_editor.TOOLBAR_OPEN, self.load_from_file)
        assign(metomi.rose.config_editor.TOOLBAR_SAVE, self.save_to_file)
        assign(metomi.rose.config_editor.TOOLBAR_CHECK_AND_SAVE, self.save_to_file,
               [None, True])
        assign(metomi.rose.config_editor.TOOLBAR_LOAD_APPS, self.handle_load_all)
        assign(metomi.rose.config_editor.TOOLBAR_BROWSE,
               self.main_handle.launch_browser)
        assign(metomi.rose.config_editor.TOOLBAR_UNDO, self.perform_undo)
        assign(metomi.rose.config_editor.TOOLBAR_REDO, self.perform_undo, [True])
        assign(metomi.rose.config_editor.TOOLBAR_REVERT, self.revert_to_saved_data)
        assign(metomi.rose.config_editor.TOOLBAR_FIND_NEXT, self._launch_find)
        assign(metomi.rose.config_editor.TOOLBAR_VALIDATE,
               self.main_handle.check_all_extra)
        assign(metomi.rose.config_editor.TOOLBAR_TRANSFORM,
               self.main_handle.transform_default)
        self.find_entry = self.toolbar.item_dict.get(
            metomi.rose.config_editor.TOOLBAR_FIND)['widget']
        self.find_entry.connect("activate", self._launch_find)
        self.find_entry.connect("changed", self._clear_find)
        Gtk.Entry.set_placeholder_text(self.find_entry, "Search")
        add_icon = self.toolbar.item_dict.get(
            metomi.rose.config_editor.TOOLBAR_ADD)['widget']
        add_icon.connect('button_press_event', self.add_page_variable)

    def generate_menubar(self):
        """Link in the menu functionality and accelerators."""
        self.menubar = metomi.rose.config_editor.menu.MenuBar()
        self.menu_widgets = {}
        menu_list = [
            ('/TopMenuBar/File/Open...', self.load_from_file),
            ('/TopMenuBar/File/Save', lambda m: self.save_to_file()),
            ('/TopMenuBar/File/Check and save',
             lambda m: self.save_to_file(check_on_save=True)),
            ('/TopMenuBar/File/Load All Apps',
             lambda m: self.handle_load_all()),
            ('/TopMenuBar/File/Quit', self.main_handle.destroy),
            ('/TopMenuBar/Edit/Undo',
             lambda m: self.perform_undo()),
            ('/TopMenuBar/Edit/Redo',
             lambda m: self.perform_undo(redo_mode_on=True)),
            ('/TopMenuBar/Edit/Find', self._launch_find),
            ('/TopMenuBar/Edit/Find Next',
             lambda m: self.perform_find(self.find_hist['regex'])),
            ('/TopMenuBar/Edit/Preferences', self.main_handle.prefs),
            ('/TopMenuBar/Edit/Stack', self.main_handle.view_stack),
            ('/TopMenuBar/View/View fixed vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_FIXED,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View ignored vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_IGNORED,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View user-ignored vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_USER_IGNORED,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View latent vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_LATENT,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View ignored pages',
             lambda m: self._set_page_ns_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_IGNORED,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View user-ignored pages',
             lambda m: self._set_page_ns_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_USER_IGNORED,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View latent pages',
             lambda m: self._set_page_ns_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_LATENT,
                 m.get_active()
             )),
            ('/TopMenuBar/View/Flag no-metadata vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_FLAG_NO_META,
                 m.get_active()
             )),
            ('/TopMenuBar/View/Flag opt config vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_FLAG_OPT_CONF,
                 m.get_active()
             )),
            ('/TopMenuBar/View/Flag optional vars',
             lambda m: self._set_page_var_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_FLAG_OPTIONAL,
                 m.get_active()
             )),
            ('/TopMenuBar/View/View status bar',
             lambda m: self._set_show_status_bar(m.get_active())),
            ('/TopMenuBar/Metadata/Prefs/View without descriptions',
             lambda m: self._set_page_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_NO_DESCRIPTION,
                 m.get_active()
             )),
            ('/TopMenuBar/Metadata/Prefs/View without help',
             lambda m: self._set_page_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_NO_HELP,
                 m.get_active()
             )),
            ('/TopMenuBar/Metadata/Prefs/View without titles',
             lambda m: self._set_page_show_modes(
                 metomi.rose.config_editor.SHOW_MODE_NO_TITLE,
                 m.get_active()
             )),
            ('/TopMenuBar/Metadata/All V',
             lambda m: self.main_handle.handle_run_custom_macro(
                 method_name=metomi.rose.macro.VALIDATE_METHOD
             )),
            ('/TopMenuBar/Metadata/Autofix',
             lambda m: self.main_handle.transform_default()),
            ('/TopMenuBar/Metadata/Extra checks',
             lambda m: self.main_handle.check_fail_rules()),
            ('/TopMenuBar/Metadata/Graph',
             lambda m: self.main_handle.handle_graph()),
            ('/TopMenuBar/Metadata/Reload metadata',
             lambda m: self._refresh_metadata_if_on()),
            ('/TopMenuBar/Metadata/Load custom metadata',
             lambda m: self.load_custom_metadata()),
            ('/TopMenuBar/Metadata/Switch off metadata',
             lambda m: self.refresh_metadata(m.get_active())),
            ('/TopMenuBar/Metadata/Upgrade',
             lambda m: self.main_handle.handle_upgrade()),
            ('/TopMenuBar/Tools/Browser',
             lambda m: self.main_handle.launch_browser()),
            ('/TopMenuBar/Tools/Terminal',
             lambda m: self.main_handle.launch_terminal()),
            ('/TopMenuBar/Page/Revert',
             lambda m: self.revert_to_saved_data()),
            ('/TopMenuBar/Page/Page Info',
             lambda m: self.nav_handle.info_request(
                 self._get_current_page().namespace
             )),
            ('/TopMenuBar/Page/Page Help',
             lambda m: self._get_current_page().launch_help()),
            ('/TopMenuBar/Page/Page Web Help',
             lambda m: self._get_current_page().launch_url()),
            ('/TopMenuBar/Help/Documentation', self.main_handle.help),
            ('/TopMenuBar/Help/About', self.main_handle.about_dialog)
        ]
        is_toggled = dict(
            [('/TopMenuBar/View/View fixed vars',
              metomi.rose.config_editor.SHOULD_SHOW_FIXED_VARS),
             ('/TopMenuBar/View/View ignored vars',
              metomi.rose.config_editor.SHOULD_SHOW_IGNORED_VARS),
             ('/TopMenuBar/View/View user-ignored vars',
              metomi.rose.config_editor.SHOULD_SHOW_USER_IGNORED_VARS),
             ('/TopMenuBar/View/View latent vars',
              metomi.rose.config_editor.SHOULD_SHOW_LATENT_VARS),
             ('/TopMenuBar/Metadata/Prefs/View without descriptions',
              metomi.rose.config_editor.SHOULD_SHOW_NO_DESCRIPTION),
             ('/TopMenuBar/Metadata/Prefs/View without help',
              metomi.rose.config_editor.SHOULD_SHOW_NO_HELP),
             ('/TopMenuBar/Metadata/Prefs/View without titles',
              metomi.rose.config_editor.SHOULD_SHOW_NO_TITLE),
             ('/TopMenuBar/View/View ignored pages',
              metomi.rose.config_editor.SHOULD_SHOW_IGNORED_PAGES),
             ('/TopMenuBar/View/View user-ignored pages',
              metomi.rose.config_editor.SHOULD_SHOW_USER_IGNORED_PAGES),
             ('/TopMenuBar/View/View latent pages',
              metomi.rose.config_editor.SHOULD_SHOW_LATENT_PAGES),
             ('/TopMenuBar/View/Flag opt config vars',
              metomi.rose.config_editor.SHOULD_SHOW_FLAG_OPT_CONF_VARS),
             ('/TopMenuBar/View/Flag optional vars',
              metomi.rose.config_editor.SHOULD_SHOW_FLAG_OPTIONAL_VARS),
             ('/TopMenuBar/View/Flag no-metadata vars',
              metomi.rose.config_editor.SHOULD_SHOW_FLAG_NO_META_VARS),
             ('/TopMenuBar/View/View status bar',
              metomi.rose.config_editor.SHOULD_SHOW_STATUS_BAR),
             ('/TopMenuBar/Metadata/Switch off metadata',
              self.metadata_off)]
        )
        for (address, action) in menu_list:
            widget = self.menubar.uimanager.get_widget(address)
            self.menu_widgets.update({address: widget})
            if address in is_toggled:
                widget.set_active(is_toggled[address])
                if (address.endswith("View user-ignored pages") and
                        metomi.rose.config_editor.SHOULD_SHOW_IGNORED_PAGES):
                    widget.set_sensitive(False)
                if (address.endswith("View user-ignored vars") and
                        metomi.rose.config_editor.SHOULD_SHOW_IGNORED_VARS):
                    widget.set_sensitive(False)
            if address.endswith("Reload metadata") and self.metadata_off:
                widget.set_sensitive(False)
            widget.connect('activate', action)
        page_menu = self.menubar.uimanager.get_widget("/TopMenuBar/Page")
        add_menuitem = self.menubar.uimanager.get_widget(
            "/TopMenuBar/Page/Add variable")
        page_menu.connect(
            "activate",
            lambda m: self.main_handle.load_page_menu(
                self.menubar,
                add_menuitem,
                self._get_current_page()
            ))
        page_menu.get_submenu().connect(
            "deactivate",
            lambda m: self.main_handle.clear_page_menu(
                self.menubar,
                add_menuitem
            ))
        self.main_handle.load_macro_menu(self.menubar)
        self.update_bar_widgets()
        self.top_menu = self.menubar.uimanager.get_widget('/TopMenuBar')
        # Load the keyboard accelerators.
        accel = {
            metomi.rose.config_editor.ACCEL_UNDO:
            self.perform_undo,
            metomi.rose.config_editor.ACCEL_REDO:
            lambda: self.perform_undo(redo_mode_on=True),
            metomi.rose.config_editor.ACCEL_FIND:
            self.find_entry.grab_focus,
            metomi.rose.config_editor.ACCEL_FIND_NEXT:
            lambda: self.perform_find(self.find_hist['regex']),
            metomi.rose.config_editor.ACCEL_HELP_GUI:
            self.main_handle.help,
            metomi.rose.config_editor.ACCEL_OPEN:
            self.load_from_file,
            metomi.rose.config_editor.ACCEL_SAVE:
            self.save_to_file,
            metomi.rose.config_editor.ACCEL_QUIT:
            self.main_handle.destroy,
            metomi.rose.config_editor.ACCEL_METADATA_REFRESH:
            self._refresh_metadata_if_on,
            metomi.rose.config_editor.ACCEL_BROWSER:
            self.main_handle.launch_browser,
            metomi.rose.config_editor.ACCEL_TERMINAL:
            self.main_handle.launch_terminal,
        }
        self.menubar.set_accelerators(accel)

    def generate_nav_panel(self):
        """"Create tree panel and link functions."""
        self.nav_panel = metomi.rose.config_editor.nav_panel.PageNavigationPanel(
            self.nav_controller.namespace_tree,
            self.handle_launch_request,
            self.nav_handle.get_ns_metadata_and_comments,
            self.nav_handle.popup_panel_menu,
            self.nav_handle.get_can_show_page,
            self.nav_handle.ask_is_preview
        )

    def generate_status_bar(self):
        """Create a status bar."""
        self.status_bar = metomi.rose.config_editor.status.StatusBar(
            verbosity=metomi.rose.config_editor.STATUS_BAR_VERBOSITY)
        self._set_show_status_bar(metomi.rose.config_editor.SHOULD_SHOW_STATUS_BAR)

# ----------------- Page manipulation functions ------------------------------

    def handle_load_all(self, *args):
        """Handle a request to load all preview configurations."""
        load_these = []
        for item in list(self.data.config.keys()):
            if self.data.config[item].is_preview:
                load_these.append(item)
        load_these.sort()
        number_of_events = (len(load_these) *
                            metomi.rose.config_editor.LOAD_NUMBER_OF_EVENTS + 2)
        self.reporter.report_load_event(
            "Loading all preview apps",
            new_total_events=number_of_events
        )
        for namespace_name in load_these:
            config_data = self.data.config[namespace_name]
            self.data.load_config(config_data.directory, preview=False,
                                  metadata_off=self.metadata_off)
            self.reporter.report_load_event(
                metomi.rose.config_editor.EVENT_LOADED.format(namespace_name[1:]),
                no_progress=True
            )
        self.reload_namespace_tree()
        self.reporter.stop()
        self.nav_panel.update_row_tooltips()
        if hasattr(self, 'menubar'):
            self.main_handle.load_macro_menu(self.menubar)
        self.update_bar_widgets()
        self.updater.perform_startup_check()
        return

    def handle_launch_request(self, namespace_name, as_new=False):
        """Handle a request to create a page.

        It normally returns a page containing all variables associated with
        the namespace namespace_name, but it won't create a page if it is
        already open. It will overwrite the existing current page, if any,
        in the internal notebook, unless as_new is True.

        """
        if not namespace_name.startswith('/'):
            namespace_name = '/' + namespace_name

        config_name = self.util.split_full_ns(self.data, namespace_name)[0]
        config_data = self.data.config[config_name]

        if config_data.is_preview:
            self.reporter.report_load_event(
                metomi.rose.config_editor.EVENT_LOAD_ATTEMPT.format(
                    namespace_name),
                new_total_events=3)
            self.data.load_config(config_data.directory, preview=False,
                                  metadata_off=self.metadata_off)
            self.reload_namespace_tree()
            self.nav_panel.update_row_tooltips()
            self.reporter.report_load_event(
                metomi.rose.config_editor.EVENT_LOADED.format(namespace_name),
                no_progress=True)
            self.reporter.stop()
            if hasattr(self, 'menubar'):
                self.main_handle.load_macro_menu(self.menubar)
            self.update_bar_widgets()
            self.updater.perform_startup_check()

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
            index = self.notebook.get_current_page()
            self.notebook.insert_page(page, page.labelwidget, index)
            self.notebook.set_current_page(index)
            if index != -1:
                self.notebook.remove_page(index + 1)
        self.notebook.set_tab_label_packing(page, page.labelwidget)

    def make_page(self, namespace_name):
        """Look up page data and attributes and call a page constructor."""
        config_name, subspace = self.util.split_full_ns(self.data,
                                                        namespace_name)
        data, latent_data = self.data.helper.get_data_for_namespace(
            namespace_name)
        config_data = self.data.config[config_name]
        ns_metadata = self.data.namespace_meta_lookup.get(namespace_name, {})
        description = ns_metadata.get(metomi.rose.META_PROP_DESCRIPTION, '')
        duplicate = ns_metadata.get(metomi.rose.META_PROP_DUPLICATE)
        help_ = ns_metadata.get(metomi.rose.META_PROP_HELP)
        url = ns_metadata.get(metomi.rose.META_PROP_URL)
        custom_widget = ns_metadata.get(metomi.rose.config_editor.META_PROP_WIDGET)
        custom_sub_widget = ns_metadata.get(
            metomi.rose.config_editor.META_PROP_WIDGET_SUB_NS)
        has_sub_data = self.data.helper.is_ns_sub_data(namespace_name)
        label = ns_metadata.get(metomi.rose.META_PROP_TITLE)
        if label is None:
            label = subspace.split('/')[-1]
        if duplicate == metomi.rose.META_PROP_VALUE_TRUE and not has_sub_data:
            # For example, namelist/foo/1 should be shown as foo(1).
            label = "(".join(subspace.split('/')[-2:]) + ")"
        section_data_objects, latent_section_data_objects = (
            self.data.helper.get_section_data_for_namespace(namespace_name))
        # Related pages
        see_also = ''
        sections = [s for s in ns_metadata.get('sections', [])]
        for section_name in [s for s in sections if s.startswith('namelist')]:
            no_num_name = metomi.rose.macro.REC_ID_STRIP_DUPL.sub("", section_name)
            no_mod_name = metomi.rose.macro.REC_ID_STRIP.sub("", section_name)
            ok_names = [section_name, no_num_name + "(:)",
                        no_mod_name + "(:)"]
            if no_mod_name != no_num_name:
                # There's a modifier in the section name.
                ok_names.append(no_num_name)
            for section, variables in list(config_data.vars.now.items()):
                if not section.startswith(metomi.rose.SUB_CONFIG_FILE_DIR):
                    continue
                for variable in variables:
                    if variable.name != metomi.rose.FILE_VAR_SOURCE:
                        continue
                    var_values = metomi.rose.variable.array_split(variable.value)
                    for i, val in enumerate(var_values):
                        if val.startswith("(") and val.endswith(")"):
                            # It is optional - e.g. "(namelist:baz)".
                            var_values[i] = val[1:-1]
                    if set(ok_names) & set(var_values):
                        var_id = variable.metadata['id']
                        see_also += ", " + var_id
        see_also = see_also.replace(", ", "", 1)
        # Icon
        icon_path = self.data.helper.get_icon_path_for_config(config_name)
        is_default = self.data.helper.get_ns_is_default(namespace_name)
        sub_data = None
        sub_ops = None
        if has_sub_data:
            sub_data = self.data.helper.get_sub_data_for_namespace(
                namespace_name)
            sub_ops = self.group_ops.get_sub_ops_for_namespace(namespace_name)
        macro_info = self.data.helper.get_macro_info_for_namespace(
            namespace_name)
        page_metadata = {
            "namespace": namespace_name,
            "ns_is_default": is_default,
            "label": label,
            "description": description,
            "duplicate": duplicate,
            "help": help_,
            "url": url,
            "macro": macro_info,
            "widget": custom_widget,
            "widget_sub_ns": custom_sub_widget,
            "see_also": see_also,
            "config_name": config_name,
            "show_modes": self.page_var_show_modes,
            "icon": icon_path
        }
        if len(sections) == 1:
            page_metadata.update({"id": sections.pop()})
        sect_ops = metomi.rose.config_editor.ops.section.SectionOperations(
            self.data, self.util, self.reporter,
            self.undo_stack, self.redo_stack,
            self.check_cannot_enable_setting,
            self.updater.update_namespace,
            self.updater.update_ns_sub_data,
            self.updater.update_ns_info,
            update_tree_func=self.reload_namespace_tree,
            view_page_func=self.view_page,
            kill_page_func=self.kill_page
        )
        var_ops = metomi.rose.config_editor.ops.variable.VariableOperations(
            self.data, self.util, self.reporter,
            self.undo_stack, self.redo_stack,
            sect_ops.add_section,
            self.check_cannot_enable_setting,
            self.updater.update_namespace,
            search_id_func=self.perform_find_by_id
        )
        directory = None
        if namespace_name == config_name:
            directory = config_data.directory
        launch_info = lambda: self.nav_handle.info_request(
            namespace_name)
        launch_edit = lambda: self.nav_handle.edit_request(
            namespace_name)
        page = metomi.rose.config_editor.page.ConfigPage(
            page_metadata,
            data,
            latent_data,
            sect_ops,
            var_ops,
            section_data_objects,
            latent_section_data_objects,
            self.data.helper.get_format_sections,
            self.reporter,
            directory,
            sub_data=sub_data,
            sub_ops=sub_ops,
            launch_info_func=launch_info,
            launch_edit_func=launch_edit,
            launch_macro_func=self.main_handle.handle_run_custom_macro
        )
        # FIXME: These three should go.
        page.trigger_tab_detach = lambda b: self._handle_detach_request(page)
        var_ops.trigger_ignored_update = lambda v: page.update_ignored()
        page.trigger_update_status = lambda: self.updater.update_status(page)
        return page

    def get_orphan_page(self, namespace):
        """Return a page widget for embedding somewhere else."""
        page = self.make_page(namespace)
        orphan_container = self.main_handle.get_orphan_container(page)
        self.orphan_pages.append(page)
        return orphan_container

    def _handle_detach_request(self, page, old_window=None):
        """Open tab (or 'page') in a window and manage close page events."""
        if old_window is None:
            tab_window = Gtk.Window()
            tab_window.set_icon(self.mainwindow.window.get_icon())
            tab_window.add_accel_group(self.menubar.accelerators)
            tab_window.set_default_size(*metomi.rose.config_editor.SIZE_PAGE_DETACH)
            tab_window.connect('destroy-event', lambda w, e:
                               self.tab_windows.remove(w) and False)
            tab_window.connect('delete-event', lambda w, e:
                               self.tab_windows.remove(w) and False)
        else:
            tab_window = old_window
        add_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_ADD,
            tip_text=metomi.rose.config_editor.TIP_ADD_TO_PAGE,
            size=Gtk.IconSize.LARGE_TOOLBAR,
            as_tool=True
        )
        revert_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_REVERT_TO_SAVED,
            tip_text=metomi.rose.config_editor.TIP_REVERT_PAGE,
            size=Gtk.IconSize.LARGE_TOOLBAR,
            as_tool=True
        )
        add_button.connect('button_press_event', self.add_page_variable)
        revert_button.connect('clicked',
                              lambda b: self.revert_to_saved_data())
        if old_window is None:
            parent = self.notebook
        else:
            parent = old_window
        page.reshuffle_for_detached(add_button, revert_button, parent)
        tab_window.set_title(' - '.join([page.label, self.data.top_level_name,
                                         metomi.rose.config_editor.PROGRAM_NAME]))
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
        self.update_page_bar_sensitivity(current_page)
        if current_page is None:
            self.nav_panel.select_row(None)
            return False
        self.set_current_page_indicator(current_page.namespace)
        return False

    def update_page_bar_sensitivity(self, current_page):
        """Update the top 'Page' menu and the toolbar."""
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
                metomi.rose.META_PROP_HELP in metadata)
            get_widget("/TopMenuBar/Page/Page Web Help").set_sensitive(
                metomi.rose.META_PROP_URL in metadata)

    def set_current_page_indicator(self, namespace):
        """Make sure the current page is highlighted in the nav panel."""
        if hasattr(self, 'nav_panel'):
            self.nav_panel.select_row(namespace.lstrip('/').split('/'))

    def add_page_variable(self, widget, event):
        """Launch an add menu based on page content."""
        page = self._get_current_page()
        if page is None:
            return False
        page.launch_add_menu(event)

    def revert_to_saved_data(self):
        """Reload the page data from saved configuration information."""
        page = self._get_current_page()
        if page is None:
            return
        namespace = page.namespace
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        self.data.load_node_namespaces(config_name, from_saved=True)
        config_data, ghost_data = self.data.helper.get_data_for_namespace(
            namespace, from_saved=True)
        page.reload_from_data(config_data, ghost_data)
        self.data.load_node_namespaces(config_name)
        self.updater.update_status(page)
        self.reporter.report(metomi.rose.config_editor.EVENT_REVERT.format(
            namespace.lstrip("/")))

    def _get_pagelist(self):
        """Load an attribute self.pagelist with a list of open pages."""
        self.pagelist = []
        if hasattr(self, 'notebook'):
            for index in range(self.notebook.get_n_pages()):
                if hasattr(self.notebook.get_nth_page(index), 'panel_data'):
                    self.pagelist.append(self.notebook.get_nth_page(index))
        if hasattr(self, 'tab_windows'):
            for window in self.tab_windows:
                if hasattr(window.get_child(), 'panel_data'):
                    self.pagelist.append(window.get_child())
        self.pagelist.extend(self.orphan_pages)
        return self.pagelist

    def _get_current_page(self):
        """Return the currently focused page."""
        self._get_pagelist()
        if not self.pagelist:
            return None
        for window in self.tab_windows:
            if window.has_toplevel_focus():
                return window.get_child()
        for page in self.orphan_pages:
            if page.get_toplevel().is_active():
                return page
        if hasattr(self, "notebook"):
            index = self.notebook.get_current_page()
            return self.notebook.get_nth_page(index)
        return None

    def _get_current_page_and_id(self):
        """Return the currently focused page and the variable id (if any)."""
        page = self._get_current_page()
        if page is None:
            return None, None
        return page, page.get_main_focus()

    def _set_show_status_bar(self, should_show_status_bar):
        """Set whether the status bar is shown or hidden."""
        if hasattr(self, "status_bar") and self.status_bar is not None:
            if should_show_status_bar:
                self.status_bar.show()
            else:
                self.status_bar.hide()

    def _set_page_show_modes(self, key, is_key_allowed):
        """Set generic variable/namespace view options."""
        self._set_page_var_show_modes(key, is_key_allowed)
        self._set_page_ns_show_modes(key, is_key_allowed)

    def _set_page_ns_show_modes(self, key, is_key_allowed):
        """Set namespace view options."""
        self.page_ns_show_modes[key] = is_key_allowed
        if (hasattr(self, "menubar") and
                key == metomi.rose.config_editor.SHOW_MODE_IGNORED):
            user_ign_item = self.menubar.uimanager.get_widget(
                "/TopMenuBar/View/View user-ignored pages")
            user_ign_item.set_sensitive(not is_key_allowed)

    def _set_page_var_show_modes(self, key, is_key_allowed):
        """Set variable widgets' view options."""
        self.page_var_show_modes[key] = is_key_allowed
        self._get_pagelist()
        for page in self.pagelist:
            page.react_to_show_modes(key, is_key_allowed)
        if (hasattr(self, "menubar") and
                key == metomi.rose.config_editor.SHOW_MODE_IGNORED):
            user_ign_item = self.menubar.uimanager.get_widget(
                "/TopMenuBar/View/View user-ignored vars")
            user_ign_item.set_sensitive(not is_key_allowed)

    def kill_page(self, namespace):
        """Destroy a page if it has the same namespace as the argument."""
        self._get_pagelist()
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

# ----------------- Update functions -----------------------------------------

    def reload_namespace_tree(self, *args, **kwargs):
        """Redraw the navigation namespace tree."""
        self.nav_controller.reload_namespace_tree(*args, **kwargs)

    def tree_trigger_update(self, *args, **kwargs):
        """Placeholder for updater function of the same name."""
        self.updater.tree_trigger_update(*args, **kwargs)

    def update_config(self, *args, **kwargs):
        """Placeholder for updater function of the same name."""
        self.updater.update_config(*args, **kwargs)

    def update_namespace(self, *args, **kwargs):
        """Placeholder for updater function of the same name."""
        self.updater.update_namespace(*args, **kwargs)

    def update_namespace_sub_data(self, *args, **kwargs):
        """Placeholder for updater function of the same name."""
        self.updater.update_ns_sub_data(*args, **kwargs)

    def update_ns_info(self, *args, **kwargs):
        """Placeholder for updater function of the same name."""
        self.updater.update_ns_info(*args, **kwargs)

    def update_ns_sub_data(self, *args, **kwargs):
        """Placeholder for updater function of the same name."""
        self.updater.update_ns_sub_data(*args, **kwargs)

# ----------------- Page viewer function -------------------------------------

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
        self._get_pagelist()
        if (page_id not in [p.namespace for p in self.pagelist]):
            self.handle_launch_request(page_id, as_new=True)
            index = self.notebook.get_current_page()
            page = self.notebook.get_nth_page(index)
        if page_id in self.notebook.get_page_ids():
            index = self.notebook.get_page_ids().index(page_id)
            page = self.notebook.get_nth_page(index)
            self.notebook.set_current_page(index)
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

# ----------------- Primary menu functions -----------------------------------

    def load_from_file(self, somewidget=None):
        """Open a standard dialogue and load a config file, if selected."""
        dirname = self.mainwindow.launch_open_dirname_dialog()
        if dirname is None or not os.path.isdir(dirname):
            return False
        if self.data.top_level_directory is None and not self.is_pluggable:
            self.data.load_top_config(dirname)
            self.data.saved_config_names = set(self.data.config.keys())
            self.mainwindow.window.set_title(self.data.top_level_name +
                                             ' - rose-config-editor')
            self.updater.update_all()
            self.updater.perform_startup_check()
        else:
            spawn_subprocess_window(dirname)

    def save_to_file(self, only_config_name=None, check_on_save=False):
        """Dump the component configurations in memory to disk."""
        if only_config_name is None:
            config_names = []
            for config_name in list(self.data.config.keys()):
                if not self.data.config[config_name].is_preview:
                    config_names.append(config_name)
        else:
            config_names = [only_config_name]
        save_ok = True
        if check_on_save:
            self.main_handle.check_all_extra()

        for config_name in sorted(config_names):
            short_config_name = config_name.lstrip("/")
            config = self.data.dump_to_internal_config(config_name)
            new_save_config = self.data.dump_to_internal_config(config_name)
            config_data = self.data.config[config_name]
            vars_ok = True
            for var in config_data.vars.get_all(skip_latent=True):
                if not var.name:
                    self.view_page(var.metadata["full_ns"],
                                   var.metadata["id"])
                    page_address = var.metadata["full_ns"].lstrip("/")
                    metomi.rose.gtk.dialog.run_dialog(
                        metomi.rose.gtk.dialog.DIALOG_TYPE_ERROR,
                        metomi.rose.config_editor.ERROR_SAVE_BLANK.format(
                            short_config_name,
                            page_address
                        ),
                        title=metomi.rose.config_editor.ERROR_SAVE_TITLE.format(
                            short_config_name),
                        modal=False
                    )
                    vars_ok = False
                    break
            if not vars_ok:
                save_ok = False
                continue
            directory = config_data.directory
            config_vars = config_data.vars
            config_sections = config_data.sections

            # Run check fail-if, warn-if and validator macros if check_on_save
            if check_on_save:
                errors = self.nav_panel.get_change_error_totals(
                    config_name=short_config_name)[1]
                if errors > 0:
                    dialog = Gtk.MessageDialog(
                        None,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        Gtk.MessageType.INFO,
                        Gtk.ButtonsType.YES_NO,
                        None
                    )
                    dialog.set_markup(
                        metomi.rose.config_editor.WARNING_ERRORS_FOUND_ON_SAVE.format(
                            short_config_name
                        ))
                    res = dialog.run()
                    dialog.destroy()
                    if res == Gtk.ResponseType.NO:
                        continue

            # Dump the configuration.
            filename = config_data.config_type
            if (directory is None and
                    config_data.config_type == metomi.rose.INFO_CONFIG_NAME):
                directory = self.data.top_level_directory
            save_path = os.path.join(directory, filename)
            metomi.rose.macro.pretty_format_config(config, ignore_error=True)
            try:
                metomi.rose.config.dump(config, save_path)
            except (OSError, IOError) as exc:
                metomi.rose.gtk.dialog.run_dialog(
                    metomi.rose.gtk.dialog.DIALOG_TYPE_ERROR,
                    metomi.rose.config_editor.ERROR_SAVE_PATH_FAIL.format(exc),
                    title=metomi.rose.config_editor.ERROR_SAVE_TITLE.format(
                        short_config_name),
                    modal=False
                )
                save_ok = False
                continue
            # Un-prettify.
            config = self.data.dump_to_internal_config(config_name)
            # Update the last save data.
            config_data.save_config = new_save_config
            config_vars.save.clear()
            config_vars.latent_save.clear()
            for section, variables in list(config_vars.now.items()):
                config_vars.save.update({section: []})
                for variable in variables:
                    config_vars.save[section].append(variable.copy())
            for section, variables in list(config_vars.latent.items()):
                config_vars.latent_save.update({section: []})
                for variable in variables:
                    config_vars.latent_save[section].append(variable.copy())
            config_sections.save.clear()
            config_sections.latent_save.clear()
            for section, data in list(config_sections.now.items()):
                config_sections.save.update({section: data.copy()})
            for section, data in list(config_sections.latent.items()):
                config_sections.latent_save.update({section: data.copy()})
        self.data.saved_config_names = set(self.data.config.keys())
        # Update open pages.
        self._get_pagelist()
        for page in self.pagelist:
            page.refresh_widget_status()
        # Update everything else.
        self.updater.update_all()
        return save_ok

    def output_config_objects(self, only_config_name=None):
        """Return a dict of config name - object pairs from this session."""
        if only_config_name is None:
            config_names = list(self.data.config.keys())
        else:
            config_names = [only_config_name]
        return_dict = {}
        for config_name in config_names:
            config = self.data.dump_to_internal_config(config_name)
            return_dict.update({config_name: config})
        return return_dict

# ----------------- Secondary Menu/Dialog handling functions -----------------

    def apply_macro_transform(self, *args, **kwargs):
        """Placeholder for updater module function."""
        self.updater.apply_macro_transform(*args, **kwargs)

    def apply_macro_validation(self, *args, **kwargs):
        """Placeholder for updater module function."""
        self.updater.apply_macro_validation(*args, **kwargs)

    def _add_config(self, config_name, meta=None):
        """Add a configuration, optionally with META=TYPE=meta."""
        config_short_name = config_name.split("/")[-1]
        root = os.path.join(self.data.top_level_directory,
                            metomi.rose.SUB_CONFIGS_DIR)
        new_path = os.path.join(root, config_short_name, metomi.rose.SUB_CONFIG_NAME)
        new_config = metomi.rose.config.ConfigNode()
        if meta is not None:
            new_config.set(
                [metomi.rose.CONFIG_SECT_TOP, metomi.rose.CONFIG_OPT_META_TYPE],
                meta
            )
        try:
            os.mkdir(os.path.dirname(new_path))
            metomi.rose.config.dump(new_config, new_path)
        except (OSError, IOError) as exc:
            text = metomi.rose.config_editor.ERROR_CONFIG_CREATE.format(
                new_path, type(exc), str(exc))
            title = metomi.rose.config_editor.ERROR_CONFIG_CREATE_TITLE
            metomi.rose.gtk.dialog.run_dialog(metomi.rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                       text, title)
            return False
        self.data.load_config(os.path.dirname(new_path), reload_tree_on=True,
                              skip_load_event=True)
        stack_item = metomi.rose.config_editor.stack.StackItem(
            config_name,
            metomi.rose.config_editor.STACK_ACTION_ADDED,
            metomi.rose.variable.Variable('', '', {}),
            self._remove_config,
            (config_name, meta)
        )
        self.undo_stack.append(stack_item)
        while self.redo_stack:
            self.redo_stack.pop()
        self.view_page(config_name)
        self.updater.update_namespace(config_name)

    def _remove_config(self, config_name, meta=None):
        """Remove a configuration, optionally caching a meta id."""
        config_data = self.data.config[config_name]
        dirpath = config_data.directory
        nses = self.data.helper.get_all_namespaces(config_name)
        nses.remove(config_name)
        self._get_pagelist()
        for page in self.pagelist:
            name = self.util.split_full_ns(self.data, page.namespace)[0]
            if name == config_name:
                if name in self.notebook.get_page_ids():
                    self.notebook.delete_by_id(name)
                else:
                    tab_nses = [w.get_child().namespace
                                for w in self.tab_windows]
                    page_window = self.tab_windows[tab_nses.index(name)]
                    page_window.destroy()
        self.group_ops.remove_sections(config_name,
                                       list(config_data.sections.now.keys()))
        if dirpath is not None:
            try:
                shutil.rmtree(dirpath)
            except (shutil.Error, OSError, IOError) as exc:
                text = metomi.rose.config_editor.ERROR_CONFIG_DELETE.format(
                    dirpath, type(exc), str(exc))
                title = metomi.rose.config_editor.ERROR_CONFIG_CREATE_TITLE
                metomi.rose.gtk.dialog.run_dialog(metomi.rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                           text, title)
                return False
        self.data.config.pop(config_name)
        self.reload_namespace_tree()
        stack_item = metomi.rose.config_editor.stack.StackItem(
            config_name,
            metomi.rose.config_editor.STACK_ACTION_REMOVED,
            metomi.rose.variable.Variable('', '', {}),
            self._add_config,
            (config_name, meta)
        )
        self.undo_stack.append(stack_item)
        while self.redo_stack:
            self.redo_stack.pop()

    def _get_menu_widget(self, suffix):
        """Return the menu widget whose ui address ends with suffix."""
        for address in self.menu_widgets:
            if address.endswith(suffix):
                return self.menu_widgets[address]
        return None

    def _has_preview_apps(self):
        """Return whether any configurations are currently just previews."""
        for item in list(self.data.config.keys()):
            if self.data.config[item].is_preview:
                return True
        else:
            return False

    def update_bar_widgets(self):
        """Update bar functionality like Undo and Redo."""
        if not hasattr(self, 'toolbar'):
            return False
        self.toolbar.set_widget_sensitive(metomi.rose.config_editor.TOOLBAR_UNDO,
                                          len(self.undo_stack) > 0)
        self.toolbar.set_widget_sensitive(metomi.rose.config_editor.TOOLBAR_REDO,
                                          len(self.redo_stack) > 0)
        self._get_menu_widget('/Undo').set_sensitive(len(self.undo_stack) > 0)
        self._get_menu_widget('/Redo').set_sensitive(len(self.redo_stack) > 0)
        self._get_menu_widget('/Find Next').set_sensitive(
            len(self.find_hist['ids']) > 0)
        self._get_menu_widget('/Load All Apps').set_sensitive(
            self._has_preview_apps())
        self.toolbar.set_widget_sensitive(metomi.rose.config_editor.TOOLBAR_LOAD_APPS,
                                          self._has_preview_apps())
        if not hasattr(self, "nav_panel"):
            return False
        changes, errors = self.nav_panel.get_change_error_totals()
        self.status_bar.set_num_errors(errors)
        self._get_menu_widget('/Autofix').set_sensitive(bool(errors))
        self.toolbar.set_widget_sensitive(metomi.rose.config_editor.TOOLBAR_TRANSFORM,
                                          bool(errors))
        self._update_changed_sensitivity(is_changed=bool(changes))

    def update_status_text(self, *args, **kwargs):
        """Update the message displayed in the status bar."""
        if hasattr(self, "status_bar"):
            self.status_bar.set_message(*args, **kwargs)

    def _update_changed_sensitivity(self, is_changed=False):
        """Alter sensitivity of 'unsaved changes' related widgets."""
        self.toolbar.set_widget_sensitive(metomi.rose.config_editor.TOOLBAR_SAVE,
                                          is_changed)
        self.toolbar.set_widget_sensitive(
            metomi.rose.config_editor.TOOLBAR_CHECK_AND_SAVE,
            is_changed
        )
        self._get_menu_widget('/Save').set_sensitive(is_changed)
        self._get_menu_widget('/Check and save').set_sensitive(is_changed)
        self._get_menu_widget('/Graph').set_sensitive(not is_changed)

    def _refresh_metadata_if_on(self, config_name=None):
        """Reload any metadata, if present - otherwise do nothing."""
        if not self.metadata_off:
            self.refresh_metadata(only_this_config=config_name)

    def refresh_metadata(self, metadata_off=False, only_this_config=None):
        """Switch metadata on/off and reloads namespaces."""
        self.metadata_off = metadata_off
        if hasattr(self, 'menubar'):
            self._get_menu_widget('/Reload metadata').set_sensitive(
                not self.metadata_off)
        if only_this_config is None:
            configs = list(self.data.config.keys())
        else:
            configs = [only_this_config]
        for config_name in configs:
            if self.data.config[config_name].is_preview:
                continue
            self.data.clear_meta_lookups(config_name)
            config = self.data.dump_to_internal_config(config_name)
            config_data = self.data.config[config_name]
            config_data.config = config
            directory = config_data.directory
            del config_data.macros
            meta_config = config_data.meta
            if metadata_off:
                meta_config_tree = self.data.load_meta_config_tree(
                    config_type=config_data.config_type,
                    opt_meta_paths=self.data.opt_meta_paths)
                meta_config = meta_config_tree.node
                meta_files = self.data.load_meta_files(meta_config_tree)
                macros = []
            else:
                meta_config_tree = self.data.load_meta_config_tree(
                    config, directory, config_type=config_data.config_type,
                    opt_meta_paths=self.data.opt_meta_paths)
                meta_config = meta_config_tree.node
                meta_files = self.data.load_meta_files(meta_config_tree)
                macro_module_prefix = (
                    self.data.helper.get_macro_module_prefix(config_name))
                macros = metomi.rose.macro.load_meta_macro_modules(
                    meta_files, module_prefix=macro_module_prefix)
            config_data.meta = meta_config
            self.data.load_builtin_macros(config_name)
            self.data.load_file_metadata(config_name)
            self.data.filter_meta_config(config_name)
            # Load section and variable data into the object.
            sects, l_sects = self.data.load_sections_from_config(config_name)
            s_sects, s_l_sects = self.data.load_sections_from_config(
                config_name, save=True)
            config_data.sections = metomi.rose.config_editor.data.SectData(
                sects, l_sects, s_sects, s_l_sects)
            var, l_var = self.data.load_vars_from_config(config_name)
            s_var, s_l_var = self.data.load_vars_from_config(
                config_name, save=True)
            config_data.vars = metomi.rose.config_editor.data.VarData(
                var, l_var, s_var, s_l_var)
            config_data.meta_files = meta_files
            config_data.macros = macros
            self.data.load_node_namespaces(config_name)
            self.data.load_node_namespaces(config_name, from_saved=True)
            self.data.load_ignored_data(config_name)
            self.data.load_metadata_for_namespaces(config_name)
        self.reload_namespace_tree()
        if self.is_pluggable:
            self.updater.update_all()
        if hasattr(self, 'menubar'):
            self.main_handle.load_macro_menu(self.menubar)
        namespaces_updated = []
        for config_name in configs:
            config_data = self.data.config[config_name]
            for variable in config_data.vars.get_all(skip_latent=True):
                ns = variable.metadata.get('full_ns')
                if ns not in namespaces_updated:
                    self.updater.update_tree_status(ns, icon_type='changed')
                    namespaces_updated.append(ns)
        self._get_pagelist()
        current_page, current_id = self._get_current_page_and_id()
        current_namespace = None
        if current_page is not None:
            current_namespace = current_page.namespace

        # Generate replacements for existing pages.
        for page in self.pagelist:
            namespace = page.namespace
            config_name = self.util.split_full_ns(self.data, namespace)[0]
            if config_name not in configs:
                continue
            data, missing_data = self.data.helper.get_data_for_namespace(
                namespace)
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
                        parent.pack_start(new_page, True, True, 0)
                    self.orphan_pages.remove(page)
                    self.orphan_pages.append(new_page)
            else:
                self.kill_page(page.namespace)

        # Preserve the old current page view, if possible.
        if current_namespace is not None:
            config_name = self.util.split_full_ns(self.data,
                                                  current_namespace)[0]
            self._get_pagelist()
            page_namespaces = [page.namespace for page in self.pagelist]
            if config_name in configs:
                if current_namespace in page_namespaces:
                    self.view_page(current_namespace, current_id)

    def load_custom_metadata(self):
        # open metadata dialog, use list() to pass by value
        paths = self.mainwindow.launch_metadata_manager(
            list(self.data.opt_meta_paths))
        if paths is not None:
            # if form submitted
            self.data.opt_meta_paths = paths
            self.refresh_metadata()

# ----------------- Data-intensive menu functions / utilities ----------------

    def _launch_find(self, *args):
        """Get the find expression from a dialog."""
        if not self.find_entry.is_focus():
            self.find_entry.grab_focus()
        expression = self.find_entry.get_text()
        start_page = self._get_current_page()
        if expression is not None and expression != '':
            page, var_id = self.perform_find(expression, start_page)
            if page is None:
                text = metomi.rose.config_editor.WARNING_NOT_FOUND
                self.find_entry.set_icon_from_stock(
                    0, Gtk.STOCK_DIALOG_WARNING)
                self.find_entry.set_icon_tooltip_text(0, text)
            else:
                if var_id is not None:
                    self.reporter.report(
                        metomi.rose.config_editor.EVENT_FOUND_ID.format(var_id))
                self._clear_find()

    def _clear_find(self, *args):
        """Clear any warning icons from the find entry."""
        self.find_entry.set_icon_from_stock(0, None)

    def perform_find(self, expression, start_page=None):
        """Drive the finding of the regex 'expression' within the data."""
        if expression == '':
            return None, None
        page_id, var_id = self.get_found_page_and_id(expression, start_page)
        return self.view_page(page_id, var_id), var_id

    def perform_find_by_ns_id(self, namespace, setting_id):
        """Drive find by id."""
        config_name = self.util.split_full_ns(self.data, namespace)[0]
        self.perform_find_by_id(config_name, setting_id)

    def perform_find_by_id(self, config_name, setting_id):
        """Drive the finding of a setting id within the data."""
        section, option = self.util.get_section_option_from_id(setting_id)
        if option is None:
            page_id = self.data.helper.get_default_section_namespace(
                section, config_name)
            self.view_page(page_id)
        else:
            var = self.data.helper.get_variable_by_id(setting_id, config_name)
            if var is None:
                var = self.data.helper.get_variable_by_id(setting_id,
                                                          config_name,
                                                          latent=True)
            if var is not None:
                page_id = var.metadata["full_ns"]
                self.view_page(page_id, setting_id)

    def get_found_page_and_id(self, expression, start_page):
        """Using regex expression, return a matching page and variable."""
        try:
            reg_find = re.compile(expression).search
        except sre_constants.error as exc:
            metomi.rose.gtk.dialog.run_dialog(
                metomi.rose.gtk.dialog.DIALOG_TYPE_ERROR,
                metomi.rose.config_editor.ERROR_NOT_REGEX.format(
                    expression, str(exc)),
                metomi.rose.config_editor.ERROR_BAD_FIND)
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
        config_keys = sorted(list(self.data.config.keys()))
        config_keys.sort(key=cmp_to_key(name_cmp))
        for config_name in config_keys:
            config_data = self.data.config[config_name]
            search_vars = config_data.vars.get_all(
                skip_latent=not self.page_var_show_modes["latent"])
            found_ns_vars = {}
            for variable in search_vars:
                var_id = variable.metadata.get('id')
                ns = variable.metadata.get('full_ns')
                if (metomi.rose.META_PROP_TITLE in variable.metadata and
                        reg_find(variable.metadata[metomi.rose.META_PROP_TITLE])):
                    found_ns_vars.setdefault(ns, [])
                    found_ns_vars[ns].append(variable)
                    continue
                if reg_find(variable.name) or reg_find(variable.value):
                    found_ns_vars.setdefault(ns, [])
                    found_ns_vars[ns].append(variable)
            ns_list = sorted(list(found_ns_vars.keys()))
            ns_list.sort(key=cmp_to_key(ns_cmp))
            for ns in ns_list:
                variables = found_ns_vars[ns]
                variables.sort(key=lambda x: x.metadata['id'])
                for variable in variables:
                    var_id = variable.metadata['id']
                    if (config_name, var_id) not in self.find_hist['ids']:
                        if (not self.page_var_show_modes['fixed'] and
                                len(variable.metadata.get('values', [])) == 1):
                            continue
                        if (not self.page_var_show_modes['ignored'] and
                                variable.ignored_reason):
                            continue
                        self.find_hist['ids'].append((config_name, var_id))
                        return ns, var_id
        if self.find_hist['ids']:
            config_name, var_id = self.find_hist['ids'][0]
            config_data = self.data.config[config_name]
            var = self.data.helper.get_variable_by_id(var_id, config_name)
            if var is None:
                var = self.data.helper.get_variable_by_id(var_id, config_name,
                                                          latent=True)
            if var is not None:
                self.find_hist['ids'] = [self.find_hist['ids'][0]]
                return var.metadata['full_ns'], var_id
        return None, None

    def check_cannot_enable_setting(self, config_name, setting_id):
        """Check if the setting is involved in the trigger mechanism."""
        return setting_id in self.data.trigger[config_name].get_all_ids()

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
        if self.performing_undo:
            # Prevent multiple calls from existing concurrently.
            return False
        else:
            self.performing_undo = True
        self._get_pagelist()
        do_list = [stack[-1]]
        # We should undo/redo all same-grouped items together.
        for stack_item in reversed(stack[:-1]):
            if (stack_item.group is None or
                    stack_item.group != do_list[0].group):
                break
            do_list.append(stack_item)
        group = do_list[0].group
        is_group = len(do_list) > 1
        stack_info = []
        namespace_id_map = {}
        event_text = metomi.rose.config_editor.EVENT_UNDO
        if redo_mode_on:
            event_text = metomi.rose.config_editor.EVENT_REDO
        for stack_item in do_list:
            action = stack_item.action
            node = stack_item.node
            node_id = None
            try:
                node_id = node.metadata['id']
            except (AttributeError, KeyError):
                pass
            # We need to handle namespace and metadata changes
            if node_id is None:
                # Not a variable or section
                namespace = stack_item.page_label
                node_is_section = False
            else:
                # A variable or section
                opt = self.util.get_section_option_from_id(node_id)[1]
                node_is_section = (opt is None)
                namespace = node.metadata.get('full_ns')
                if namespace is None:
                    namespace = stack_item.page_label
                config_name = self.util.split_full_ns(
                    self.data, namespace)[0]
                node.process_metadata(
                    self.data.helper.get_metadata_for_config_id(node_id,
                                                                config_name))
                self.data.load_ns_for_node(node, config_name)
                namespace = node.metadata.get('full_ns')
            if (not is_group and
                    self.nav_controller.is_ns_in_tree(namespace) and
                    not node_is_section):
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
            self.redo_stack.extend(redo_items)
            just_done_item = self.undo_stack[-1]
            just_done_item.group = group
            del self.undo_stack[-1]
            del stack[-1]
            if redo_mode_on:
                self.undo_stack.append(just_done_item)
            else:
                self.redo_stack.append(just_done_item)
            if not self.nav_controller.is_ns_in_tree(namespace):
                self.reload_namespace_tree()
            page = None
            if is_group:
                # Store namespaces and ids for later updating.
                stack_info.extend([namespace, stack_item.page_label])
                namespace_id_map.setdefault(namespace, [])
                namespace_id_map[namespace].append(node_id)
                if namespace != stack_item.page_label:
                    namespace_id_map.setdefault(stack_item.page_label, [])
                    namespace_id_map[stack_item.page_label].append(node_id)
            elif self.nav_controller.is_ns_in_tree(namespace):
                if not node_is_section:
                    # Section operations should not require pages.
                    page = self.view_page(namespace, node_id)
                    self.updater.sync_page_var_lists(page)
                    page.sort_data()
                    page.refresh(node_id)
                    page.update_ignored()
                    page.update_info()
                    page.set_main_focus(node_id)
                    self.set_current_page_indicator(page.namespace)
                    if namespace != stack_item.page_label:
                        # Make sure the right status update is made.
                        self.updater.update_status(page)
                self.update_bar_widgets()
                self.updater.update_stack_viewer_if_open()
            if not is_group:
                if namespace is not None:
                    self.updater.focus_sub_page_if_open(namespace, node_id)
                if node_id is None:
                    title = stack_item.name
                else:
                    title = node_id
                id_text = metomi.rose.config_editor.EVENT_UNDO_ACTION_ID.format(
                    action, title)
                self.reporter.report(event_text.format(id_text))
        if is_group:
            group_name = do_list[0].group.split("-")[0]
            self.reporter.report(event_text.format(group_name))
        namespace = None
        for namespace in set(stack_info):
            self.reload_namespace_tree(namespace)
        # Use the last node_id for a sub page focus (if any).
        if namespace:
            focus_id = namespace_id_map[namespace][-1]
            self.updater.focus_sub_page_if_open(namespace, focus_id)
        self.performing_undo = False
        return True

# ----------------------- System functions -----------------------------------


def spawn_window(config_directory_path=None, debug_mode=False,
                 load_all_apps=False, load_no_apps=False, metadata_off=False,
                 initial_namespaces=None, opt_meta_paths=None,
                 no_warn=None):
    """Create a window and load the configuration into it. Run Gtk."""
    if opt_meta_paths is None:
        opt_meta_paths = []
    if not debug_mode:
        warnings.filterwarnings('ignore')
    resourcer = metomi.rose.resource.ResourceLocator(paths=sys.path)
    metomi.rose.gtk.util.rc_setup(
        str(resourcer.locate('etc/rose-config-edit/.gtkrc-2.0')))
    metomi.rose.gtk.util.setup_stock_icons()
    logo = resourcer.locate('etc/images/rose-splash-logo.png')
    if metomi.rose.config_editor.ICON_PATH_SCHEDULER is None:
        gcontrol_icon = None
    else:
        try:
            gcontrol_icon = resourcer.locate(
                metomi.rose.config_editor.ICON_PATH_SCHEDULER)
        except metomi.rose.resource.ResourceError:
            gcontrol_icon = None
    metomi.rose.gtk.util.setup_scheduler_icon(gcontrol_icon)
    number_of_events = (get_number_of_configs(config_directory_path) *
                        metomi.rose.config_editor.LOAD_NUMBER_OF_EVENTS + 2)
    if config_directory_path is None:
        title = metomi.rose.config_editor.UNTITLED_NAME
    else:
        title = config_directory_path.split("/")[-1]
    splash_screen = metomi.rose.gtk.splash.SplashScreenProcess(logo, title,
                                                        number_of_events)
    try:
        ctrl = MainController(config_directory_path,
                              load_updater=splash_screen,
                              load_all_apps=load_all_apps,
                              load_no_apps=load_no_apps,
                              metadata_off=metadata_off,
                              opt_meta_paths=opt_meta_paths,
                              no_warn=no_warn)
    except BaseException:
        splash_screen.stop()
        raise

    # open up any initial_namespaces the user has provided us with
    if initial_namespaces:
        # if the namespace ends with a / remove it
        for i in range(len(initial_namespaces)):
            if (len(initial_namespaces[i]) > 1 and
                    initial_namespaces[i][-1] == '/'):
                initial_namespaces[i] = initial_namespaces[i][0:-1]

        # for each partial namespace get the full namespace
        full_namespaces = []
        for namespace in initial_namespaces:
            exp = re.compile(r'(.*%s?[^\/]+)' % (re.escape(namespace),))
            for ns in sorted(sorted(ctrl.data.namespace_meta_lookup),
                             key=len):
                match = exp.search(ns)
                if match:
                    full_namespaces.append(match.groups()[0])
                    break

        # open each namespace in a new tab
        for namespace in full_namespaces:
            # if the namespace begins with a / remove it
            if namespace[0] == '/':
                namespace = namespace[1:]
            # open namespace
            try:
                ctrl.view_page(namespace)
            except Exception:
                print('could not open ' + namespace, file=sys.stderr)
            # expand namespace in nav_panel
            path = ctrl.nav_panel.get_path_from_names(namespace.split('/'))
            if path:
                ctrl.nav_panel.tree.expand_to_path(path)

    Gtk.Settings.get_default().set_long_property("gtk-button-images",
                                                 True, "main")
    Gtk.Settings.get_default().set_long_property("gtk-menu-images",
                                                 True, "main")
    splash_screen.stop()
    Gtk.main()


def spawn_subprocess_window(config_directory_path=None):
    """Launch a subprocess for a new config editor. Is it safe?"""
    if config_directory_path is None:
        os.system(metomi.rose.config_editor.LAUNCH_COMMAND + ' --new &')
        return
    elif not os.path.isdir(str(config_directory_path)):
        return
    os.system(metomi.rose.config_editor.LAUNCH_COMMAND_CONFIG +
              config_directory_path + " &")


def get_number_of_configs(config_directory_path=None):
    """Return the number of configurations that will be loaded."""
    number_to_load = 0
    if config_directory_path is not None:
        for listing in set(os.listdir(config_directory_path)):
            if listing in metomi.rose.CONFIG_NAMES:
                number_to_load += 1
        app_dir = os.path.join(config_directory_path, metomi.rose.SUB_CONFIGS_DIR)
        if os.path.exists(app_dir):
            for entry in os.listdir(app_dir):
                if (os.path.isdir(os.path.join(app_dir, entry)) and
                        not entry.startswith('.')):
                    number_to_load += 1
    return number_to_load


def main():
    """Launch from the command line."""
    sys.path.append(os.getenv('ROSE_HOME'))
    opt_parser = metomi.rose.opt_parse.RoseOptionParser()
    opt_parser.add_my_options("conf_dir", "meta_path", "new_mode",
                              "load_no_apps", "load_all_apps", "no_metadata",
                              "no_warn")
    opts, args = opt_parser.parse_args()
    metomi.rose.macro.add_meta_paths()
    opt_meta_paths = []
    if opts.meta_path:
        for meta_path in opts.meta_path:
            for path in meta_path.split(os.pathsep):
                opt_meta_paths.append(
                    os.path.abspath(
                        os.path.expandvars(
                            os.path.expanduser(path))))
    if opts.conf_dir:
        os.chdir(opts.conf_dir)
    path = os.getcwd()
    name_set = set([metomi.rose.SUB_CONFIG_NAME, metomi.rose.TOP_CONFIG_NAME])
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
    metomi.rose.gtk.dialog.set_exception_hook_dialog(keep_alive=True)

    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    locator = metomi.rose.resource.ResourceLocator(paths=sys.path)
    css_path = locator.locate('etc/rose-config-edit/style.css')
    provider.load_from_path(str(css_path))

    if opts.profile_mode:
        handle = tempfile.NamedTemporaryFile()
        cProfile.runctx("""spawn_window(cwd, debug_mode=opts.debug_mode,
                                        load_all_apps=opts.load_all_apps,
                                        load_no_apps=opts.load_no_apps,
                                        metadata_off=opts.no_metadata,
                                        initial_namespaces=args,
                                        opt_meta_paths=opt_meta_paths,
                                        no_warn=opts.no_warn)
                        """, globals(), locals(), handle.name)
        pstat = pstats.Stats(handle.name)
        pstat.strip_dirs().sort_stats("cumulative").print_stats()
        handle.close()
    else:
        spawn_window(cwd, debug_mode=opts.debug_mode,
                     load_all_apps=opts.load_all_apps,
                     load_no_apps=opts.load_no_apps,
                     metadata_off=opts.no_metadata,
                     initial_namespaces=args,
                     opt_meta_paths=opt_meta_paths,
                     no_warn=opts.no_warn)


if __name__ == '__main__':
    main()
