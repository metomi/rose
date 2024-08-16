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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import Pango

import metomi.rose.config
import metomi.rose.config_editor
import metomi.rose.config_editor.util
import metomi.rose.gtk.util

from functools import cmp_to_key


class BaseSummaryDataPanel(Gtk.Box):

    """A base class for summarising data across many namespaces.

    Subclasses should provide the following methods:
    - def add_cell_renderer_for_value(self, column, column_title):
    - def get_model_data(self):
    - def get_section_column_index(self):
    - def set_tree_cell_status(self, column, cell, model, row_iter):
    - def set_tree_tip(self, treeview, row_iter, col_index, tip):

    Subclasses may provide the following methods:
    - def _get_custom_menu_items(self, path, column, event):

    These are described below in their placeholder methods.

    """

    def __init__(self, sections, variables, sect_ops, var_ops,
                 search_function, sub_ops,
                 is_duplicate, arg_str=None):
        super(BaseSummaryDataPanel, self).__init__()
        self.sections = sections
        self.variables = variables
        self._section_data_list = None
        self._last_column_names = []
        self.column_names = []
        self.sect_ops = sect_ops
        self.var_ops = var_ops
        self.search_function = search_function
        self.sub_ops = sub_ops
        self.is_duplicate = is_duplicate
        self.group_index = None
        self.util = metomi.rose.config_editor.util.Lookup()
        self.control_widget_hbox = self._get_control_widget_hbox()
        self.pack_start(self.control_widget_hbox, expand=False, fill=False, padding=0)
        self._prev_store = None
        self._prev_sort_model = None
        self._view = metomi.rose.gtk.util.TooltipTreeView(
            get_tooltip_func=self.set_tree_tip,
            multiple_selection=True)
        self._view.set_rules_hint(True)
        self.sort_util = metomi.rose.gtk.util.TreeModelSortUtil(
            self._view.get_model, multi_sort_num=2)
        self._view.show()
        self._view.connect("button-press-event",
                           self._handle_button_press_event)
        self._view.connect("key-press-event",
                           self._handle_key_press_event)
        self._window = Gtk.ScrolledWindow()
        self._window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.update()
        self._window.add(self._view)
        self._window.show()
        self.pack_start(self._window, expand=True, fill=True, padding=0)
        self.show()

    def add_cell_renderer_for_value(self, column, column_title):
        """Add a cell renderer to represent the model value.

        column is the Gtk.TreeColumn to pack the cell in.
        column_title is the title of column.

        You may want to use column.set_cell_data_func.

        """
        raise NotImplementedError()

    def get_model_data(self):
        """Return a list of data tuples, plus column names.

        The returned list should contain lists of items for each row.
        The column names should be a list of strings for column titles.

        """
        raise NotImplementedError()

    def get_section_column_index(self):
        """Return the section name column index from the Gtk.TreeView.

        This may change based on the grouping (self.group_index).

        """
        raise NotImplementedError()

    def set_tree_cell_status(self, column, cell, model, row_iter, _):
        """Add status markup to the cell - e.g. error notification.

        column is the Gtk.TreeColumn where the cell is
        cell is the Gtk.CellRendererText to add markup to
        model is the Gtk.TreeModel-derived data store
        row_iter is the Gtk.TreeIter pointing to the cell's row

        """
        raise NotImplementedError()

    def set_tree_tip(self, treeview, row_iter, col_index, tip):
        """Add the hover-over text for a cell to 'tip'.

        treeview is the Gtk.TreeView object
        row_iter is the Gtk.TreeIter for the row
        col_index is the index of the Gtk.TreeColumn in
        e.g. treeview.get_columns()
        tip is the Gtk.Tooltip object that the text needs to be set in.

        """
        raise NotImplementedError()

    def _get_custom_menu_items(self, path, column, event):
        """Override this method to add to the right click menu.

        This should return a list of Gtk.MenuItem subclass instances.

        """
        return []

    def _get_control_widget_hbox(self):
        filter_label = Gtk.Label(label=
            metomi.rose.config_editor.SUMMARY_DATA_PANEL_FILTER_LABEL)
        filter_label.show()
        self._filter_widget = Gtk.Entry()
        self._filter_widget.set_width_chars(
            metomi.rose.config_editor.SUMMARY_DATA_PANEL_FILTER_MAX_CHAR)
        self._filter_widget.connect("changed", self._refilter)
        self._filter_widget.show()
        group_label = Gtk.Label(label=
            metomi.rose.config_editor.SUMMARY_DATA_PANEL_GROUP_LABEL)
        group_label.show()
        self._group_widget = Gtk.ComboBox()
        cell = Gtk.CellRendererText()
        self._group_widget.pack_start(cell, True)
        self._group_widget.add_attribute(cell, 'text', 0)
        self._group_widget.connect("changed", self._handle_group_change)
        self._group_widget.show()
        filter_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        filter_hbox.pack_start(group_label, expand=False, fill=False, padding=0)
        filter_hbox.pack_start(self._group_widget, expand=False, fill=False, padding=0)
        filter_hbox.pack_start(filter_label, expand=False, fill=False,
                               padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        filter_hbox.pack_start(self._filter_widget, expand=False, fill=False, padding=0)
        filter_hbox.show()
        return filter_hbox

    def update_tree_model(self):
        """Construct a data model of other page data."""
        self.var_id_map = {}
        for variables in list(self.variables.values()):
            for variable in variables:
                self.var_id_map[variable.metadata["id"]] = variable
        data_rows, column_names = self.get_model_data()
        data_rows, column_names, rows_are_descendants = self._apply_grouping(
            data_rows, column_names, self.group_index)
        self.column_names = column_names
        should_redraw = self.column_names != self._last_column_names
        if data_rows:
            col_types = [str] * len(data_rows[0])
        else:
            col_types = []
        need_new_store = (should_redraw or self.group_index)
        if need_new_store:
            # We need to construct a new TreeModel.
            if self._prev_sort_model is not None:
                prev_sort_id = self._prev_sort_model.get_sort_column_id()
            store = Gtk.TreeStore(*col_types)
            self._prev_store = store
        else:
            store = self._prev_store
        parent_iter = None
        for i, row_data in enumerate(data_rows):
            insert_iter = store.iter_nth_child(None, i)
            if insert_iter is not None:
                for j, value in enumerate(row_data):
                    store.set_value(insert_iter, j, value)
            elif not rows_are_descendants:
                store.append(None, row_data)
            elif rows_are_descendants[i]:
                store.append(parent_iter, row_data)
            else:
                parent_data = [row_data[0]] + [None] * len(row_data[1:])
                parent_iter = store.append(None, parent_data)
                store.append(parent_iter, row_data)
        for extra_index in range(i + 1, store.iter_n_children(None)):
            remove_iter = store.iter_nth_child(None, extra_index)
            if remove_iter is not None:
                store.remove(remove_iter)
        if need_new_store:
            filter_model = store.filter_new()
            filter_model.set_visible_func(self._filter_visible)
            sort_model = Gtk.TreeModelSort(filter_model)
            for i in range(len(self.column_names)):
                sort_model.set_sort_func(i, self.sort_util.sort_column, i)
            if (self._prev_sort_model is not None and
                    prev_sort_id[0] is not None):
                sort_model.set_sort_column_id(*prev_sort_id)
            self._prev_sort_model = sort_model
            sort_model.connect("sort-column-changed",
                               self.sort_util.handle_sort_column_change)
            if should_redraw:
                self.sort_util.clear_sort_columns()
                for column in list(self._view.get_columns()):
                    self._view.remove_column(column)
            self._view.set_model(sort_model)
        self._last_column_names = self.column_names
        return should_redraw

    def set_focus_node_id(self, node_id):
        """Set the focus on a particular node id, if possible."""
        section = self.util.get_section_option_from_id(node_id)[0]
        self.scroll_to_section(section)

    def update(self, sections=None, variables=None):
        """Update the summary of page data."""
        if sections is not None:
            self.sections = sections
        if variables is not None:
            self.variables = variables
        old_cols = set(self.column_names)

        # Generate a set of expanded sections (one level only).
        expanded_sections = set()
        model = self._view.get_model()
        self._view.map_expanded_rows(
            lambda r, p:
            expanded_sections.add(model.get_value(model.get_iter(p), 0)))

        should_redraw = self.update_tree_model()
        if should_redraw:
            self.add_new_columns(self._view, self.column_names)
            if old_cols != set(self.column_names):
                iter_ = self._group_widget.get_active_iter()
                if self.group_index is not None:
                    current_model = self._group_widget.get_model()
                    current_group = None
                    if current_model is not None:
                        current_group = current_model().get_value(iter_, 0)
                group_model = Gtk.TreeStore(str)
                group_model.append(None, [""])
                start_index = 0
                for i, name in enumerate(self.column_names):
                    if self.group_index is not None and name == current_group:
                        start_index = i
                    group_model.append(None, [name])
                if self.group_index is not None:
                    group_model.append(None, [""])
                self._group_widget.set_model(group_model)
                self._group_widget.set_active(start_index)
        model = self._view.get_model()

        # Expand previously expanded sections (one level only).
        path = (0,)
        while True:
            if model.get_value(model.get_iter(path), 0) in expanded_sections:
                self._view.expand_to_path(path)

            sibling = model.iter_next(model.get_iter(path))
            if sibling:
                path = model.get_path(sibling)
            else:
                break

    def add_new_columns(self, treeview, column_names):
        """Create new columns."""
        for i, column_name in enumerate(column_names):
            col = Gtk.TreeViewColumn()
            col.set_title(column_name.replace("_", "__"))
            cell_for_status = Gtk.CellRendererText()
            col.pack_start(cell_for_status, False)
            col.set_cell_data_func(cell_for_status,
                                   self.set_tree_cell_status)
            self.add_cell_renderer_for_value(col, column_name)
            if i < len(column_names) - 1:
                col.set_resizable(True)
            col.set_sort_column_id(i)
            treeview.append_column(col)

    def get_status_from_data(self, node_data):
        """Return markup corresponding to changes since the last save."""
        text = ""
        mod_markup = metomi.rose.config_editor.SUMMARY_DATA_PANEL_MODIFIED_MARKUP
        err_markup = metomi.rose.config_editor.SUMMARY_DATA_PANEL_ERROR_MARKUP
        if node_data is None:
            return None
        if metomi.rose.variable.IGNORED_BY_SYSTEM in node_data.ignored_reason:
            text += metomi.rose.config_editor.SUMMARY_DATA_PANEL_IGNORED_SYST_MARKUP
        elif metomi.rose.variable.IGNORED_BY_USER in node_data.ignored_reason:
            text += metomi.rose.config_editor.SUMMARY_DATA_PANEL_IGNORED_USER_MARKUP
        if metomi.rose.variable.IGNORED_BY_SECTION in node_data.ignored_reason:
            text += metomi.rose.config_editor.SUMMARY_DATA_PANEL_IGNORED_SECT_MARKUP
        if isinstance(node_data, metomi.rose.section.Section):
            # Modified status
            section = node_data.metadata["id"]
            if self.sect_ops.is_section_modified(node_data):
                text += mod_markup
            else:
                for var in self.variables.get(section, []):
                    if self.var_ops.is_var_modified(var):
                        text += mod_markup
                        break
            # Error status
            if node_data.error:
                text += err_markup
            else:
                for var in self.variables.get(section, []):
                    if var.error:
                        text += err_markup
                        break
        elif isinstance(node_data, metomi.rose.variable.Variable):
            if self.var_ops.is_var_modified(node_data):
                text += mod_markup
            if node_data.error:
                text += err_markup
        return text

    def _refilter(self, widget=None):
        self._view.get_model().get_model().refilter()

    def _filter_visible(self, model, iter_, _):
        filt_text = self._filter_widget.get_text()
        if not filt_text:
            return True
        for i in range(model.get_n_columns()):
            col_text = model.get_value(iter_, i)
            if isinstance(col_text, str) and filt_text in col_text:
                return True
        child_iter = model.iter_children(iter_)
        while child_iter is not None:
            if self._filter_visible(model, child_iter, _):
                return True
            child_iter = model.iter_next(child_iter)
        return False

    def _handle_activation(self, view, path, column):
        if path is None:
            return False
        model = view.get_model()
        row_iter = model.get_iter(path)
        col_index = view.get_columns().index(column)
        cell_data = model.get_value(row_iter, col_index)
        sect_index = self.get_section_column_index()
        section = model.get_value(row_iter, sect_index)
        option = None
        if col_index != sect_index and cell_data is not None:
            option = self.column_names[col_index]
        id_ = self.util.get_id_from_section_option(section, option)
        self.search_function(id_)

    def _handle_button_press_event(self, treeview, event):
        pathinfo = treeview.get_path_at_pos(int(event.x),
                                            int(event.y))
        if pathinfo is not None:
            path, col = pathinfo[0:2]
            if event.button == 3:
                rows = self._view.get_selection().get_selected_rows()[1]
                if len(rows) > 1:
                    # Multiple selection.
                    self._popup_tree_multi_menu(event)
                else:
                    # Single selection.
                    self._popup_tree_menu(path, col, event)
                return True
            elif event.button == 2:
                self._handle_activation(treeview, path, col)
        return False

    def _get_selected_sections(self):
        """Return a set of the names of any sections that are currently being
        selected by the user."""
        ret = set([])
        col = self.get_section_column_index()
        model, rows = self._view.get_selection().get_selected_rows()
        for row in rows:
            iter_ = model.get_iter(row)
            section = model.get_value(iter_, col)
            if section:
                # This row is a section.
                ret.add(section)
            else:
                # This may be the parent of some sections.
                ret.update(self._get_child_row_sections(model, iter_, col))
        return ret

    def _get_child_row_sections(self, model, iter_, col):
        """Return a set of any sub-sections contained within the section
        represented by the provided iter_. Method is recursive so will iterate
        down the tree."""
        ret = set([])
        for child_no in range(model.iter_n_children(iter_)):
            child_iter = model.iter_nth_child(iter_, child_no)
            if not child_iter:
                continue
            section = model.get_value(child_iter, col)
            if not section:
                # Recursively acquire sub-sections if present.
                ret.update(self._get_child_rows(child_iter))
            ret.add(section)
        return ret

    def _popup_tree_multi_menu(self, event):
        """Launch a menu for these main treeview rows (multi-selection)."""
        menu = Gtk.Menu()
        menu.show()
        shortcuts = []

        # Ignore all.
        ign_menuitem_box = Gtk.Box()
        ign_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_NO, Gtk.IconSize.MENU)
        ign_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_IGNORE_MULTI)
        ign_menuitem = Gtk.MenuItem()
        ign_menuitem_box.pack_start(ign_menuitem_icon, False, False, 0)
        ign_menuitem_box.pack_start(ign_menuitem_label, False, False, 0)
        Gtk.Container.add(ign_menuitem, ign_menuitem_box)
        ign_menuitem.connect("activate", self._ignore_selected_sections, True)
        ign_menuitem.show()
        menu.append(ign_menuitem)
        shortcuts.append((metomi.rose.config_editor.ACCEL_IGNORE,
                          ign_menuitem))
        # Enable all.
        ign_menuitem_box = Gtk.Box()
        ign_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_YES, Gtk.IconSize.MENU)
        ign_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_ENABLE_MULTI)
        ign_menuitem = Gtk.MenuItem()
        ign_menuitem_box.pack_start(ign_menuitem_icon, False, False, 0)
        ign_menuitem_box.pack_start(ign_menuitem_label, False, False, 0)
        Gtk.Container.add(ign_menuitem, ign_menuitem_box)
        ign_menuitem.connect("activate", self._ignore_selected_sections, False)
        ign_menuitem.show()
        menu.append(ign_menuitem)
        shortcuts.append((metomi.rose.config_editor.ACCEL_IGNORE,
                          ign_menuitem))
        # Remove all.
        rem_menuitem_box = Gtk.Box()
        rem_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_REMOVE, Gtk.IconSize.MENU)
        rem_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_REMOVE_MULTI)
        rem_menuitem = Gtk.MenuItem()
        rem_menuitem_box.pack_start(rem_menuitem_icon, False, False, 0)
        rem_menuitem_box.pack_start(rem_menuitem_label, False, False, 0)
        Gtk.Container.add(rem_menuitem, rem_menuitem_box)
        rem_menuitem.connect("activate", self._remove_selected_sections)
        rem_menuitem.show()
        menu.append(rem_menuitem)
        shortcuts.append((metomi.rose.config_editor.ACCEL_REMOVE, rem_menuitem))

        # list shortcut keys
        accel = Gtk.AccelGroup()
        menu.set_accel_group(accel)
        for key_press, menuitem in shortcuts:
            key, mod = Gtk.accelerator_parse(key_press)
            menuitem.add_accelerator(
                'activate',
                accel,
                key,
                mod,
                Gtk.AccelFlags.VISIBLE
            )

        menu.popup(None, None, None, event.button, event.time)
        return False

    def _popup_tree_menu(self, path, col, event):
        """Launch a menu for this main treeview row (single selection)."""
        shortcuts = []
        menu = Gtk.Menu()
        menu.show()
        model = self._view.get_model()
        row_iter = model.get_iter(path)
        sect_index = self.get_section_column_index()
        this_section = model.get_value(row_iter, sect_index)
        if this_section is not None:
            # Jump to section.
            label = metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_GO_TO.format(
                this_section.replace("_", "__"))
            menuitem_box = Gtk.Box()
            menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_JUMP_TO, Gtk.IconSize.MENU)
            menuitem_label = Gtk.Label(label=label)
            menuitem = Gtk.MenuItem()
            menuitem_box.pack_start(menuitem_icon, False, False, 0)
            menuitem_box.pack_start(menuitem_label, False, False, 0)
            Gtk.Container.add(menuitem, menuitem_box)
            menuitem._section = this_section
            menuitem.connect("activate",
                             lambda i: self.search_function(i._section))
            menuitem.show()
            menu.append(menuitem)
            sep = Gtk.SeparatorMenuItem()
            sep.show()
            menu.append(sep)
        extra_menuitems = self._get_custom_menu_items(path, col, event)
        if extra_menuitems:
            for extra_menuitem in extra_menuitems:
                menu.append(extra_menuitem)
            if this_section is not None:
                sep = Gtk.SeparatorMenuItem()
                sep.show()
                menu.append(sep)
        if self.is_duplicate:
            # A section is currently selected
            if this_section is not None:
                # Add section.
                add_menuitem_box = Gtk.Box()
                add_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_ADD, Gtk.IconSize.MENU)
                add_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_ADD)
                add_menuitem = Gtk.MenuItem()
                add_menuitem_box.pack_start(add_menuitem_icon, False, False, 0)
                add_menuitem_box.pack_start(add_menuitem_label, False, False, 0)
                Gtk.Container.add(add_menuitem, add_menuitem_box)
                add_menuitem.connect("activate",
                                     lambda i: self.add_section())
                add_menuitem.show()
                menu.append(add_menuitem)
                # Copy section.
                copy_menuitem_box = Gtk.Box()
                copy_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_COPY, Gtk.IconSize.MENU)
                copy_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_COPY)
                copy_menuitem = Gtk.MenuItem()
                copy_menuitem_box.pack_start(copy_menuitem_icon, False, False, 0)
                copy_menuitem_box.pack_start(copy_menuitem_label, False, False, 0)
                Gtk.Container.add(copy_menuitem, copy_menuitem_box)
                copy_menuitem.connect(
                    "activate", lambda i: self.copy_section(this_section))
                copy_menuitem.show()
                menu.append(copy_menuitem)
                if (metomi.rose.variable.IGNORED_BY_USER in
                        self.sections[this_section].ignored_reason):
                    # Enable section.
                    enab_menuitem_box = Gtk.Box()
                    enab_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_YES, Gtk.IconSize.MENU)
                    enab_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_ENABLE)
                    enab_menuitem = Gtk.MenuItem()
                    enab_menuitem_box.pack_start(enab_menuitem_icon, False, False, 0)
                    enab_menuitem_box.pack_start(enab_menuitem_label, False, False, 0)
                    Gtk.Container.add(enab_menuitem, enab_menuitem_box)
                    enab_menuitem.connect(
                        "activate",
                        lambda i: self.sub_ops.ignore_section(this_section,
                                                              False))
                    enab_menuitem.show()
                    menu.append(enab_menuitem)
                    shortcuts.append((metomi.rose.config_editor.ACCEL_IGNORE,
                                      enab_menuitem))
                else:
                    # Ignore section.
                    ign_menuitem_box = Gtk.Box()
                    ign_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_NO, Gtk.IconSize.MENU)
                    ign_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_IGNORE)
                    ign_menuitem = Gtk.MenuItem()
                    ign_menuitem_box.pack_start(ign_menuitem_icon, False, False, 0)
                    ign_menuitem_box.pack_start(ign_menuitem_label, False, False, 0)
                    Gtk.Container.add(ign_menuitem, ign_menuitem_box)
                    ign_menuitem.connect(
                        "activate",
                        lambda i: self.sub_ops.ignore_section(this_section,
                                                              True))
                    ign_menuitem.show()
                    menu.append(ign_menuitem)
                    shortcuts.append((metomi.rose.config_editor.ACCEL_IGNORE,
                                      ign_menuitem))
                # Remove section.
                rem_menuitem_box = Gtk.Box()
                rem_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_REMOVE, Gtk.IconSize.MENU)
                rem_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_REMOVE)
                rem_menuitem = Gtk.MenuItem()
                rem_menuitem_box.pack_start(rem_menuitem_icon, False, False, 0)
                rem_menuitem_box.pack_start(rem_menuitem_label, False, False, 0)
                Gtk.Container.add(rem_menuitem, rem_menuitem_box)
                rem_menuitem.connect(
                    "activate", lambda i: self.remove_section(this_section))
                rem_menuitem.show()
                menu.append(rem_menuitem)
                shortcuts.append((metomi.rose.config_editor.ACCEL_REMOVE,
                                  rem_menuitem))
            else:  # A group is currently selected.
                # Ignore all
                ign_menuitem_box = Gtk.Box()
                ign_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_NO, Gtk.IconSize.MENU)
                ign_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_IGNORE)
                ign_menuitem = Gtk.MenuItem()
                ign_menuitem_box.pack_start(ign_menuitem_icon, False, False, 0)
                ign_menuitem_box.pack_start(ign_menuitem_label, False, False, 0)
                Gtk.Container.add(ign_menuitem, ign_menuitem_box)
                ign_menuitem.connect("activate",
                                     self._ignore_selected_sections,
                                     True)
                ign_menuitem.show()
                menu.append(ign_menuitem)
                shortcuts.append((metomi.rose.config_editor.ACCEL_IGNORE,
                                  ign_menuitem))
                # Enable all
                ign_menuitem_box = Gtk.Box()
                ign_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_YES, Gtk.IconSize.MENU)
                ign_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_ENABLE)
                ign_menuitem = Gtk.MenuItem()
                ign_menuitem_box.pack_start(ign_menuitem_icon, False, False, 0)
                ign_menuitem_box.pack_start(ign_menuitem_label, False, False, 0)
                Gtk.Container.add(ign_menuitem, ign_menuitem_box)
                ign_menuitem.connect("activate",
                                     self._ignore_selected_sections,
                                     False)
                ign_menuitem.show()
                menu.append(ign_menuitem)
                shortcuts.append((metomi.rose.config_editor.ACCEL_IGNORE,
                                  ign_menuitem))
                # Delete all.
                rem_menuitem_box = Gtk.Box()
                rem_menuitem_icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_REMOVE, Gtk.IconSize.MENU)
                rem_menuitem_label = Gtk.Label(label=metomi.rose.config_editor.SUMMARY_DATA_PANEL_MENU_REMOVE)
                rem_menuitem = Gtk.MenuItem()
                rem_menuitem_box.pack_start(rem_menuitem_icon, False, False, 0)
                rem_menuitem_box.pack_start(rem_menuitem_label, False, False, 0)
                Gtk.Container.add(rem_menuitem, rem_menuitem_box)
                rem_menuitem.connect(
                    "activate", self._remove_selected_sections)
                rem_menuitem.show()
                menu.append(rem_menuitem)
                shortcuts.append((metomi.rose.config_editor.ACCEL_REMOVE,
                                  rem_menuitem))

            # list shortcut keys
            accel = Gtk.AccelGroup()
            menu.set_accel_group(accel)
            for key_press, menuitem in shortcuts:
                key, mod = Gtk.accelerator_parse(key_press)
                menuitem.add_accelerator(
                    'activate',
                    accel,
                    key,
                    mod,
                    Gtk.AccelFlags.VISIBLE
                )

        menu.popup(None, None, None, event.button, event.time)
        return False

    def add_section(self, section=None, opt_map=None):
        """Add a new section.

        section is the optional name for the new section - otherwise
        one will be calculated, if the sub data sections are duplicates
        opt_map is a dictionary of option names and values to add with
        the section

        """
        if section is None:
            if not self.sections or not self.is_duplicate:
                return False
            section_base = list(self.sections.keys())[0].rsplit("(", 1)[0]
            i = 1
            section = section_base + "(" + str(i) + ")"
            while section in self.sections:
                i += 1
                section = section_base + "(" + str(i) + ")"
        self.sub_ops.add_section(section, opt_map=opt_map)
        self.scroll_to_section(section)
        return section

    def copy_section(self, section):
        """Copy a section and its content into a new section name."""
        new_section = self.sub_ops.clone_section(section)
        self.scroll_to_section(new_section)

    def _handle_key_press_event(self, treeview, event):
        if event.keyval == Gdk.KEY_Delete:
            # `Delete` - remove section(s)
            self._remove_selected_sections()
        # detect key combination
        elif 'GDK_CONTROL_MASK' in event.get_state().value_names:
            # `Ctrl + ?`
            if event.keyval == Gdk.KEY_i:
                # `Ctrl + i` - ignore section(s)
                self._ignore_selected_sections(None)

    def _remove_selected_sections(self, *args):
        """Remove any sections currently selected by the user."""
        sections = self._get_selected_sections()
        self.sub_ops.remove_sections(sections)
        self._view.get_selection().unselect_all()

    def _ignore_selected_sections(self, _, ignore=None):
        """Ignores any sections currently selected by the user. Ignore mode is
        set by the 'ignore' kwarg:
            True:  Ignore all sections (if not already ignored)
            False: Enable all sections (if not already enabled)
            None:  Ignore all sections, if sections are all already ignored
                   then enable all sections inserted.
        """
        sections_ = self._get_selected_sections()
        ignored = [metomi.rose.variable.IGNORED_BY_USER in
                   self.sections[section_].ignored_reason for
                   section_ in sections_]
        # If ignore mode is not specified decide whether to ignore or enable.
        if ignore is None:
            ignore = not all(ignored)
        # Filter out sections that are already ignored/enabled.
        sections_ = [section_ for section_, ignored in zip(sections_, ignored)
                     if ignored != ignore]
        self.sub_ops.ignore_sections(
            sections_, ignore, skip_sub_data_update=False)

    def remove_section(self, section):
        """Remove a section."""
        self.sub_ops.remove_section(section)

    def scroll_to_section(self, section):
        """Find a particular section in the treeview and scroll to it."""
        iter_ = self.get_section_iter(section)
        if iter_ is not None:
            path = self._view.get_model().get_path(iter_)
            self._view.scroll_to_cell(path)
            self._view.set_cursor(path)

    def get_section_iter(self, section):
        """Get the Gtk.TreeIter of this section."""
        iters = []
        sect_index = self.get_section_column_index()
        self._view.get_model().foreach(self._check_value_iter,
                                       [sect_index, section, iters])
        if iters:
            return iters[0]
        return None

    def _check_value_iter(self, model, path, iter_, data):
        value_index, value, iters = data
        if model.get_value(iter_, value_index) == value:
            iters.append(iter_)
            return True
        return False

    def _sort_row_data(self, row1, row2):
        return self.sort_util.cmp_(row1[0], row2[0])

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
        self.update()
        return False

    def _apply_grouping(self, data_rows, column_names, group_index=None,
                        descending=False):
        rows_are_descendants = []
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


