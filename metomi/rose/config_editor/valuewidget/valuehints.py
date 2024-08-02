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

from gi.repository import GObject
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import rose.config_editor.util
import rose.gtk.util
import rose.variable


class HintsValueWidget(Gtk.HBox):
    """This class generates a widget for entering value-hints."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(HintsValueWidget, self).__init__(homogeneous=False, spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.entry = Gtk.Entry()
        self.entry.set_text(self.value)
        self.entry.connect_after("paste-clipboard", self._setter)
        self.entry.connect_after("key-release-event", self._setter)
        self.entry.connect_after("button-release-event", self._setter)
        self.entry.show()
        GObject.idle_add(self._set_completion, self.metadata)
        self.pack_start(self.entry, expand=True, fill=True,
                        padding=0)
        self.entry.connect('focus-in-event',
                           hook.trigger_scroll)
        self.grab_focus = lambda: hook.get_focus(self.entry)

    def _setter(self, *args):
        """Alter the variable value and update status."""
        self.value = self.entry.get_text()
        self.set_value(self.value)
        return False

    def get_focus_index(self):
        """Return the cursor position within the variable value."""
        return self.entry.get_position()

    def set_focus_index(self, focus_index=None):
        """Set the cursor position within the variable value."""
        if focus_index is None:
            return False
        self.entry.set_position(focus_index)

    def _set_completion(self, metadata):
        """ Return a predictive text model for value-hints."""
        completion = Gtk.EntryCompletion()
        model = Gtk.ListStore(str)
        var_hints = metadata.get(rose.META_PROP_VALUE_HINTS)
        for hint in var_hints:
            model.append([hint])
        completion.set_model(model)
        completion.set_text_column(0)
        completion.set_inline_completion(True)
        completion.set_minimum_key_length(0)
        self.entry.set_completion(completion)
