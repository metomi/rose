#!/usr/bin/env python3
"""
This module contains value widgets for helping enter usernames.

Classes:
    UsernameValueWidget - makes a helpful widget for usernames.

"""

from functools import partial

import pygtk

pygtk.require('2.0')
# flake8: noqa: E402
import gtk


class UsernameValueWidget(gtk.HBox):

    """This class generates a widget for entering usernames."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(UsernameValueWidget, self).__init__(homogeneous=False, spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.entry = gtk.Entry()
        self.entry.set_text(self.value)
        self.entry.connect_after("paste-clipboard", self._setter)
        self.entry.connect_after("key-release-event", self._setter)
        self.entry.connect_after("button-release-event", self._setter)
        self.entry.show()
        self.pack_start(self.entry, expand=True, fill=True, padding=0)
        self.entry.connect('focus-in-event', hook.trigger_scroll)
        self.grab_focus = partial(hook.get_focus, self.entry)

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
