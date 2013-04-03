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

    def __init__(self, stash_lookup, sections, variables,
                 add_stash_request_func):
        super(AddStashDiagnosticsPanelv1, self).__init__(self)
        self.set_property("homogeneous", False)
        self.stash_lookup = stash_lookup
        self.sections = sections
        self.variables = variables
        self.add_stash_request = add_stash_request_func
        self.group_index = 0
        self.control_widget_hbox = self._get_control_widget_box()
        self.pack_start(self.control_widget_hbox, expand=False, fill=False)
        self._view = rose.gtk.util.TooltipTreeView(
                                   get_tooltip_func=self.get_tree_tip)
        self._view.set_rules_hint(True)
        self._view.show()
        self._view.connect("button-press-event",
                           self._handle_button_press_event)
        self._window = gtk.ScrolledWindow()
        self._window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.generate_tree_view(is_startup=True)
        self._window.add(self._view)
        self._window.show()
        self.pack_start(self._window, expand=True, fill=True)
        self.show()

    def add_cell_renderer_for_value(self, column):
        """Add a cell renderer to represent the model value."""
        cell_for_value = gtk.CellRendererText()
        column.pack_start(cell_for_value, expand=True)
        column.set_cell_data_func(cell_for_value,
                                  self._set_tree_cell_value)

    def _set_tree_cell_value(self, column, cell, treemodel, iter_):
        cell.set_property("visible", True)
        col_index = self._view.get_columns().index(column)
        value = self._view.get_model().get_value(iter_, col_index)
        max_len = 30
        if (value is not None and len(value) > max_len
            and col_index != 0):
            cell.set_property("width-chars", max_len)
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        if value is not None:
            value = rose.gtk.util.safe_str(value)
        cell.set_property("markup", value)

    def get_model_data_and_columns(self):
        """Return a list of data tuples and columns"""
        data_rows = []
        columns = ["Section", "Item", "Description"]
        sections = self.stash_lookup.keys()
        sections.sort(self.numeric_sorter)
        for section in sections:
            if section == "-1":
                continue
            items = self.stash_lookup[section].keys()
            items.sort(self.numeric_sorter)
            for item in items:
                data = self.stash_lookup[section][item]
                this_row = [section, item, data[self.STASH_PARSE_DESC_OPT]]
                for prop in sorted(data.keys()):
                    if prop != self.STASH_PARSE_DESC_OPT:
                        this_row.append(data[prop])
                        if prop not in columns:
                            columns.append(prop)
                data_rows.append(this_row)
        return data_rows, columns
    
    def numeric_sorter(self, item1, item2):
        if item1.strip().isdigit() and item2.strip().isdigit():
            return cmp(int(item1), int(item2))
        return cmp(item1, item2)

    def get_tree_tip(self, treeview, row_iter, col_index, tip):
        """Add the hover-over text for a cell to 'tip'.
        
        treeview is the gtk.TreeView object
        row_iter is the gtk.TreeIter for the row
        col_index is the index of the gtk.TreeColumn in
        e.g. treeview.get_columns()
        tip is the gtk.Tooltip object that the text needs to be set in.
        
        """
        model = treeview.get_model()
        name = self.column_names[col_index]
        value = model.get_value(row_iter, col_index)
        if value is None:
            return False
        text = name + ": " + str(value) + "\n\n"
        for column_name in ["Section", "Item", "Description"]:
            index = self.column_names.index(column_name)
            value = model.get_value(row_iter, index)
            text += column_name + ": " + str(value) + "\n"
        text = text.strip()
        tip.set_text(text)
        return True

    def _get_control_widget_box(self):
        filter_label = gtk.Label(
                      rose.config_editor.SUMMARY_DATA_PANEL_FILTER_LABEL)
        filter_label.show()
        self._filter_widget = gtk.Entry()
        self._filter_widget.set_width_chars(
                     rose.config_editor.SUMMARY_DATA_PANEL_FILTER_MAX_CHAR)
        self._filter_widget.connect("changed", self._refilter)
        self._filter_widget.show()
        group_label = gtk.Label(
                     rose.config_editor.SUMMARY_DATA_PANEL_GROUP_LABEL)
        group_label.show()
        self._group_widget = gtk.ComboBox()
        cell = gtk.CellRendererText()
        self._group_widget.pack_start(cell, expand=True)
        self._group_widget.add_attribute(cell, 'text', 0)
        self._group_widget.show()
        filter_hbox = gtk.HBox()
        filter_hbox.pack_start(group_label, expand=False, fill=False)
        filter_hbox.pack_start(self._group_widget, expand=False, fill=False)
        filter_hbox.pack_end(self._filter_widget, expand=False, fill=False)
        filter_hbox.pack_end(filter_label, expand=False, fill=False)
        filter_hbox.show()
        return filter_hbox

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
        store = gtk.TreeStore(*col_types)
        parent_iter_ = None
        for i, row_data in enumerate(data_rows):
            if rows_are_descendants is None:
                store.append(None, row_data)
            elif rows_are_descendants[i]:
                store.append(parent_iter, row_data)
            else:
                parent_data = [row_data[0]] + [None] * len(row_data[1:])
                parent_iter = store.append(None, parent_data) 
                store.append(parent_iter, row_data)
        filter_model = store.filter_new()
        filter_model.set_visible_func(self._filter_visible)
        sort_model = gtk.TreeModelSort(filter_model)
        for i in range(len(self.column_names)):
            sort_model.set_sort_func(i, self._sort_model_dupl, i)
        return sort_model

    def generate_tree_view(self, is_startup=False):
        """Create the summary of page data."""
        for column in self._view.get_columns():
            self._view.remove_column(column)
        self.update_tree_model()
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
                group_model.append(None, [name])
            self._group_widget.set_model(group_model)
            self._group_widget.set_active(self.group_index + 1)
            self._group_widget.connect("changed", self._handle_group_change)

    def _sort_model_dupl(self, model, iter1, iter2, col_index):
        val1 = model.get_value(iter1, col_index)
        val2 = model.get_value(iter2, col_index)
        if (isinstance(val1, basestring) and isinstance(val2, basestring) and
            val1.isdigit() and val2.isdigit()):
            rval = cmp(float(val1), float(val2))
        else:
            rval = rose.config.sort_settings(val1, val2)
        if rval == 0:
            return cmp(model.get_path(iter1), model.get_path(iter2))
        return rval

    def update_tree_model(self):
        self._view.set_model(self.get_tree_model())

    def _get_status_from_data(self, node_data):
        status = ""
        return status

    def _refilter(self, widget=None):
        self._view.get_model().get_model().refilter()

    def _filter_visible(self, model, iter_):
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
         
    def _handle_activation(self, view, path, column):
        model = view.get_model()
        row_iter = model.get_iter(path)
        col_index = view.get_columns().index(column)       
        cell_data = model.get_value(row_iter, col_index)
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
        section = model.get_value(row_iter, sect_index)
        item = model.get_value(row_iter, item_index)
        return self.add_stash_request(section, item)

    def _handle_button_press_event(self, treeview, event):
        pathinfo = treeview.get_path_at_pos(int(event.x),
                                            int(event.y))
        if pathinfo is not None:
            path, col, cell_x, cell_y = pathinfo
            if event.button != 3:
                if event.type == gtk.gdk._2BUTTON_PRESS:
                    self._handle_activation(treeview, path, col)
            else:
                self._popup_tree_menu(path, col, event)

    def _popup_tree_menu(self, path, col, event):
        """Launch a menu for this main treeview row."""
        menu = gtk.Menu()
        menu.show()
        model = self._view.get_model()
        row_iter = model.get_iter(path)
        sect_index = 0
        if self.group_index is not None and self.group_index != 0:
            sect_index = 1
        this_section = model.get_value(row_iter, sect_index)
        add_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_ADD)
        add_menuitem.set_label(
                     rose.config_editor.SUMMARY_DATA_PANEL_MENU_ADD)
        add_menuitem.connect("activate",
                             lambda i: self.add_section(this_section))
        add_menuitem.show()
        menu.popup(None, None, None, event.button, event.time)
        return False

    def _append_row_data(self, model, path, iter_, data_rows):
        data_rows.append(model.get(iter_))

    def _sort_row_data(self, row1, row2, sort_index, descending=False):
        fac = (-1 if descending else 1)
        x = row1[sort_index]
        y = row2[sort_index]
        if isinstance(x, basestring) and isinstance(y, basestring):
            if x.isdigit() and y.isdigit():
                return fac * cmp(int(x), int(y))
            return fac * rose.config.sort_settings(x, y)        
        return fac * cmp(x, y)

    def _handle_group_change(self, combobox):
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

    def _apply_grouping(self, data_rows, column_names, group_index=None,
                        descending=False):
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
