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

import shlex

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import metomi.rose.config
import metomi.rose.config_editor.util
import metomi.rose.config_editor.variable
import metomi.rose.formats
import metomi.rose.variable

from functools import cmp_to_key


class PageTable(Gtk.Table):

    """Return a widget table generated from panel_data.

    It uses the variable information to create instances of
    VariableWidget, which are then asked to insert themselves into the
    table.

    """

    MAX_ROWS = 2000
    MAX_COLS = 3
    BORDER_WIDTH = metomi.rose.config_editor.SPACING_SUB_PAGE

    def __init__(self, panel_data, ghost_data, var_ops, show_modes,
                 arg_str=None):
        super(PageTable, self).__init__(rows=self.MAX_ROWS,
                                        columns=self.MAX_COLS,
                                        homogeneous=False)
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        variable_is_ghost_list = self._get_sorted_variables()
        self.attach_variable_widgets(variable_is_ghost_list, start_index=0)
        self._show_and_hide_variable_widgets()
        self.show()

    def add_variable_widget(self, variable):
        """Add a variable widget that was previously in ghost_data."""
        new_variable_widget = self.get_variable_widget(variable)
        widget_coordinate_list = []
        for child in self.get_children():
            top_row = self.child_get(child, 'top_attach')[0]
            variable_widget = child.get_parent()
            if variable_widget not in [x[0] for x in widget_coordinate_list]:
                widget_coordinate_list.append((variable_widget, top_row))
        widget_coordinate_list.sort(key=lambda x: x[1])
        old_index = None
        for widget, index in widget_coordinate_list:
            if widget.variable.metadata["id"] == variable.metadata["id"]:
                old_index = index
                break
        if old_index is None:
            variable_is_ghost_list = self._get_sorted_variables()
            variables = [x[0] for x in variable_is_ghost_list]
            num_vars_above_this = variables.index(variable)
            if num_vars_above_this == 0:
                row_above_new = -1
            else:
                row_above_new = widget_coordinate_list[
                    num_vars_above_this - 1][1]
            for variable_widget, widget_row in widget_coordinate_list:
                if widget_row > row_above_new:
                    for child in self.get_children():
                        if child.get_parent() == variable_widget:
                            self.remove(child)
            new_variable_widget.insert_into(
                self, self.MAX_COLS, row_above_new + 1)
            self._show_and_hide_variable_widgets(new_variable_widget)
            rownum = row_above_new + 2
            for variable_widget, widget_row in widget_coordinate_list:
                if (widget_row > row_above_new and
                        variable_widget.variable.metadata.get('id') !=
                        variable.metadata.get('id')):
                    variable_widget.insert_into(self, self.MAX_COLS, rownum)
                    rownum += 1
        else:
            self.reload_variable_widget(variable)

    def attach_variable_widgets(self, variable_is_ghost_list, start_index=0):
        """Create and attach variable widgets for these inputs."""
        rownum = start_index
        for variable, is_ghost in variable_is_ghost_list:
            variable_widget = self.get_variable_widget(variable, is_ghost)
            variable_widget.insert_into(self, self.MAX_COLS, rownum + 1)
            variable_widget.set_sensitive(not is_ghost)
            rownum += 1

    def get_variable_widget(self, variable, is_ghost=False):
        """Create a variable widget for this variable."""
        return metomi.rose.config_editor.variable.VariableWidget(
            variable,
            self.var_ops,
            is_ghost=is_ghost,
            show_modes=self.show_modes)

    def reload_variable_widget(self, variable):
        """Reload the widgets for the given variable."""
        is_ghost = variable in self.ghost_data
        new_variable_widget = self.get_variable_widget(variable, is_ghost)
        new_variable_widget.set_sensitive(not is_ghost)
        focus_dict = {"had_focus": False}
        variable_row = None
        for child in self.get_children():
            variable_widget = child.get_parent()
            if (variable_widget.variable.name == variable.name and
                    variable_widget.variable.metadata.get('id') ==
                    variable.metadata.get('id')):
                if "index" not in focus_dict:
                    focus_dict["index"] = variable_widget.get_focus_index()
                if self.get_focus_child() == child:
                    focus_dict["had_focus"] = True
                top_row = self.child_get(child, 'top_attach')[0]
                variable_row = top_row
                self.remove(child)
                child.destroy()
        if variable_row is None:
            return False
        new_variable_widget.insert_into(self, self.MAX_COLS, variable_row)
        self._show_and_hide_variable_widgets(new_variable_widget)
        if focus_dict["had_focus"]:
            new_variable_widget.grab_focus(index=focus_dict.get("index"))

    def remove_variable_widget(self, variable):
        """Remove the selected widget and/or relocate to ghosts."""
        self.reload_variable_widget(variable)

    def _get_sorted_variables(self):
        sort_key_vars = []
        for val in self.panel_data + self.ghost_data:
            sort_key = (
                (val.metadata.get("sort-key", "~")), val.metadata["id"])
            is_ghost = val in self.ghost_data
            sort_key_vars.append((sort_key, val, is_ghost))
        sort_key_vars.sort(key=cmp_to_key(lambda x, y: metomi.rose.config_editor.util.null_cmp(x[0], y[0])))
        sort_key_vars.sort(key=lambda x: "=null" in x[1].metadata["id"])
        return [(x[1], x[2]) for x in sort_key_vars]

    def _show_and_hide_variable_widgets(self, just_this_widget=None):
        """Figure out whether to display a widget or not."""
        modes = self.show_modes
        if just_this_widget:
            variable_widgets = [just_this_widget]
        else:
            variable_widgets = []
            for child in self.get_children():
                if child.get_parent() not in variable_widgets:
                    variable_widgets.append(child.get_parent())
        for variable_widget in variable_widgets:
            variable = variable_widget.variable
            ign_reason = variable.ignored_reason
            if variable.error:
                variable_widget.show()
            elif (len(variable.metadata.get(
                    metomi.rose.META_PROP_VALUES, [])) == 1 and
                    not modes[metomi.rose.config_editor.SHOW_MODE_FIXED]):
                variable_widget.hide()
            elif (variable_widget.is_ghost and
                  not modes[metomi.rose.config_editor.SHOW_MODE_LATENT]):
                variable_widget.hide()
            elif ((metomi.rose.variable.IGNORED_BY_SYSTEM in ign_reason or
                   metomi.rose.variable.IGNORED_BY_SECTION in ign_reason) and
                  not modes[metomi.rose.config_editor.SHOW_MODE_IGNORED]):
                variable_widget.hide()
            elif (metomi.rose.variable.IGNORED_BY_USER in ign_reason and
                  not (modes[metomi.rose.config_editor.SHOW_MODE_IGNORED] or
                       modes[metomi.rose.config_editor.SHOW_MODE_USER_IGNORED])):
                variable_widget.hide()
            else:
                variable_widget.show()

    def show_mode_change(self, mode, mode_on=False):
        done_variable_widgets = []
        for child in self.get_children():
            parent = child.get_parent()
            if parent in done_variable_widgets:
                continue
            parent.set_show_mode(mode, mode_on)
            done_variable_widgets.append(parent)
        self._show_and_hide_variable_widgets()

    def update_ignored(self):
        self._show_and_hide_variable_widgets()


