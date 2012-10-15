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

import rose.config_editor
import rose.config_editor.valuewidget
import rose.env

ENV_COLOUR = gtk.gdk.color_parse(
                     rose.config_editor.COLOUR_VARIABLE_TEXT_VAL_ENV)


class RawValueWidget(gtk.HBox):

    """This class generates a basic entry widget for an unformatted value."""

    def __init__(self, value, metadata, set_value, hook, widget_args=None):
        super(RawValueWidget, self).__init__(homogeneous=False, spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        self.entry = gtk.Entry()
        insensitive_colour = gtk.Style().bg[0]
        self.entry.modify_bg(gtk.STATE_INSENSITIVE,
                             insensitive_colour)
        self.normal_colour = gtk.Style().fg[gtk.STATE_NORMAL]
        if rose.env.contains_env_var(self.value):
            self.entry.modify_text(gtk.STATE_NORMAL,
                                   ENV_COLOUR)
            self.entry.set_tooltip_text(
                       rose.config_editor.VAR_WIDGET_ENV_INFO)
        self.entry.set_text(self.value)
        self.entry.connect_after("paste-clipboard", self.setter)
        self.entry.connect_after("key-release-event", self.setter)
        self.entry.connect_after("button-release-event", self.setter)
        self.entry.show()
        self.pack_start(self.entry, expand=True, fill=True,
                                    padding=0)
        self.entry.connect('focus-in-event',
                           self.hook.trigger_scroll)
        self.grab_focus = lambda : self.hook.get_focus(self.entry)

    def setter(self, widget, *args):
        new_value = widget.get_text()
        if new_value == self.value:
            return False
        self.value = new_value
        self.set_value(self.value)
        if rose.env.contains_env_var(self.value):
            self.entry.modify_text(gtk.STATE_NORMAL,
                                   ENV_COLOUR)
            self.entry.set_tooltip_text(
                       rose.config_editor.VAR_WIDGET_ENV_INFO)
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


class TextMultilineValueWidget(gtk.HBox):

    """This class displays text with multiple lines."""

    def __init__(self, value, metadata, set_value, hook, widget_args=None):
        super(TextMultilineValueWidget, self).__init__(homogeneous=False,
                                                       spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        self.event_box = gtk.EventBox()
        self.pack_start(self.event_box, expand=True)
        self.event_box.show()
        self.entry_scroller = gtk.ScrolledWindow()
        self.entry_scroller.set_shadow_type(gtk.SHADOW_IN)
        self.entry_scroller.set_policy(gtk.POLICY_AUTOMATIC,
                                  gtk.POLICY_NEVER)
        self.entry_scroller.show()
        self.entrybuffer = gtk.TextBuffer()
        self.entrybuffer.set_text(self.value)
        self.entry = gtk.TextView(self.entrybuffer)
        self.entry.set_wrap_mode(gtk.WRAP_WORD)
        self.entry.set_left_margin(rose.config_editor.SPACING_SUB_PAGE)
        self.entry.set_right_margin(rose.config_editor.SPACING_SUB_PAGE)
        self.entry.connect('focus-in-event', self.hook.trigger_scroll)
        self.entry.show()
        self.entry_scroller.add(self.entry)
        self.grab_focus = lambda : self.hook.get_focus(self.entry)
        self.entrybuffer.connect('changed', self.setter)
        self.event_box.add(self.entry_scroller)

    def setter(self, widget):
        text = widget.get_text(widget.get_start_iter(),
                               widget.get_end_iter())
        self.value = text
        self.set_value(self.value)
        return False
