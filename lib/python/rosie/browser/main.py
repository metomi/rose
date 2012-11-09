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

import ast
import functools
import os
import re
import shlex
import subprocess
import sys
import threading
import time
import urllib
import webbrowser

import pygtk
pygtk.require("2.0")
import gtk

import rose.config_editor
import rose.config_editor.main
import rose.env
import rose.external
import rose.gtk.run
import rose.gtk.util
from rose.opt_parse import RoseOptionParser
from rose.resource import ResourceLocator, ResourceError
import rosie.browser.history
import rosie.browser.result
import rosie.browser.search
import rosie.browser.status
import rosie.browser.suite
import rosie.browser.util
from rosie.suite_id import SuiteId
import rosie.vc
import rosie.ws_client

STATUS_TIP = {rosie.ws_client.STATUS_DO: rosie.browser.LOCAL_STATUS_DOWNDATE,
              rosie.ws_client.STATUS_NO: rosie.browser.LOCAL_STATUS_NO,
              rosie.ws_client.STATUS_OK: rosie.browser.LOCAL_STATUS_OK,
              rosie.ws_client.STATUS_MO: rosie.browser.LOCAL_STATUS_MODIFIED,
              rosie.ws_client.STATUS_SW: rosie.browser.LOCAL_STATUS_SWITCH,
              rosie.ws_client.STATUS_UP: rosie.browser.LOCAL_STATUS_UPDATE}


