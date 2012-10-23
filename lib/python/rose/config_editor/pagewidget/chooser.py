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
import rose.gtk.choice
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
        self._internal_value_listview = rose.gtk.choice.ChoicesListView(
                                      self._set_content_value_listview,
                                      self._get_included_sections,
                                      self._handle_search)
        self._internal_value_listview.set_tooltip_text(
                       rose.config_editor.FILE_CONTENT_PANEL_TIP)
        frame = gtk.Frame()
        frame.show()
        frame.add(self._internal_value_listview)
        value_vbox = gtk.VBox()
        value_vbox.show()
        value_vbox.pack_start(frame, expand=False, fill=False)
        value_eb = gtk.EventBox()
        value_eb.show()
        value_vbox.pack_start(value_eb, expand=True, fill=True)
        self._internal_avail_treeview = rose.gtk.choice.ChoicesTreeView(
                           self._set_content_avail_treeview,
                           self._get_included_sections,
                           self._get_available_sections,
                           self._get_groups)
        self._internal_avail_treeview.set_tooltip_text(
                       rose.config_editor.FILE_CONTENT_PANEL_OPT_TIP)
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

    def _get_groups(self, name, avail_names):
        """Return any groups in avail_names that supercede name."""
        name_all = name.rsplit("(", 1)[0]  + "(:)"
        if name_all in avail_names and name != name_all:
            return [name_all]
        return []

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
