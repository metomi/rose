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

import rose.config_editor.variable
import rose.formats

class Table(gtk.Table):

    """Return a widget table generated from panel_data.

    It uses the variable information to create instances of
    VariableWidget, which are then asked to insert themselves into the
    table.

    """

    MAX_ROWS = 2000
    MAX_COLS = 3
    BORDER_WIDTH = rose.config_editor.SPACING_SUB_PAGE

    def __init__(self, panel_data, ghost_data, var_ops, show_modes):
        super(Table, self).__init__(rows=self.MAX_ROWS,
                                    columns=self.MAX_COLS,
                                    homogeneous=False)
        self.num_removes = 0
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        self.title_on = (not self.show_modes[
                                  rose.config_editor.SHOW_MODE_NO_TITLE])
        r = 0
        for variable in self.panel_data:
            variablewidget = rose.config_editor.variable.VariableWidget(
                                                variable,
                                                self.var_ops,
                                                is_ghost=False,
                                                show_title=self.title_on)
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
                                                    show_title=self.title_on)
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
                                                    show_title=self.title_on)
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
                                                show_title=self.title_on)
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
                                                show_title=self.title_on)
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
                                                    show_title=self.title_on)
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

    def show_fixed(self, should_show_fixed=False):
        """Display or hide 'fixed' variables."""
        for child in self.get_children():
            variable = child.get_parent().variable
            if len(variable.metadata.get(rose.META_PROP_VALUES, [])) == 1:
                if should_show_fixed:
                    child.get_parent().show()
                elif not variable.error:
                    child.get_parent().hide()

    def show_latent(self, should_show_latent=False):
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
                                                    show_title=self.title_on)
                variablewidget.insert_into(self, self.MAX_COLS, ghost_row + 1)
                variablewidget.set_sensitive(False)
                ghost_row = ghost_row + 1
        else:
            for child in self.get_children():
                top_row = self.child_get(child, 'top_attach')[0]
                if top_row >= ghost_row:
                    self.remove(child)

    def show_title(self, title_off=False):
        done_variable_widgets = []
        self.title_on = not title_off
        for child in self.get_children():
            parent = child.get_parent()
            if parent in done_variable_widgets:
                continue
            parent.set_titled(not title_off)
            done_variable_widgets.append(parent)


