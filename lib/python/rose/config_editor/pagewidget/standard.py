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

import rose.config
import rose.config_editor.variable
import rose.formats
import rose.variable


class PageTable(gtk.Table):

    """Return a widget table generated from panel_data.

    It uses the variable information to create instances of
    VariableWidget, which are then asked to insert themselves into the
    table.

    """

    MAX_ROWS = 2000
    MAX_COLS = 3
    BORDER_WIDTH = rose.config_editor.SPACING_SUB_PAGE

    def __init__(self, panel_data, ghost_data, var_ops, show_modes):
        super(PageTable, self).__init__(rows=self.MAX_ROWS,
                                     columns=self.MAX_COLS,
                                     homogeneous=False)
        self.num_removes = 0
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        r = 0
        for variable in self.panel_data:
            variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost=False,
                                                show_modes=self.show_modes)
            variablewidget.insert_into(self, self.MAX_COLS, r + 1)
            if (self._should_hide_var_fixed(variable) and 
                not variable.error):
                variablewidget.hide()
            r = r + 1
        ghost_r = 0
        for variable in self.ghost_data:
            if self._is_var_compulsory(variable):
                variablewidget = rose.config_editor.variable.VariableWidget(
                                                    variable,
                                                    self.var_ops,
                                                    is_ghost=True,
                                                    show_modes=self.show_modes)
                variablewidget.insert_into(self, self.MAX_COLS,
                                           ghost_r + r + 1)
                variablewidget.set_sensitive(False)
                ghost_r = ghost_r + 1
        if self.show_modes[rose.config_editor.SHOW_MODE_LATENT]:
            for variable in self.ghost_data:
                if self._is_var_compulsory(variable):
                    continue
                variablewidget = rose.config_editor.variable.VariableWidget(
                                                    variable,
                                                    self.var_ops,
                                                    is_ghost=True,
                                                    show_modes=self.show_modes)
                variablewidget.insert_into(self, self.MAX_COLS,
                                           ghost_r + r + 1)
                variablewidget.set_sensitive(False)
                ghost_r = ghost_r + 1
        self.show()

    def add_variable_widget(self, variable):
        """Add a variable widget that was previously in ghost_data."""
        widget_coordinate_list = []
        for child in self.get_children():
            top_row = self.child_get(child, 'top_attach')[0]
            variablewidget = child.get_parent()
            if variablewidget not in [x[0] for x in widget_coordinate_list]:
                widget_coordinate_list.append((variablewidget, top_row))
        widget_coordinate_list.sort(lambda x, y: cmp(x[1], y[1]))
        num_vars_above_this = self.panel_data.index(variable)
        if num_vars_above_this == 0:
            row_above_new = -1
        else:
            row_above_new = widget_coordinate_list[num_vars_above_this - 1][1]
        new_variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost=False,
                                                show_modes=self.show_modes)
        for variablewidget, widget_row in widget_coordinate_list:
            if widget_row > row_above_new:
                for child in self.get_children():
                    if child.get_parent() == variablewidget:
                        self.remove(child)
        new_variablewidget.insert_into(self, self.MAX_COLS, row_above_new + 1)
        if (self._should_hide_var_fixed(variable) and 
            not variable.error):
            new_variablewidget.hide()
        r = row_above_new + 2
        for variablewidget, widget_row in widget_coordinate_list:
            if (widget_row > row_above_new and
                variablewidget.variable.metadata.get('id') !=
                variable.metadata.get('id')):
                variablewidget.insert_into(self, self.MAX_COLS, r)
                r += 1

    def reload_variable_widget(self, variable):
        """Reload the widgets for the given variable."""
        is_ghost = variable in self.ghost_data
        new_variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost,
                                                show_modes=self.show_modes)
        new_variablewidget.set_sensitive(not is_ghost)
        focus_dict = {"had_focus": False}
        for child in self.get_children():
            variablewidget = child.get_parent()
            if (variablewidget.variable.name == variable.name and
                variablewidget.variable.metadata.get('id') ==
                variable.metadata.get('id')):
                if "index" not in focus_dict:
                    focus_dict["index"] = variablewidget.get_focus_index()
                if getattr(self, 'focus_child') == child:
                    focus_dict["had_focus"] = True
                top_row = self.child_get(child, 'top_attach')[0]
                variable_row = top_row
                self.remove(child)
                child.destroy()
        new_variablewidget.insert_into(self, self.MAX_COLS, variable_row)
        if (self._should_hide_var_fixed(variable) and not variable.error):
            new_variablewidget.hide()
        else:
            if focus_dict["had_focus"]:
                new_variablewidget.grab_focus(index=focus_dict.get("index"))


    def remove_variable_widget(self, variable):
        """Remove the selected widget and/or relocate to ghosts."""
        was_removed = 0
        for child in self.get_children():
            variablewidget = child.get_parent()
            if (not variablewidget.is_ghost and
                variablewidget.variable.name == variable.name and
                variablewidget.variable.metadata.get('id') ==
                variable.metadata.get('id')):
                self.remove(child)
                child.destroy()
                was_removed = 1
        self.num_removes += was_removed
        if (self.show_modes[rose.config_editor.SHOW_MODE_LATENT] or
            self._is_var_compulsory(variable)):
            widget_coordinate_list = []
            ghost_top_row = 0
            for child in self.get_children():
                top_row = self.child_get(child, 'top_attach')[0]
                if (child.get_parent() not in
                    [x[0] for x in widget_coordinate_list]):
                    widget_coordinate_list.append((child.get_parent(),
                                                   top_row))
                if (ghost_top_row is None or top_row > ghost_top_row):
                    if not self._is_vwidget_optional_ghost(
                                            child.get_parent()):
                        ghost_top_row = top_row
            for child in self.get_children():
                top_row = self.child_get(child, 'top_attach')[0]
                if self._is_vwidget_optional_ghost(child.get_parent()):
                    self.remove(child)
            ghost_top_row += 1
            new_variablewidget = rose.config_editor.variable.VariableWidget(
                                                    variable,
                                                    self.var_ops,
                                                    is_ghost=True,
                                                    show_modes=self.show_modes)
            new_variablewidget.set_sensitive(False)
            if (self._should_hide_var_fixed(variable) and 
                not variable.error):
                new_variablewidget.hide()
            if variable.name == '':
                new_variablewidget.hide()
            row_cmp = lambda x, y: cmp(x[1], y[1])
            widget_coordinate_list.sort(row_cmp)
            new_variablewidget.insert_into(self, self.MAX_COLS, ghost_top_row)
            r = ghost_top_row + 1
            for variablewidget, top_row in widget_coordinate_list:
                if self._is_vwidget_optional_ghost(variablewidget):
                    variablewidget.insert_into(self, self.MAX_COLS, r)
                    r += 1
            for child in self.get_children():
                top_row = self.child_get(child, 'top_attach')[0]

    def _is_var_compulsory(self, variable):
        comp_val = variable.metadata.get(rose.META_PROP_COMPULSORY)
        return comp_val == rose.META_PROP_VALUE_TRUE

    def _should_hide_var_fixed(self, variable):
        return (not self.show_modes[rose.config_editor.SHOW_MODE_FIXED] and
                len(variable.metadata.get(rose.META_PROP_VALUES, [])) == 1 and
                variable not in self.ghost_data)

    def _is_vwidget_optional_ghost(self, variablewidget):
        return (variablewidget.is_ghost and
                not self._is_var_compulsory(variablewidget.variable))

    def _show_fixed(self, should_show_fixed=False):
        """Display or hide 'fixed' variables."""
        for child in self.get_children():
            variable = child.get_parent().variable
            if len(variable.metadata.get(rose.META_PROP_VALUES, [])) == 1:
                if should_show_fixed:
                    child.get_parent().show()
                elif not variable.error:
                    child.get_parent().hide()

    def _show_latent(self, should_show_latent=False):
        """Display or remove 'ghost' variables."""
        max_normal_row = 0
        for child in self.get_children():
            top_row = self.child_get(child, 'top_attach')[0]
            if top_row > max_normal_row:
                var = child.get_parent().variable
                if not self._is_vwidget_optional_ghost(child.get_parent()):
                    max_normal_row = top_row
        ghost_row = max_normal_row + 1
        if should_show_latent:
            for variable in self.ghost_data:
                if (variable.metadata.get(rose.META_PROP_COMPULSORY) ==
                    rose.META_PROP_VALUE_TRUE):
                    continue
                variablewidget = rose.config_editor.variable.VariableWidget(
                                                    variable,
                                                    self.var_ops,
                                                    is_ghost=True,
                                                    show_modes=self.show_modes)
                variablewidget.insert_into(self, self.MAX_COLS, ghost_row + 1)
                variablewidget.set_sensitive(False)
                ghost_row = ghost_row + 1
        else:
            for child in self.get_children():
                top_row = self.child_get(child, 'top_attach')[0]
                if top_row >= ghost_row:
                    self.remove(child)

    def show_mode_change(self, mode, mode_on=False):
        done_variable_widgets = []
        for child in self.get_children():
            parent = child.get_parent()
            if parent in done_variable_widgets:
                continue
            parent.set_show_mode(mode, mode_on)
            done_variable_widgets.append(parent)
        if mode == rose.config_editor.SHOW_MODE_LATENT:
            self._show_latent(mode_on)
        elif mode == rose.config_editor.SHOW_MODE_FIXED:
            self._show_fixed(mode_on)