class PageArrayTable(PageTable):

    """Return a widget table that treats array values as row elements."""

    def __init__(self, *args, **kwargs):
        arg_str = kwargs.get("arg_str", "")
        if arg_str is None:
            arg_str = ""
        self.headings = shlex.split(arg_str)
        super(PageArrayTable, self).__init__(*args, **kwargs)
        self._set_length()

    def attach_variable_widgets(self, variable_is_ghost_list, start_index=0):
        """Create and attach variable widgets for these inputs."""
        self._set_length()
        rownum = start_index
        for variable, is_ghost in variable_is_ghost_list:
            variable_widget = self.get_variable_widget(variable, is_ghost)
            variable_widget.insert_into(self, self.MAX_COLS, rownum + 1)
            variable_widget.set_sensitive(not is_ghost)
            rownum += 1

    def get_variable_widget(self, variable, is_ghost=False):
        """Create a variable widget for this variable."""
        if (metomi.rose.META_PROP_LENGTH in variable.metadata or
                isinstance(variable.metadata.get(metomi.rose.META_PROP_TYPE), list)):
            return metomi.rose.config_editor.variable.RowVariableWidget(
                variable,
                self.var_ops,
                is_ghost=is_ghost,
                show_modes=self.show_modes,
                length=self.array_length)
        return metomi.rose.config_editor.variable.VariableWidget(
            variable,
            self.var_ops,
            is_ghost=is_ghost,
            show_modes=self.show_modes)

    def _set_length(self):
        max_meta_length = 0
        max_values_length = 0
        for variable in self.panel_data + self.ghost_data:
            length = variable.metadata.get(metomi.rose.META_PROP_LENGTH)
            if (length is not None and length.isdigit() and
                    int(length) > max_meta_length):
                max_meta_length = int(length)
            types = variable.metadata.get(metomi.rose.META_PROP_TYPE)
            if isinstance(types, list) and len(types) > max_meta_length:
                max_meta_length = len(types)
            values_length = len(metomi.rose.variable.array_split(variable.value))
            if values_length > max_values_length:
                max_values_length = values_length
        self.array_length = max([max_meta_length, max_values_length])


