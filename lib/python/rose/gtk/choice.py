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

import pygtk
pygtk.require('2.0')
import gtk

import rose


class ChoicesListView(gtk.TreeView):

    """Class to hold and display an ordered list of strings.

    set_value is a function, accepting a new value string.
    get_data is a function that accepts no arguments and returns an
    ordered list of included names to display.
    handle_search is a function that accepts a name and triggers a
    search for it.
    title is displayed as the column header, if given.

    """

    def __init__(self, set_value, get_data, handle_search,
                 title=rose.config_editor.CHOICE_TITLE_INCLUDED):
        super(ChoicesListView, self).__init__()
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
        self.connect("button-press-event", self._handle_button_press)
        self.connect("drag-data-get", self._handle_drag_get)
        self.connect_after("drag-data-received",
                           self._handle_drag_received)
        self.set_rules_hint(True)
        self.connect("row-activated", self._handle_activation)
        self.show()
        col = gtk.TreeViewColumn()
        col.set_title(title)
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
        self._popup_menu(iter_, event)
        return False

    def _handle_drag_get(self, treeview, drag, sel, info, time):
        """Handle an outgoing drag request."""
        model, iter_ = treeview.get_selection().get_selected()
        text = model.get_value(iter_, 0)
        sel.set_text(text)
        model.remove(iter_)  # Triggers the 'row-deleted' signal, sets value
        if not model.iter_n_children(None):
            model.append([rose.config_editor.CHOICE_LABEL_EMPTY])

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

    def _handle_reordering(self, model=None, path=None):
        """Handle a drag-and-drop rearrangement in the main list view."""
        if model is None:
            model = self.get_model()
        ok_values = []
        iter_ = model.get_iter_first()
        num_entries = model.iter_n_children(None)
        while iter_ is not None:
            name = model.get_value(iter_, 0)
            next_iter = model.iter_next(iter_)
            if name == rose.config_editor.CHOICE_LABEL_EMPTY:
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
            values = [rose.config_editor.CHOICE_LABEL_EMPTY]
        for value in values:
            model.append([value])
        model.connect_after("row-deleted", self._handle_reordering)
        self.set_model(model)

    def _popup_menu(self, iter_, event): 
        # Pop up a menu for the main list view. 
        """Launch a popup menu for add/clone/remove.""" 
        ui_config_string = """<ui> <popup name='Popup'> 
                              <menuitem action="Remove"/> 
                              </popup></ui>""" 
        text = rose.config_editor.CHOICE_MENU_REMOVE 
        actions = [("Remove", gtk.STOCK_DELETE, text)] 
        uimanager = gtk.UIManager() 
        actiongroup = gtk.ActionGroup('Popup') 
        actiongroup.add_actions(actions) 
        uimanager.insert_action_group(actiongroup, pos=0) 
        uimanager.add_ui_from_string(ui_config_string) 
        remove_item = uimanager.get_widget('/Popup/Remove') 
        remove_item.connect("activate", 
                            lambda b: self._remove_iter(iter_)) 
        menu = uimanager.get_widget('/Popup') 
        menu.popup(None, None, None, event.button, event.time) 
        return False

    def _remove_iter(self, iter_):
        self.get_model().remove(iter_)
        self._handle_reordering()
        self._populate()

    def _set_cell_text(self, column, cell, model, r_iter):
        name = model.get_value(r_iter, 0)
        if name == rose.config_editor.CHOICE_LABEL_EMPTY:
            cell.set_property("markup", "<i>" + name + "</i>")
        else:
            cell.set_property("markup", "<b>" + name + "</b>")

    def refresh(self):
        """Update the model values."""
        self._populate()


class ChoicesTreeView(gtk.TreeView):

    """Class to hold and display a tree of content.

    set_value is a function, accepting a new value string.
    get_data is a function that accepts no arguments and returns a
    list of included names.
    get_available_data is a function that accepts no arguments and
    returns a list of available names.
    get_groups is a function that accepts a name and a list of
    available names and returns groups that supercede name.
    get_is_implicit is an optional function that accepts a name and
    returns whether the name is implicitly included in the content.
    title is displayed as the column header, if given.

    """

    def __init__(self, set_value, get_data, get_available_data,
                 get_groups, get_is_implicit=None,
                 title=rose.config_editor.CHOICE_TITLE_AVAILABLE):
        super(ChoicesTreeView, self).__init__()
        # Generate the 'available' sections view.
        self._set_value = set_value
        self._get_data = get_data
        self._get_available_data = get_available_data
        self._get_groups = get_groups
        self._get_is_implicit = get_is_implicit
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
        col.set_title(title)
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
        self._name_iter_map = {}
        while sections_left:
            name = sections_left.pop(0)
            is_included = name in ok_values
            groups = self._get_groups(name, ok_content_sections)
            if self._get_is_implicit is None:
                is_implicit = any([g in ok_values for g in groups])
            else:
                is_implicit = self._get_is_implicit(name)
            if groups:
                iter_ = model.append(self._name_iter_map[groups[-1]],
                                     [name, is_included, is_implicit])
            else:
                iter_ = model.append(None, [name, is_included, is_implicit])
            self._name_iter_map[name] = iter_

    def _realign(self):
        """Refresh the states in the model."""
        ok_values = self._get_data()
        model = self.get_model()
        ok_content_sections = self._get_available_data()
        for name, iter_ in self._name_iter_map.items():
            is_in_value = name in ok_values
            if self._get_is_implicit is None:
                groups = self._get_groups(name, ok_content_sections)
                is_implicit = any([g in ok_values for g in groups])
            else:
                is_implicit = self._get_is_implicit(name)
            if model.get_value(iter_, 1) != is_in_value:
                model.set_value(iter_, 1, is_in_value)
            if model.get_value(iter_, 2) != is_implicit:
                model.set_value(iter_, 2, is_implicit)

    def _set_cell_text(self, column, cell, model, r_iter):
        """Set markup for a section depending on its status."""
        section_name = model.get_value(r_iter, 0)
        is_in_value = model.get_value(r_iter, 1)
        is_implicit = model.get_value(r_iter, 2)
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
        should_add = False
        if ((should_turn_off is None or should_turn_off)
            and this_name in ok_values):
            ok_values.remove(this_name)
        elif should_turn_off is None or not should_turn_off:
            if not can_add:
                return False
            should_add = True
            ok_values = ok_values + [this_name]
        else:
            self._realign()
            return False
        model.set_value(r_iter, 1, should_add)
        if model.iter_n_children(r_iter):
            self._toggle_internal_base(r_iter, this_name, should_add)
        self._set_value(" ".join(ok_values))
        self._realign()
        return False

    def _toggle_internal_base(self, base_iter, base_name, added=False):
        """Connect a toggle of a group to its children.
        
        base_iter is the iter pointing to the group
        base_name is the name of the group
        added is a boolean denoting toggle state

        """
        model = self.get_model()
        iter_ = model.iter_children(base_iter)
        skip_children = False
        while iter_ is not None:
            model.set_value(iter_, 2, added)
            if not skip_children:
                next_iter = model.iter_children(iter_)
            if skip_children or next_iter is None:
                next_iter = model.iter_next(iter_)
                skip_children = False
            if next_iter is None:
                next_iter = model.iter_parent(iter_)
                skip_children = True
            iter_ = next_iter
        return False

    def refresh(self):
        """Refresh the model."""
        self._realign()
