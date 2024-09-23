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

from gi.repository import Pango
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

import metomi.rose.config
import metomi.rose.config_editor
import metomi.rose.gtk.util

import metomi.rose.config_editor.plugin.um.widget.stash_util as stash_util

from functools import cmp_to_key

class AddStashDiagnosticsPanelv1(Gtk.Box):

    """Display a grouped set of stash requests to add."""

    STASH_PARSE_DESC_OPT = "name"
    STASH_PARSE_ITEM_OPT = "item"
    STASH_PARSE_SECT_OPT = "sectn"

    def __init__(self, stash_lookup, request_lookup,
                 changed_request_lookup, stash_meta_lookup,
                 add_stash_request_func,
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

        stash_meta_lookup is a dictionary of STASHmaster property
        names (keys) with value-metadata-dict key-value pairs (values).
        To extract the metadata dict for a 'grid' value of "2", look
        at stash_meta_lookup["grid=2"] which should be a dict of normal
        Rose metadata key-value pairs such as:
        {"description": "2 means Something something"}.

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
        super(AddStashDiagnosticsPanelv1, self).__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.set_property("homogeneous", False)
        self.stash_lookup = stash_lookup
        self.request_lookup = request_lookup
        self.changed_request_lookup = changed_request_lookup
        self.stash_meta_lookup = stash_meta_lookup
        self._add_stash_request = add_stash_request_func
        self.navigate_to_stash_request = navigate_to_stash_request_func
        self.refresh_stash_requests = refresh_stash_requests_func
        self.group_index = 0
        self._visible_metadata_columns = ["Section"]

        # Automatically hide columns which have fixed-value metadata.
        self._hidden_column_names = []
        for key, metadata in list(self.stash_meta_lookup.items()):
            if "=" in key:
                continue
            values_string = metadata.get(metomi.rose.META_PROP_VALUES, "0, 1")
            if len(metomi.rose.variable.array_split(values_string)) == 1:
                self._hidden_column_names.append(key)

        self._should_show_meta_column_titles = False
        self.control_widget_hbox = self._get_control_widget_hbox()
        self.pack_start(self.control_widget_hbox, expand=False, fill=False, padding=0)
        self._view = metomi.rose.gtk.util.TooltipTreeView(
            get_tooltip_func=self.set_tree_tip)
        self._view.set_rules_hint(True)
        self.sort_util = metomi.rose.gtk.util.TreeModelSortUtil(
            self._view.get_model, 2)
        self._view.show()
        self._view.connect("button-press-event",
                           self._handle_button_press_event)
        self._view.connect("cursor-changed", self._update_control_sensitivity)
        self._window = Gtk.ScrolledWindow()
        self._window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.generate_tree_view(is_startup=True)
        self._window.add(self._view)
        self._window.show()
        self.pack_start(self._window, expand=True, fill=True, padding=0)
        self._update_control_sensitivity()
        self.show()

    def add_cell_renderer_for_value(self, column):
        """Add a cell renderer to represent the model value."""
        cell_for_value = Gtk.CellRendererText()
        column.pack_start(cell_for_value, True)
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
            col = Gtk.TreeViewColumn()
            if column_name in self._hidden_column_names:
                col.set_visible(False)
            col_title = column_name.replace("_", "__")
            if self._should_show_meta_column_titles:
                col_meta = self.stash_meta_lookup.get(column_name, {})
                title = col_meta.get(metomi.rose.META_PROP_TITLE)
                if title is not None:
                    col_title = title
            col.set_title(col_title)
            self.add_cell_renderer_for_value(col)
            if i < len(self.column_names) - 1:
                col.set_resizable(True)
            col.set_sort_column_id(i)
            self._view.append_column(col)
        if is_startup:
            group_model = Gtk.TreeStore(str)
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
        sections = list(self.stash_lookup.keys())
        sections.sort(key=cmp_to_key(self.sort_util.cmp_))
        props_excess = [self.STASH_PARSE_DESC_OPT, self.STASH_PARSE_ITEM_OPT,
                        self.STASH_PARSE_SECT_OPT]
        for section in sections:
            if section == "-1":
                continue
            items = list(self.stash_lookup[section].keys())
            items.sort(key=cmp_to_key(self.sort_util.cmp_))
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
        self._store = Gtk.TreeStore(*col_types)
        parent_iter = None
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
        sort_model = Gtk.TreeModelSort(filter_model)
        for i in range(len(self.column_names)):
            sort_model.set_sort_func(i, self.sort_util.sort_column, i)
        sort_model.connect("sort-column-changed",
                           self.sort_util.handle_sort_column_change)
        return sort_model

    def set_tree_tip(self, treeview, row_iter, col_index, tip):
        """Add the hover-over text for a cell to 'tip'.

        treeview is the Gtk.TreeView object
        row_iter is the Gtk.TreeIter for the row
        col_index is the index of the Gtk.TreeColumn in
        e.g. treeview.get_columns()
        tip is the Gtk.Tooltip object that the text needs to be set in.

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
        help_ = None
        if value is None:
            return False
        if name == "?":
            name = "Requests Status"
            if value == metomi.rose.config_editor.SUMMARY_DATA_PANEL_MODIFIED_MARKUP:
                value = "changed"
            else:
                value = "no changes"
        elif name == "#":
            name = "Requests"
            if stash_request_num != "None":
                sect_streqs = self.request_lookup.get(stash_section, {})
                streqs = list(sect_streqs.get(stash_item, {}).keys())
                streqs.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
                if streqs:
                    value = "\n    " + "\n    ".join(streqs)
                else:
                    value = stash_request_num + " total"
        if name == "Section":
            meta_key = self.STASH_PARSE_SECT_OPT + "=" + value
        elif name == "Description":
            metadata = stash_util.get_stash_section_meta(
                self.stash_meta_lookup, stash_section, stash_item, value
            )
            help_ = metadata.get(metomi.rose.META_PROP_HELP)
            meta_key = self.STASH_PARSE_DESC_OPT + "=" + value
        else:
            meta_key = name + "=" + value
        value_meta = self.stash_meta_lookup.get(meta_key, {})
        title = value_meta.get(metomi.rose.META_PROP_TITLE, "")
        if help_ is None:
            help_ = value_meta.get(metomi.rose.META_PROP_HELP, "")
        if title and not help_:
            value += "\n" + title
        if help_:
            value += "\n" + metomi.rose.gtk.util.safe_str(help_)
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
                if isinstance(num, str) and num.isdigit():
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
        mod_markup = metomi.rose.config_editor.SUMMARY_DATA_PANEL_MODIFIED_MARKUP
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
        if descending:
            data_rows.sort(key=cmp_to_key(self._sort_row_data), reverse=True)
        else:
            data_rows.sort(key=cmp_to_key(self._sort_row_data))
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
        for col_text in model.get(iter_, *list(range(len(self.column_names)))):
            if (isinstance(col_text, str) and
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
        filter_label = Gtk.Label(label=
            metomi.rose.config_editor.SUMMARY_DATA_PANEL_FILTER_LABEL)
        filter_label.show()
        self._filter_widget = Gtk.Entry()
        self._filter_widget.set_width_chars(
            metomi.rose.config_editor.SUMMARY_DATA_PANEL_FILTER_MAX_CHAR)
        self._filter_widget.connect("changed", self._filter_refresh)
        self._filter_widget.set_tooltip_text("Filter by literal values")
        self._filter_widget.show()
        group_label = Gtk.Label(label=
            metomi.rose.config_editor.SUMMARY_DATA_PANEL_GROUP_LABEL)
        group_label.show()
        self._group_widget = Gtk.ComboBox()
        cell = Gtk.CellRendererText()
        self._group_widget.pack_start(cell, True)
        self._group_widget.add_attribute(cell, 'text', 0)
        self._group_widget.show()
        self._add_button = metomi.rose.gtk.util.CustomButton(
            label="Add",
            stock_id=Gtk.STOCK_ADD,
            tip_text="Add a new request for this entry")
        self._add_button.connect("activate",
                                 lambda b: self._handle_add_current_row())
        self._add_button.connect("clicked",
                                 lambda b: self._handle_add_current_row())
        self._refresh_button = metomi.rose.gtk.util.CustomButton(
            label="Refresh",
            stock_id=Gtk.STOCK_REFRESH,
            tip_text="Refresh namelist:streq statuses")
        self._refresh_button.connect("activate",
                                     lambda b: self.refresh_stash_requests())
        self._refresh_button.connect("clicked",
                                     lambda b: self.refresh_stash_requests())
        self._view_button = metomi.rose.gtk.util.CustomButton(
            label="View",
            tip_text="Select view options",
            has_menu=True)
        self._view_button.connect("button-press-event",
                                  self._popup_view_menu)
        filter_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        filter_hbox.pack_start(group_label, expand=False, fill=False, padding=0)
        filter_hbox.pack_start(self._group_widget, expand=False, fill=False, padding=0)
        filter_hbox.pack_start(filter_label, expand=False, fill=False,
                               padding=10)
        filter_hbox.pack_start(self._filter_widget, expand=False, fill=False, padding=0)
        filter_hbox.pack_end(self._view_button, expand=False, fill=False, padding=0)
        filter_hbox.pack_end(self._refresh_button, expand=False, fill=False, padding=0)
        filter_hbox.pack_end(self._add_button, expand=False, fill=False, padding=0)
        filter_hbox.show()
        return filter_hbox

    def _get_current_section_item(self):
        """Return the current highlighted section and item."""
        current_path = self._view.get_cursor()[0]
        if current_path is None:
            return (None, None)
        current_iter = self._view.get_model().get_iter(current_path)
        return self._get_section_item_from_iter(current_iter)

    def _get_section_item_col_indices(self):
        """Return the column indices of the STASH section and item."""
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
        """Return the STASH section and item numbers for this row."""
        sect_index, item_index = self._get_section_item_col_indices()
        model = self._view.get_model()
        section = model.get_value(iter_, sect_index)
        item = model.get_value(iter_, item_index)
        return section, item

    def _handle_add_current_row(self):
        section, item = self._get_current_section_item()
        return self.add_stash_request(section, item)

    def _handle_activation(self, view, path, column):
        """React to an activation of a row in the dialog."""
        model = view.get_model()
        row_iter = model.get_iter(path)
        section, item = self._get_section_item_from_iter(row_iter)
        if section is None or item is None:
            return False
        return self.add_stash_request(section, item)

    def _handle_button_press_event(self, treeview, event):
        """React to a button press (mouse click)."""
        pathinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if pathinfo is not None:
            path, col = pathinfo[0:2]
            if event.button != 3:
                if event.type == Gdk._2BUTTON_PRESS:
                    self._handle_activation(treeview, path, col)
            else:
                self._popup_tree_menu(path, col, event)

    def _handle_group_change(self, combobox):
        """Handle grouping (nesting) status changes."""
        model = combobox.get_model()
        col_name = model.get_value(combobox.get_active_iter(), 0)
        if col_name:
            if col_name in self._hidden_column_names:
                self._hidden_column_names.remove(col_name)
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

    def _launch_record_help(self, menuitem):
        """Launch the help from a menu."""
        metomi.rose.gtk.dialog.run_scrolled_dialog(menuitem._help_text,
                                            menuitem._help_title)

    def _popup_tree_menu(self, path, col, event):
        """Launch a menu for this main treeview row."""
        menu = Gtk.Menu()
        menu.show()
        model = self._view.get_model()
        row_iter = model.get_iter(path)
        section, item = self._get_section_item_from_iter(row_iter)
        if section is None or item is None:
            return False
        add_menuitem_box = Gtk.Box()
        add_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_ADD, Gtk.IconSize.MENU)
        add_menuitem_label = Gtk.Label(label="Add STASH request")
        add_menuitem = Gtk.MenuItem()
        add_menuitem_box.pack_start(add_menuitem_icon, False, False, 0)
        add_menuitem_box.pack_start(add_menuitem_label, False, False, 0)
        Gtk.Container.add(add_menuitem, add_menuitem_box)
        add_menuitem.connect("activate",
                             lambda i: self.add_stash_request(section, item))
        add_menuitem.show()
        menu.append(add_menuitem)
        stash_desc_index = self.column_names.index("Description")
        stash_desc_value = model.get_value(row_iter, stash_desc_index)
        desc_meta = self.stash_meta_lookup.get(
            self.STASH_PARSE_DESC_OPT + "=" + str(stash_desc_value), {})
        desc_meta_help = desc_meta.get(metomi.rose.META_PROP_HELP)
        if desc_meta_help is not None:
            help_menuitem_box = Gtk.Box()
            help_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_HELP, Gtk.IconSize.MENU)
            help_menuitem_label = Gtk.Label(label="Help")
            help_menuitem = Gtk.MenuItem()
            help_menuitem_box.pack_start(help_menuitem_icon, False, False, 0)
            help_menuitem_box.pack_start(help_menuitem_label, False, False, 0)
            Gtk.Container.add(help_menuitem, help_menuitem_box)
            help_menuitem._help_text = desc_meta_help
            help_menuitem._help_title = "Help for %s" % stash_desc_value
            help_menuitem.connect("activate", self._launch_record_help)
            help_menuitem.show()
            menu.append(help_menuitem)
        streqs = list(self.request_lookup.get(section, {}).get(item, {}).keys())
        if streqs:
            view_menuitem_box = Gtk.Box()
            view_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_FIND, Gtk.IconSize.MENU)
            view_menuitem_label = Gtk.Label(label="View...")
            view_menuitem = Gtk.MenuItem()
            view_menuitem_box.pack_start(view_menuitem_icon, False, False, 0)
            view_menuitem_box.pack_start(view_menuitem_label, False, False, 0)
            Gtk.Container.add(view_menuitem, view_menuitem_box)
            view_menuitem.show()
            view_menu = Gtk.Menu()
            view_menu.show()
            view_menuitem.set_submenu(view_menu)
            streqs.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
            for streq in streqs:
                view_streq_menuitem = Gtk.MenuItem(label=streq)
                view_streq_menuitem._section = streq
                view_streq_menuitem.connect(
                    "button-release-event",
                    lambda m, e: self.navigate_to_stash_request(m._section))
                view_streq_menuitem.show()
                view_menu.append(view_streq_menuitem)
            menu.append(view_menuitem)
        menu.popup_at_widget(event.button, None, None, event)
        return False

    def _popup_view_menu(self, widget, event):
        # Create a menu below the widget for view options.
        menu = Gtk.Menu()
        meta_menuitem = Gtk.CheckMenuItem(label="Show expanded value info")
        if len(self.column_names) == len(self._visible_metadata_columns):
            meta_menuitem.set_active(True)
        meta_menuitem.connect("toggled", self._toggle_show_more_info)
        meta_menuitem.show()
        if not self.stash_meta_lookup:
            meta_menuitem.set_sensitive(False)
        menu.append(meta_menuitem)
        col_title_menuitem = Gtk.CheckMenuItem(
            label="Show expanded column titles")
        if self._should_show_meta_column_titles:
            col_title_menuitem.set_active(True)
        col_title_menuitem.connect("toggled",
                                   self._toggle_show_meta_column_titles)
        col_title_menuitem.show()
        if not self.stash_meta_lookup:
            col_title_menuitem.set_sensitive(False)
        menu.append(col_title_menuitem)
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        menu.append(sep)
        show_column_menuitem = Gtk.MenuItem("Show/hide columns")
        show_column_menuitem.show()
        show_column_menu = Gtk.Menu()
        show_column_menuitem.set_submenu(show_column_menu)
        menu.append(show_column_menuitem)
        for i, column in enumerate(self._view.get_columns()):
            col_name = self.column_names[i]
            col_title = col_name.replace("_", "__")
            if self._should_show_meta_column_titles:
                col_meta = self.stash_meta_lookup.get(col_name, {})
                title = col_meta.get(metomi.rose.META_PROP_TITLE)
                if title is not None:
                    col_title = title
            col_menuitem = Gtk.CheckMenuItem(label=col_title,
                                             use_underline=False)
            col_menuitem.show()
            col_menuitem.set_active(column.get_visible())
            col_menuitem._connect_args = (col_name,)
            col_menuitem.connect(
                "toggled",
                lambda c: self._toggle_show_column_name(*c._connect_args))
            show_column_menu.append(col_menuitem)
        menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, event)

    def _set_tree_cell_value(self, column, cell, treemodel, iter_):
        # Extract an appropriate value for this cell from the model.
        cell.set_property("visible", True)
        col_index = self._view.get_columns().index(column)
        col_title = self.column_names[col_index]
        value = self._view.get_model().get_value(iter_, col_index)
        if col_title in self._visible_metadata_columns and value is not None:
            if col_title == "Section":
                key = self.STASH_PARSE_SECT_OPT + "=" + value
            else:
                key = col_title + "=" + value
            value_meta = self.stash_meta_lookup.get(key, {})
            title = value_meta.get(metomi.rose.META_PROP_TITLE, "")
            if title:
                value = title
            desc = value_meta.get(metomi.rose.META_PROP_DESCRIPTION, "")
            if desc:
                value += ": " + desc
        max_len = 36
        if value is not None and len(value) > max_len and col_index != 0:
            cell.set_property("width-chars", max_len)
            cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        if value is not None and col_title != "?":
            value = metomi.rose.gtk.util.safe_str(value)
        cell.set_property("markup", value)

    def _sort_row_data(self, row1, row2):
        """Handle column sorting."""
        return self.sort_util.cmp_(row1[0], row2[0])

    def _toggle_show_column_name(self, column_name):
        """Handle a show/hide of a particular column."""
        col_index = self.column_names.index(column_name)
        column = self._view.get_columns()[col_index]
        if column.get_visible():
            return column.set_visible(False)
        return column.set_visible(True)

    def _toggle_show_more_info(self, widget, column_name=None):
        """Handle a show/hide of extra information."""
        should_show = widget.get_active()
        if column_name is None:
            column_names = self.column_names
        else:
            column_names = [column_name]
        for name in column_names:
            if should_show:
                if name not in self._visible_metadata_columns:
                    self._visible_metadata_columns.append(name)
            elif name in self._visible_metadata_columns:
                if name != "Section":
                    self._visible_metadata_columns.remove(name)
        self._view.columns_autosize()

    def _toggle_show_meta_column_titles(self, widget):
        self._should_show_meta_column_titles = widget.get_active()
        self.generate_tree_view()

    def _update_control_sensitivity(self, _=None):
        section, item = self._get_current_section_item()
        self._add_button.set_sensitive(section is not None and
                                       item is not None)
