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
        r = 0
        for variable, is_ghost in variable_is_ghost_list:
            variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost=is_ghost,
                                                show_modes=self.show_modes)
            variablewidget.insert_into(self, self.MAX_COLS, r + 1)
            if is_ghost:
                variablewidget.set_sensitive(False)
                if (not self._is_var_compulsory(variable) and
                    not self.show_modes[rose.config_editor.SHOW_MODE_LATENT]):
                    # Hidden if not compulsory and not SHOW_MODE_LATENT.
                    variablewidget.hide()
            if (self._should_hide_var_fixed(variable) and 
                not variable.error):
                variablewidget.hide()
            r = r + 1
        self.show()

    def add_variable_widget(self, variable):
        """Add a variable widget that was previously in ghost_data."""
        new_variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost=False,
                                                show_modes=self.show_modes)
        widget_coordinate_list = []
        for child in self.get_children():
            top_row = self.child_get(child, 'top_attach')[0]
            variablewidget = child.get_parent()
            if variablewidget not in [x[0] for x in widget_coordinate_list]:
                widget_coordinate_list.append((variablewidget, top_row))
        widget_coordinate_list.sort(lambda x, y: cmp(x[1], y[1]))
        old_index = None
        for widget, index in widget_coordinate_list:
            if widget.variable.metadata["id"] == variable.metadata["id"]:
                old_index = index
                parent = widget.get_parent()
                break
        if old_index is None:
            variable_is_ghost_list = self._get_sorted_variables()
            variables = [x[0] for x in variable_is_ghost_list]
            num_vars_above_this = variables.index(variable)
            if num_vars_above_this == 0:
                row_above_new = -1
            else:
                row_above_new = widget_coordinate_list[num_vars_above_this - 1][1]
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
        else:            
            self.reload_variable_widget(variable)

    def reload_variable_widget(self, variable):
        """Reload the widgets for the given variable."""
        is_ghost = variable in self.ghost_data
        new_variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost,
                                                show_modes=self.show_modes)
        new_variablewidget.set_sensitive(not is_ghost)
        if (is_ghost and
            not self._is_var_compulsory(variable) and
            not self.show_modes[rose.config_editor.SHOW_MODE_LATENT]):
            # Hidden if not compulsory and not SHOW_MODE_LATENT.
            new_variablewidget.hide()
        else:
            new_variablewidget.show()
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
        self.reload_variable_widget(variable)

    def _get_sorted_variables(self):
        sort_key_vars = []
        for v in self.panel_data + self.ghost_data:
            sort_key = v.metadata.get("sort-key", "") + "~" + v.metadata["id"]
            is_ghost = v in self.ghost_data
            sort_key_vars.append((sort_key, v, is_ghost))
        sort_key_vars.sort(
               lambda x, y: rose.config.sort_settings(x[0], y[0]))
        sort_key_vars.sort(lambda x, y: cmp("=null" in x[1].metadata["id"],
                                            "=null" in y[1].metadata["id"]))
        return [(x[1], x[2]) for x in sort_key_vars]

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
        for child in self.get_children():
            variablewidget = child.get_parent()
            variable = variablewidget.variable
            if variablewidget.is_ghost:
                if should_show_latent:
                    variablewidget.show()
                elif not self._is_var_compulsory(variable):
                    variablewidget.hide()

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

    def __init__(self, panel_data, ghost_data, var_ops, show_modes,
                 arg_str=None):
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
