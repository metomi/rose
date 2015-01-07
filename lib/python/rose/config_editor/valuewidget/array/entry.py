# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
#-----------------------------------------------------------------------------

import re
import sys

import pygtk
pygtk.require('2.0')
import gtk
import pango

import rose.config_editor.util
import rose.gtk.util
import rose.variable


class EntryArrayValueWidget(gtk.HBox):

    """This is a class to represent multiple array entries."""

    TIP_ADD = "Add array element"
    TIP_DEL = "Remove array element"
    TIP_ELEMENT = "Element {0}"
    TIP_ELEMENT_CHAR = "Element {0}: '{1}'"
    TIP_LEFT = "Move array element left"
    TIP_RIGHT = "Move array element right"

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(EntryArrayValueWidget, self).__init__(homogeneous=False,
                                                    spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.max_length = self.metadata[rose.META_PROP_LENGTH]

        value_array = rose.variable.array_split(self.value)
        self.chars_width = max([len(v) for v in value_array] + [1]) + 1
        self.last_selected_src = None
        arr_type = self.metadata.get(rose.META_PROP_TYPE)
        self.is_char_array = (arr_type == "character")
        self.is_quoted_array = (arr_type == "quoted")
        # Do not treat character or quoted arrays specially when incorrect.
        if self.is_char_array:
            checker = rose.macros.value.ValueChecker()
            for val in value_array:
                if not checker.check_character(val):
                    self.is_char_array = False
        if self.is_quoted_array:
            checker = rose.macros.value.ValueChecker()
            for val in value_array:
                if not checker.check_quoted(val):
                    self.is_quoted_array = False
        if self.is_char_array:
            for i, val in enumerate(value_array):
                value_array[i] = (
                      rose.config_editor.util.text_for_character_widget(val))
        if self.is_quoted_array:
            for i, val in enumerate(value_array):
                value_array[i] = (
                      rose.config_editor.util.text_for_quoted_widget(val))
        # Designate the number of allowed columns - 10 for 4 chars width
        self.num_allowed_columns = 3
        self.entry_table = gtk.Table(rows=1,
                                     columns=self.num_allowed_columns,
                                     homogeneous=True)
        self.entry_table.connect('focus-in-event', self.hook.trigger_scroll)
        self.entry_table.show()

        self.entries = []
        self.generate_entries(value_array)
        self.generate_buttons()
        self.populate_table()
        self.pack_start(self.add_del_button_box, expand=False, fill=False)
        self.pack_start(self.entry_table, expand=True, fill=True)
        self.entry_table.connect_after('size-allocate',
                                       lambda w, e: self.reshape_table())
        self.connect('focus-in-event',
                     lambda w, e: self.hook.get_focus(self.get_focus_entry()))

    def get_focus_entry(self):
        """Get either the last selected entry or the last one."""
        if self.last_selected_src is not None:
            return self.last_selected_src
        if len(self.entries) > 0:
            return self.entries[-1]
        return None

    def get_focus_index(self):
        """Get the focus and position within the table of entries."""
        text = ''
        for entry in self.entries:
            val = entry.get_text()
            if self.is_char_array:
                val = rose.config_editor.util.text_from_character_widget(val)
            elif self.is_quoted_array:
                val = rose.config_editor.util.text_from_quoted_widget(val)
            prefix = get_next_delimiter(self.value[len(text):], val)
            if entry == self.entry_table.focus_child:
                return len(text + prefix) + entry.get_position()
            text += prefix + val
        return None

    def set_focus_index(self, focus_index=None):
        """Set the focus and position within the table of entries."""
        if focus_index is None:
            return
        value_array = rose.variable.array_split(self.value)
        text = ''
        for i, val in enumerate(value_array):
            j = len(text)
            v = self.value[j:].index(val)
            prefix = get_next_delimiter(self.value[len(text):],
                                        val)
            if (len(text + prefix + val) >= focus_index or
                i == len(value_array) - 1):
                if len(self.entries) > i:
                    self.entries[i].grab_focus()
                    val_offset = focus_index - len(text + prefix)
                    if self.is_char_array or self.is_quoted_array:
                        val_offset = max([0, val_offset - 1])
                    self.entries[i].set_position(val_offset)
                    return
            text += prefix + val

    def generate_entries(self, value_array=None):
        """Create the gtk.Entry objects for elements in the array."""
        if value_array is None:
            value_array = rose.variable.array_split(self.value)
        entries = []
        existing_entries_text = [e.get_text() for e in self.entries]
        for value_item in value_array:
            for entry in self.entries:
                if entry.get_text() == value_item and entry not in entries:
                    entries.append(entry)
                    break
            else:
                entries.append(self.get_entry(value_item))
        self.entries = entries

    def generate_buttons(self):
        """Create the left-right movement arrows and add button."""
        left_arrow = gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_IN)
        left_arrow.show()
        left_event_box = gtk.EventBox()
        left_event_box.add(left_arrow)
        left_event_box.show()
        left_event_box.connect('button-press-event',
                               lambda b, e: self.move_element(-1))
        left_event_box.connect('enter-notify-event', self._handle_arrow_enter)
        left_event_box.connect('leave-notify-event', self._handle_arrow_leave)
        left_event_box.set_tooltip_text(self.TIP_LEFT)
        right_arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_IN)
        right_arrow.show()
        right_event_box = gtk.EventBox()
        right_event_box.show()
        right_event_box.add(right_arrow)
        right_event_box.connect(
                        'button-press-event',
                        lambda b, e: self.move_element(1))
        right_event_box.connect('enter-notify-event', self._handle_arrow_enter)
        right_event_box.connect('leave-notify-event', self._handle_arrow_leave)
        right_event_box.set_tooltip_text(self.TIP_RIGHT)
        self.arrow_box = gtk.HBox()
        self.arrow_box.show()
        self.arrow_box.pack_start(left_event_box, expand=False, fill=False)
        self.arrow_box.pack_end(right_event_box, expand=False, fill=False)
        self.set_arrow_sensitive(False, False)
        del_image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,
                                             gtk.ICON_SIZE_MENU)
        del_image.show()
        self.del_button = gtk.EventBox()
        self.del_button.set_tooltip_text(self.TIP_DEL)
        self.del_button.add(del_image)
        self.del_button.show()
        self.del_button.connect('button-release-event',
                                lambda b, e: self.remove_entry())
        self.del_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_ACTIVE))
        self.del_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_NORMAL))
        self.button_box = gtk.HBox()
        self.button_box.show()
        self.button_box.pack_start(self.arrow_box, expand=False, fill=True)
        #self.button_box.pack_start(self.del_button, expand=False, fill=False)
        add_image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
        add_image.show()
        self.add_button = gtk.EventBox()
        self.add_button.set_tooltip_text(self.TIP_ADD)
        self.add_button.add(add_image)
        self.add_button.show()
        self.add_button.connect('button-release-event',
                                lambda b, e: self.add_entry())
        self.add_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_ACTIVE))
        self.add_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_NORMAL))
        self.add_del_button_box = gtk.VBox()
        self.add_del_button_box.pack_start(self.add_button, expand=False, fill=False)
        self.add_del_button_box.pack_start(self.del_button, expand=False, fill=False)
        self.add_del_button_box.show()

    def _handle_arrow_enter(self, arrow_event_box, event):
        if arrow_event_box.get_child().state != gtk.STATE_INSENSITIVE:
            arrow_event_box.set_state(gtk.STATE_ACTIVE)

    def _handle_arrow_leave(self, arrow_event_box, event):
        if arrow_event_box.get_child().state != gtk.STATE_INSENSITIVE:
            arrow_event_box.set_state(gtk.STATE_NORMAL)

    def set_arrow_sensitive(self, is_left_sensitive, is_right_sensitive):
        """Control the sensitivity of the movement buttons."""
        sens_tuple = (is_left_sensitive, is_right_sensitive)
        for i, event_box in enumerate(self.arrow_box.get_children()):
            event_box.get_child().set_sensitive(sens_tuple[i])
            if not sens_tuple[i]:
                event_box.set_state(gtk.STATE_NORMAL)

    def move_element(self, num_places_right):
        """Move the entry left or right."""
        entry = self.last_selected_src
        if entry is None:
            return
        old_index = self.entries.index(entry)
        if (old_index + num_places_right < 0 or
            old_index + num_places_right > len(self.entries) - 1):
            return
        self.entries.remove(entry)
        self.entries.insert(old_index + num_places_right, entry)
        self.populate_table()
        self.setter(entry)

    def get_entry(self, value_item):
        """Create a gtk Entry for this array element."""
        entry = gtk.Entry()
        entry.set_text(value_item)
        entry.connect('focus-in-event',
                      self._handle_focus_on_entry)
        entry.connect("button-release-event",
                      self._handle_middle_click_paste)
        entry.connect_after("paste-clipboard", self.setter)
        entry.connect_after("key-release-event",
                            lambda e, v: self.setter(e))
        entry.connect_after("button-release-event",
                            lambda e, v: self.setter(e))
        entry.connect('focus-out-event',
                      self._handle_focus_off_entry)
        entry.set_width_chars(self.chars_width - 1)
        entry.show()
        return entry

    def populate_table(self, focus_widget=None):
        """Populate a table with the array elements, dynamically."""
        position = None
        table_widgets = self.entries + [self.button_box]
        table_children = self.entry_table.get_children()
        if focus_widget is None:
            for child in table_children:
                if child.is_focus() and isinstance(child, gtk.Entry):
                    focus_widget = child
                    position = focus_widget.get_position()
        else:
            position = focus_widget.get_position()
        for child in self.entry_table.get_children():
            self.entry_table.remove(child)
        if (focus_widget is None and self.entry_table.is_focus()
            and len(self.entries) > 0):
            focus_widget = self.entries[-1]
            position = len(focus_widget.get_text())
        num_fields = len(self.entries + [self.button_box])
        num_rows_now = 1 + (num_fields - 1) / self.num_allowed_columns
        self.entry_table.resize(num_rows_now, self.num_allowed_columns)
        if (self.max_length.isdigit() and
            len(self.entries) >= int(self.max_length)):
            self.add_button.hide()
        else:
            self.add_button.show()
        if (self.max_length.isdigit() and
            len(self.entries) <= int(self.max_length)):
            self.del_button.hide()
        elif len(self.entries) == 0:
            self.del_button.hide()
        else:
            self.del_button.show()
        if (self.last_selected_src is not None and
            self.last_selected_src in self.entries):
            index = self.entries.index(self.last_selected_src)
            if index == 0:
                self.set_arrow_sensitive(False, True)
            elif index == len(self.entries) - 1:
                self.set_arrow_sensitive(True, False)
        if len(self.entries) < 2:
            self.set_arrow_sensitive(False, False)
        for i, widget in enumerate(table_widgets):
            if isinstance(widget, gtk.Entry):
                if self.is_char_array or self.is_quoted_array:
                    w_value = widget.get_text()
                    widget.set_tooltip_text(self.TIP_ELEMENT_CHAR.format(
                                            (i + 1), w_value))
                else:
                    widget.set_tooltip_text(self.TIP_ELEMENT.format((i + 1)))
            row = i // self.num_allowed_columns
            column = i % self.num_allowed_columns
            self.entry_table.attach(widget,
                                    column, column + 1,
                                    row, row + 1,
                                    xoptions=gtk.FILL,
                                    yoptions=gtk.SHRINK)
        if focus_widget is not None:
            focus_widget.grab_focus()
            focus_widget.set_position(position)
            focus_widget.select_region(position, position)
        self.grab_focus = lambda : self.hook.get_focus(
                                                 self._get_widget_for_focus())
        self.check_resize()

    def reshape_table(self):
        """Reshape a table according to the space allocated."""
        total_x_bound = self.entry_table.get_allocation().width
        if not len(self.entries):
            return False
        entries_bound = sum([e.get_allocation().width for e in self.entries])
        each_entry_bound = entries_bound / len(self.entries)
        maximum_entry_number = float(total_x_bound) / float(each_entry_bound)
        rounded_max = int(maximum_entry_number) + 1
        if (rounded_max != self.num_allowed_columns + 2 and
            rounded_max > 2):
            self.num_allowed_columns = max(1, rounded_max - 2)
            self.populate_table()

    def add_entry(self):
        """Add a new entry (with null text) to the variable array."""
        entry = self.get_entry('')
        self.entries.append(entry)
        self._adjust_entry_length()
        self.populate_table(focus_widget=entry)
        if (self.metadata.get(rose.META_PROP_COMPULSORY) !=
            rose.META_PROP_VALUE_TRUE):
            self.setter(entry)

    def remove_entry(self):
        """Remove the last selected or the last entry."""
        if (self.last_selected_src is not None and
            self.last_selected_src in self.entries):
            text = self.last_selected_src.get_text()
            entry = self.entries.remove(self.last_selected_src)
            self.last_selected_src = None
        else:
            text = self.entries[-1].get_text()
            entry = self.entries.pop()
        self.populate_table()
        if (self.metadata.get(rose.META_PROP_COMPULSORY) !=
            rose.META_PROP_VALUE_TRUE or text):
            # Optional, or compulsory but not blank.
            self.setter(entry)

    def setter(self, widget):
        """Reconstruct the new variable value from the entry array."""
        val_array = [e.get_text() for e in self.entries]
        max_length = max([len(v) for v in val_array] + [1])
        if max_length + 1 != self.chars_width:
            self.chars_width = max_length + 1
            self._adjust_entry_length()
            if widget is not None and not widget.is_focus():
                widget.grab_focus()
                widget.set_position(len(widget.get_text()))
                widget.select_region(widget.get_position(),
                                     widget.get_position())
        if self.is_char_array:
            for i, val in enumerate(val_array):
                val_array[i] = (
                      rose.config_editor.util.text_from_character_widget(val))
        elif self.is_quoted_array:
            for i, val in enumerate(val_array):
                val_array[i] = (
                      rose.config_editor.util.text_from_quoted_widget(val))
        entries_have_commas = any(["," in v for v in val_array])
        new_value = rose.variable.array_join(val_array)
        if new_value != self.value:
            self.value = new_value
            self.set_value(new_value)
            if (entries_have_commas and
                not (self.is_char_array or self.is_quoted_array)):
                new_val_array = rose.variable.array_split(new_value)
                if len(new_val_array) != len(self.entries):
                    self.generate_entries()
                    focus_index = None
                    for i, val in enumerate(val_array):
                        if "," in val:
                            val_post_comma = val[:val.index(",") + 1]
                            focus_index = len(rose.variable.array_join(
                                  new_val_array[:i] + [val_post_comma]))
                    self.populate_table()
                    self.set_focus_index(focus_index)
        return False

    def _adjust_entry_length(self):
        for entry in self.entries:
            entry.set_width_chars(self.chars_width)
            entry.set_max_length(self.chars_width)
        self.reshape_table()

    def _get_widget_for_focus(self):
        if self.entries:
            return self.entries[-1]
        return self.entry_table

    def _handle_focus_off_entry(self, widget, event):
        if widget == self.last_selected_src:
            try:
                widget.set_progress_fraction(1.0)
            except AttributeError:
                widget.drag_highlight()
            if widget.get_position() is None:
                widget.set_position(len(widget.get_text()))

    def _handle_focus_on_entry(self, widget, event):
        if self.last_selected_src is not None:
            try:
                self.last_selected_src.set_progress_fraction(0.0)
            except AttributeError:
                self.last_selected_src.drag_unhighlight()
        self.last_selected_src = widget
        is_start = (widget in self.entries and self.entries[0] == widget)
        is_end = (widget in self.entries and self.entries[-1] == widget)
        self.set_arrow_sensitive(not is_start, not is_end)
        if widget.get_text() != '':
            widget.select_region(widget.get_position(),
                                 widget.get_position())
        return False

    def _handle_middle_click_paste(self, widget, event):
        if event.button == 2:
            self.setter(widget)
        return False


def get_next_delimiter(array_text, next_element):
    """Return the part of array_text immediately preceding next_element."""
    v = array_text.index(next_element)
    if v == 0 and len(array_text) > 1:  # Null or whitespace element.
        while array_text[v].isspace():
            v += 1
        if array_text[v] == ",":
            v += 1
    return array_text[:v]
