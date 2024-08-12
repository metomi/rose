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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import metomi.rose.config_editor
import metomi.rose.config_editor.valuewidget
import metomi.rose.env
import metomi.rose.gtk.util

ENV_COLOUR = metomi.rose.gtk.util.color_parse(
    metomi.rose.config_editor.COLOUR_VARIABLE_TEXT_VAL_ENV)


class RawValueWidget(Gtk.Box):

    """This class generates a basic entry widget for an unformatted value."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(RawValueWidget, self).__init__(homogeneous=False, spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.entry = Gtk.Entry()
        if metomi.rose.env.contains_env_var(self.value):
            self.entry.modify_text(Gtk.StateType.NORMAL, ENV_COLOUR)
            self.entry.set_tooltip_text(metomi.rose.config_editor.VAR_WIDGET_ENV_INFO)
        self.entry.set_text(self.value)
        self.entry.connect("button-release-event",
                           self._handle_middle_click_paste)
        self.entry.connect_after("paste-clipboard", self.setter)
        self.entry.connect_after("key-release-event",
                                 lambda e, v: self.setter(e))
        self.entry.connect_after("button-release-event",
                                 lambda e, v: self.setter(e))
        self.entry.show()
        self.pack_start(self.entry, expand=True, fill=True, padding=0)
        self.entry.connect('focus-in-event',
                           self.hook.trigger_scroll)
        self.grab_focus = lambda: self.hook.get_focus(self.entry)

    def setter(self, widget, *args):
        new_value = widget.get_text()
        if new_value == self.value:
            return False
        self.value = new_value
        self.set_value(self.value)
        if metomi.rose.env.contains_env_var(self.value):
            self.entry.modify_text(Gtk.StateType.NORMAL, ENV_COLOUR)
            self.entry.set_tooltip_text(metomi.rose.config_editor.VAR_WIDGET_ENV_INFO)
        else:
            self.entry.set_tooltip_text(None)
        return False

    def get_focus_index(self):
        """Return the cursor position within the variable value."""
        return self.entry.get_position()

    def set_focus_index(self, focus_index=None):
        if focus_index is None:
            return False
        self.entry.set_position(focus_index)

    def _handle_middle_click_paste(self, widget, event):
        if event.button == 2:
            self.setter(widget)
        return False


class TextMultilineValueWidget(Gtk.Box):

    """This class displays text with multiple lines."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(TextMultilineValueWidget, self).__init__(homogeneous=False,
                                                       spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        self.entrybuffer = Gtk.TextBuffer()
        self.entrybuffer.set_text(self.value)
        self.entry = Gtk.TextView(buffer=self.entrybuffer)
        self.entry.set_wrap_mode(Gtk.WrapMode.WORD)
        self.entry.set_left_margin(metomi.rose.config_editor.SPACING_SUB_PAGE)
        self.entry.set_right_margin(metomi.rose.config_editor.SPACING_SUB_PAGE)
        self.entry.connect('focus-in-event', self.hook.trigger_scroll)
        self.entry.show()

        viewport = Gtk.Viewport()
        viewport.add(self.entry)
        viewport.show()

        self.grab_focus = lambda: self.hook.get_focus(self.entry)
        self.entrybuffer.connect('changed', self.setter)
        self.pack_start(viewport, expand=True, fill=True)

    def get_focus_index(self):
        """Return the cursor position within the variable value."""
        mark = self.entrybuffer.get_insert()
        iter_ = self.entrybuffer.get_iter_at_mark(mark)
        return iter_.get_offset()

    def set_focus_index(self, focus_index=None):
        """Set the cursor position within the variable value."""
        if focus_index is None:
            return False
        iter_ = self.entrybuffer.get_iter_at_offset(focus_index)
        self.entrybuffer.place_cursor(iter_)

    def setter(self, widget):
        text = widget.get_text(widget.get_start_iter(),
                               widget.get_end_iter())
        if text != self.value:
            self.value = text
            self.set_value(self.value)
        return False