class MainWindow(gtk.Window):

    """The main window containing the database viewer."""
    
    def __init__(self, opts=None, args=None):

        super(MainWindow, self).__init__()
        self.refresh_url = ""
        self.search_manager = rosie.browser.search.SearchManager(opts.prefix)        
        locator = ResourceLocator(paths=sys.path)
        self.config = locator.get_conf()
        icon_path = locator.locate(rosie.browser.ICON_PATH_WINDOW)
        self.set_icon_from_file(icon_path)
        try:
            self.sched_icon_path = locator.locate(
                                          rosie.browser.ICON_PATH_SCHEDULER)
        except ResourceError:
            self.sched_icon_path = None
        self.query_rows = None
        self.adv_controls_on = rosie.browser.SHOULD_SHOW_ADVANCED_CONTROLS
        self.search_history = False
        self.hist = rosie.browser.history.HistoryManager(
                    rosie.browser.HISTORY_LOCATION, rosie.browser.SIZE_HISTORY)
        self.last_search_historical = False
        self.local_updater = rosie.browser.status.LocalStatusUpdater(
                                   self.handle_update_treemodel_local_status)
        self.repeat_last_request = lambda: None
        self.setup_window()
        self.suite_director = rosie.browser.suite.SuiteDirector(
                                            event_handler=self.handle_vc_event)
        self.set_title(rosie.browser.TITLEBAR.format(
                                     self.search_manager.get_datasource()))                                  
        self.initial_filter(opts, args)
        self.nav_bar.simple_search_entry.grab_focus()
        self.show()

    def setup_window(self):
        """Construct the window."""
        self.set_size_request(*rosie.browser.SIZE_WINDOW)
        self.vbox = gtk.VBox()
        self.main_vbox = gtk.VPaned()
        self.main_vbox.set_position(rosie.browser.SIZE_TOP_TREES)
        self.generate_search()
        self.generate_results_treeview()
        self.main_vbox.pack1(self.advanced_search_widget, resize=True, 
                             shrink=False)
        self.main_vbox.pack2(self.display_box, resize=True, shrink=True)
        self.generate_menu()
        self.add_accel_group(self.menubar.accelerators)
        self.generate_toolbar()
        self.setup_navbar()
        self.statusbar = rosie.browser.util.StatusBarWidget()
        self.hbox = gtk.HPaned()
        self.generate_treeview_history()
        self.pop_treeview_history()
        self.hbox.pack1(self.history_pane, resize=True, shrink=True)
        self.hbox.pack2(self.main_vbox, resize=True, shrink=True)
        self.hbox.show()
        self.vbox.pack_start(self.top_menu, expand=False, fill=True)
        self.vbox.pack_start(self.toolbar, expand=False, fill=True)
        self.vbox.pack_start(self.nav_bar, expand=False, fill=True)
        self.vbox.pack_start(self.hbox, expand=True, fill=True, padding=5)
        self.vbox.pack_start(self.statusbar, expand=False, fill=True)
        self.statusbar.show()
        self.main_vbox.show()
        self.vbox.show()
        self.add(self.vbox)
        self.connect("destroy", self.handle_destroy)

    def address_bar_handler(self, widget, is_entry, record=False):
        """Handle selection of items and text entry for the address bar."""  
        if self.nav_bar.address_box.get_active() == -1:
            if is_entry:
                if self.nav_bar.address_box.child.get_text() != "":
                    self.address_bar_lookup(None, record)
        else:
            self.address_bar_lookup(None, record)        
        return
   
    def address_bar_lookup(self, widget, record=True):
        """Run a search based on the address bar."""
        self.local_updater.update_now()
        address_url = self.nav_bar.address_box.child.get_text()
        self.refresh_url = address_url

        # if the url string doesn't begin with a valid prefix       
        if not (address_url.find("http://") == 0 or 
                address_url.find("search?s=") == 0 or 
                address_url.find("query?q=") == 0):
            self.nav_bar.simple_search_entry.set_text(address_url)
            self.handle_search(None)
        else:
            items = {}

            if not address_url.endswith("&format=json"):
                address_url += "&format=json"
            
            #set the all revisions to the setting specified *by the url*
            self.history_menuitem.set_active("all_revs=" in address_url)
            
            # convert partial addresses to full ones for purposes of searching
            if (address_url.find("search?s=") == 0 or 
                address_url.find("query?q=") == 0):
                address_url = (self.search_manager.ws_client.get_query_prefix()
                              + address_url)
            try:
                items.update({"url": address_url})
                results = self.search_manager.address_lookup(**items)
                if record == True:
                    if (self.nav_bar.address_box
                        .get_model().iter_n_children(None) > 0):
                        if address_url != str(
                                          self.nav_bar.address_box.get_model()
                                          .get_value(self.nav_bar.address_box
                                          .get_model().get_iter_first(), 0)):
                            self.nav_bar.address_box.insert_text(
                                                     0, address_url)
                            if (self.nav_bar.address_box.get_model()
                                .iter_n_children(None)
                                > rosie.browser.SIZE_ADDRESS):
                                self.nav_bar.address_box.remove_text(
                                                    rosie.browser.SIZE_ADDRESS)
                    else:                        
                        self.nav_bar.address_box.insert_text(0, address_url)
                        
                    recorded = self.hist.record_search(
                                                "url", 
                                                repr(address_url),
                                                self.search_history)
                    if recorded == True:
                        self.handle_record_search_ui("url", 
                                                     address_url,
                                                     self.search_history)
                
            except rosie.ws_client.QueryError as e:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                         str(e),
                                         rosie.browser.TITLE_INVALID_QUERY)
                results = []
            self.display_maps_result(results)

    def clear_filters(self, *args):
        """Remove all filters from the GUI."""
        self.advanced_search_widget.remove_filter()
        added_ok = self.advanced_search_widget.add_filter()

    def close_history(self, widget):
        """Close down the history panel"""
        self.menubar.uimanager.get_widget(
             '/TopMenuBar/History/Show search history').set_active(False) 

    def _create_suite_hook(self, config, from_id=None):
        """Hook function to create a suite from a configuration."""
        if config is None:
            return
        try:
            new_id = self.suite_director.vc_client.create(config, from_id,
                                         self.search_manager.ws_client.prefix)
        except Exception as e:
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     type(e).__name__ + ": " + str(e))
            return None
        self.handle_checkout(id_=new_id)
        self.repeat_last_request()

    def display_local_suites(self, a_widget=None):
        """Get and display the locally stored suites."""
        self.nav_bar.address_box.child.set_text("")
        self.refresh_url = ""
        self.statusbar.set_status_text(rosie.browser.STATUS_FETCHING, 
                                       instant=True)
        self.statusbar.set_progressbar_pulsing(True)
        res = rosie.ws_client.get_local_suite_details( 
                              self.search_manager.get_datasource() )
        self.display_maps_result(res, True)
        self.repeat_last_request = self.display_local_suites
        self.statusbar.set_progressbar_pulsing(False)

    def display_maps_result(self, result_maps, is_local=False):
        """Process the results of calling function(*function_args)."""
        self.statusbar.set_datasource(self.search_manager.get_datasource())
        while gtk.events_pending():
            gtk.main_iteration()
        self.statusbar.set_status_text(rosie.browser.STATUS_UPDATE,
                                       instant=True)
        while gtk.events_pending():
            gtk.main_iteration()
        result_columns = [c for c in self.get_tree_columns() if c != "local"]
        results = []
        idx_index = result_columns.index("idx")
        branch_index = result_columns.index("branch")
        rev_index = result_columns.index("revision")
        self.display_box._result_info = {}
        for result_map in result_maps:
            results.append([])
            idx = result_map["idx"]
            branch = result_map["branch"]
            revision = result_map["revision"]
            if is_local:
                local_status = result_map.pop("local")
            else:
                local_status = rosie.ws_client.get_local_status(
                                    self.local_updater.local_suites,
                                    self.search_manager.get_datasource(),
                                    idx, branch, revision)
            id_ = (idx, branch, revision)
            self.display_box.update_result_info(id_, result_map, local_status, 
                                                self.search_manager, 
                                                self.format_suite_id)
            for key in result_columns:
                try:
                    value = result_map.pop(key)
                except KeyError:
                    value = None
                results[-1].append(value)
            results[-1].insert(0, local_status)
        self.handle_update_treeview(results)
        self.last_search_historical = self.search_history
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if not is_local:        
            self.statusbar.set_status_text(rosie.browser.STATUS_GOT.format(
                                           len(results), str(now)), 
                                           instant=True)
        elif is_local and len(results) > 0:
            self.statusbar.set_status_text(
                           rosie.browser.STATUS_LOCAL_GOT.format(
                           len(results),str(now)), instant=True)
        elif is_local and len(results) == 0:                       
            self.statusbar.set_status_text(
                 rosie.browser.STATUS_NO_LOCAL_SUITES.format(str(now)),  
                 instant=True)

    def display_toggle(self, title):
        """Alter the display settings."""
        filters = self.advanced_search_widget.display_filters[title]
        self.advanced_search_widget.display_filters[title] = not filters
        self.handle_update_treeview()

    def format_suite_id(self, prefix, idx, branch, revision):
        """Convenience method for formatting the suite id."""
        return "{0}-{1}/{2}@{3}".format(prefix, idx, branch, revision)

    def generate_menu(self):
        """Generate the top menu."""
        self.menubar = rosie.browser.util.MenuBar(
                                self.advanced_search_widget.display_columns)
        menu_list = [('/TopMenuBar/File/New Suite',
                      lambda m: self.handle_create()),
                     ('/TopMenuBar/File/Quit', self.handle_destroy),
                     ('/TopMenuBar/Edit/Preferences', lambda m: False),
                     ('/TopMenuBar/View/View advanced controls',
                      self.toggle_advanced_controls),
                     ('/TopMenuBar/View/Include history',
                      self.toggle_history),
                     ('/TopMenuBar/History/Show search history',
                      self.show_search_history),
                     ('/TopMenuBar/History/Clear history',
                      self.handle_clear_history),
                     ('/TopMenuBar/Help/GUI Help', 
                      lambda m: self.launch_help()),
                     ('/TopMenuBar/Help/About', 
                      rosie.browser.util.launch_about_dialog)]
        for prefix in self.menubar.prefixes:
            address = "/TopMenuBar/Edit/Source/_{0}_".format(prefix)
            widget = self.menubar.uimanager.get_widget(address)
            widget.set_active(prefix == self.search_manager.get_datasource())
            widget.prefix_text = prefix
            widget.connect("toggled", self._handle_prefix_change)

        for key in self.menubar.known_keys:
            address = "/TopMenuBar/View/View _{0}_".format(key)
            widget = self.menubar.uimanager.get_widget(address)
            if widget is not None:
                widget.column = key
                widget.set_active(key in rosie.browser.COLUMNS_SHOWN)
                widget.connect("toggled", self._handle_display_change)
        
        for (address, action) in menu_list:
            widget = self.menubar.uimanager.get_widget(address)
            widget.connect('activate', action)

        self.advanced_search_widget.adv_control_menuitem = (
                                    self.menubar.uimanager.get_widget(
                                    '/TopMenuBar/View/View advanced controls'))
        self.advanced_search_widget.adv_control_menuitem.set_active(
                                    self.adv_controls_on)
        
        self.history_menuitem = self.menubar.uimanager.get_widget(
                                     '/TopMenuBar/View/Include history')
        self.show_history_menuitem = self.menubar.uimanager.get_widget(
                                     '/TopMenuBar/History/Show search history') 
        self.top_menu = self.menubar.uimanager.get_widget('/TopMenuBar')
        accel = {
            rose.config_editor.ACCEL_NEW: lambda: self.handle_create(),
            rose.config_editor.ACCEL_QUIT: lambda: self.handle_destroy(),
            rose.config_editor.ACCEL_HELP_GUI: lambda: self.launch_help(),
            rosie.browser.ACCEL_REFRESH: lambda: self.handle_refresh(),
            rosie.browser.ACCEL_HISTORY_SHOW: 
                          lambda: self.handle_toggle_history(),
            rosie.browser.ACCEL_PREVIOUS_SEARCH: 
                          lambda: self.handle_previous_search(),
            rosie.browser.ACCEL_NEXT_SEARCH: lambda: self.handle_next_search()}
        
        self.menubar.set_accelerators(accel)

    def generate_results_treeview(self):
        """Generate the main treeview used to display search results."""
        self.display_box = rosie.browser.result.DisplayBox(
                                         self.get_tree_columns, 
                                         self.get_display_columns)
        self.display_box.treeview.connect("button-press-event", 
                                          self.handle_activation)
        self.display_box.treeview.connect("cursor-changed", 
                                          self.handle_activation)
        self.display_box.treeview.connect("drag-data-get",
                                          self._get_treeview_drag_data)
        self.display_box.treestore.connect("row-deleted", 
                                           self.handle_activation) 

    def generate_search(self):
        """Generate the top display widgets."""
        self.advanced_search_widget = self.get_advanced_search_widget()

    def generate_toolbar(self):
        """Generate the toolbar."""
        self.toolbar = rose.gtk.util.ToolBar(
                       widgets=[(rosie.browser.TIP_TOOLBAR_NEW, 
                                 "gtk.STOCK_NEW"),
                                (rosie.browser.TIP_TOOLBAR_EDIT,
                                 "gtk.STOCK_EDIT"),
                                (rosie.browser.TIP_TOOLBAR_CHECKOUT,
                                 "gtk.STOCK_GO_DOWN"),
                                (rosie.browser.TIP_TOOLBAR_COPY,
                                 "gtk.STOCK_COPY"),
                                (rosie.browser.TIP_TOOLBAR_VIEW_WEB,
                                 "gtk.STOCK_ABOUT"),
                                (rosie.browser.TIP_TOOLBAR_VIEW_OUTPUT,
                                 "gtk.STOCK_DIRECTORY"),
                                (rosie.browser.TIP_TOOLBAR_LAUNCH_TERMINAL,
                                 "gtk.STOCK_EXECUTE"),
                                (rosie.browser.TIP_TOOLBAR_LAUNCH_SCHEDULER,
                                 self.get_sched_toolitem)],
                       sep_on_name=[rosie.browser.TIP_TOOLBAR_COPY,
                                    rosie.browser.TIP_TOOLBAR_LAUNCH_TERMINAL])
        self.toolbar.set_widget_function(rosie.browser.TIP_TOOLBAR_NEW, 
                                         self.handle_create)
        self.toolbar.set_widget_function(rosie.browser.TIP_TOOLBAR_EDIT,
                                         self.handle_edit)
        self.toolbar.set_widget_function(rosie.browser.TIP_TOOLBAR_CHECKOUT,
                                         self.handle_checkout)
        self.toolbar.set_widget_function(rosie.browser.TIP_TOOLBAR_COPY,
                                         self.handle_copy)
        self.toolbar.set_widget_function(rosie.browser.TIP_TOOLBAR_VIEW_WEB,
                                         self.handle_view_web)
        self.toolbar.set_widget_function(rosie.browser.TIP_TOOLBAR_VIEW_OUTPUT,
                                         self.handle_view_output)
        self.toolbar.set_widget_function(
                     rosie.browser.TIP_TOOLBAR_LAUNCH_TERMINAL,
                     self.handle_launch_terminal)
        self.toolbar.set_widget_function(
                     rosie.browser.TIP_TOOLBAR_LAUNCH_SCHEDULER,
                     self.handle_run_scheduler)
        custom_text = rose.config_editor.TOOLBAR_SUITE_RUN_MENU
        self.run_button = rose.gtk.util.CustomMenuButton(
                            stock_id=gtk.STOCK_MEDIA_PLAY,
                            menu_items=[(custom_text, gtk.STOCK_MEDIA_PLAY)],
                            menu_funcs=[self.handle_run_custom],
                            tip_text=rose.config_editor.TOOLBAR_SUITE_RUN)
        self.run_button.connect("clicked", self.handle_run)
        self.run_button.set_sensitive(False)
        self.toolbar.insert(self.run_button, -1)
        sep = gtk.SeparatorToolItem()
        sep.show()
        self.toolbar.insert(sep, -1)
        for toolitem_name in [rosie.browser.TIP_TOOLBAR_EDIT,
                              rosie.browser.TIP_TOOLBAR_CHECKOUT,
                              rosie.browser.TIP_TOOLBAR_COPY,
                              rosie.browser.TIP_TOOLBAR_VIEW_WEB,
                              rosie.browser.TIP_TOOLBAR_VIEW_OUTPUT,
                              rosie.browser.TIP_TOOLBAR_LAUNCH_TERMINAL,
                              rosie.browser.TIP_TOOLBAR_LAUNCH_SCHEDULER]:
            self.toolbar.set_widget_sensitive(toolitem_name, False)
        
        history_item = gtk.ToolItem()
        self.history_button = gtk.CheckButton()
        self.history_button.set_label(rosie.browser.LABEL_HISTORY_BUTTON)
        self.history_button.show()
        self.history_button.set_tooltip_text(rosie.browser.TIP_HISTORY_BUTTON)
        self.history_button.connect("clicked", self.toggle_history)
        history_item.add(self.history_button)
        history_item.show()
        self.toolbar.insert(history_item, -1)

    def generate_treeview_history(self):
        """Generate a treeview for viewing search history."""
        self.history_pane = rosie.browser.util.HistoryTreeview()
        self.history_pane.treeview_hist.connect("button-release-event",
                                                self.handle_historical_search)
        self.history_pane.close_button.connect("clicked", self.close_history)                                        

    def get_advanced_search_widget(self):
        """Create a list of filters and a "search" button."""
        advanced_search_widget = rosie.browser.util.AdvancedSearchWidget(
                                       self.search_manager,
                                       self.adv_controls_on, 
                                       self.handle_query,
                                       self.handle_show_hide_query_panel)
        return advanced_search_widget

    def get_display_columns(self):
        """Return the display columns."""
        return self.advanced_search_widget.display_columns

    def _get_sched_image(self, size=gtk.ICON_SIZE_MENU):
        if self.sched_icon_path is None:
            image = gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE, size)
        else:
            w, h = gtk.icon_size_lookup(size)
            pix = gtk.gdk.pixbuf_new_from_file(self.sched_icon_path)
            pix = pix.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)
            image = gtk.image_new_from_pixbuf(pix)
        return image

    def get_sched_toolitem(self):
        """Return a button for the suite scheduler."""
        image = self._get_sched_image(gtk.ICON_SIZE_SMALL_TOOLBAR)
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.set_image(image)
        button.show()
        return button
        
    def get_selected_suite_id(self, path=None):
        """Return the currently selected suite id in the rosie CLI format."""
        idx, branch, revision = self.display_box.get_suite_keys_treeview(path)
        prefix = self.search_manager.get_datasource()
        return self.format_suite_id(prefix, idx, branch, revision)

    def get_tree_columns(self):
        """Return the columns to display."""
        titles = [t for t in self.advanced_search_widget.display_columns]
        return titles

    def _get_treeview_drag_data(self, widget, context, selection, info, time):
        """Set the drag data for the search treeview."""
        selection.set_text(self.get_selected_suite_id())

    def handle_activation(self, treeview=None, event=None, somewidget=None):
        """Handle a button click on the main treeview."""
        path, col = self.display_box.treeview.get_cursor()
        self.update_toolbar_sensitivity(path)
        if hasattr(event, "button"):
            pathinfo = treeview.get_path_at_pos(int(event.x),
                                                int(event.y))
            if pathinfo is not None:
                path, col, cell_x, cell_y = pathinfo
                if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                    status = self.display_box._get_treeview_path_status(path)
                    if status in [rosie.ws_client.STATUS_OK,
                                  rosie.ws_client.STATUS_MO]:
                        self.handle_edit()
                    elif status == rosie.ws_client.STATUS_NO:
                        self.handle_checkout()
                        self.handle_edit()
            if event.button == 3:
                pathinfo = treeview.get_path_at_pos(int(event.x),
                                                    int(event.y))
                if pathinfo is not None:
                    path, col, cell_x, cell_y = pathinfo
                    self.popup_tree_menu(path, col, event)
        return False
        
    def handle_checkout(self, *args, **kwargs):
        """Checkout a suite."""
        if kwargs.get("id_") is None:
            id_text = self.get_selected_suite_id()
            kwargs['id_'] = SuiteId(id_text=id_text)
        self.suite_director.checkout(*args, **kwargs)
        self.local_updater.update_now()

    def handle_clear_history(self, *args):
        """Clear the search history."""
        warning = rosie.browser.DIALOG_MESSAGE_CLEAR_HISTORY_CONFIRMATION
        label = gtk.Label(warning)
        label.set_line_wrap(True)
        dialog = gtk.MessageDialog(self,
                                   gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK_CANCEL,
                                   warning)
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            self.history_pane.clear_treestore_history()
            self.nav_bar.clear_address_box()
            self.hist.clear_history()
            self.nav_bar.next_search_button.set_sensitive(False)
            self.nav_bar.previous_search_button.set_sensitive(False)
            self.hist.store_history()

    def handle_copy(self, *args):
        """Copy a suite."""
        id_string = self.get_selected_suite_id()
        from_id = SuiteId(id_text=id_string)
        self.handle_create(from_id)

    def handle_create(self, from_id=None):
        """Create a new suite."""
        config = self.suite_director.vc_client.generate_info_config(from_id)
        finish_func = functools.partial(self._create_suite_hook,
                                        from_id=from_id)
        return self.suite_director.run_new_suite_wizard(
                          config, finish_func, self)

    def handle_delete(self, *args):
        """"Handles deletion of a suite."""
        to_delete = self.get_selected_suite_id()
        if self.suite_director.delete(to_delete, *args):
            self.local_updater.update_now()
            self.repeat_last_request()
            
    def handle_delete_local(self, *args):
        """"Handles deletion of a suite."""
        to_delete = self.get_selected_suite_id()
        if self.suite_director.delete_local(to_delete, *args):
            self.local_updater.update_now()
            self.repeat_last_request()      
        
    def handle_destroy(self, *args):
        """Handles the destruction of the window."""
        self.local_updater.stop()
        self.hist.store_history()
        gtk.main_quit()

    def handle_edit(self, *args):
        """Edit a checked-out suite."""
        id_text = self.get_selected_suite_id()
        subprocess.Popen(["rose", "edit", "-C", 
                          SuiteId(id_text).to_local_copy()])

    def handle_grouping(self, menuitem):
        """Handles grouping of search results."""
        self.display_box._handle_grouping(menuitem)
        self.handle_update_treeview()

    def handle_historical_search(self, *args):
        """For running searches selected from the history menu."""
        path, col = self.history_pane.treeview_hist.get_cursor()
        self.nav_bar.next_search_button.set_sensitive(False)
        if path is not None:
            this_iter = self.history_pane.treestore_hist.get_iter(path)
            q_type = self.history_pane.treestore_hist.get_value(this_iter, 0)
            q_par = self.history_pane.treestore_hist.get_value(this_iter, 1)
            q_hist = self.history_pane.treestore_hist.get_value(this_iter, 2)
            self.set_search_details(q_type, q_par, q_hist)
            if q_type == "search":
                self.handle_search(None)# could set record to false if this new 
                                        # run shouldn't be recorded
            elif q_type == "query":
                self.handle_query(None)
            elif q_type == "url":
                self.address_bar_lookup(None, True)
            else:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                              rosie.browser.ERROR_CORRUPTED_HISTORY_ITEM,
                              rosie.browser.DIALOG_TITLE_HISTORY_ERROR,
                              modal=True)                

    def handle_info(self, *args):
        """Handle display of suite info."""
        rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_INFO,
                                 self.display_box.get_info_text(),
                                 rosie.browser.DIALOG_TITLE_INFO,
                                 modal=False)

    def handle_launch_terminal(self, *args):
        """Launch a terminal at the current suite directory."""
        id_text = self.get_selected_suite_id()
        rose.external.launch_terminal(cwd=SuiteId(id_text).to_local_copy())

    def handle_next_search(self, *args):
        """Handles trying to run next search."""
        if self.nav_bar.next_search_button.get_property('sensitive'):
            self.handle_search_navigation(next=True)
    
    def _handle_display_change(self, menuitem):
        """Handles changing view options."""
        self.display_toggle(menuitem.column)
    
    def _handle_prefix_change(self, menuitem):
        """Handles changing the datasource."""
        if menuitem.get_active():
            self.set_ws_client(menuitem.prefix_text)
            self.display_local_suites()
            self.statusbar.set_datasource(menuitem.prefix_text)
            self.statusbar.set_status_text(
                 rosie.browser.STATUS_SOURCE_CHANGED.format( 
                                                     menuitem.prefix_text))
            self.set_title(
                 rosie.browser.TITLEBAR.format(menuitem.prefix_text))                   

    def handle_previous_search(self, *args):
        """Handles trying to run the previous search."""
        if self.nav_bar.previous_search_button.get_property('sensitive'):
            self.handle_search_navigation(next=False)

    def handle_query(self, widget = None, record = True, *args):
        """Retrieve filters from widgets and apply."""
        self.local_updater.update_now()
        filters, proceed = self.advanced_search_widget.get_query()
        if proceed:   
            self.statusbar.set_status_text(rosie.browser.STATUS_FETCHING, 
                                           instant=True)
            self.statusbar.set_progressbar_pulsing(True)
            items = {}
            if self.search_history:
                items.update({"all_revs": ""})
            try:
                results, url = self.search_manager.ws_query(filters, **items)
                if url.endswith("&format=json"):
                    url = url.replace("&format=json", "")
                
                self.nav_bar.address_box.child.set_text(url)
                self.refresh_url = url   
                if record == True:
                    recorded = self.hist.record_search("query", repr(filters), 
                                                        self.search_history)
                    if recorded == True:
                        for h in filters: # Hacky but needed otherwise 
                                          # entries in history menu appear 
                                          # with unicode marker
                            msg = "["
                            for m in range(len(filters)-1):
                                msg = msg + "'" + filters[m] + "', "
                            msg = msg + "'" + filters[-1] + "']"
                        self.handle_record_search_ui("query", msg, 
                                                     self.search_history)
            except rosie.ws_client.QueryError as e:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                         str(e),
                                         rosie.browser.TITLE_INVALID_QUERY)
                results = []
            self.statusbar.set_progressbar_pulsing(False)
            self.display_maps_result(results)
            self.repeat_last_request = self.handle_query

    def handle_record_search_ui(self, s_type, msg, all_revs):
        """Handles ui updating on recording a search/query/url lookup"""
        self.history_pane.treestore_hist.prepend(None, [s_type, msg, all_revs]) 
        
        if self.hist.get_n_searches() > 1:
            self.nav_bar.previous_search_button.set_sensitive(True)
            self.nav_bar.next_search_button.set_sensitive(False)

    def handle_refresh(self, *args):
        """Handles refreshing the search results."""
        self.nav_bar.address_box.child.set_text(self.refresh_url)
        if self.nav_bar.address_box.child.get_text() == "":
            self.display_local_suites()
        else:
             self.address_bar_lookup(None, False)

    def handle_run(self, *args):
        """Run a checked-out suite."""
        self._run_suite()

    def handle_run_custom(self, *args):
        """Get custom arguments for running a suite."""
        help_cmds = ["rose", "help", "suite-run"]
        help_text = subprocess.Popen(help_cmds,
                                     stdout=subprocess.PIPE).communicate()[0]
        rose.gtk.util.run_command_arg_dialog("rose suite-run", help_text, 
                                             self._run_suite_check_args)

    def handle_run_scheduler(self, *args):
        """Run the scheduler for this suite."""
        this_id = SuiteId(id_text=self.get_selected_suite_id())
        cmd_string = rosie.browser.SCHEDULER_COMMAND.format(this_id)
        subprocess.Popen(shlex.split(cmd_string))

    def handle_search(self, widget=None, record=True, *args):
        """Get results that contain the values in the search widget."""
        self.local_updater.update_now()
        search_text = self.nav_bar.simple_search_entry.get_text()
        if not search_text:
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     rosie.browser.ERROR_ENTER_SEARCH,
                                     rosie.browser.TITLE_INVALID_QUERY)
            return
        self.statusbar.set_status_text(rosie.browser.STATUS_FETCHING,
                                       instant=True)
        self.statusbar.set_progressbar_pulsing(True)
        items = {}
        if self.search_history:
            items.update({"all_revs": ""})
        try:
            results, url = self.search_manager.ws_search(search_text, **items)
            if url.endswith("&format=json"):
                url = url.replace("&format=json", "")
            self.nav_bar.address_box.child.set_text(url)
            self.refresh_url = url
            if record == True:
                recorded = self.hist.record_search("search", repr(search_text),
                                                   self.search_history)
                if recorded == True:
                    self.handle_record_search_ui("search", search_text,
                                                 self.search_history)
        except rosie.ws_client.QueryError as e:
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     str(e),
                                     rosie.browser.TITLE_INVALID_QUERY)
            results = []
        self.display_maps_result(results)
        self.repeat_last_request = self.handle_search
        self.statusbar.set_progressbar_pulsing(False)

    def handle_search_navigation(self, next=None, *args):
        """Handle running either previous or next search in session history"""
        
        if next is not None:
            if next:
                self.nav_bar.previous_search_button.set_sensitive(True)
                search, enable = self.hist.get_next()
                self.nav_bar.next_search_button.set_sensitive(enable)            
            else:
                self.nav_bar.next_search_button.set_sensitive(True)
                search, enable = self.hist.get_previous()
                self.nav_bar.previous_search_button.set_sensitive(enable)
        else:
            return

        if search is not None:
            if search.h_type == "search":
                self.clear_filters()
                self.history_button.set_active(search.search_history)
                self.nav_bar.simple_search_entry.set_text(str(search.details))
                self.handle_search(None, False)
            elif search.h_type == "query":
                self.history_button.set_active(search.search_history)
                self.nav_bar.simple_search_entry.set_text("")
                self.set_query_filters(search.details)
                self.handle_query(None, False)
            elif search.h_type == "url":
                self.history_button.set_active(search.search_history)
                self.nav_bar.simple_search_entry.set_text("")
                self.clear_filters()
                self.nav_bar.address_box.child.set_text(search.details)
                self.address_bar_lookup(None, False)                
            else:
                if next:
                    msg = rosie.browser.ERROR_UNRECOGNISED_NEXT_SEARCH
                else:
                    msg = rosie.browser.ERROR_UNRECOGNISED_LAST_SEARCH
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                              msg,
                              rosie.browser.TITLE_HISTORY_NAVIGATION_ERROR)
        else:
            if next:
                err = rosie.browser.ERROR_NO_NEXT_SEARCH
            else:
                err = rosie.browser.ERROR_NO_PREVIOUS_SEARCH
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                              err,
                              rosie.browser.TITLE_HISTORY_NAVIGATION_ERROR)        

    def handle_show_hide_query_panel(self):
        """Handle resizing window contents on query panel visibility change."""
        self.main_vbox.set_position(0)
           
    def handle_toggle_history(self):
        """Toggle showing the history menu."""
        show_history = not self.show_history_menuitem.get_active()
        self.show_history_menuitem.set_active(show_history)

    def handle_update_treemodel_local_status(self, local_suites):
        """Update the local status column in the main tree model."""
        self.display_box.update_treemodel_local_status(local_suites, 
                                                       self.search_manager)
        self.update_toolbar_sensitivity(
             self.display_box.treeview.get_cursor()[0])

    def handle_update_treeview(self, query_rows=None, sort_title=None,
                               descending=False):
        """Handles updating the search results treeview."""
        self.display_box.update_treeview(self.handle_activation, 
                         self.advanced_search_widget.display_filters.get,
                         query_rows,
                         sort_title, 
                         descending)

    def handle_vc_event(self, event):
        """Handles setting the status bar text based on version control events.
        """
        self.statusbar.set_status_text(str(event))

    def handle_view_output(self, *args, **kwargs):
        """View a suite's output, if any."""
        test = kwargs.get("test", False)
        path = kwargs.get("path", None)
        output_dir = SuiteId(
                     id_text=self.get_selected_suite_id(path)).to_output()
        output_path = os.path.join(output_dir, "index.html") 
        try:
            urllib.urlopen(output_path)
        except IOError as e:
            if test:
                return False
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     str(e))
        else:
            if test:
                return True
            webbrowser.open(output_path, new=True, autoraise=True)
            self.statusbar.set_status_text(rosie.browser.STATUS_OPENING_LOG, 
                                       instant=True)


    def handle_view_web(self, *args):
        """View a suite's web source URL."""
        this_id = SuiteId(id_text=self.get_selected_suite_id())
        webbrowser.open(this_id.to_web(), new=True, autoraise=True)
        self.statusbar.set_status_text(rosie.browser.STATUS_OPENING_WEB, 
                                       instant=True)

    def initial_filter(self, opts, args):
        """Get some initial results to display on startup."""

        if not args:
            self.advanced_search_widget.add_filter()
            return
        elif args == "list_my_suites":
            self.display_local_suites()
            self.advanced_search_widget.add_filter()
            return
        elif not opts.query and not opts.search and not opts.url:
            if args[0].startswith("http"):
                opts.url = True
            else:
                opts.search = True 

        if not opts.query:
            self.advanced_search_widget.add_filter()

        if opts.url:
            self.nav_bar.address_box.child.set_text(args[0])
            self.address_bar_handler(None, True, True)
            return
        elif opts.search:
            self.history_button.set_active(opts.all_revs)
            self.nav_bar.simple_search_entry.set_text(' '.join(args))
            self.handle_search()
            return
        elif opts.query:
            self.nav_bar.expander.child.toggle(False)
            try:
                args = [rose.env.environment_variable_process(arg) for arg in args]
            except rose.env.UnboundEnvironmentVariableError as e:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                         str(e),
                                         rosie.browser.TITLE_INVALID_QUERY)
                self.advanced_search_widget.add_filter()
                return
            filters = rosie.ws_client.query_split(args)
            if filters is None:
                self.advanced_search_widget.add_filter()
                return
            for filter_pieces in rosie.ws_client.query_split(args):
                if not self.advanced_search_widget.add_filter(filter_pieces):
                    break
            else:
                self.history_button.set_active(opts.all_revs)
                self.handle_query()
                self.handle_update_treeview(sort_title="revision",
                                            descending=True)
                
        return
            
    def launch_help(self, *args):
        """Launch a browser to open the help url."""
        webbrowser.open(rose.resource.ResourceLocator.default().get_doc_url() +
                        rosie.browser.HELP_FILE, new=True, autoraise=True)
        self.statusbar.set_status_text(rosie.browser.STATUS_OPENING_HELP, 
                                       instant=True)
        return False
    
    def pop_treeview_history(self):
        """Populate the search history list."""
        self.history_pane.pop_treeview_history(self.hist.get_archive())

    def popup_tree_menu(self, path, col, event):
        """Launch a menu for this main treeview row."""
        columns = [c.get_widget().get_text()
                   for c in self.display_box.treeview.get_columns()]
        suite_col_index = columns.index("idx")
        model = self.display_box.treeview.get_model()
        this_iter = model.get_iter(path)
        idx = model.get_value(this_iter, suite_col_index)
        col_index = self.display_box.treeview.get_columns().index(col)
        col_widget = self.display_box.treeview.get_columns()[col_index].get_widget()
        col_name = col_widget.get_text()
        ui_config_string = """<ui> <popup name='Popup'>
                              <menuitem action="Info"/>
                              <separator name="actionsep"/>
                              <menuitem action="Edit"/>
                              <menuitem action="Checkout"/>
                              <menuitem action="Delete Working Copy"/>
                              <menuitem action="Delete"/>
                              <menuitem action="Copy"/>
                              <separator name="urlssep"/>
                              <menuitem action="View Web"/>
                              <menuitem action="View Output"/>
                              <menuitem action="Terminal"/>
                              <separator name="schedsep"/>
                              <menuitem action="Scheduler"/>
                              <separator name="runsep"/>
                              <menuitem action="Run"/>
                              <menuitem action="Run custom"/>
                              <separator name="groupsep"/>
                              <menuitem action="Group"/>
                              <menuitem action="Ungroup"/>
                              </popup> </ui>"""
        actions = [("Info", gtk.STOCK_INFO,
                    rosie.browser.RESULT_MENU_INFO_SUITE),
                   ("Edit", gtk.STOCK_EDIT,
                    rosie.browser.RESULT_MENU_EDIT_SUITE),
                   ("Checkout", gtk.STOCK_GO_DOWN,
                    rosie.browser.RESULT_MENU_CHECKOUT_SUITE),
                   ("Copy", gtk.STOCK_COPY,
                    rosie.browser.RESULT_MENU_COPY_SUITE),
                   ("Delete Working Copy", gtk.STOCK_CLOSE,
                    rosie.browser.RESULT_MENU_DELETE_LOCAL_SUITE),
                   ("Delete", gtk.STOCK_CLOSE,
                    rosie.browser.RESULT_MENU_DELETE_SUITE),
                   ("View Web", gtk.STOCK_ABOUT,
                    rosie.browser.RESULT_MENU_VIEW_SOURCE_SUITE),
                   ("View Output", gtk.STOCK_DIRECTORY,
                    rosie.browser.RESULT_MENU_VIEW_OUTPUT_SUITE),
                   ("Terminal", gtk.STOCK_EXECUTE,
                    rosie.browser.RESULT_MENU_LAUNCH_TERMINAL),
                   ("Scheduler", gtk.STOCK_MISSING_IMAGE,
                    rosie.browser.RESULT_MENU_SCHEDULER),
                   ("Run", gtk.STOCK_MEDIA_PLAY,
                    rosie.browser.RESULT_MENU_RUN_SUITE),
                   ("Run custom", gtk.STOCK_MEDIA_PLAY,
                    rosie.browser.RESULT_MENU_RUN_SUITE_CUSTOM),
                   ("Group", gtk.STOCK_CONNECT,
                    rosie.browser.RESULT_MENU_GROUP_COL),
                   ("Ungroup", gtk.STOCK_DISCONNECT,
                    rosie.browser.RESULT_MENU_UNGROUP)]
        uimanager = gtk.UIManager()
        actiongroup = gtk.ActionGroup("Popup")
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(ui_config_string)
        status = self.display_box._get_treeview_path_status(path)
        can_edit = (status in [rosie.ws_client.STATUS_OK,
                               rosie.ws_client.STATUS_MO])
        can_checkout = (status == rosie.ws_client.STATUS_NO)
        info_item = uimanager.get_widget("/Popup/Info")
        info_item.connect("activate", self.handle_info)
        edit_item = uimanager.get_widget("/Popup/Edit")
        edit_item.connect("activate", self.handle_edit)
        edit_item.set_sensitive(can_edit)
        check_item = uimanager.get_widget("/Popup/Checkout")
        check_item.connect("activate", self.handle_checkout)
        check_item.set_sensitive(can_checkout)
        copy_item = uimanager.get_widget("/Popup/Copy")
        copy_item.connect("activate", self.handle_copy)
        delete_working_item = uimanager.get_widget(
                                        "/Popup/Delete Working Copy")
        delete_working_item.connect("activate", self.handle_delete_local)
        delete_working_item.set_sensitive(status == rosie.ws_client.STATUS_OK)
        delete_item = uimanager.get_widget("/Popup/Delete")
        delete_item.connect("activate", self.handle_delete)
        source_item = uimanager.get_widget("/Popup/View Web")
        source_item.connect("activate", self.handle_view_web)
        output_item = uimanager.get_widget("/Popup/View Output")
        output_item.connect("activate", self.handle_view_output)
        output_item.set_sensitive(self.handle_view_output(test=True,
                                                          path=path))
        term_item = uimanager.get_widget("/Popup/Terminal")
        term_item.connect("activate", self.handle_launch_terminal)
        term_item.set_sensitive(not can_checkout)
        sched_item = uimanager.get_widget("/Popup/Scheduler")
        sched_item.set_image(self._get_sched_image())
        sched_item.connect("activate", self.handle_run_scheduler)
        sched_item.set_sensitive(can_edit)
        run_item = uimanager.get_widget("/Popup/Run")
        run_item.connect("activate", self.handle_run)
        run_item.set_sensitive(can_edit)
        run_custom_item = uimanager.get_widget("/Popup/Run custom")
        run_custom_item.connect("activate", self.handle_run_custom)
        run_custom_item.set_sensitive(can_edit)
        group_item = uimanager.get_widget("/Popup/Group")
        group_item.col_name = col_name
        group_item.connect("activate", self.handle_grouping)
        display_group_index = self.display_box.group_index
        if self.get_tree_columns().index(col_name) == display_group_index:
            group_item.set_sensitive(False)
        ungroup_item = uimanager.get_widget("/Popup/Ungroup")
        ungroup_item.col_name = None
        ungroup_item.connect("activate", self.handle_grouping)
        if self.display_box.group_index is None:
            ungroup_item.set_sensitive(False)
        menu = uimanager.get_widget('/Popup')
        menu.popup(None, None, None, event.button, event.time)
        return False

    def _run_suite(self, args=None, **kwargs):
        """Run the suite, if possible."""
        if not isinstance(args, list):
            args = []
        for key, value in kwargs.items():
            args.extend([key, value])
        suite_local_copy = SuiteId(
                            self.get_selected_suite_id()).to_local_copy()
        args = ["-C", suite_local_copy] + args
        rose.gtk.run.run_suite(*args)
        return False

    def _run_suite_check_args(self, args):
        """Check args and run suite."""
        if args is None:
            return False
        self._run_suite(args)

    def set_config(self, editor, config):
        """Assign the updated config."""
        config = editor.output_config_objects()['/discovery']
        return config

    def set_query_filters(self, filters):
        """Clear the front end filters and populate with specified filters."""
        self.advanced_search_widget.remove_filter()
        self.nav_bar.expander.child.toggle(False)
        filters = " ".join(filters).split(" ")
        for f in rosie.ws_client.query_split(filters):
            self.advanced_search_widget.add_filter(f)

    def set_search_details(self, s_type, s_params, s_use_hist):
        """Set the front end search and query details."""
        self.history_button.set_active(s_use_hist)
        if s_type == "query":
            self.nav_bar.simple_search_entry.set_text("")
            self.set_query_filters(ast.literal_eval(s_params))
        elif s_type == "search":
            self.clear_filters()
            self.nav_bar.simple_search_entry.set_text(str(s_params))
        elif s_type == "url":
            self.clear_filters()
            self.nav_bar.simple_search_entry.set_text("")
            self.nav_bar.address_box.child.set_text(s_params)

    def set_ws_client(self, prefix):
        """Load a web client to interrogate."""
        self.search_manager.set_datasource(prefix=prefix)

    def setup_navbar(self):
        """Sets up the navigation bar."""
        self.nav_bar = rosie.browser.util.AddressBar(
                                self.advanced_search_widget.toggle_visibility,
                                rosie.browser.TIP_SHOW_HIDE_BUTTON)
        
        self.nav_bar.previous_search_button.child.connect("clicked", 
                                                  self.handle_previous_search)
        self.nav_bar.next_search_button.child.connect("clicked", 
                                              self.handle_next_search)
        self.nav_bar.address_box.child.connect("activate", 
                                               self.address_bar_handler,
                                                True, True)
        self.nav_bar.address_box.connect('changed', 
                                         self.address_bar_handler,
                                         False, False)
        self.nav_bar.pop_address_box(self.hist.get_archive())                
        self.nav_bar.refresh_button.child.connect("clicked", 
                                                  self.handle_refresh,
                                                  False)
        self.nav_bar.home_button.child.connect("clicked",
                                               self.display_local_suites)
        self.nav_bar.simple_search_entry.connect("activate", 
                                                 self.handle_search)        
        self.nav_bar.search_button.child.connect("clicked", 
                                                 self.handle_search)

    def show_search_history(self,widget):
        """Toggle the display of the search history."""
        search_history = widget.get_active()
        if search_history:
            self.history_pane.show()
        else:
            self.history_pane.hide()        

    def toggle_advanced_controls(self, widget=None):
        """Toggle the display of advanced search controls."""
        active = self.advanced_search_widget.adv_control_menuitem.get_active()
        if active == self.advanced_search_widget.adv_controls_on:
            return False
        self.advanced_search_widget.adv_controls_on = active
        self.advanced_search_widget.set_show_controls()

    def toggle_history(self, widget):
        """Toggle the display of superceded or deleted suites."""
        search_history = widget.get_active()
        if search_history == self.search_history:
            return False
        self.search_history = search_history
        if isinstance(widget, gtk.CheckButton):
            self.history_menuitem.set_active(search_history)
        elif isinstance(widget, gtk.CheckMenuItem):
            self.history_button.set_active(search_history)
        return False
        
    def update_filter_grouping(self):
        """Update grouping of filters."""
        group_num = 0
        for child in reversed(self.filter_table.get_children()):
            if isinstance(child, rosie.browser.util.ConjunctionWidget):
                child.update_indent(group_num)
            if isinstance(child, rosie.browser.util.BracketWidget):
                if child.is_end:
                    group_num -= child.number
                else:
                    group_num += child.number
                    
    def update_toolbar_sensitivity(self, path):
        """Control the sensitivity of toolbar buttons."""
        self.toolbar.set_widget_sensitive("Copy", path is not None)
        self.toolbar.set_widget_sensitive("View Web", path is not None)
        self.toolbar.set_widget_sensitive("View Output", path is not None)
        self.toolbar.set_widget_sensitive("Launch Terminal", path is not None)
        self.toolbar.set_widget_sensitive("Launch Scheduler",
                                          path is not None)
        if path is not None:
            status = self.display_box._get_treeview_path_status(path)
            can_edit = (status in [rosie.ws_client.STATUS_OK,
                                   rosie.ws_client.STATUS_MO])
            can_checkout = (status == rosie.ws_client.STATUS_NO)
            has_output = self.handle_view_output(test=True)
            self.toolbar.set_widget_sensitive("Edit", can_edit)
            self.toolbar.set_widget_sensitive("Checkout", can_checkout)
            self.toolbar.set_widget_sensitive("View Output", has_output)
            self.toolbar.set_widget_sensitive("Launch Terminal",
                                              not can_checkout)
            self.toolbar.set_widget_sensitive("Launch Scheduler", can_edit)
            self.run_button.set_sensitive(can_edit)


if __name__ == "__main__":

    opt_parser = RoseOptionParser().add_my_options("all_revs",
                                                   "prefix", "query", 
                                                   "search", "url")   
    opts, args = opt_parser.parse_args()

    if not args:
        args = rosie.browser.DEFAULT_QUERY
    sys.path.append(os.getenv('ROSE_HOME'))
    rose.gtk.util.setup_stock_icons()
    rose.gtk.util.set_exception_hook()
    MainWindow(opts, args)
    gtk.settings_get_default().set_long_property("gtk-button-images",
                                                 True, "main")
    gtk.settings_get_default().set_long_property("gtk-menu-images",
                                                 True, "main")
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()
    try:
        gtk.main()
    finally:
        gtk.gdk.threads_leave()
        for thread in threading.enumerate():
            if hasattr(thread, "stop"):
                thread.stop()
