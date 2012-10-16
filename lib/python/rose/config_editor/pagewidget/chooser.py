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

import shlex

import gobject
import pygtk
pygtk.require('2.0')
import gtk

import rose.config
import rose.config_editor.variable
import rose.formats
import rose.variable


class PageFormatTree(gtk.VBox):

    """Return a custom container for file-level options."""

    MAX_COLS_SOURCE = 3
    MAX_ROWS_SOURCE = 3
    SPACING = rose.config_editor.SPACING_SUB_PAGE
    CONTENT_LABEL = 'internal'
    EMPTY_LABEL = 'empty'
    RESOURCE_LABEL = 'external'

    def __init__(self, panel_data, ghost_data, var_ops, show_modes,
                 format_keys_func):
        super(PageFormatTree, self).__init__(spacing=self.SPACING)
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        self.trigger_ask_for_config_keys = format_keys_func
        self._state = None
        format = [f for f in rose.formats.__dict__ if not f.startswith('__')]
        external_trigger_widget = gtk.RadioButton(label=self.RESOURCE_LABEL)
        external_trigger_widget.connect_after(
                 'toggled', lambda b: self._toggle(b.get_active(), "ext"))
        external_trigger_widget.show()
        internal_trigger_widget = gtk.RadioButton(external_trigger_widget,
                                                  label=self.CONTENT_LABEL)
        internal_trigger_widget.connect_after(
                 'toggled', lambda b: self._toggle(b.get_active(), "int"))
        internal_trigger_widget.show()
        empty_trigger_widget = gtk.RadioButton(external_trigger_widget,
                                               label=self.EMPTY_LABEL)
        empty_trigger_widget.connect_after(
                 'toggled', lambda b: self._toggle(b.get_active(), "emp"))
        empty_trigger_widget.show()
        self.trigger_hbox = gtk.HBox()
        pad_eventbox1 = gtk.EventBox()
        pad_eventbox1.show()
        self.trigger_hbox.pack_start(pad_eventbox1, expand=True, fill=True)
        self.trigger_hbox.pack_start(internal_trigger_widget, expand=False,
                                     fill=False, padding=self.SPACING)
        self.trigger_hbox.pack_start(external_trigger_widget, expand=False,
                                     fill=False, padding=self.SPACING)
        self.trigger_hbox.pack_start(empty_trigger_widget, expand=False,
                                     fill=False, padding=self.SPACING)
        pad_eventbox2 = gtk.EventBox()
        pad_eventbox2.show()
        self.trigger_hbox.pack_end(pad_eventbox2, expand=True, fill=True)
        self.trigger_hbox.show()
        self.pack_start(self.trigger_hbox, expand=False, fill=False)
        self.external_hbox = gtk.HBox()
        self.pack_start(self.external_hbox, expand=False, fill=False)
        self.internal_vbox = gtk.VBox()
        self.pack_start(self.internal_vbox, expand=True, fill=True)
        self.show()
        if rose.FILE_VAR_CONTENT in [x.name for x in self.panel_data]:
            self.internal_vbox.show()
            self._generate_internal_table()
            internal_trigger_widget.set_active(True)
        elif not self.panel_data:
            empty_trigger_widget.set_active(True)
        else:
            self.external_hbox.show()
            self._generate_external_table()
            external_trigger_widget.set_active(True)
        return

    def _variable_toggle(self, check, var_widget):
        """Only add the variable if the check box is enabled."""
        variable = var_widget.variable
        if check.get_active():
            if variable in self.ghost_data:
                self.var_ops.add_var(variable)
        else:
            if variable in self.panel_data:
                self.var_ops.remove_var(variable)
        var_widget.update_status()

    def _toggle(self, is_on, state=None):
        """Change state e.g. external -> internal."""
        if not is_on:
            return False
        new_state = state
        if self._state == new_state:
            return False
        self._state = new_state
      
        ext_vars = [rose.FILE_VAR_SOURCE, rose.FILE_VAR_CHECKSUM,
                    rose.FILE_VAR_MODE]
        int_vars = [rose.FILE_VAR_CONTENT]
        if self._state == "ext":
            for var in list(self.panel_data):
                if var.name in int_vars:
                    self.var_ops.remove_var(var)
            for var in list(self.ghost_data):
                if var.name in ext_vars:
                    if ((var.name == rose.FILE_VAR_CHECKSUM and
                         not var.value) or (var.name == rose.FILE_VAR_MODE and
                         var.value == "auto")):
                        continue
                    self.var_ops.add_var(var)
        elif self._state == "int":
            for var in list(self.panel_data):
                if var.name in ext_vars:
                    self.var_ops.remove_var(var)
            for var in list(self.ghost_data):
                if var.name in int_vars:
                    self.var_ops.add_var(var)
        else:
            for var in list(self.panel_data):
                self.var_ops.remove_var(var)
        return False

    def _generate_external_table(self):
        """Generate the table for the checksum, mode, source widgets."""
        table = gtk.Table(rows=self.MAX_ROWS_SOURCE,
                          columns=self.MAX_COLS_SOURCE,
                          homogeneous=False)
        table.set_border_width(self.SPACING)
        setattr(table, 'num_removes', 0)
        r = 0
        data = []
        variable_list = [v for v in self.panel_data + self.ghost_data]
        my_cmp = lambda v1, v2: cmp(v1.name, v2.name)
        variable_list.sort(my_cmp)
        for variable in variable_list:
            r += 1
            if variable.name not in [rose.FILE_VAR_CHECKSUM,
                                     rose.FILE_VAR_MODE,
                                     rose.FILE_VAR_SOURCE]:
                continue
            is_ghost = (variable not in self.panel_data)
            widget = rose.config_editor.variable.VariableWidget(
                                        variable, self.var_ops,
                                        is_ghost=is_ghost)
            widget.set_sensitive(not is_ghost)
            widget.insert_into(table, self.MAX_COLS_SOURCE - 1, r + 1)
            if variable.name in [rose.FILE_VAR_CHECKSUM, rose.FILE_VAR_MODE]:
                check_button = gtk.CheckButton()
                check_button.var_widget = widget
                check_button.set_active(not is_ghost)
                check_button.connect(
                             'toggled',
                             lambda c: self._variable_toggle(c,
                                                             c.var_widget))
                check_button.show()
                table.attach(check_button,
                             self.MAX_COLS_SOURCE - 1, self.MAX_COLS_SOURCE,
                             r + 1, r + 2,
                             xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.show()
        self.external_hbox.pack_start(table, expand=True, fill=True)
        return table

    def _generate_internal_table(self):
        """Generate the internal content tables."""
        self._ok_content_sections = set([None])
        treeviews_hbox = gtk.HPaned()
        treeviews_hbox.show()
        self._internal_value_listview = FileListView(
                                      self._set_content_value_listview,
                                      self._get_included_sections,
                                      self._handle_search)
        frame = gtk.Frame()
        frame.show()
        frame.add(self._internal_value_listview)
        value_vbox = gtk.VBox()
        value_vbox.show()
        value_vbox.pack_start(frame, expand=False, fill=False)
        value_eb = gtk.EventBox()
        value_eb.show()
        value_vbox.pack_start(value_eb, expand=True, fill=True)
        self._internal_avail_treeview = FileTreeView(
                           self._set_content_avail_treeview,
                           self._get_included_sections,
                           self._get_available_sections)
        avail_frame = gtk.Frame()
        avail_frame.show()
        avail_frame.add(self._internal_avail_treeview)
        treeviews_hbox.add1(value_vbox)
        treeviews_hbox.add2(avail_frame)
        self.internal_vbox.pack_start(treeviews_hbox, expand=True, fill=True)

    def _get_included_sections(self):
        """Return sections included in the content variable."""
        variables = [v for v in self.panel_data + self.ghost_data]
        names = [v.name for v in variables]
        content_value = variables[names.index(rose.FILE_VAR_CONTENT)].value
        return shlex.split(content_value)

    def _get_available_sections(self):
        """Return sections available to the content variable."""
        ok_content_sections = list(self.trigger_ask_for_config_keys())
        for section in ok_content_sections:
            if section.endswith(")"):
                section_all = section.rsplit("(", 1)[0] + "(:)"
                if section_all not in ok_content_sections:
                    ok_content_sections.append(section_all)
        ok_content_sections.sort(rose.config.sort_settings)
        ok_content_sections.sort(self._sort_settings_duplicate)
        return ok_content_sections

    def _handle_search(self, name):
        """Trigger a search for a section."""
        variables = self.panel_data + self.ghost_data
        ns = variables[0].metadata["full_ns"]
        self.var_ops.search_for_var(ns, name)

    def _set_content_value_listview(self, new_value):
        """React to a set value request from the list view."""
        self._set_content_value(new_value)
        self._internal_avail_treeview._realign()

    def _set_content_avail_treeview(self, new_value):
        """React to a set value request from the tree view."""
        self._set_content_value(new_value)
        self._internal_value_listview._populate()  

    def _set_content_value(self, new_value):
        """Set the content variable value."""
        variables = [v for v in self.panel_data + self.ghost_data]
        names = [v.name for v in variables]
        content_var = variables[names.index(rose.FILE_VAR_CONTENT)]
        if content_var.value != new_value:
            self.var_ops.set_var_value(content_var, new_value)
         
    def _sort_settings_duplicate(self, sect1, sect2):
        """Sort settings such that xyz(:) appears above xyz(1)."""
        sect1_base = sect1.rsplit("(", 1)[0]
        sect2_base = sect2.rsplit("(", 1)[0]
        if sect1_base != sect2_base:
            return 0
        sect1_ind = sect1.replace(sect1_base, "", 1)
        sect2_ind = sect2.replace(sect2_base, "", 1)
        return (sect2_ind == "(:)") - (sect1_ind == "(:)")

    def refresh(self, var_id=None):
        """Reload the container - don't need this at the moment."""
        pass


class FileListView(gtk.TreeView):

    """Class to hold and display an ordered list of strings.

    set_value is a function, accepting a new value string.
    get_data is a function that accepts no arguments and returns an
    ordered list of included names to display.
    handle_search is a function that accepts a name and triggers a
    search for it.

    """

    def __init__(self, set_value, get_data, handle_search):
        super(FileListView, self).__init__()
        self._set_value = set_value
        self._get_data = get_data
        self._handle_search = handle_search
        self.enable_model_drag_dest(
                  [('text/plain', 0, 0)],
                  gtk.gdk.ACTION_MOVE)
        self.enable_model_drag_source(
                  gtk.gdk.BUTTON1_MASK,
                  [('text/plain', 0, 0)],
                  gtk.gdk.ACTION_MOVE)
        self.connect("drag-data-get", self._handle_drag_get)
        self.connect_after("drag-data-received",
                           self._handle_drag_received)
        self.set_rules_hint(True)
        self.set_tooltip_text(
                       rose.config_editor.FILE_CONTENT_PANEL_TIP)
        self.connect("row-activated", self._handle_activation)
        self.show()
        col = gtk.TreeViewColumn()
        col.set_title(rose.config_editor.FILE_CONTENT_PANEL_TITLE)
        cell_text = gtk.CellRendererText()
        col.pack_start(cell_text, expand=True)
        col.set_cell_data_func(cell_text, self._set_cell_text)
        self.append_column(col)
        self._populate()

    def _handle_activation(self, treeview, path, col):
        """Handle a click on the main list view - start a search."""
        iter_ = treeview.get_model().get_iter(path)
        name = treeview.get_model().get_value(iter_, 0)
        self._handle_search(name)
        return False

    def _handle_button_press(self, treeview, event):
        """Handle a right click event on the main list view."""
        if not hasattr(event, "button") or event.button != 3:
            return False
        pathinfo = treeview.get_path_at_pos(int(event.x),
                                            int(event.y))
        if pathinfo is None:
            return False
        path, col, cell_x, cell_y = pathinfo
        iter_ = treeview.get_model().get_iter(path)
        name = treeview.get_model().get_value(iter_, 0)  
        self._popup_menu(name, event)
        return False

    def _handle_drag_get(self, treeview, drag, sel, info, time):
        """Handle an outgoing drag request."""
        model, iter_ = treeview.get_selection().get_selected()
        text = model.get_value(iter_, 0)
        sel.set_text(text)
        model.remove(iter_)  # Triggers the 'row-deleted' signal, sets value
        if not model.iter_n_children(None):
            model.append([rose.config_editor.FILE_CONTENT_PANEL_EMPTY])

    def _handle_drag_received(self, treeview, drag, x, y, sel, info,
                                       time):
        """Handle an incoming drag request."""
        if sel.data is None:
            return False
        drop_info = treeview.get_dest_row_at_pos(x, y)
        model = treeview.get_model()
        if drop_info:
            path, position = drop_info
            if (position == gtk.TREE_VIEW_DROP_BEFORE or
                position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                model.insert(path[0], [sel.data])
            else:
                model.insert(path[0] + 1, [sel.data])
        else:
            model.append([sel.data])
            path = None
        self._handle_reordering(model, path)

    def _handle_reordering(self, model, path):
        """Handle a drag-and-drop rearrangement in the main list view."""
        ok_values = []
        iter_ = model.get_iter_first()
        num_entries = model.iter_n_children(None)
        while iter_ is not None:
            name = model.get_value(iter_, 0)
            next_iter = model.iter_next(iter_)
            if name == rose.config_editor.FILE_CONTENT_PANEL_EMPTY:
                if num_entries > 1:
                    model.remove(iter_)
            else:
                ok_values.append(name)
            iter_ = next_iter
        new_value = " ".join(ok_values)
        self._set_value(new_value)

    def _populate(self):
        """Populate the main list view."""
        values = self._get_data()
        model = gtk.ListStore(str)
        if not values:
            values = [rose.config_editor.FILE_CONTENT_PANEL_EMPTY]
        for value in values:
            model.append([value])
        model.connect_after("row-deleted", self._handle_reordering)
        self.set_model(model)

    def _set_cell_text(self, column, cell, model, r_iter):
        name = model.get_value(r_iter, 0)
        if name == rose.config_editor.FILE_CONTENT_PANEL_EMPTY:
            cell.set_property("markup", "<i>" + name + "</i>")
        else:
            cell.set_property("markup", "<b>" + name + "</b>")

    def refresh(self):
        """Update the model values."""
        self._populate()


class FileTreeView(gtk.TreeView):

    """Class to hold and display a tree of content.

    set_value is a function, accepting a new value string.
    get_data is a function that accepts no arguments and returns a
    list of included names.
    get_available_data is a function that accepts no arguments and
    returns a list of available names.

    """

    def __init__(self, set_value, get_data, get_available_data):
        super(FileTreeView, self).__init__()
        # Generate the 'available' sections view.
        self._set_value = set_value
        self._get_data = get_data
        self._get_available_data = get_available_data
        self.set_headers_visible(True)
        self.set_rules_hint(True)
        self.enable_model_drag_dest(
                  [('text/plain', 0, 0)],
                  gtk.gdk.ACTION_MOVE)
        self.enable_model_drag_source(
                  gtk.gdk.BUTTON1_MASK,
                  [('text/plain', 0, 0)],
                  gtk.gdk.ACTION_MOVE)
        self.connect_after("button-release-event", self._handle_button)
        self.connect("drag-begin", self._handle_drag_begin)
        self.connect("drag-data-get", self._handle_drag_get)
        self.connect("drag-end", self._handle_drag_end)
        self._is_dragging = False
        model = gtk.TreeStore(str, bool, bool)
        self.set_model(model)
        col = gtk.TreeViewColumn()
        cell_toggle = gtk.CellRendererToggle()
        cell_toggle.connect_after("toggled", self._handle_cell_toggle)
        col.pack_start(cell_toggle, expand=False)
        col.set_cell_data_func(cell_toggle, self._set_cell_state)
        self.append_column(col)
        col = gtk.TreeViewColumn()
        col.set_title(rose.config_editor.FILE_CONTENT_PANEL_OPT_TITLE)
        cell_text = gtk.CellRendererText()
        col.pack_start(cell_text, expand=True)
        col.set_cell_data_func(cell_text, self._set_cell_text)
        self.append_column(col)
        self.set_expander_column(col)
        self.show()
        self._populate()

    def _populate(self):
        """Populate the 'available' sections view."""
        ok_content_sections = self._get_available_data()
        self._ok_content_sections = set(ok_content_sections)
        ok_values = self._get_data()
        model = self.get_model()
        sections_left = list(ok_content_sections)
        level_iter = None
        prev_name_all = None
        self._name_iter_map = {}
        while sections_left:
            name = sections_left.pop(0)
            name_base = name.rsplit("(", 1)[0]
            name_all = name_base + "(:)"
            is_in_value = name in ok_values
            is_implicit = name_all in ok_values and name != name_all
            if name == name_all:
                iter_ = model.append(None, [name, is_in_value, is_implicit])
                level_iter = iter_
                prev_name_all = name_all
            elif name_all != prev_name_all:
                iter_ = model.append(None, [name, is_in_value, is_implicit])
                level_iter = None
            else:
                iter_ = model.append(level_iter, [name, is_in_value,
                                                  is_implicit])
            self._name_iter_map[name] = iter_

    def _realign(self):
        """Refresh the states in the model."""
        ok_values = self._get_data()
        model = self.get_model()
        for name, iter_ in self._name_iter_map.items():
            is_in_value = name in ok_values
            is_implicit = name.rsplit("(", 1)[0] + "(:)" in ok_values
            if model.get_value(iter_, 1) != is_in_value:
                model.set_value(iter_, 1, is_in_value)
            if model.get_value(iter_, 2) != is_implicit:
                model.set_value(iter_, 2, is_implicit)

    def _set_cell_text(self, column, cell, model, r_iter):
        """Set markup for a section depending on its status."""
        section_name = model.get_value(r_iter, 0)
        is_in_value = model.get_value(r_iter, 1)
        is_implicit = model.get_value(r_iter, 2)
        if section_name.endswith("(:)"):
            r_iter = model.iter_children(r_iter)
            while r_iter is not None:
                if model.get_value(r_iter, 1) == True:
                    is_in_value = True
                    break
                r_iter = model.iter_next(r_iter)
        if is_in_value:
            cell.set_property("markup", "<b>{0}</b>".format(section_name))
            cell.set_property("sensitive", True)
        elif is_implicit:
            cell.set_property("markup", "{0}".format(section_name))
            cell.set_property("sensitive", False)
        else:
            cell.set_property("markup", section_name)
            cell.set_property("sensitive", True)

    def _set_cell_state(self, column, cell, model, r_iter):
        """Set the check box for a section depending on its status."""
        is_in_value = model.get_value(r_iter, 1)
        is_implicit = model.get_value(r_iter, 2)
        if is_in_value:
            cell.set_property("active", True)
            cell.set_property("sensitive", True)
        elif is_implicit:
            cell.set_property("active", True)
            cell.set_property("sensitive", False)
        else:
            cell.set_property("active", False)
            cell.set_property("sensitive", True)
            if not self._check_can_add(r_iter):
                cell.set_property("sensitive", False)
 
    def _handle_drag_begin(self, widget, drag):
        self._is_dragging = True

    def _handle_drag_end(self, widget, drag):
        self._is_dragging = False

    def _handle_drag_get(self, treeview, drag, sel, info, time):
        """Handle a drag data get."""
        model, iter_ = treeview.get_selection().get_selected()
        if not self._check_can_add(iter_):
            return False
        name = model.get_value(iter_, 0)
        sel.set("text/plain", 8, name)

    def _check_can_add(self, iter_):
        """Check whether a name can be added to the data."""
        model = self.get_model()
        if model.get_value(iter_, 1) or model.get_value(iter_, 2):
            return False
        child_iter = model.iter_children(iter_)
        while child_iter is not None:
            if (model.get_value(child_iter, 1) or
                model.get_value(child_iter, 2)):
                return False
            child_iter = model.iter_next(child_iter)
        return True

    def _handle_button(self, treeview, event):
        """Connect a left click on the available section to a toggle."""
        if event.button != 1 or self._is_dragging:
            return False
        pathinfo = treeview.get_path_at_pos(int(event.x),
                                            int(event.y))
        if pathinfo is None:
            return False
        path, col, cell_x, cell_y = pathinfo
        iter_ = treeview.get_model().get_iter(path)
        name = treeview.get_model().get_value(iter_, 0)
        if treeview.get_columns().index(col) == 1:
            self._handle_cell_toggle(None, path)

    def _handle_cell_toggle(self, cell, path, should_turn_off=None):
        """Change the content variable value here.
        
        cell is not used.
        path is the name to turn off or on.
        should_turn_off is as follows:
               None - toggle based on the cell value
               False - toggle on
               True - toggle off

        """
        text_index = 0
        model = self.get_model()
        r_iter = model.get_iter(path)
        this_name = model.get_value(r_iter, text_index)
        ok_values = self._get_data()
        model = self.get_model()
        can_add = self._check_can_add(r_iter)
        if ((should_turn_off is None or should_turn_off)
            and this_name in ok_values):
            ok_values.remove(this_name)
            model.set_value(r_iter, 1, False)
            if this_name.endswith("(:)"):
                basename = this_name.rsplit("(", 1)[0]
                self._toggle_internal_base(r_iter, basename, False)
            self._set_value(" ".join(ok_values))
        elif should_turn_off is None or not should_turn_off:
            if not can_add:
                return False
            ok_values = ok_values + [this_name]
            model.set_value(r_iter, 1, True)
            if this_name.endswith("(:)"):
                basename = this_name.rsplit("(", 1)[0]
                self._toggle_internal_base(r_iter, basename, True)
            self._set_value(" ".join(ok_values))
        self._realign()
        return False

    def _toggle_internal_base(self, base_iter, base_name, added=False):
        """Connect a toggle of xyz(:) to xyz(1), xyz(2), etc.
        
        base_iter is the iter pointing to xyz(:)
        base_name is the name without brackets e.g. xyz
        added is a boolean denoting toggle state

        """
        model = self.get_model()
        iter_ = model.iter_children(base_iter)
        while iter_ is not None:
            model.set_value(iter_, 2, added)
            iter_ = model.iter_next(iter_)
        return False

    def refresh(self):
        """Refresh the model."""
        self._realign()
