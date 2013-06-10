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

import re

import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor


class QuotedTextValueWidget(gtk.HBox):

    """This class represents 'character' and 'quoted' types in an entry."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(QuotedTextValueWidget, self).__init__(homogeneous=False,
                                                   spacing=0)
        # Importing here prevents cyclic imports
        import rose.macros.value
        self.type = metadata.get(rose.META_PROP_TYPE)
        checker = rose.macros.value.ValueChecker()
        if self.type == "character":
            self.type_checker = checker.check_character
            self.format_text_in = text_for_character_widget
            self.format_text_out = text_from_character_widget
            self.quote_char = "'"
            self.esc_quote_chars = "''"
        elif self.type == "quoted":
            self.type_checker = checker.check_quoted
            self.format_text_in = text_for_quoted_widget
            self.format_text_out = text_from_quoted_widget
            self.quote_char = '"'
            self.esc_quote_chars = '\\"'
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.entry = gtk.Entry()
        insensitive_colour = gtk.Style().bg[0]
        self.entry.modify_bg(gtk.STATE_INSENSITIVE,
                             insensitive_colour)
        self.in_error = not self.type_checker(self.value)
        self.set_entry_text()
        self.entry.connect_after("changed", self.setter)
        self.entry.show()
        self.pack_start(self.entry, expand=True, fill=True,
                        padding=0)
        self.entry.connect('focus-in-event', self.hook.trigger_scroll)
        self.grab_focus = lambda : self.hook.get_focus(self.entry)

    def set_entry_text(self):
        """Initialise the text in the widget."""
        raw_text = self.value
        if not self.in_error:
            self.entry.set_text(self.format_text_in(raw_text))
        else:
            self.entry.set_text(raw_text)

    def setter(self, *args):
        var_text = self.entry.get_text()
        if not self.value or not self.in_error:
            # Text was in processed form
            var_text = self.format_text_out(var_text)
        if var_text != self.value:
            self.value = var_text
            self.set_value(var_text)
        return False

    def get_focus_index(self):
        """Retrieve the current cursor index."""
        position = self.entry.get_position()
        if self.in_error:
            return position
        text = self.entry.get_text()
        prefix = text[:position]
        i = 0
        while prefix:
            if self.value[i] == prefix[0]:
                prefix = prefix[1:]
            i = i + 1
            if not prefix:
                break
        return i
        
    def set_focus_index(self, focus_index):
        """Set the current cursor index."""
        self.entry.set_position(focus_index - 1)

    def handle_type_error(self, has_error):
        """Handle a change in error related to the value.

        We need to distinguish between quote-related errors and errors
        related to pattern matching or other attributes.

        """
        position = self.entry.get_position()
        text = self.entry.get_text()
        was_in_error = self.in_error
        self.in_error = not self.type_checker(self.value)
        if self.in_error and not was_in_error:
            # This is an incoming quote error.
            position += 1 + text[:position].count(self.quote_char)
        elif was_in_error and not self.in_error:
            # This is an outgoing quote error.
            position -= 1 + text[:position].count(self.esc_quote_chars)
        else:
            # The error isn't related to quotes, so don't do anything.
            return False
        self.set_entry_text()
        self.entry.set_position(position)


def text_for_character_widget(text):
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    text = text.replace("''", "'")
    return text

def text_from_character_widget(text):
    return "'" + text.replace("'", "''") + "'"

def text_for_quoted_widget(text):
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    text = text.replace('\\"', '"')
    return text

def text_from_quoted_widget(text):
    return '"' + text.replace('"', '\\"') + '"'
