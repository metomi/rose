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


class MetaValueWidget(gtk.HBox):

    """This class generates an entry and button for a metadata flag value."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(MetaValueWidget, self).__init__(homogeneous=False, spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.entry = gtk.Entry()
        self.normal_colour = self.entry.style.text[gtk.STATE_NORMAL]
        self.insens_colour = self.entry.style.text[gtk.STATE_INSENSITIVE]
        self.entry.set_text(self.value)
        self.entry.connect_after("paste-clipboard", self._check_diff)
        self.entry.connect_after("key-release-event", self._check_diff)
        self.entry.connect_after("button-release-event", self._check_diff)
        self.entry.connect("activate", self._setter)
        self.entry.connect("focus-out-event", self._setter)
        self.entry.show()
        self.button = gtk.Button(stock=gtk.STOCK_APPLY)
        self.button.connect("clicked", self._setter)
        self.button.set_sensitive(False)
        self.button.show()
        self.pack_start(self.entry, expand=True, fill=True,
                        padding=0)
        self.pack_start(self.button, expand=False, fill=False,
                        padding=0)
        self.entry.connect('focus-in-event',
                           self.hook.trigger_scroll)
        self.grab_focus = lambda : self.hook.get_focus(self.entry)

    def _check_diff(self, *args):
        text = self.entry.get_text()
        if text == self.value:
            self.entry.modify_text(gtk.STATE_NORMAL, self.normal_colour)
            self.button.set_sensitive(False)
        else:
            self.entry.modify_text(gtk.STATE_NORMAL, self.insens_colour)
            self.button.set_sensitive(True)
        if not text:
            self.button.set_sensitive(False)

    def _setter(self, *args):
        text_value = self.entry.get_text()
        if text_value and text_value != self.value:
            self.value = self.entry.get_text()
            self.set_value(self.value)
        self._check_diff()
        return False

    def get_focus_index(self):
        """Return the cursor position within the variable value."""
        return self.entry.get_position()

    def set_focus_index(self, focus_index=None):
        if focus_index is None:
            return False
        self.entry.set_position(focus_index)

