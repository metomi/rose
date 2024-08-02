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
"""This module contains a value widget for the 'source' file setting."""

import shlex

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import metomi.rose.config
import metomi.rose.config_editor
import metomi.rose.formats
import metomi.rose.gtk.choice


class SourceValueWidget(Gtk.HBox):

    """This class generates a special widget for the file source variable.

    It cheats by passing in a special VariableOperations instance as
    arg_str. This is used for search and getting and updating the
    available sections.

    """

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(SourceValueWidget, self).__init__(homogeneous=False, spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.var_ops = arg_str
        formats = [f for f in metomi.rose.formats.__dict__ if not f.startswith('__')]
        self.formats = formats
        self.formats_ok = None
        self._ok_content_sections = set([None])
        if self.formats_ok is None:
            content_sections = self._get_available_sections()
            self.formats_ok = bool(content_sections)
        vbox = Gtk.VBox()
        vbox.show()
        formats_check_button = Gtk.CheckButton(
            metomi.rose.config_editor.FILE_CONTENT_PANEL_FORMAT_LABEL)
        formats_check_button.set_active(not self.formats_ok)
        formats_check_button.connect("toggled", self._toggle_formats)
        formats_check_button.show()
        formats_check_hbox = Gtk.HBox()
        formats_check_hbox.show()
        formats_check_hbox.pack_end(formats_check_button, expand=False,
                                    fill=False)
        vbox.pack_start(formats_check_hbox, expand=False, fill=False)
        treeviews_hbox = Gtk.HPaned()
        treeviews_hbox.show()
        self._listview = metomi.rose.gtk.choice.ChoicesListView(
            self._set_listview,
            self._get_included_sources,
            self._handle_search,
            get_custom_menu_items=self._get_custom_menu_items
        )
        self._listview.set_tooltip_text(
            metomi.rose.config_editor.FILE_CONTENT_PANEL_TIP)
        frame = Gtk.Frame()
        frame.show()
        frame.add(self._listview)
        value_vbox = Gtk.VBox()
        value_vbox.show()
        value_vbox.pack_start(frame, expand=False, fill=False)
        value_eb = Gtk.EventBox()
        value_eb.show()
        value_vbox.pack_start(value_eb, expand=True, fill=True)

        self._available_frame = Gtk.Frame()
        self._generate_available_treeview()
        adder_value = ""
        adder_metadata = {}
        adder_set_value = lambda v: None
        adder_hook = metomi.rose.config_editor.valuewidget.ValueWidgetHook()
        self._adder = (
            metomi.rose.config_editor.valuewidget.files.FileChooserValueWidget(
                adder_value, adder_metadata, adder_set_value, adder_hook))
        self._adder.entry.connect("activate", self._add_file_source)
        self._adder.entry.set_tooltip_text(
            metomi.rose.config_editor.TIP_VALUE_ADD_URI)
        self._adder.show()
        treeviews_hbox.add1(value_vbox)
        treeviews_hbox.add2(self._available_frame)
        vbox.pack_start(treeviews_hbox, expand=True, fill=True)
        vbox.pack_start(self._adder, expand=True, fill=True)
        self.grab_focus = lambda: self.hook.get_focus(self._listview)
        self.pack_start(vbox, True, True, 0)

    def _toggle_formats(self, widget):
        """Toggle the show/hide of the available format sections."""
        self.formats_ok = not widget.get_active()
        if widget.get_active():
            self._available_frame.hide()
        else:
            self._available_frame.show()

    def _generate_available_treeview(self):
        """Generate an available choices widget."""
        existing_widget = self._available_frame.get_child()
        if existing_widget is not None:
            self._available_frame.remove(existing_widget)
        self._available_treeview = metomi.rose.gtk.choice.ChoicesTreeView(
            self._set_available_treeview,
            self._get_included_sources,
            self._get_available_sections,
            self._get_groups,
            title=metomi.rose.config_editor.FILE_CONTENT_PANEL_TITLE,
            get_is_included=self._get_section_is_included
        )
        self._available_treeview.set_tooltip_text(
            metomi.rose.config_editor.FILE_CONTENT_PANEL_OPT_TIP)
        self._available_frame.show()
        if not self.formats_ok:
            self._available_frame.hide()
        self._available_frame.add(self._available_treeview)

    def _get_custom_menu_items(self):
        """Return some custom menuitems for use in the list view."""
        menuitem = Gtk.ImageMenuItem(
            metomi.rose.config_editor.FILE_CONTENT_PANEL_MENU_OPTIONAL)
        image = Gtk.Image.new_from_stock(
            Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.MENU)
        menuitem.set_image(image)
        menuitem.connect(
            "button-press-event", self._toggle_menu_optional_status)
        menuitem.show()
        return [menuitem]

    def _get_included_sources(self):
        """Return sections included in the source variable."""
        return shlex.split(self.value)

    def _get_section_is_included(self, section, included_sections=None):
        """Return whether a section is included or not."""
        if included_sections is None:
            included_sections = self._get_included_sources()
        for i, included_section in enumerate(included_sections):
            if (included_section.startswith("(") and
                    included_section.endswith(")")):
                included_sections[i] = included_section[1:-1]
        return section in included_sections

    def _get_available_sections(self):
        """Return sections available to the source variable."""
        ok_content_sections = []
        sections = list(self.var_ops.get_sections(self.metadata["full_ns"]))
        for section in sections:
            section_has_format = False
            for format_ in self.formats:
                if section.startswith(format_ + ":"):
                    section_has_format = True
                    break
            if not section_has_format:
                continue
            if section.endswith(")"):
                section_all = section.rsplit("(", 1)[0] + "(:)"
                if section_all not in ok_content_sections:
                    ok_content_sections.append(section_all)
            ok_content_sections.append(section)
        ok_content_sections.sort(metomi.rose.config.sort_settings)
        ok_content_sections.sort(self._sort_settings_duplicate)
        return ok_content_sections

    def _get_groups(self, name, available_names):
        """Return any groups in available_names that supersede name."""
        name_all = name.rsplit("(", 1)[0] + "(:)"
        if name_all in available_names and name != name_all:
            return [name_all]
        return []

    def _handle_search(self, name):
        """Trigger a search for a section."""
        self.var_ops.search_for_var(self.metadata["full_ns"], name)

    def _set_listview(self, new_value):
        """React to a set value request from the list view."""
        self._set_value(new_value)
        self._available_treeview._realign()

    def _set_available_treeview(self, new_value):
        """React to a set value request from the tree view."""
        new_values = shlex.split(new_value)
        # Preserve optional values.
        old_values = self._get_included_sources()
        for i, value in enumerate(new_values):
            if "(" + value + ")" in old_values:
                new_values[i] = "(" + value + ")"
        new_value = " ".join(new_values)
        self._set_value(new_value)
        self._listview._populate()

    def _add_file_source(self, entry):
        """Add a file to the sources list."""
        url = entry.get_text()
        if not url:
            return False
        if self.value:
            new_value = self.value + " " + url
        else:
            new_value = url
        self._set_value(new_value)
        self._set_available_treeview(new_value)
        entry.set_text("")

    def _set_value(self, new_value):
        """Set the source variable value."""
        if new_value != self.value:
            self.set_value(new_value)
            self.value = new_value

    def _sort_settings_duplicate(self, sect1, sect2):
        """Sort settings such that xyz(:) appears above xyz(1)."""
        sect1_base = sect1.rsplit("(", 1)[0]
        sect2_base = sect2.rsplit("(", 1)[0]
        if sect1_base != sect2_base:
            return 0
        sect1_ind = sect1.replace(sect1_base, "", 1)
        sect2_ind = sect2.replace(sect2_base, "", 1)
        return (sect2_ind == "(:)") - (sect1_ind == "(:)")

    def _toggle_menu_optional_status(self, menuitem, event):
        """Toggle a source's optional status (surrounding brackets or not)."""
        iter_ = menuitem._listview_iter
        model = menuitem._listview_model
        old_section_value = model.get_value(iter_, 0)
        if (old_section_value.startswith("(") and
                old_section_value.endswith(")")):
            section_value = old_section_value[1:-1]
        else:
            section_value = "(" + old_section_value + ")"
        model.set_value(iter_, 0, section_value)
        values = self._get_included_sources()
        for i, value in enumerate(values):
            if value == old_section_value:
                values[i] = section_value
        self._set_value(" ".join(values))
