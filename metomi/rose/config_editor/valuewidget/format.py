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

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import metomi.rose.config

from functools import cmp_to_key


class FormatsChooserValueWidget(Gtk.Box):
    """This class allows the addition of section names to a variable value."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(FormatsChooserValueWidget, self).__init__(
            homogeneous=False, spacing=0
        )
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        if "values_getter" in self.metadata:
            meta = self.metadata
            self.values_getter = meta["values_getter"]
        else:
            self.values_getter = lambda: meta.get("values", [])
        num_entries = len(value.split(" "))
        self.entry_table = Gtk.Table(rows=num_entries + 1, columns=1)
        self.entry_table.show()
        self.entries = []
        for format_name in value.split():
            entry = self.get_entry(format_name)
            self.entries.append(entry)
        self.add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_box.show()
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.MENU)
        image.show()
        image_event = Gtk.EventBox()
        image_event.add(image)
        image_event.show()
        self.add_box.pack_start(
            image_event, expand=False, fill=False, padding=5
        )
        self.data_chooser = Gtk.ComboBoxText()
        self.data_chooser.connect(
            "focus-in-event", lambda d, e: self.load_data_chooser()
        )
        self.data_chooser.connect("changed", lambda d: self.add_new_section())
        self.data_chooser.show()
        image_event.connect(
            "button-press-event",
            lambda i, w: (
                self.load_data_chooser() and self.data_chooser.popup()
            ),
        )
        self.add_box.pack_start(
            self.data_chooser, expand=False, fill=False, padding=0
        )

        self.load_data_chooser()
        self.populate_table()
        self.pack_start(self.entry_table, expand=True, fill=True, padding=20)

    def get_entry(self, format_name):
        """Create an entry box for a format name."""
        entry = Gtk.Entry()
        entry.set_text(format_name)
        entry.connect("focus-in-event", self.hook.trigger_scroll)
        entry.connect("changed", self.entry_change_handler)
        entry.show()
        return entry

    def populate_table(self):
        """Create a table for the format list and the add widget."""
        self.load_data_chooser()
        for child in self.entry_table.get_children():
            self.entry_table.remove(child)
        self.entry_table.resize(rows=len(self.entries) + 1, columns=1)
        for i, widget in enumerate(self.entries + [self.add_box]):
            self.entry_table.attach(
                widget, 0, 1, i, i + 1, xoptions=Gtk.AttachOptions.FILL
            )
        self.grab_focus = lambda: self.hook.get_focus(self.entries[-1])

    def add_new_section(self):
        value = self.get_active_text(self.data_chooser)
        self.data_chooser.set_active(-1)
        if value is None:
            return False
        self.entries.append(self.get_entry(value))
        self.entry_change_handler(self.entries[-1])
        self.populate_table()
        return True

    def get_active_text(self, combobox):
        index = combobox.get_active()
        if index < 0:
            return None
        return combobox.get_model()[index][0]

    def entry_change_handler(self, entry):
        position = entry.get_position()
        if entry.get_text() == "" and len(self.entries) > 1:
            self.entries.remove(entry)
        new_value = " ".join([e.get_text() for e in self.entries])
        self.value = new_value
        self.set_value(new_value)
        self.populate_table()
        self.update_status()
        self.load_data_chooser()
        self.data_chooser.set_active(-1)
        if entry in self.entries and not entry.is_focus():
            entry.grab_focus()
            entry.set_position(position)
        return False

    def load_data_chooser(self):
        data_model = Gtk.ListStore(str)
        options = self.values_getter()
        options.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
        for value in options:
            if value not in [e.get_text() for e in self.entries]:
                data_model.append([str(value)])
        self.data_chooser.set_model(data_model)
        return True
