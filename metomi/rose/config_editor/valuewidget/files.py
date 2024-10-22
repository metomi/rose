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

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import metomi.rose.config_editor
import metomi.rose.external
import metomi.rose.gtk.util


class FileChooserValueWidget(Gtk.Box):
    """This class displays a path, with an open dialog to define a new one."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(FileChooserValueWidget, self).__init__(
            homogeneous=False, spacing=0
        )
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.generate_entry()
        self.generate_editor_launcher()
        self.open_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_OPEN,
            size=Gtk.IconSize.MENU,
            as_tool=False,
            tip_text="Browse for a filename",
        )
        self.open_button.show()
        self.open_button.connect("clicked", self.run_and_destroy)
        self.pack_end(self.open_button, expand=False, fill=False, padding=0)
        self.edit_button.set_sensitive(os.path.isfile(self.value))

    def generate_entry(self):
        self.entry = Gtk.Entry()
        self.entry.set_text(self.value)
        self.entry.show()
        self.entry.connect("changed", self.setter)
        self.entry.connect("focus-in-event", self.hook.trigger_scroll)
        self.pack_start(self.entry, True, True, 0)
        self.grab_focus = lambda: self.hook.get_focus(self.entry)

    def run_and_destroy(self, *args):
        file_chooser_widget = Gtk.FileChooserDialog(
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.REJECT,
                Gtk.STOCK_OK,
                Gtk.ResponseType.ACCEPT,
            )
        )
        if os.path.exists(os.path.dirname(self.value)):
            file_chooser_widget.set_filename(self.value)
        response = file_chooser_widget.run()
        if response in [
            Gtk.ResponseType.ACCEPT,
            Gtk.ResponseType.OK,
            Gtk.ResponseType.YES,
        ]:
            self.entry.set_text(file_chooser_widget.get_filename())
        file_chooser_widget.destroy()
        return False

    def generate_editor_launcher(self):
        self.edit_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_DND,
            size=Gtk.IconSize.MENU,
            as_tool=False,
            tip_text="Edit the file",
        )
        self.edit_button.connect(
            "clicked",
            lambda b: metomi.rose.external.launch_geditor(self.value),
        )
        self.pack_end(self.edit_button, expand=False, fill=False, padding=0)

    def setter(self, widget):
        self.value = widget.get_text()
        self.set_value(self.value)
        self.edit_button.set_sensitive(os.path.isfile(self.value))
        return False


class FileEditorValueWidget(Gtk.Box):
    """This class creates a button that launches an editor for a file path."""

    FILE_PROTOCOL = "file://{0}"

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(FileEditorValueWidget, self).__init__(
            homogeneous=False, spacing=0
        )
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.generate_editor_launcher()

    def generate_editor_launcher(self):
        self.edit_button = metomi.rose.gtk.util.CustomButton(
            label=metomi.rose.config_editor.LABEL_EDIT,
            stock_id=Gtk.STOCK_DND,
            size=Gtk.IconSize.MENU,
            as_tool=False,
            tip_text="Edit the file",
        )
        self.edit_button.connect("clicked", self.on_click)
        self.pack_start(
            self.edit_button,
            expand=False,
            fill=False,
            padding=metomi.rose.config_editor.SPACING_SUB_PAGE,
        )

    def retrieve_path(self):
        root = self.metadata[metomi.rose.config_editor.META_PROP_INTERNAL]
        return os.path.join(root, self.value)

    def on_click(self, button):
        path = self.retrieve_path()
        metomi.rose.external.launch_geditor(path)
