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

import sys

import pygtk
pygtk.require("2.0")
import gtk

import rose.external
import rose.gtk.util
from rose.opt_parse import RoseOptionParser
import rosie.browser
from rosie.suite_id import SuiteId


class AddressBar(rose.gtk.util.ToolBar):

    """Custom address bar widget"""

    def __init__(self, expand_control=None, expander_tip=None):
        """Create a search box and button in the toolbar."""
        super(AddressBar, self).__init__()        
        
        self.previous_search_button = gtk.ToolItem()
        button = rose.gtk.util.CustomButton(stock_id=gtk.STOCK_GO_BACK,
                                            as_tool=True)
        self.previous_search_button.add(button)
        self.previous_search_button.set_tooltip_text(
                                                rosie.browser.TIP_PREV_SEARCH)
        self.previous_search_button.set_sensitive(False)
        self.previous_search_button.show()
        self.insert(self.previous_search_button, -1)   
        self.next_search_button = gtk.ToolItem()
        button = rose.gtk.util.CustomButton(stock_id=gtk.STOCK_GO_FORWARD,
                                            as_tool=True)
        self.next_search_button.add(button)
        self.next_search_button.set_tooltip_text(rosie.browser.TIP_NEXT_SEARCH)
        self.next_search_button.set_sensitive(False)
        self.next_search_button.show()
        self.insert(self.next_search_button, -1)
        self.address_box = gtk.combo_box_entry_new_text()
        self.address_box.show()
        
        self.address_box.set_tooltip_text(rosie.browser.TIP_ADDRESS_BAR)
        address_toolitem = gtk.ToolItem()
        address_toolitem.add(self.address_box)
        address_toolitem.set_expand(True)
        address_toolitem.show()
        self.insert(address_toolitem, -1)
                           
        self.refresh_button = gtk.ToolItem()
        button = rose.gtk.util.CustomButton(stock_id=gtk.STOCK_REFRESH,
                                            as_tool=True)
        self.refresh_button.add(button)
        self.refresh_button.set_tooltip_text(rosie.browser.TIP_REFRESH)
        self.refresh_button.set_sensitive(True)
        self.refresh_button.show()
        self.insert(self.refresh_button, -1)
        
        self.home_button = gtk.ToolItem()
        button = rose.gtk.util.CustomButton(stock_id=gtk.STOCK_HOME,
                                            as_tool=True)
        self.home_button.add(button)
        self.home_button.set_tooltip_text(rosie.browser.TIP_LOCAL_SUITES)
        self.home_button.set_sensitive(True)
        self.home_button.show()
        self.insert(self.home_button, -1)        
        self.simple_search_entry = gtk.Entry()
        self.simple_search_entry.show()
        self.simple_search_entry.set_width_chars(20)
        self.simple_search_entry.set_tooltip_text(
                           rosie.browser.TIP_SEARCH_SIMPLE_ENTRY)
        search_toolitem = gtk.ToolItem()
        search_toolitem.add(self.simple_search_entry)
        search_toolitem.show()
        self.insert(search_toolitem, -1)
        
        image = gtk.image_new_from_stock(gtk.STOCK_FIND,
                                         gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.search_button = gtk.ToolItem()
        button = rose.gtk.util.CustomButton(
                               label=rosie.browser.LABEL_SEARCH_SIMPLE,
                               stock_id=gtk.STOCK_FIND,
                               as_tool=True)
        self.search_button.add(button)
        self.search_button.set_tooltip_text(rosie.browser.TIP_SEARCH_BUTTON)
        self.search_button.show()
        self.insert(self.search_button, -1)

        if expand_control is not None:
            self.expander = gtk.ToolItem()
            button = rose.gtk.util.CustomExpandButton(
                                   expander_function=expand_control,
                                   as_tool=True)
            self.expander.add(button)
            if expander_tip is not None:
                self.expander.set_tooltip_text(expander_tip)
            self.insert(self.expander, -1)
            self.expander.show()

    def clear_address_box(self, widget=None):
        """Clears the entries from the address box"""
        self.address_box.clear()
        
    def pop_address_box(self, hist):
        """Populates the address box on startup."""
        for h in hist:
            if h.h_type == "url":
                if (self.address_box.get_model().iter_n_children(None) < 
                                                rosie.browser.SIZE_ADDRESS):
                    self.address_box.append_text(h.details)
                else:
                    break
                    

class BracketWidget(gtk.HBox):

    """Class to represent a group start or end."""

    CHARS = ["(", ")"]
    MAX_NUM = 5

    def __init__(self, number=0, is_end=False, change_hook=None,
                 show_controls=False):
        super(BracketWidget, self).__init__()
        self.number = number
        self.is_end = is_end
        self.change_hook = change_hook
        self.show_controls = show_controls
        self.combo_box = gtk.combo_box_new_text()
        self.char = self.CHARS[is_end]
        for n in range(max(number, self.MAX_NUM) + 1):
            self.combo_box.append_text(self.char * n)
        self.combo_box.set_active(number)
        self.combo_box.connect("changed", self.change_number)
        self.combo_box.show()
        self.pack_start(self.combo_box, expand=False, fill=False,
                        padding=5)
        self.set_show_controls()

    def set_show_controls(self, show_controls=None):
        """Set whether the bracket controls should be displayed."""
        if show_controls is not None:
            self.show_controls = show_controls
        if self.show_controls:
            self.show()
        else:
            self.hide()

    def change_number(self, *args):
        """Add or remove a group character."""
        self.number = self.combo_box.get_active()
        if self.change_hook is not None:
            self.change_hook()

    def get_text(self):
        """Return the text representation of the grouping data."""
        return self.char * self.number


class ConjunctionWidget(gtk.HBox):

    """Represent the and/or and indentation for a query widget."""

    INDENT_STRING = " " * 8

    def __init__(self, choices, indent=0):
        super(ConjunctionWidget, self).__init__()
        self.indent = indent
        self.combo = gtk.combo_box_new_text()
        for conjunction in choices:
            self.combo.append_text(conjunction)
        self.combo.show()
        self.combo.set_tooltip_text(rosie.browser.TIP_FILTER_OPERATOR)
        self.combo.set_active(0)
        self.indent_label = gtk.Label()
        self.indent_label.show()
        filler_label = gtk.Label()
        filler_label.show()
        self.pack_start(self.indent_label, expand=False, fill=False)
        self.pack_start(self.combo, expand=False, fill=False)
        self.pack_end(filler_label, expand=True, fill=True)
        self.update_indent()
        self.show()

    def incr_indent(self, extra_indent):
        """Add extra indentation to the existing amount."""
        self.indent += extra_indent
        self.update_indent()

    def update_indent(self, new_indent=None):
        """Update the indentation, optionally setting it with new_indent."""
        if new_indent is not None:
            self.indent = new_indent
        self.indent_label.set_text(self.INDENT_STRING * self.indent)


class FilterError(Exception):

    pass


class HistoryTreeview(gtk.VBox):

    """History treeview custom widget"""

    def __init__(self):
        """Generate a treeview for viewing search history"""
        super(HistoryTreeview, self).__init__()
        self.treestore_hist = gtk.TreeStore(str, str, bool)
        self.treeview_hist = gtk.TreeView(self.treestore_hist)
        self.treeview_hist.show()
        self.treeview_hist.set_rules_hint(True)
        self.treeview_scroll_hist = gtk.ScrolledWindow()
        self.treeview_scroll_hist.set_policy(gtk.POLICY_AUTOMATIC,
                                             gtk.POLICY_AUTOMATIC)
        self.treeview_scroll_hist.add(self.treeview_hist)
        self.treeview_scroll_hist.set_shadow_type(gtk.SHADOW_IN)
        cols = [rosie.browser.HISTORY_TREEVIEW_TYPE,       
                rosie.browser.HISTORY_TREEVIEW_PARAMETERS,
                rosie.browser.HISTORY_TREEVIEW_ALL_REVISIONS]
        for i, title in enumerate(cols):
            col = gtk.TreeViewColumn()
            col.set_title(title.replace("_", "__"))

            if title != rosie.browser.HISTORY_TREEVIEW_ALL_REVISIONS:
                cell = gtk.CellRendererText()
                col.pack_start(cell)
                col.add_attribute(cell, attribute='text',
                                  column=i)
            else:
                cell = gtk.CellRendererToggle()
                col.pack_start(cell)
                col.add_attribute(cell, attribute='active',
                                  column=i)

            col.set_sort_column_id(i)
            col.set_resizable(True)
            self.treeview_hist.append_column(col)
        self.treeview_hist.set_search_column(1)
        self.close_pane = gtk.HBox()
        self.close_button = rose.gtk.util.CustomButton(
                             stock_id=gtk.STOCK_CLOSE,
                             tip_text=rosie.browser.TIP_CLOSE_HISTORY_BUTTON)
        
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        setattr(style, "inner-border", [0, 0, 0, 0] )
        self.close_button.modify_style(style)     
                             
        self.close_button.show()
        label = gtk.Label()
        label.set_text(rosie.browser.LABEL_HISTORY_TREEVIEW)                     
        label.show()
        self.close_pane.pack_end(self.close_button, expand=False, fill=False)
        self.close_pane.pack_start(label, expand=False, fill=False, padding=5)
        self.close_pane.show()        
        self.pack_start(self.close_pane, expand=False, fill=False)
        self.pack_start(self.treeview_scroll_hist, padding=5)
        self.treeview_scroll_hist.show()                            

    def clear_treestore_history(self, widget=None):
        """Clear the history treeview"""
        self.treestore_hist.clear()

    def pop_treeview_history(self, archive):
        """Populate the search history list"""
        for h in archive:
            if h.h_type == "query":
                msg = "["
                for m in range(len(h.details) - 1):
                    msg = msg + "'" + h.details[m] + "', "
                msg = msg + "'" + h.details[-1] + "']"
                self.treestore_hist.append(None, [h.h_type,
                                                  msg, h.search_history])
            else:
                self.treestore_hist.append(None, [h.h_type, str(h.details),
                                                  h.search_history])
                                                  

class MenuBar(object):

    """Generate the menu bar, using the GTK UIManager.

    Parses the settings in 'ui_config_string'. Connection of buttons is done
    at a higher level.

    """

    ui_config_string = """<ui>
    <menubar name="TopMenuBar">
      <menu action="File">
        <menuitem action="New Suite"/>
        <menuitem action="Quit"/>
      </menu>
      <menu action="Edit">
        <menu action="Source"></menu>
        <menuitem action="Preferences"/>
      </menu>
      <menu action="View">
        <separator name="view-adv-control-sep"/>
        <menuitem action="View advanced controls"/>
        <separator name="view-hist-sep"/>
        <menuitem action="Include history"/>
      </menu>
      <menu action="History">
        <menuitem action="Show search history"/>
        <separator name="clear-hist-sep"/>
        <menuitem action="Clear history"/>
      </menu>          
      <menu action="Help">
        <menuitem action="GUI Help"/>
        <menuitem action="About"/>
      </menu>
    </menubar>
    </ui>"""

    action_details = [('File', None, rosie.browser.TOP_MENU_FILE),
                      ('New Suite', gtk.STOCK_NEW, 
                       rosie.browser.TOP_MENU_NEW_SUITE, 
                       rose.config_editor.ACCEL_NEW),
                      ('Quit', gtk.STOCK_QUIT, rosie.browser.TOP_MENU_QUIT, 
                       rose.config_editor.ACCEL_QUIT),
                      ('Edit', None, rosie.browser.TOP_MENU_EDIT),
                      ('Source', gtk.STOCK_NETWORK, 
                       rosie.browser.TOP_MENU_SOURCE),
                      ('Preferences', gtk.STOCK_PREFERENCES, 
                       rosie.browser.TOP_MENU_PREFERENCES),
                      ('View', None, rosie.browser.TOP_MENU_VIEW),
                      ('History', None, rosie.browser.TOP_MENU_HISTORY),
                      ('Clear history', gtk.STOCK_CLEAR, 
                       rosie.browser.TOP_MENU_CLEAR_HISTORY),                                             
                      ('Help', None, rosie.browser.TOP_MENU_HELP),
                      ('GUI Help', gtk.STOCK_HELP, 
                       rosie.browser.TOP_MENU_GUI_HELP, 
                       rose.config_editor.ACCEL_HELP_GUI),
                      ('About', gtk.STOCK_DIALOG_INFO, 
                       rosie.browser.TOP_MENU_ABOUT)]

    radio_action_details = []

    toggle_action_details = [
                             ('View advanced controls', None,
                              'View advanced _controls'),
                             ('Include history', None,
                              rosie.browser.TOGGLE_ACTION_VIEW_ALL_REVISIONS),
                             ('Show search history', None,
                              rosie.browser.TOGGLE_ACTION_VIEW_SEARCH_HISTORY, 
                              rosie.browser.ACCEL_HISTORY_SHOW)]

    def __init__(self, known_keys):
        self.known_keys = known_keys
        self.uimanager = gtk.UIManager()
        self.actiongroup = gtk.ActionGroup('MenuBar')
        self.add_prefix_choices()
        self.add_key_choices()
        self.actiongroup.add_actions(self.action_details)
        self.actiongroup.add_radio_actions(self.radio_action_details)
        self.actiongroup.add_toggle_actions(self.toggle_action_details)
        self.uimanager.insert_action_group(self.actiongroup, pos=0)
        self.uimanager.add_ui_from_string(self.ui_config_string)

    def add_prefix_choices(self):
        """Add the prefix choices."""
        self.prefixes = SuiteId.get_prefix_locations().keys()
        self.prefixes.sort()
        self.prefixes.reverse()
        for prefix in self.prefixes:
            search = '<menu action="Source">'
            repl = search + '<menuitem action="_{0}_"/>'.format(prefix)
            self.ui_config_string = self.ui_config_string.replace(
                                            search, repl, 1)
            self.radio_action_details.append(
                              ("_{0}_".format(prefix), None, prefix))
                              
    def add_key_choices(self):
        """Add the key choices."""
        
        for key in list(reversed(self.known_keys)):
            view = '<menu action="View">'
            repl = view + '<menuitem action="View _{0}_"/>'.format(key)
            self.ui_config_string = self.ui_config_string.replace(
                                            view, repl, 1)
            self.toggle_action_details.append(
                                ("View _{0}_".format(key), None, 
                                 "View " + key.replace("_","__")))
    
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


class StatusBarWidget(gtk.VBox):

    """Class to create a statusbar with a datasource box, messagebox and a 
       progressbar."""

    def __init__(self, prefix=""):
        """Generate the status bar."""
        super(StatusBarWidget, self).__init__()
        self.statusbar = gtk.VBox()
        hline = gtk.HSeparator()
        self.statusbar.pack_start(hline)
        hline.show()
        
        hbox = gtk.HBox()
        
        self.datasource_display = rose.gtk.util.AsyncLabel()
        self.datasource_display.set_text(prefix)
        self.datasource_display.set_width_chars(rosie.browser.PREFIX_LEN)
        self.datasource_display.set_justify(gtk.JUSTIFY_CENTER)
        self.datasource_display.set_tooltip_text(
                                            rosie.browser.TIP_STATUSBAR_SOURCE)
        hbox.pack_start(self.datasource_display, expand=False,
                                  fill=False)
        self.datasource_display.show()
        vline = gtk.VSeparator()
        vline.show()
        hbox.pack_start(vline, expand=False, fill=False)
        
        self.statusbox = rose.gtk.util.AsyncLabel()
        x, y = self.statusbox.get_alignment()
        self.statusbox.set_alignment(0, y)
        hbox.pack_start(self.statusbox, expand=True, fill=True, padding=5)
        self.statusbox.show()
        self.progressbar = rose.gtk.util.ThreadedProgressBar(adjustment=None)
        self.statusbox.set_size_request(-1,
                                        self.progressbar.size_request()[1])
        hbox.pack_start(self.progressbar, expand=False, fill=False)
        #only show the progressbar when in use
        hbox.show()
        self.statusbar.pack_start(hbox, fill=True)
        self.statusbar.show()
        
        self.pack_start(self.statusbar, fill=True)
        self.show()
        
    def set_datasource(self, prefix):
        """Set the datasource to display on the statusbar."""
        self.datasource_display.set_text(prefix)

    def set_status_text(self, msg, instant=True):
        """Set the statusbar text."""
        self.statusbox.put(msg, instant)       
        
    def set_progressbar_visible(self, visible=False):
        """Show/hide the progress bar."""
        if visible:
            self.progressbar.show()
        else:
            self.progressbar.hide()
            
    def set_progressbar_pulsing(self, pulsing=False):
        """Start/stop the progress bar pulsing.""" 
        if pulsing:
            self.progressbar.start_pulsing()
        else:               
            self.progressbar.stop_pulsing()  


class AdvancedSearchWidget(gtk.VBox):

    """Widget to create and manipulate the query panel"""

    def __init__(self, search_manager, adv_controls_on, query_handler, 
                 display_redrawer):
        """Create a list of filters and a "search" button."""
        super(AdvancedSearchWidget, self).__init__()         
        self.handle_query = query_handler
        self.adv_controls_on = adv_controls_on
        self.display_redrawer = display_redrawer
        try:
            known_keys = search_manager.ws_client.get_known_keys()
            query_operators = search_manager.ws_client.get_query_operators()
        except rosie.ws_client.QueryError as e:
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     str(e))
            sys.exit(str(e))
        self.display_columns = ["local"] + known_keys
        self.display_filters = {}
        for column in self.display_columns:
            self.display_filters.update(
                         {column:
                          column in rosie.browser.COLUMNS_SHOWN})
        self.filter_columns = [c for c in self.display_columns if c != "local"]
        self.filter_exprs = []
        for operator in query_operators:
            self.filter_exprs.append(operator)
        self.filter_ops = ["and", "or"]
        self.filter_table = gtk.Table(rows=6, columns=100, homogeneous=False)
        self.filter_table.show()
        self.num_filters = 0
        self.filter_expr_getters = []
        filter_scroll = gtk.ScrolledWindow()
        filter_scroll.set_policy(gtk.POLICY_AUTOMATIC,
                                 gtk.POLICY_AUTOMATIC)
        filter_scroll.show()
        filter_sub_scroll = gtk.HBox()
        filter_sub_scroll.show()
        filter_table_vbox = gtk.VBox(spacing=10)
        filter_table_vbox.show()
        filter_table_vbox.pack_start(self.filter_table,
                                     expand=False, fill=False)
        filter_sub_scroll.pack_start(filter_table_vbox,
                                     expand=True, fill=True)
        self.add_button = rose.gtk.util.CustomButton(
                          stock_id=gtk.STOCK_ADD,
                          label=rosie.browser.LABEL_ADD_FILTER,
                          tip_text=rosie.browser.TIP_ADD_FILTER_BUTTON)
        self.add_button.connect("clicked", lambda b: self.add_filter())
        self.search_button = rose.gtk.util.CustomButton(
                             stock_id=gtk.STOCK_FIND,
                             label=rosie.browser.LABEL_SEARCH_ADVANCED,
                             tip_text=rosie.browser.TIP_SEARCH_BUTTON)
        self.search_button.connect("clicked", self.handle_query)
        self.clear_button = rose.gtk.util.CustomButton(
                             stock_id=gtk.STOCK_CLEAR,
                             label=rosie.browser.LABEL_CLEAR_ADVANCED,
                             tip_text=rosie.browser.TIP_CLEAR_BUTTON)
        self.clear_button.connect("clicked", self.clear_filters)
        
        button_bar = gtk.HBox()
        button_bar.pack_end(self.search_button, expand=False, fill=False)
        button_bar.pack_end(self.add_button, expand=False, fill=False)
        button_bar.pack_start(self.clear_button, expand=False, fill=False)
        button_bar.show()
        
        self.button_top_vbox = gtk.VBox()
        filter_scroll.add_with_viewport(filter_sub_scroll)
        filter_scroll.get_child().set_shadow_type(gtk.SHADOW_NONE)
        self.button_top_vbox.pack_start(filter_scroll, expand=True, fill=True,
                                        padding=5)
        self.pack_start(self.button_top_vbox, expand=True, fill=True)
        self.pack_start(button_bar, expand=False, fill=False)
        self.connect("expose-event",
                     lambda w, e: self.filter_table.check_resize())
        self.button_top_vbox.show()     
        self.filter_scroll = filter_scroll
        self.toggle_visibility(None, False)

    def add_filter(self, query_pieces=None):
        """Create a row of widgets for a filter."""
        added_ok = True
        close_button = rose.gtk.util.CustomButton(
                            stock_id=gtk.STOCK_CLOSE,
                            tip_text=rosie.browser.TIP_REMOVE_FILTER_BUTTON,
                            as_tool=True)
        conj_box = rosie.browser.util.ConjunctionWidget(
                                             choices=self.filter_ops)
        left_group_num = 0
        column_combo = gtk.combo_box_new_text()
        for column in self.filter_columns:
            column_combo.append_text(column)
        column_combo.show()
        column_combo.set_tooltip_text(rosie.browser.TIP_FILTER_COLUMN)
        expr_combo = gtk.combo_box_new_text()
        for expr in self.filter_exprs:
            expr_combo.append_text(expr)
        expr_combo.show()
        expr_combo.set_tooltip_text(rosie.browser.TIP_FILTER_ACTION)
        string_entry = gtk.Entry()
        string_entry.show()
        string_entry.set_tooltip_text(rosie.browser.TIP_FILTER_TEXT)
        string_entry.connect("activate", self.handle_query)
        right_group_num = 0
        if query_pieces:
            if len(query_pieces) > 1:
                if all([s == "(" for s in query_pieces[1]]):
                    left_group_num = len(query_pieces.pop(1))
                if all([s == ")" for s in query_pieces[-1]]):
                    right_group_num = len(query_pieces.pop(-1))
            while len(query_pieces) > 4:
                query_pieces[3] += " " + query_pieces.pop(4)
            try:
                if len(query_pieces) == 3:  #catch for empty string searches
                    query_pieces.append('')
                conjunction, col, expr, text = query_pieces
            except ValueError:
                added_ok = False
                self.run_invalid_query_dialog(" ".join(query_pieces))
            else:
                try:
                    conj_box.combo.set_active(
                                   self.filter_ops.index(conjunction))
                except (IndexError, ValueError):
                    added_ok = False
                    self.run_invalid_query_dialog(conjunction)
                try:
                    column_combo.set_active(self.filter_columns.index(col))
                except (IndexError, ValueError):
                    added_ok = False
                    self.run_invalid_query_dialog(col)
                try:
                    expr_combo.set_active(self.filter_exprs.index(expr))
                except (IndexError, ValueError):
                    added_ok = False
                    self.run_invalid_query_dialog(expr)
                string_entry.set_text(text)
        if not added_ok:
            return False
        left_bracket_box = rosie.browser.util.BracketWidget(
                                      number=left_group_num,
                                      is_end=False,
                                      change_hook=self.update_filter_grouping)
        right_bracket_box = rosie.browser.util.BracketWidget(
                                      number=right_group_num,
                                      is_end=True,
                                      change_hook=self.update_filter_grouping)
        getter = lambda: self.get_filter(conj_box.combo, left_bracket_box,
                                         column_combo, expr_combo,
                                         string_entry, right_bracket_box)
        self.filter_expr_getters.append(getter)
        lowest_row = -1
        for child in self.filter_table.get_children():
            child_row = self.filter_table.child_get(child, 'top_attach')[0]
            if child_row > lowest_row:
                lowest_row = child_row
        this_row = lowest_row + 1
        self.filter_table.attach(
                          conj_box,
                          0, 1,
                          this_row, this_row + 1,
                          xoptions=gtk.FILL,
                          xpadding=5,
                          ypadding=5)
        if self.filter_table.get_children()[-1] == conj_box:
            conj_box.set_sensitive(False)
        self.filter_table.attach(
                         left_bracket_box,
                         1, 2,
                         this_row, this_row + 1,
                         xoptions=gtk.FILL,
                         ypadding=5)
        self.filter_table.attach(
                         column_combo,
                         2, 3,
                         this_row, this_row + 1,
                         xoptions=gtk.FILL,
                         xpadding=5,
                         ypadding=5)
        self.filter_table.attach(
                         expr_combo,
                         3, 4,
                         this_row, this_row + 1,
                         xoptions=gtk.FILL,
                         xpadding=5,
                         ypadding=5)
        self.filter_table.attach(
                         string_entry,
                         4, 5,
                         this_row, this_row + 1,
                         xoptions=gtk.EXPAND|gtk.FILL,
                         xpadding=5,
                         ypadding=5)
        self.filter_table.attach(
                         right_bracket_box,
                         5, 6,
                         this_row, this_row + 1,
                         xoptions=gtk.FILL,
                         ypadding=5)
        self.filter_table.attach(
                         close_button,
                         6, 7,
                         this_row, this_row + 1,
                         xoptions=gtk.FILL,
                         xpadding=5,
                         ypadding=5)
        close_button._number = this_row
        close_button.connect('clicked',
                             lambda b: self.remove_filter(b._number))
        self.num_filters += 1
        if self.num_filters == 1:
            close_button.set_sensitive(False)
        else:
            for widget in reversed(self.filter_table.get_children()):
                if hasattr(widget, "_number"):
                    widget.set_sensitive(True)
                    break
        self.filter_scroll.resize_children()
        self.update_filter_grouping()
        if left_group_num or right_group_num:
            self.adv_controls_on = True
        self.set_show_controls()
        return True

    def clear_filters(self, *args):
        """Remove all filters from the GUI."""
        self.remove_filter()
        added_ok = self.add_filter() 

    def get_filter(self, and_or_combo, left_bracket_box, column_combo,
                   expr_combo, string_entry, right_bracket_box):
        """Extract values from the widgets."""
        filter_strings = []
        for widget, f_list in [(and_or_combo, self.filter_ops),
                               (column_combo, self.filter_columns),
                               (expr_combo, self.filter_exprs)]:
            value = widget.get_active()
            if value == -1:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                              rosie.browser.DIALOG_MESSAGE_UNCOMPLETED_FILTER, 
                              rosie.browser.DIALOG_TITLE_UNCOMPLETED_FILTER)
                raise FilterError
            filter_strings.append(f_list[value])
            if widget == and_or_combo:
                left_bracket_text = left_bracket_box.get_text()
                if left_bracket_text:
                    filter_strings.append(left_bracket_text)
        filter_strings.append(string_entry.get_text())
        right_bracket_text = right_bracket_box.get_text()
        if right_bracket_text:
            filter_strings.append(right_bracket_text)
        return filter_strings

    def get_query(self):
        """Get the query from the filters."""
        filters = []
        group_num = 0        
        
        for function in self.filter_expr_getters: 
            try:
                filter_tuple = function()
            except FilterError:
                return None, False
            if filter_tuple is None:
                continue
            offset = 0
            if all([s == "(" for s in filter_tuple[1]]):
                group_num += len(filter_tuple[1])
                offset = 1
            if (len(filter_tuple) > 4 + offset and
                all([s == ")" for s in filter_tuple[-1]])):
                group_num -= len(filter_tuple[-1])
            filters.append(" ".join(filter_tuple))
        if group_num != 0:
            text = rosie.browser.ERROR_INVALID_QUERY.format(" ".join(filters))
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     text,
                                     rosie.browser.TITLE_INVALID_QUERY)
            return None, False      
    
        return filters, True

    def remove_filter(self, filter_number=None):
        """Remove a row of widgets for a filter."""
        for child in self.filter_table.get_children():
            top_row = self.filter_table.child_get(child, 'top_attach')[0]
            if top_row == filter_number or filter_number is None:
                self.filter_table.remove(child)
        if filter_number is None:
            self.filter_expr_getters = []
            self.num_filters = 0
        else:
            self.filter_expr_getters[filter_number] = lambda: None
            self.filter_table.get_children()[-1].set_sensitive(False)
            self.num_filters -= 1
            if self.num_filters == 1:
                for widget in reversed(self.filter_table.get_children()):
                    if hasattr(widget, "_number"):
                        widget.set_sensitive(False)
                        break   

    def run_invalid_query_dialog(self, error_info):
        """Notify the user of an invalid query."""
        text = rosie.browser.ERROR_INVALID_QUERY.format(error_info)
        rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                 text,
                                 rosie.browser.TITLE_INVALID_QUERY)

    def set_button_visibility(self, visible):
        """Set the visibility of the search, add and clear buttons"""
        if visible:
            self.search_button.show()
            self.add_button.show()
            self.clear_button.show()
        else:
            self.search_button.hide()
            self.add_button.hide()
            self.clear_button.hide()

    def set_show_controls(self):
        """Set the display of advanced search controls."""
        try:
            if self.adv_control_menuitem.get_active() != self.adv_controls_on:
                self.adv_control_menuitem.set_active(self.adv_controls_on)
        except:
            pass
        for child in self.filter_table.get_children():
            if isinstance(child, rosie.browser.util.BracketWidget):
                child.set_show_controls(self.adv_controls_on)  

    def toggle_visibility(self, widget=None, set_visibility=None):
        """Show/hide the filters menu"""
        
        if set_visibility:
            self.show()
        else:
            self.hide()
        self.display_redrawer()
        
    def update_filter_grouping(self):
        """Update the grouping of the filters."""
        group_num = 0
        for child in reversed(self.filter_table.get_children()):
            if isinstance(child, ConjunctionWidget):
                child.update_indent(group_num)
            if isinstance(child, BracketWidget):
                if child.is_end:
                    group_num -= child.number
                else:
                    group_num += child.number 
                    
        
def launch_about_dialog(self, *args):
    """Create a dialog showing the 'About' information."""
    return rose.gtk.util.run_about_dialog(
                rosie.browser.PROGRAM_NAME,
                rosie.browser.COPYRIGHT,
                rosie.browser.LOGO_PATH,
                rosie.browser.PROJECT_URL)      