class FileVBox(gtk.VBox):

    """Return a custom container for file-level options."""

    MAX_COLS_CONTENT = 2
    MAX_COLS_SOURCE = 3
    MAX_ROWS_CONTENT = 1
    MAX_ROWS_SOURCE = 3
    SPACING = rose.config_editor.SPACING_SUB_PAGE
    CONTENT_LABEL = 'use internal data'
    EMPTY_LABEL = 'file is empty'
    RESOURCE_LABEL = 'use file from resource'

    def __init__(self, panel_data, ghost_data, var_ops, show_modes,
                 format_keys_func):
        super(FileVBox, self).__init__(spacing=self.SPACING)
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        self.trigger_ask_for_config_keys = format_keys_func
        format = [f for f in rose.formats.__dict__ if not f.startswith('__')]
        original_data = self.panel_data
        hbox = gtk.HBox(spacing=self.SPACING)
        external_label = gtk.RadioButton(label=self.RESOURCE_LABEL)
        self.external_frame = gtk.Frame()
        self.external_frame.set_label_widget(external_label)
        external_label.set_active(True)
        if rose.FILE_VAR_SOURCE not in [x.name for x in self.panel_data]:
            external_label.set_active(False)
        external_label.connect('toggled',
                               lambda b: self._type_toggle(b, table))
        external_label.show()
        table = self._make_and_insert_table()
        if not external_label.get_active():
            for widget in table.get_children():
                widget.set_sensitive(False)
        self.external_frame.show()
        hbox.pack_start(self.external_frame, expand=True, fill=True,
                        padding=self.SPACING)
        hbox.show()
        self.pack_start(hbox, expand=False, fill=False, padding=self.SPACING)
        self.show()
        for variable in self.panel_data + self.ghost_data:
            if variable.name == rose.FILE_VAR_CONTENT:
                break
        else:
            if not self.panel_data:
                hbox.remove(self.external_frame)
            return
        content_format_frame = gtk.Frame()
        content_format_label = gtk.RadioButton(external_label,
                                               label=self.CONTENT_LABEL)
        content_format_frame.set_label_widget(content_format_label)
        content_format_frame.show()
        content_format_label.show()
        content_format_hbox = gtk.HBox(spacing=self.SPACING)
        content_format_hbox.show()
        content_format_table = gtk.Table(rows=self.MAX_ROWS_CONTENT,
                                         columns=self.MAX_COLS_CONTENT,
                                         homogeneous=False)
        content_format_table.show()
        for variable in self.panel_data + self.ghost_data:
            if variable.name == rose.FILE_VAR_CONTENT:
                break
        variable.metadata.update(
                 {rose.META_PROP_TYPE: rose.config_editor.FILE_TYPE_FORMATS})
        config_key_func = (lambda:
                           self.trigger_ask_for_config_keys())
        variable.metadata.update({'values_getter': config_key_func})
        for_widget = rose.config_editor.variable.VariableWidget(
                                        variable, self.var_ops)
        for_widget.insert_into(content_format_table,
                               self.MAX_ROWS_CONTENT + 1,
                               1)
        for_widget.set_sensitive(False)
        content_format_label.connect('toggled',
                                     lambda b: self._type_toggle(
                                                b, content_format_table))
        content_format_frame.add(content_format_table)
        content_format_hbox.pack_start(content_format_frame,
                                       expand=True,
                                       fill=True,
                                       padding=self.SPACING)
        self.pack_start(content_format_hbox, expand=False, fill=False,
                        padding=self.SPACING)
        empty_file_hbox = gtk.HBox()
        empty_file_label = gtk.RadioButton(external_label,
                                           label=self.EMPTY_LABEL)
        empty_file_label.show()
        empty_file_table = gtk.Table()
        empty_file_table.show()
        empty_file_hbox.pack_start(empty_file_label, expand=False,
                                   fill=False, padding=self.SPACING)
        empty_file_hbox.pack_start(empty_file_table, expand=True,
                                   fill=True, padding=self.SPACING)
        empty_file_hbox.show()
        empty_file_label.connect('toggled',
                                 lambda b: self._type_toggle(
                                                    b, empty_file_table))
        self.pack_start(empty_file_hbox, expand=False, fill=False,
                        padding=self.SPACING)
        for variable in self.panel_data + self.ghost_data:
            if (variable.metadata.get(rose.META_PROP_COMPULSORY) ==
                rose.META_PROP_VALUE_TRUE):
                if (variable.name == rose.FILE_VAR_SOURCE or
                    variable.name == rose.FILE_VAR_CHECKSUM or
                    variable.name == rose.FILE_VAR_MODE):
                    content_format_hbox.hide()
                    empty_file_hbox.hide()
                    break
                elif variable.name == rose.FILE_VAR_CONTENT:
                    hbox.hide()
                    empty_file_hbox.hide()
                    break
        if (rose.FILE_VAR_SOURCE in [x.name for x in self.panel_data] and
            (rose.FILE_VAR_SOURCE, '') not in
            [(x.name, x.value) for x in self.panel_data]):
            for variable in self.panel_data:
                if (variable.name == rose.FILE_VAR_SOURCE and
                    (variable.metadata.get(rose.META_PROP_TYPE) == 
                     rose.config_editor.FILE_TYPE_INTERNAL)):
                    content_format_label.set_sensitive(False)
                    empty_file_label.set_sensitive(False)
            external_label.set_active(True)
        elif rose.FILE_VAR_CONTENT in [x.name for x in original_data]:
            content_format_label.set_active(True)
        else:
            empty_file_label.set_active(True)
        return

    def _checksum_toggle(self, check, var_widget):
        variable = var_widget.variable
        if check.get_active():
            if variable in self.ghost_data:
                self.var_ops.add_var(variable)
        else:
            if variable in self.panel_data:
                self.var_ops.remove_var(variable)
        var_widget.update_status()

    def _type_toggle(self, button, table):
        if button.get_active():
            for widget in table.get_children():
                widget.set_sensitive(True)
                var_keys = [x.name for x in self.panel_data]
                if hasattr(widget.get_parent(), 'variable'):
                    var = widget.get_parent().variable
                    if (var.name not in var_keys and
                        var.name != rose.FILE_VAR_CHECKSUM or 
                        var.value != ''):
                        self.var_ops.add_var(var)
                        widget.get_parent().update_status()

        else:
            for widget in table.get_children():
                widget.set_sensitive(False)
                var_keys = [x.name for x in self.panel_data]
                if hasattr(widget.get_parent(), 'variable'):
                    var = widget.get_parent().variable
                    if var.name in var_keys:
                        self.var_ops.remove_var(widget.get_parent().variable)
                        widget.get_parent().update_status()

    def _make_and_insert_table(self):
        table = gtk.Table(rows=self.MAX_ROWS_SOURCE,
                          columns=self.MAX_COLS_SOURCE,
                          homogeneous=False)
        table.set_border_width(self.SPACING)
        setattr(table, 'num_removes', 0)
        r = 0
        data = []
        external_names_left = [rose.FILE_VAR_CHECKSUM, rose.FILE_VAR_MODE,
                               rose.FILE_VAR_SOURCE]
        variable_list = [v for v in self.panel_data + self.ghost_data]
        my_cmp = lambda v1, v2: cmp(v1.name, v2.name)
        variable_list.sort(my_cmp)
        for variable in variable_list:
            if (variable.name == rose.FILE_VAR_SOURCE and
                (variable.metadata.get(rose.META_PROP_TYPE) == 
                 rose.config_editor.FILE_TYPE_INTERNAL)):
                external_names_left.remove(rose.FILE_VAR_MODE)
                external_names_left.remove(rose.FILE_VAR_CHECKSUM)
                break
        for variable in variable_list:
            if variable.name not in external_names_left:
                continue
            r += 1
            external_names_left.remove(variable.name)
            widget = rose.config_editor.variable.VariableWidget(
                                        variable, self.var_ops)
            widget.insert_into(table, self.MAX_COLS_SOURCE - 1, r + 1)
            if variable.name == rose.FILE_VAR_CHECKSUM:
                check_button = gtk.CheckButton()
                check_button.var_widget = widget
                check_button.set_active(variable in self.panel_data)
                check_button.connect(
                             'toggled',
                             lambda c: self._checksum_toggle(c,
                                                             c.var_widget))
                check_button.connect(
                             'state-changed',
                             lambda c, s: s != gtk.STATE_INSENSITIVE and
                                          self._checksum_toggle(c,
                                                                c.var_widget))
                check_button.show()
                table.attach(check_button,
                             self.MAX_COLS_SOURCE - 1, self.MAX_COLS_SOURCE,
                             r + 1, r + 2,
                             xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
                                     
        table.show()
        self.external_frame.add(table)
        return table

    def refresh(self, var_id=None):
        """Reload the container - don't need this at the moment."""
        pass


class LatentTable(gtk.Table):

    """Return a widget table generated from panel_data.

    It uses the variable information to create instances of
    VariableWidget, which are then asked to insert themselves into the
    table.

    This particular container always shows latent variables.

    """

    MAX_ROWS = 2000
    MAX_COLS = 3

    def __init__(self, panel_data, ghost_data, var_ops, show_modes):
        super(LatentTable, self).__init__(rows=self.MAX_ROWS,
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
                                                show_title=self.title_on)
            variablewidget.insert_into(self, self.MAX_COLS, r + 1)
            variablewidget.set_sensitive(not is_ghost)
            r = r + 1

    def show_title(self, title_off=False):
        done_variable_widgets = []
        self.title_on = not title_off
        for child in self.get_children():
            parent = child.get_parent()
            if parent in done_variable_widgets:
                continue
            parent.set_titled(not title_off)
            done_variable_widgets.append(parent)

    def refresh(self, var_id=None):
        """Reload the container - don't need this at the moment."""
        pass
