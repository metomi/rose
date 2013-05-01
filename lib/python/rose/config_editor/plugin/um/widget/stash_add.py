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

import pango
import pygtk
pygtk.require("2.0")
import gtk

import rose.config
import rose.config_editor
import rose.gtk.util


class AddStashDiagnosticsPanelv1(gtk.VBox):

    """Display a grouped set of stash requests to add."""

    STASH_PARSE_DESC_OPT = "name"
    STASH_PARSE_ITEM_OPT = "item"
    STASH_PARSE_SECT_OPT = "sectn"

    def __init__(self, stash_lookup, request_lookup,
                 changed_request_lookup, add_stash_request_func,
                 navigate_to_stash_request_func,
                 refresh_stash_requests_func):
        """Create a widget displaying STASHmaster information.

        stash_lookup is a nested dictionary that uses STASH section
        numbers and item numbers as a key chain to get the information
        about a specific record - e.g. stash_lookup[1][0]["name"] may
        return the 'name' (text description) for stash section 1, item
        0.

        request_lookup is a nested dictionary in the same form as stash
        lookup (section numbers, item numbers), but then contains
        a dictionary of relevant streq namelists vs option-value pairs
        as a sub-level - e.g. request_lookup[1][0].keys() gives all the
        relevant streq indices for stash section 1, item 0.
        request_lookup[1][0]["0abcd123"]["dom_name"] may give the
        domain profile name for the relevant namelist:streq(0abcd123).

        changed_request_lookup is a dictionary of changed streq
        namelists (keys) and their change description text (values).

        add_stash_request_func is a hook function that should take a
        STASH section number argument and a STASH item number argument,
        and add this request as a new namelist in a configuration.

        navigate_to_stash_request_func is a hook function that should
        take a streq namelist section id and search for it. It should
        display it if found.

        refresh_stash_requests_func is a hook function that should call
        the update_request_info method with updated streq namelist
        info.
        """
        super(AddStashDiagnosticsPanelv1, self).__init__(self)
        self.set_property("homogeneous", False)
        self.stash_lookup = stash_lookup
        self.request_lookup = request_lookup
        self.changed_request_lookup = changed_request_lookup
        self._add_stash_request = add_stash_request_func
        self.navigate_to_stash_request = navigate_to_stash_request_func
        self.refresh_stash_requests = refresh_stash_requests_func
        self.group_index = 0
        self.control_widget_hbox = self._get_control_widget_hbox()
        self.pack_start(self.control_widget_hbox, expand=False, fill=False)
        self._view = rose.gtk.util.TooltipTreeView(
                                   get_tooltip_func=self.set_tree_tip)
        self._view.set_rules_hint(True)
        self.sort_util = rose.gtk.util.TreeModelSortUtil(
                              lambda: self._view.get_model(), 2)
        self._view.show()
        self._view.connect("button-press-event",
                           self._handle_button_press_event)
        self._view.connect("cursor-changed",
                           lambda v: self._update_control_widget_sensitivity())
        self._window = gtk.ScrolledWindow()
        self._window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.generate_tree_view(is_startup=True)
        self._window.add(self._view)
        self._window.show()
        self.pack_start(self._window, expand=True, fill=True)
        self._update_control_widget_sensitivity()
        self.show()

    def add_cell_renderer_for_value(self, column):
        """Add a cell renderer to represent the model value."""
        cell_for_value = gtk.CellRendererText()
        column.pack_start(cell_for_value, expand=True)
        column.set_cell_data_func(cell_for_value,
                                  self._set_tree_cell_value)

    def add_stash_request(self, section, item):
        """Handle an add stash request call."""
        self._add_stash_request(section, item)
        self.refresh_stash_requests()

    def generate_tree_view(self, is_startup=False):
        """Create the summary of page data."""
        for column in self._view.get_columns():
            self._view.remove_column(column)
        self._view.set_model(self.get_tree_model())
        for i, column_name in enumerate(self.column_names):
            col = gtk.TreeViewColumn()
            col.set_title(column_name.replace("_", "__"))
            self.add_cell_renderer_for_value(col)
            if i < len(self.column_names) - 1:
                col.set_resizable(True)
            col.set_sort_column_id(i)
            self._view.append_column(col)
        if is_startup:
            group_model = gtk.TreeStore(str)
            group_model.append(None, [""])
            for i, name in enumerate(self.column_names):
                if name not in ["?", "#"]:
                    group_model.append(None, [name])
            self._group_widget.set_model(group_model)
            self._group_widget.set_active(self.group_index + 1)
            self._group_widget.connect("changed", self._handle_group_change)
        self.update_request_info()

    def get_model_data_and_columns(self):
        """Return a list of data tuples and columns"""
        data_rows = []
        columns = ["Section", "Item", "Description", "?", "#"]
        sections = self.stash_lookup.keys()
        sections.sort(self.sort_util.cmp_)
        mod_markup = rose.config_editor.SUMMARY_DATA_PANEL_MODIFIED_MARKUP
        props_excess = [self.STASH_PARSE_DESC_OPT, self.STASH_PARSE_ITEM_OPT,
                        self.STASH_PARSE_SECT_OPT]
        for section in sections:
            if section == "-1":
                continue
            items = self.stash_lookup[section].keys()
            items.sort(self.sort_util.cmp_)
            for item in items:
                data = self.stash_lookup[section][item]
                this_row = [section, item, data[self.STASH_PARSE_DESC_OPT]]
                this_row += ["", ""]
                for prop in sorted(data.keys()):
                    if prop not in props_excess:
                        this_row.append(data[prop])
                        if prop not in columns:
                            columns.append(prop)
                data_rows.append(this_row)
        return data_rows, columns

    def get_tree_model(self):
        """Construct a data model of other page data."""
        data_rows, cols = self.get_model_data_and_columns()
        data_rows, cols, rows_are_descendants = self._apply_grouping(
                            data_rows, cols, self.group_index)
        self.column_names = cols
        if data_rows:
            col_types = [str] * len(data_rows[0])
        else:
            col_types = []
        self._store = gtk.TreeStore(*col_types)
        parent_iter_ = None
        for i, row_data in enumerate(data_rows):
            if rows_are_descendants is None:
                self._store.append(None, row_data)
            elif rows_are_descendants[i]:
                self._store.append(parent_iter, row_data)
            else:
                parent_data = [row_data[0]] + [None] * len(row_data[1:])
                parent_iter = self._store.append(None, parent_data) 
                self._store.append(parent_iter, row_data)
        filter_model = self._store.filter_new()
        filter_model.set_visible_func(self._filter_visible)
        sort_model = gtk.TreeModelSort(filter_model)
        for i in range(len(self.column_names)):
            sort_model.set_sort_func(i, self.sort_util.sort_column, i)
        sort_model.connect("sort-column-changed",
                           self.sort_util.handle_sort_column_change)
        return sort_model

    def set_tree_tip(self, treeview, row_iter, col_index, tip):
        """Add the hover-over text for a cell to 'tip'.
        
        treeview is the gtk.TreeView object
        row_iter is the gtk.TreeIter for the row
        col_index is the index of the gtk.TreeColumn in
        e.g. treeview.get_columns()
        tip is the gtk.Tooltip object that the text needs to be set in.
        
        """
        model = treeview.get_model()
        stash_section_index = self.column_names.index("Section")
        stash_item_index = self.column_names.index("Item")
        stash_desc_index = self.column_names.index("Description")
        stash_request_num_index = self.column_names.index("#")
        stash_section = model.get_value(row_iter, stash_section_index)
        stash_item = model.get_value(row_iter, stash_item_index)
        stash_desc = model.get_value(row_iter, stash_desc_index)
        stash_request_num = model.get_value(row_iter, stash_request_num_index)
        if not stash_request_num or stash_request_num == "0":
            stash_request_num = "None"
        name = self.column_names[col_index]
        value = model.get_value(row_iter, col_index)
        if value is None:
            return False
        if name == "?":
            name = "Requests Status"
            if value == rose.config_editor.SUMMARY_DATA_PANEL_MODIFIED_MARKUP:
                value = "changed"
            else:
                value = "no changes"
        elif name == "#":
            name = "Requests"
            if stash_request_num != "None":
                sect_streqs = self.request_lookup.get(stash_section, {})
                streqs = sect_streqs.get(stash_item, {}).keys()
                streqs.sort(rose.config.sort_settings)
                if streqs:
                    value = "\n    " + "\n    ".join(streqs)
                else:
                    value = stash_request_num + " total"
        text = name + ": " + str(value) + "\n\n"
        text += "Section: " + str(stash_section) + "\n"
        text += "Item: " + str(stash_item) + "\n"
        text += "Description: " + str(stash_desc) + "\n"
        if stash_request_num != "None":
            text += str(stash_request_num) + " request(s)"
        text = text.strip()
        tip.set_text(text)
        return True

    def update_request_info(self, request_lookup=None,
                            changed_request_lookup=None):
        """Refresh streq namelist information."""
        if request_lookup is not None:
            self.request_lookup = request_lookup
        if changed_request_lookup is not None:
            self.changed_request_lookup = changed_request_lookup
        sect_col_index = self.column_names.index("Section")
        item_col_index = self.column_names.index("Item")
        streq_info_index = self.column_names.index("?")
        num_streqs_index = self.column_names.index("#")
        parent_iter_stack = []
        # For speed, pass in the relevant indices here.
        user_data = (sect_col_index, item_col_index,
                     streq_info_index, num_streqs_index)
        self._store.foreach(self._update_row_request_info, user_data)
        # Loop over any parent rows and sum numbers and info.
        parent_iter = self._store.iter_children(None)
        while parent_iter is not None:
            num_streq_children = 0
            streq_info_children = ""
            child_iter = self._store.iter_children(parent_iter)
            if child_iter is None:
                parent_iter = self._store.iter_next(parent_iter)
                continue
            while child_iter is not None:
                num = self._store.get_value(child_iter, num_streqs_index)
                info = self._store.get_value(child_iter, streq_info_index)
                if isinstance(num, basestring) and num.isdigit():
                    num_streq_children += int(num)
                if info and not streq_info_children:
                    streq_info_children = info
                child_iter = self._store.iter_next(child_iter)
            self._store.set_value(parent_iter, num_streqs_index,
                                  str(num_streq_children))
            self._store.set_value(parent_iter, streq_info_index,
                                  streq_info_children)
            parent_iter = self._store.iter_next(parent_iter)
            
            
                    
    def _update_row_request_info(self, model, path, iter_, user_data):
        # Update the streq namelist information for a model row.
        (sect_col_index, item_col_index,
         streq_info_index, num_streqs_index) = user_data
        section = model.get_value(iter_, sect_col_index)
        item = model.get_value(iter_, item_col_index)
        if section is None or item is None:
            model.set_value(iter_, num_streqs_index, None)
            model.set_value(iter_, streq_info_index, None)
            return
        streqs = self.request_lookup.get(section, {}).get(item, {})
        model.set_value(iter_, num_streqs_index, str(len(streqs)))
        streq_info = ""
        mod_markup = rose.config_editor.SUMMARY_DATA_PANEL_MODIFIED_MARKUP
        for streq_section in streqs:
            if streq_section in self.changed_request_lookup:
                streq_info = mod_markup + streq_info
                break
        model.set_value(iter_, streq_info_index, streq_info)

    def _append_row_data(self, model, path, iter_, data_rows):
        # Append new row data.
        data_rows.append(model.get(iter_))

    def _apply_grouping(self, data_rows, column_names, group_index=None,
                        descending=False):
        # Calculate nesting (grouping) for the data.
        rows_are_descendants = None
        if group_index is None:
            return data_rows, column_names, rows_are_descendants
        k = group_index
        data_rows = [r[k:k + 1] + r[0:k] + r[k + 1:] for r in data_rows]
        column_names.insert(0, column_names.pop(k))
        data_rows.sort(lambda x, y:
                       self._sort_row_data(x, y, 0, descending))
        last_entry = None
        rows_are_descendants = []
        for i, row in enumerate(data_rows):
            if i > 0 and last_entry == row[0]:
                rows_are_descendants.append(True)
            else:
                rows_are_descendants.append(False)
                last_entry = row[0]
        return data_rows, column_names, rows_are_descendants  

    def _filter_refresh(self, widget=None):
        # Hook function that reacts to a change in filter status.
        self._view.get_model().get_model().refilter()

    def _filter_visible(self, model, iter_):
        # This returns whether a row should be visible.
        filt_text = self._filter_widget.get_text()
        if not filt_text:
            return True
        for col_text in model.get(iter_, *range(len(self.column_names))):
            if (isinstance(col_text, basestring) and
                filt_text.lower() in col_text.lower()):
                return True
        child_iter = model.iter_children(iter_)
        while child_iter is not None:
            if self._filter_visible(model, child_iter):
                return True
            child_iter = model.iter_next(child_iter)
        return False

    def _get_control_widget_hbox(self):
        # Build the control widgets for the dialog.
        filter_label = gtk.Label(
                      rose.config_editor.SUMMARY_DATA_PANEL_FILTER_LABEL)
        filter_label.show()
        self._filter_widget = gtk.Entry()
        self._filter_widget.set_width_chars(
                     rose.config_editor.SUMMARY_DATA_PANEL_FILTER_MAX_CHAR)
        self._filter_widget.connect("changed", self._filter_refresh)
        self._filter_widget.show()
        group_label = gtk.Label(
                     rose.config_editor.SUMMARY_DATA_PANEL_GROUP_LABEL)
        group_label.show()
        self._group_widget = gtk.ComboBox()
        cell = gtk.CellRendererText()
        self._group_widget.pack_start(cell, expand=True)
        self._group_widget.add_attribute(cell, 'text', 0)
        self._group_widget.show()
        self._add_button = rose.gtk.util.CustomButton(
                                label="Add",
                                stock_id=gtk.STOCK_ADD,
                                tip_text="Add a new request for this entry")
        self._add_button.connect("activate",
                                 lambda b: self._handle_add_current_row())
        self._add_button.connect("clicked",
                                 lambda b: self._handle_add_current_row())
        self._refresh_button = rose.gtk.util.CustomButton(
                                    label="Refresh",
                                    stock_id=gtk.STOCK_REFRESH,
                                    tip_text="Refresh namelist:streq statuses")
        self._refresh_button.connect("activate",
                                     lambda b: self.refresh_stash_requests())
        self._refresh_button.connect("clicked",
                                     lambda b: self.refresh_stash_requests())
         
        filter_hbox = gtk.HBox()
        filter_hbox.pack_start(group_label, expand=False, fill=False)
        filter_hbox.pack_start(self._group_widget, expand=False, fill=False)
        filter_hbox.pack_start(filter_label, expand=False, fill=False,
                               padding=10)
        filter_hbox.pack_start(self._filter_widget, expand=False, fill=False)
        filter_hbox.pack_end(self._refresh_button, expand=False, fill=False)
        filter_hbox.pack_end(self._add_button, expand=False, fill=False)
        filter_hbox.show()
        return filter_hbox

    def _get_current_section_item(self):
        # Return the current highlighted section (or None) and item (or None).
        current_path, current_column = self._view.get_cursor()
        if current_path is None:
            return (None, None)
        current_iter = self._view.get_model().get_iter(current_path)
        return self._get_section_item_from_iter(current_iter)

    def _get_section_item_col_indices(self):
        # Return the column indices of the STASH section and item.
        model = self._view.get_model()
        sect_index = 0
        if self.group_index is not None and self.group_index != sect_index:
            sect_index = 1
        item_index = 1
        if self.group_index is not None:
            if self.group_index == 0:
                item_index = 1
            elif self.group_index == 1:
                item_index = 0
            else:
                item_index = 2
        return sect_index, item_index

    def _get_section_item_from_iter(self, iter_):
        # Return the STASH section and item numbers for this row.
        sect_index, item_index = self._get_section_item_col_indices()
        model = self._view.get_model()
        section = model.get_value(iter_, sect_index)
        item = model.get_value(iter_, item_index)
        return section, item

    def _handle_add_current_row(self):
        section, item = self._get_current_section_item()
        return self.add_stash_request(section, item)

    def _handle_activation(self, view, path, column):
        # React to an activation of a row in the dialog.
        model = view.get_model()
        row_iter = model.get_iter(path)
        section, item = self._get_section_item_from_iter(row_iter)
        if section is None or item is None:
            return False
        return self.add_stash_request(section, item)

    def _handle_button_press_event(self, treeview, event):
        # React to a button press (mouse click).
        pathinfo = treeview.get_path_at_pos(int(event.x),
                                            int(event.y))
        if pathinfo is not None:
            path, col, cell_x, cell_y = pathinfo
            if event.button != 3:
                if event.type == gtk.gdk._2BUTTON_PRESS:
                    self._handle_activation(treeview, path, col)
            else:
                self._popup_tree_menu(path, col, event)

    def _handle_group_change(self, combobox):
        # Handle grouping (nesting) status changes.
        model = combobox.get_model()
        col_name = model.get_value(combobox.get_active_iter(), 0)
        if col_name:
            group_index = self.column_names.index(col_name)
            # Any existing grouping changes the order of self.column_names.
            if (self.group_index is not None and
                group_index <= self.group_index):
                group_index -= 1
        else:
            group_index = None
        if group_index == self.group_index:
            return False
        self.group_index = group_index
        self.generate_tree_view()
        return False  

    def _popup_tree_menu(self, path, col, event):
        """Launch a menu for this main treeview row."""
        menu = gtk.Menu()
        menu.show()
        model = self._view.get_model()
        row_iter = model.get_iter(path)
        section, item = self._get_section_item_from_iter(row_iter)
        if section is None or item is None:
            return False
        add_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_ADD)
        add_menuitem.set_label("Add STASH request")
        add_menuitem.connect("activate",
                             lambda i: self.add_stash_request(section, item))
        add_menuitem.show()
        menu.append(add_menuitem)
        streqs = self.request_lookup.get(section, {}).get(item, {}).keys()
        if streqs:
            view_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_FIND)
            view_menuitem.set_label(label="View...")
            view_menuitem.show()
            view_menu = gtk.Menu()
            view_menu.show()
            view_menuitem.set_submenu(view_menu)
            streqs.sort(rose.config.sort_settings)
            for streq in streqs:
                view_streq_menuitem = gtk.MenuItem(label=streq)
                view_streq_menuitem._section = streq
                view_streq_menuitem.connect(
                           "button-release-event",
                           lambda m, e: self.navigate_to_stash_request(
                                                      m._section))
                view_streq_menuitem.show()
                view_menu.append(view_streq_menuitem)
            menu.append(view_menuitem)
        menu.popup(None, None, None, event.button, event.time)
        return False

    def _set_tree_cell_value(self, column, cell, treemodel, iter_):
        # Extract an appropriate value for this cell from the model.
        cell.set_property("visible", True)
        col_index = self._view.get_columns().index(column)
        col_title = self.column_names[col_index]
        value = self._view.get_model().get_value(iter_, col_index)
        max_len = 30
        if (value is not None and len(value) > max_len
            and col_index != 0):
            cell.set_property("width-chars", max_len)
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        if value is not None and col_title != "?":
            value = rose.gtk.util.safe_str(value)
        cell.set_property("markup", value)

    def _sort_row_data(self, row1, row2, sort_index, descending=False):
        # Handle column sorting.
        fac = (-1 if descending else 1)
        x = row1[sort_index]
        y = row2[sort_index]
        return fac * self.sort_util.cmp_(x, y)

    def _update_control_widget_sensitivity(self):
        section, item = self._get_current_section_item()
        self._add_button.set_sensitive(section is not None and
                                       item is not None)
