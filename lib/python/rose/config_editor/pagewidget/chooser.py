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
import rose.config_editor.valuewidget
import rose.formats
import rose.gtk.choice
import rose.variable


class PageFormatTree(gtk.VBox):

    """Return a custom container for file-level options."""

    MAX_COLS_SOURCE = 3
    MAX_ROWS_SOURCE = 3
    SPACING = rose.config_editor.SPACING_SUB_PAGE
    CONTENT_LABEL = 'source'
    EMPTY_LABEL = 'empty'

    def __init__(self, panel_data, ghost_data, var_ops, show_modes,
                 format_keys_func):
        super(PageFormatTree, self).__init__(spacing=self.SPACING)
        self.panel_data = panel_data
        self.ghost_data = ghost_data
        self.var_ops = var_ops
        self.show_modes = show_modes
        self.trigger_ask_for_config_keys = format_keys_func
        self._state = None
        formats = [f for f in rose.formats.__dict__ if not f.startswith('__')]
        self.formats = formats
        self.formats_ok = None
        source_trigger_widget = gtk.RadioButton(label=self.CONTENT_LABEL)
        source_trigger_widget.connect_after(
                 'toggled', lambda b: self._toggle(b.get_active(), "source"))
        source_trigger_widget.show()
        empty_trigger_widget = gtk.RadioButton(source_trigger_widget,
                                               label=self.EMPTY_LABEL)
        empty_trigger_widget.connect_after(
                 'toggled', lambda b: self._toggle(b.get_active(), "emp"))
        empty_trigger_widget.show()
        self.trigger_hbox = gtk.HBox()
        pad_eventbox1 = gtk.EventBox()
        pad_eventbox1.show()
        self.trigger_hbox.pack_start(pad_eventbox1, expand=True, fill=True)
        self.trigger_hbox.pack_start(source_trigger_widget, expand=False,
                                     fill=False, padding=self.SPACING)
        self.trigger_hbox.pack_start(empty_trigger_widget, expand=False,
                                     fill=False, padding=self.SPACING)
        pad_eventbox2 = gtk.EventBox()
        pad_eventbox2.show()
        self.trigger_hbox.pack_end(pad_eventbox2, expand=True, fill=True)
        self.trigger_hbox.show()
        self.pack_start(self.trigger_hbox, expand=False, fill=False)
        self.source_vbox = gtk.VBox()
        self.pack_start(self.source_vbox, expand=True, fill=True)
        self._generate_source_table()
        self.show()
        if rose.FILE_VAR_SOURCE in [v.name for v in self.panel_data]:
            source_trigger_widget.set_active(True)
            self.source_vbox.show()
        else:
            self.source_vbox.hide()
            empty_trigger_widget.set_active(True)
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
        source_vars = [rose.FILE_VAR_SOURCE, rose.FILE_VAR_CHECKSUM,
                       rose.FILE_VAR_MODE]
        if self._state == "source":
            for var in list(self.ghost_data):
                if var.name in source_vars:
                    if ((var.name == rose.FILE_VAR_CHECKSUM and
                         not var.value) or (var.name == rose.FILE_VAR_MODE and
                         var.value == "auto")):
                        continue
                    self.var_ops.add_var(var)
            self.source_vbox.show()
        else:
            for var in list(self.panel_data):
                self.var_ops.remove_var(var)
            self.source_vbox.hide()
        return False

    def _toggle_formats(self, widget):
        """Toggle the show/hide of the available format sections."""
        self.formats_ok = not widget.get_active()
        if widget.get_active():
            self._source_avail_frame.hide()
        else:
            self._source_avail_frame.show()

    def _generate_source_table(self):
        """Generate the internal content tables."""
        self._ok_content_sections = set([None])
        if self.formats_ok is None:
            content_sections = self._get_included_sources()
            num_format_sections = 0
            for section in content_sections:
                for format in self.formats:
                    if section.startswith(format + ":"):
                        num_format_sections += 1
                        break
                if num_format_sections > 0:
                    break
            self.formats_ok = (num_format_sections > 0)
        
        formats_check_button = gtk.CheckButton(
                rose.config_editor.FILE_CONTENT_PANEL_FORMAT_LABEL)
        formats_check_button.set_active(not self.formats_ok)
        formats_check_button.connect("toggled", self._toggle_formats)
        formats_check_button.show()
        formats_check_hbox = gtk.HBox()
        formats_check_hbox.show()
        formats_check_hbox.pack_end(formats_check_button, expand=False,
                                    fill=False)
        self.source_vbox.pack_start(formats_check_hbox, expand=False,
                                    fill=False)
        treeviews_hbox = gtk.HPaned()
        treeviews_hbox.show()
        self._source_value_listview = rose.gtk.choice.ChoicesListView(
                                      self._set_source_value_listview,
                                      self._get_included_sources,
                                      self._handle_search,
                                      title=rose.FILE_VAR_SOURCE)
        self._source_value_listview.set_tooltip_text(
                       rose.config_editor.FILE_CONTENT_PANEL_TIP)
        frame = gtk.Frame()
        frame.show()
        frame.add(self._source_value_listview)
        value_vbox = gtk.VBox()
        value_vbox.show()
        value_vbox.pack_start(frame, expand=False, fill=False)
        value_eb = gtk.EventBox()
        value_eb.show()
        value_vbox.pack_start(value_eb, expand=True, fill=True)
        self._source_avail_frame = gtk.Frame()
        self._generate_source_avail_tree()
        adder_value = ""
        adder_metadata = {}
        adder_set_value = lambda v: None
        adder_hook = rose.config_editor.valuewidget.ValueWidgetHook()
        adder = rose.config_editor.valuewidget.files.FileChooserValueWidget(
                                   adder_value, adder_metadata,
                                   adder_set_value, adder_hook)
        adder.entry.connect("activate", self._add_file_source)
        adder.entry.set_tooltip_text(rose.config_editor.TIP_VALUE_ADD_URI)
        adder.show()
        treeviews_hbox.add1(value_vbox)
        treeviews_hbox.add2(self._source_avail_frame)
        self.source_vbox.pack_start(treeviews_hbox, expand=True, fill=True)
        self.source_vbox.pack_start(adder, expand=True, fill=True)
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
                                     rose.FILE_VAR_MODE]:
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
        self.source_vbox.pack_start(table, expand=False, fill=False)

    def _generate_source_avail_tree(self):
        """Generate an available choices widget."""
        existing_widget = self._source_avail_frame.get_child()
        if existing_widget is not None:
            self._source_avail_frame.remove(existing_widget)
        self._source_avail_treeview = rose.gtk.choice.ChoicesTreeView(
                     self._set_source_avail_treeview,
                     self._get_included_sources,
                     self._get_available_sections,
                     self._get_groups,
                     title=rose.config_editor.FILE_CONTENT_PANEL_TITLE)
        self._source_avail_treeview.set_tooltip_text(
                       rose.config_editor.FILE_CONTENT_PANEL_OPT_TIP)
        self._source_avail_frame.show()
        if not self.formats_ok:
            self._source_avail_frame.hide()
        self._source_avail_frame.add(self._source_avail_treeview)

    def _get_included_sources(self):
        """Return sections included in the source variable."""
        variables = [v for v in self.panel_data + self.ghost_data]
        names = [v.name for v in variables]
        content_value = variables[names.index(rose.FILE_VAR_SOURCE)].value
        return shlex.split(content_value)

    def _get_available_sections(self):
        """Return sections available to the source variable."""
        ok_content_sections = []
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

    def _set_source_value_listview(self, new_value):
        """React to a set value request from the list view."""
        self._set_source_value(new_value)
        self._source_avail_treeview._realign()

    def _set_source_avail_treeview(self, new_value):
        """React to a set value request from the tree view."""
        self._set_source_value(new_value)
        self._source_value_listview._populate()  

    def _add_file_source(self, entry):
        """Add a file to the sources list."""
        url = entry.get_text()
        if not url:
            return False
        variables = [v for v in self.panel_data + self.ghost_data]
        names = [v.name for v in variables]
        source_var = variables[names.index(rose.FILE_VAR_SOURCE)]
        if source_var.value:
            new_value = source_var.value + " " + url
        else:
            new_value = url
        if source_var.value != new_value:
            self.var_ops.set_var_value(source_var, new_value)
            self._set_source_avail_treeview(new_value)
            entry.set_text("")

    def _set_source_value(self, new_value):
        """Set the source variable value."""
        variables = [v for v in self.panel_data + self.ghost_data]
        names = [v.name for v in variables]
        source_var = variables[names.index(rose.FILE_VAR_SOURCE)]
        if source_var.value != new_value:
            self.var_ops.set_var_value(source_var, new_value)
         
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