class PageLatentTable(Gtk.Table):

    """Return a widget table generated from panel_data.

    It uses the variable information to create instances of
    VariableWidget, which are then asked to insert themselves into the
    table.

    This particular container always shows latent variables.

    """

    MAX_ROWS = 2000
    MAX_COLS = 3

    def __init__(self, panel_data, ghost_data, var_ops, show_modes,
                 arg_str=None):
        super(PageLatentTable, self).__init__(
            rows=self.MAX_ROWS, columns=self.MAX_COLS, homogeneous=False)
        self.show()
        self.num_removes = 0
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        self.title_on = (
            not self.show_modes[metomi.rose.config_editor.SHOW_MODE_NO_TITLE])
        self.alt_menu_class = metomi.rose.config_editor.menuwidget.CheckedMenuWidget
        rownum = 0
        v_sort_ids = []
        for val in self.panel_data + self.ghost_data:
            v_sort_ids.append((val.metadata.get("sort-key", ""),
                               val.metadata["id"]))
        v_sort_ids.sort(key=cmp_to_key(
            lambda x, y: metomi.rose.config.sort_settings(
                x[0] + "~" + x[1], y[0] + "~" + y[1])))
        v_sort_ids.sort(key=lambda x: "=null" in x[1])
        for _, var_id in v_sort_ids:
            is_ghost = False
            for variable in self.panel_data:
                if variable.metadata['id'] == var_id:
                    break
            else:
                for variable in self.ghost_data:
                    if variable.metadata['id'] == var_id:
                        is_ghost = True
                        break
            variable_widget = self.get_variable_widget(
                variable, is_ghost=is_ghost)
            variable_widget.insert_into(self, self.MAX_COLS, rownum + 1)
            variable_widget.set_sensitive(not is_ghost)
            rownum += 1

    def get_variable_widget(self, variable, is_ghost=False):
        """Create a variable widget for this variable."""
        return metomi.rose.config_editor.variable.VariableWidget(
            variable, self.var_ops, is_ghost=is_ghost,
            show_modes=self.show_modes)

    def reload_variable_widget(self, variable):
        """Reload the widgets for the given variable."""
        is_ghost = variable in self.ghost_data
        new_variable_widget = self.get_variable_widget(variable, is_ghost)
        new_variable_widget.set_sensitive(not is_ghost)
        focus_dict = {"had_focus": False}
        variable_row = None
        for child in self.get_children():
            variable_widget = child.get_parent()
            if (variable_widget.variable.name == variable.name and
                    variable_widget.variable.metadata.get('id') ==
                    variable.metadata.get('id')):
                if "index" not in focus_dict:
                    focus_dict["index"] = variable_widget.get_focus_index()
                if getattr(self, 'focus_child') == child:
                    focus_dict["had_focus"] = True
                top_row = self.child_get(child, 'top_attach')[0]
                variable_row = top_row
                self.remove(child)
                child.destroy()
        if variable_row is None:
            return False
        new_variable_widget.insert_into(self, self.MAX_COLS, variable_row)
        if focus_dict["had_focus"]:
            new_variable_widget.grab_focus(index=focus_dict.get("index"))

    def show_mode_change(self, mode, mode_on=False):
        done_variable_widgets = []
        for child in self.get_children():
            parent = child.get_parent()
            if parent in done_variable_widgets:
                continue
            parent.set_show_mode(mode, mode_on)
            done_variable_widgets.append(parent)

    def refresh(self, var_id=None):
        """Reload the container - don't need this at the moment."""
        pass

    def update_ignored(self):
        """Update ignored statuses - no need to do anything extra here."""
        pass