class StandardSummaryDataPanel(BaseSummaryDataPanel):

    """Class that provides a standard interface to summary data."""

    def add_cell_renderer_for_value(self, col, col_title):
        """Add a CellRendererText for the column."""
        cell_for_value = Gtk.CellRendererText()
        col.pack_start(cell_for_value, True)
        col.set_cell_data_func(cell_for_value,
                               self._set_tree_cell_value)

    def set_tree_cell_status(self, col, cell, model, row_iter, _):
        """Set the status text for a cell in this column."""
        col_index = self._view.get_columns().index(col)
        sect_index = self.get_section_column_index()
        section = model.get_value(row_iter, sect_index)
        if section is None:
            cell.set_property("markup", None)
            return False
        if col_index == sect_index:
            node_data = self.sections.get(section)
        else:
            option = self.column_names[col_index]
            id_ = self.util.get_id_from_section_option(section, option)
            node_data = self.var_id_map.get(id_)
        cell.set_property("markup",
                          self.get_status_from_data(node_data))

    def get_model_data(self):
        """Construct a data model of other page data."""
        sub_sect_names = list(self.sections.keys())
        sub_var_names = []
        self.var_id_map = {}
        for section, variables in list(self.variables.items()):
            for variable in variables:
                self.var_id_map[variable.metadata["id"]] = variable
                if variable.name not in sub_var_names:
                    sub_var_names.append(variable.name)
        sub_sect_names.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
        sub_var_names.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
        data_rows = []
        for section in sub_sect_names:
            row_data = [section]
            for opt in sub_var_names:
                id_ = self.util.get_id_from_section_option(section, opt)
                var = self.var_id_map.get(id_)
                if var is None:
                    row_data.append(None)
                else:
                    row_data.append(metomi.rose.gtk.util.safe_str(var.value))
            data_rows.append(row_data)
        if self.is_duplicate:
            sect_name = metomi.rose.config_editor.SUMMARY_DATA_PANEL_INDEX_TITLE
        else:
            sect_name = metomi.rose.config_editor.SUMMARY_DATA_PANEL_SECTION_TITLE
        column_names = [sect_name]
        column_names += sub_var_names
        return data_rows, column_names

    def _set_tree_cell_value(self, column, cell, treemodel, iter_, _):
        cell.set_property("visible", True)
        col_index = self._view.get_columns().index(column)
        value = self._view.get_model().get_value(iter_, col_index)
        max_len = metomi.rose.config_editor.SUMMARY_DATA_PANEL_MAX_LEN
        if value is not None and len(value) > max_len and col_index != 0:
            cell.set_property("width-chars", max_len)
            cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        sect_index = self.get_section_column_index()
        if (value is not None and col_index == sect_index and
                self.is_duplicate):
            value = value.split("(")[-1].rstrip(")")
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        cell.set_property("markup", value)

    def set_tree_tip(self, view, row_iter, col_index, tip):
        """Set the hover-over (Tooltip) text for the TreeView."""
        sect_index = self.get_section_column_index()
        section = view.get_model().get_value(row_iter, sect_index)
        if section is None:
            return False
        if col_index == sect_index:
            option = None
            if section not in self.sections:
                return False
            id_data = self.sections[section]
            tip_text = section
        else:
            option = self.column_names[col_index]
            id_ = self.util.get_id_from_section_option(section, option)
            if id_ not in self.var_id_map:
                return False
            id_data = self.var_id_map[id_]
            value = str(view.get_model().get_value(row_iter, col_index))
            tip_text = metomi.rose.CONFIG_DELIMITER.join([section, option, value])
        tip_text += id_data.metadata.get(metomi.rose.META_PROP_DESCRIPTION, "")
        if tip_text:
            tip_text += "\n"
        for key, value in list(id_data.error.items()):
            tip_text += (
                metomi.rose.config_editor.SUMMARY_DATA_PANEL_ERROR_TIP.format(
                    key, value))
        for key in id_data.ignored_reason:
            tip_text += key + "\n"
        if option is not None:
            change_text = self.var_ops.get_var_changes(id_data)
            tip_text += change_text + "\n"
        tip.set_text(tip_text.rstrip())
        return True

    def get_section_column_index(self):
        """Return the column index for the section name."""
        sect_index = 0
        if self.group_index is not None and self.group_index != 0:
            sect_index = 1
        return sect_index
