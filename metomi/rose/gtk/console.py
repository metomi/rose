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

import datetime

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import metomi.rose.resource


class ConsoleWindow(Gtk.Window):

    """Create an error console window."""

    CATEGORY_ALL = "All"
    COLUMN_TITLE_CATEGORY = "Type"
    COLUMN_TITLE_MESSAGE = "Message"
    COLUMN_TITLE_TIME = "Time"
    DEFAULT_SIZE = (600, 300)
    TITLE = "Error Console"

    def __init__(self, categories, category_message_time_tuples,
                 category_stock_ids, default_size=None, parent=None,
                 destroy_hook=None):
        super(ConsoleWindow, self).__init__()
        if parent is not None:
            self.set_transient_for(parent)
        if default_size is None:
            default_size = self.DEFAULT_SIZE
        self.set_default_size(*default_size)
        self.set_title(self.TITLE)
        self._filter_category = self.CATEGORY_ALL
        self.categories = categories
        self.category_icons = []
        for id_ in category_stock_ids:
            self.category_icons.append(
                self.render_icon(id_, Gtk.IconSize.MENU))
        self._destroy_hook = destroy_hook
        top_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        top_vbox.show()
        self.add(top_vbox)

        message_scrolled_window = Gtk.ScrolledWindow()
        message_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                           Gtk.PolicyType.AUTOMATIC)
        message_scrolled_window.show()
        self._message_treeview = Gtk.TreeView()
        self._message_treeview.show()
        self._message_treeview.set_rules_hint(True)

        # Set up the category column (icons).
        category_column = Gtk.TreeViewColumn()
        category_column.set_title(self.COLUMN_TITLE_CATEGORY)
        cell_category = Gtk.CellRendererPixbuf()
        category_column.pack_start(cell_category, False)
        category_column.set_cell_data_func(cell_category,
                                           self._set_category_cell, 0)
        category_column.set_clickable(True)
        category_column.connect("clicked", self._sort_column, 0)
        self._message_treeview.append_column(category_column)

        # Set up the message column (info text).
        message_column = Gtk.TreeViewColumn()
        message_column.set_title(self.COLUMN_TITLE_MESSAGE)
        cell_message = Gtk.CellRendererText()
        message_column.pack_start(cell_message, False)
        message_column.add_attribute(cell_message, attribute="text",
                                     column=1)
        message_column.set_clickable(True)
        message_column.connect("clicked", self._sort_column, 1)
        self._message_treeview.append_column(message_column)

        # Set up the time column (text).
        time_column = Gtk.TreeViewColumn()
        time_column.set_title(self.COLUMN_TITLE_TIME)
        cell_time = Gtk.CellRendererText()
        time_column.pack_start(cell_time, False)
        time_column.set_cell_data_func(cell_time, self._set_time_cell, 2)
        time_column.set_clickable(True)
        time_column.set_sort_indicator(True)
        time_column.connect("clicked", self._sort_column, 2)
        self._message_treeview.append_column(time_column)

        self._message_store = Gtk.TreeStore(str, str, int)
        for category, message, time in category_message_time_tuples:
            self._message_store.append(None, [category, message, time])
        filter_model = self._message_store.filter_new()
        filter_model.set_visible_func(self._get_should_show)
        self._message_treeview.set_model(filter_model)

        message_scrolled_window.add(self._message_treeview)
        top_vbox.pack_start(message_scrolled_window, expand=True, fill=True, padding=0)

        category_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        category_hbox.show()
        top_vbox.pack_end(category_hbox, expand=False, fill=False, padding=0)
        for category in categories + [self.CATEGORY_ALL]:
            togglebutton = Gtk.ToggleButton(label=category,
                                            use_underline=False)
            togglebutton.connect("toggled",
                                 lambda b: self._set_new_filter(
                                        b, category_hbox.get_children()))
            togglebutton.show()
            category_hbox.pack_start(togglebutton, expand=True, fill=True, padding=0)
        togglebutton.set_active(True)
        self.show()
        self._scroll_to_end()
        self.connect("destroy", self._handle_destroy)

    def _handle_destroy(self, window):
        if self._destroy_hook is not None:
            self._destroy_hook()

    def _get_should_show(self, model, iter_, _):
        # Determine whether to show a row.
        category = model.get_value(iter_, 0)
        if self._filter_category not in [self.CATEGORY_ALL, category]:
            return False
        return True

    def _scroll_to_end(self):
        # Scroll the Treeview to the end of the rows.
        model = self._message_treeview.get_model()
        iter_ = model.get_iter_first()
        if iter_ is None:
            return
        while True:
            next_iter = model.iter_next(iter_)
            if next_iter is None:
                break
            iter_ = next_iter
        path = model.get_path(iter_)
        self._message_treeview.scroll_to_cell(path)
        self._message_treeview.set_cursor(path)
        self._message_treeview.grab_focus()

    def _set_category_cell(self, column, cell, model, r_iter, index):
        category = model.get_value(r_iter, index)
        icon = self.category_icons[self.categories.index(category)]
        cell.set_property("pixbuf", icon)

    def _set_new_filter(self, togglebutton, togglebuttons):
        category = togglebutton.get_label()
        if not togglebutton.get_active():
            return False
        self._filter_category = category
        self._message_treeview.get_model().refilter()
        for button in togglebuttons:
            if button != togglebutton:
                button.set_active(False)

    def _set_time_cell(self, column, cell, model, r_iter, index):
        message_time = model.get_value(r_iter, index)
        text = datetime.datetime.fromtimestamp(message_time).strftime(
            metomi.rose.config_editor.EVENT_TIME_LONG)
        cell.set_property("text", text)

    def _sort_column(self, column, index):
        # Sort a column.
        new_sort_order = Gtk.SortType.ASCENDING
        if column.get_sort_order() == Gtk.SortType.ASCENDING:
            new_sort_order = Gtk.SortType.DESCENDING
        column.set_sort_order(new_sort_order)
        for other_column in self._message_treeview.get_columns():
            other_column.set_sort_indicator(column == other_column)
        self._message_store.set_sort_column_id(index, new_sort_order)

    def update_messages(self, category_message_time_tuples):
        # Update the messages.
        self._message_store.clear()
        for category, message, time in category_message_time_tuples:
            self._message_store.append(None, [category, message, time])
        self._scroll_to_end()