class PageLatentTable(gtk.Table):

    """Return a widget table generated from panel_data.

    It uses the variable information to create instances of
    VariableWidget, which are then asked to insert themselves into the
    table.

    This particular container always shows latent variables.

    """

    MAX_ROWS = 2000
    MAX_COLS = 3

    def __init__(self, panel_data, ghost_data, var_ops, show_modes):
        super(PageLatentTable, self).__init__(rows=self.MAX_ROWS,
                                     columns=self.MAX_COLS,
                                     homogeneous=False)
        self.show()
        self.num_removes = 0
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        self.title_on = (not self.show_modes[
                                  rose.config_editor.SHOW_MODE_NO_TITLE])
        self.alt_menu_class = rose.config_editor.menuwidget.CheckedMenuWidget
        r = 0
        v_sort_ids = []
        for v in self.panel_data + self.ghost_data:
            v_sort_ids.append((v.metadata.get("sort-key", ""),
                               v.metadata["id"]))
        v_sort_ids.sort(
               lambda x, y: rose.config.sort_settings(
                                 x[0] + "~" + x[1], y[0] + "~" + y[1]))
        v_sort_ids.sort(lambda x, y: cmp("=null" in x[1], "=null" in y[1]))
        for sort_key, var_id in v_sort_ids:
            is_ghost = False
            for variable in self.panel_data:
                if variable.metadata['id'] == var_id:
                    break
            else:
                for variable in self.ghost_data:
                    if variable.metadata['id'] == var_id:
                        is_ghost = True
                        break
            variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost=is_ghost,
                                                show_modes=self.show_modes)
            variablewidget.insert_into(self, self.MAX_COLS, r + 1)
            variablewidget.set_sensitive(not is_ghost)
            r = r + 1

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
