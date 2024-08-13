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

import ast

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import entry
import metomi.rose.config_editor.util
import metomi.rose.gtk.util
import metomi.rose.variable


class PythonListValueWidget(Gtk.Box):

    """This is a class to represent a Python-compatible list format."""

    TIP_ADD = "Add array element"
    TIP_DEL = "Remove array element"
    TIP_ELEMENT = "Element {0}"
    TIP_ELEMENT_CHAR = "Element {0}: '{1}'"
    TIP_LEFT = "Move array element left"
    TIP_RIGHT = "Move array element right"

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(PythonListValueWidget, self).__init__(homogeneous=False,
                                                    spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.max_length = ":"
        value_array = python_array_split(self.value)
        self.chars_width = max([len(v) for v in value_array] + [1]) + 1
        self.last_selected_src = None
        # Designate the number of allowed columns - 10 for 4 chars width
        self.num_allowed_columns = 3
        self.entry_table = Gtk.Table(rows=1,
                                     columns=self.num_allowed_columns,
                                     homogeneous=True)
        self.entry_table.connect('focus-in-event', self.hook.trigger_scroll)
        self.entry_table.show()

        self.entries = []
        self.generate_entries(value_array)

        self.has_titles = False
        if "element-titles" in metadata:
            self.has_titles = True

        self.generate_buttons()
        self.populate_table()
        self.pack_start(self.add_del_button_box, expand=False, fill=False, padding=0)
        self.pack_start(self.entry_table, expand=True, fill=True, padding=0)
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
        if not self.value.startswith("["):
            return
        text = '['
        for my_entry in self.entries:
            val = my_entry.get_text()
            prefix = entry.get_next_delimiter(self.value[len(text):], val)
            if prefix is None:
                return
            if my_entry == self.entry_table.focus_child:
                return len(text + prefix) + my_entry.get_position()
            text += prefix + val
        return None

    def set_focus_index(self, focus_index=None):
        """Set the focus and position within the table of entries."""
        if focus_index is None:
            return
        value_array = python_array_split(self.value)
        if not self.value.startswith("["):
            return
        text = '['
        for i, val in enumerate(value_array):
            prefix = entry.get_next_delimiter(self.value[len(text):],
                                              val)
            if prefix is None:
                return
            if (len(text + prefix + val) >= focus_index or
                    i == len(value_array) - 1):
                if len(self.entries) > i:
                    self.entries[i].grab_focus()
                    val_offset = focus_index - len(text + prefix)
                    self.entries[i].set_position(val_offset)
                    return
            text += prefix + val

    def generate_entries(self, value_array=None):
        """Create the Gtk.Entry objects for elements in the array."""
        if value_array is None:
            value_array = python_array_split(self.value)
        entries = []
        for value_item in value_array:
            for widget in self.entries:
                if widget.get_text() == value_item and widget not in entries:
                    entries.append(widget)
                    break
            else:
                entries.append(self.get_entry(value_item))
        self.entries = entries

    def generate_buttons(self):
        """Create the left-right movement arrows and add button."""
        left_arrow = Gtk.ToolButton()
        left_arrow.set_icon_name("pan-start-symbolic")
        left_arrow.show()
        left_arrow.connect('clicked', lambda x: self.move_element(-1))
        left_event_box = Gtk.EventBox()
        left_event_box.add(left_arrow)
        left_event_box.show()
        left_event_box.set_tooltip_text(self.TIP_LEFT)
        right_arrow = Gtk.ToolButton()
        right_arrow.set_icon_name("pan-end-symbolic")
        right_arrow.show()
        right_arrow.connect('clicked', lambda x: self.move_element(1))
        right_event_box = Gtk.EventBox()
        right_event_box.add(right_arrow)
        right_event_box.show()
        right_event_box.set_tooltip_text(self.TIP_RIGHT)
        self.arrow_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.arrow_box.show()
        self.arrow_box.pack_start(left_event_box, expand=False, fill=False, padding=0)
        self.arrow_box.pack_end(right_event_box, expand=False, fill=False, padding=0)
        self.set_arrow_sensitive(False, False)
        del_image = Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE,
                                             Gtk.IconSize.MENU)
        del_image.show()
        self.del_button = Gtk.EventBox()
        self.del_button.set_tooltip_text(self.TIP_DEL)
        self.del_button.add(del_image)
        self.del_button.show()
        self.del_button.connect('button-release-event',
                                lambda b, e: self.remove_entry())
        self.del_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.ACTIVE))
        self.del_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.NORMAL))
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.button_box.show()
        self.button_box.pack_start(self.arrow_box, expand=False, fill=True, padding=0)
        add_image = Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.MENU)
        add_image.show()
        self.add_button = Gtk.EventBox()
        self.add_button.set_tooltip_text(self.TIP_ADD)
        self.add_button.add(add_image)
        self.add_button.show()
        self.add_button.connect('button-release-event',
                                lambda b, e: self.add_entry())
        self.add_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.ACTIVE))
        self.add_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.NORMAL))
        self.add_del_button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add_del_button_box.pack_start(
            self.add_button, expand=False, fill=False, padding=0)
        self.add_del_button_box.pack_start(
            self.del_button, expand=False, fill=False, padding=0)
        self.add_del_button_box.show()

    def set_arrow_sensitive(self, is_left_sensitive, is_right_sensitive):
        """Control the sensitivity of the movement buttons."""
        sens_tuple = (is_left_sensitive, is_right_sensitive)
        for i, event_box in enumerate(self.arrow_box.get_children()):
            event_box.get_child().set_sensitive(sens_tuple[i])
            if not sens_tuple[i]:
                event_box.set_state(Gtk.StateType.NORMAL)

    def move_element(self, num_places_right):
        """Move the entry left or right."""
        widget = self.last_selected_src
        if widget is None:
            return
        old_index = self.entries.index(widget)
        if (old_index + num_places_right < 0 or
                old_index + num_places_right > len(self.entries) - 1):
            return
        self.entries.remove(widget)
        self.entries.insert(old_index + num_places_right, widget)
        self.populate_table()
        self.setter(widget)

    def get_entry(self, value_item):
        """Create a gtk Entry for this array element."""
        widget = Gtk.Entry()
        widget.set_text(value_item)
        widget.connect('focus-in-event', self._handle_focus_on_entry)
        widget.connect("button-release-event", self._handle_middle_click_paste)
        widget.connect_after("paste-clipboard", self.setter)
        widget.connect_after("key-release-event", lambda e, v: self.setter(e))
        widget.connect_after(
            "button-release-event", lambda e, v: self.setter(e))
        widget.connect('focus-out-event', self._handle_focus_off_entry)
        widget.set_width_chars(self.chars_width - 1)
        widget.show()
        return widget

    def populate_table(self, focus_widget=None):
        """Populate a table with the array elements, dynamically."""
        position = None
        table_widgets = self.entries + [self.button_box]
        table_children = self.entry_table.get_children()
        if focus_widget is None:
            for child in table_children:
                if child.is_focus() and isinstance(child, Gtk.Entry):
                    focus_widget = child
                    position = focus_widget.get_position()
        else:
            position = focus_widget.get_position()
        for child in self.entry_table.get_children():
            self.entry_table.remove(child)
        if (focus_widget is None and self.entry_table.is_focus() and
                len(self.entries) > 0):
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

        if self.has_titles:
            for col, label in enumerate(self.metadata['element-titles']):
                if col >= len(table_widgets) - 1:
                    break
                widget = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                label = Gtk.Label(label=self.metadata['element-titles'][col])
                label.show()
                widget.pack_start(label, expand=True, fill=True, padding=0)
                widget.show()
                self.entry_table.attach(widget,
                                        col, col + 1,
                                        0, 1,
                                        xoptions=Gtk.AttachOptions.FILL,
                                        yoptions=Gtk.AttachOptions.SHRINK)

        for i, widget in enumerate(table_widgets):
            if isinstance(widget, Gtk.Entry):
                widget.set_tooltip_text(self.TIP_ELEMENT.format((i + 1)))
            row = i // self.num_allowed_columns
            if self.has_titles:
                row += 1
            column = i % self.num_allowed_columns
            self.entry_table.attach(widget,
                                    column, column + 1,
                                    row, row + 1,
                                    xoptions=Gtk.AttachOptions.FILL,
                                    yoptions=Gtk.AttachOptions.SHRINK)
        if focus_widget is not None:
            focus_widget.grab_focus()
            focus_widget.set_position(position)
            focus_widget.select_region(position, position)
        self.grab_focus = lambda: self.hook.get_focus(
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
        if rounded_max != self.num_allowed_columns + 2 and rounded_max > 2:
            self.num_allowed_columns = max(1, rounded_max - 2)
            self.populate_table()

    def add_entry(self):
        """Add a new entry (with null text) to the variable array."""
        widget = self.get_entry('')
        self.entries.append(widget)
        self._adjust_entry_length()
        self.populate_table(focus_widget=widget)
        if (self.metadata.get(metomi.rose.META_PROP_COMPULSORY) !=
                metomi.rose.META_PROP_VALUE_TRUE):
            self.setter(widget)

    def remove_entry(self):
        """Remove the last selected or the last entry."""
        if (self.last_selected_src is not None and
                self.last_selected_src in self.entries):
            text = self.last_selected_src.get_text()
            widget = self.entries.pop(
                self.entries.index(self.last_selected_src))
            self.last_selected_src = None
        else:
            text = self.entries[-1].get_text()
            widget = self.entries.pop()
        self.populate_table()
        if (self.metadata.get(metomi.rose.META_PROP_COMPULSORY) !=
                metomi.rose.META_PROP_VALUE_TRUE or text):
            # Optional, or compulsory but not blank.
            self.setter(widget)

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
        entries_have_commas = any("," in v for v in val_array)
        new_value = python_array_join(val_array)
        if new_value != self.value:
            self.value = new_value
            self.set_value(new_value)
            if entries_have_commas:
                new_val_array = python_array_split(new_value)
                if len(new_val_array) != len(self.entries):
                    self.generate_entries()
                    focus_index = None
                    for i, val in enumerate(val_array):
                        if "," in val:
                            val_post_comma = val[:val.index(",") + 1]
                            focus_index = len(python_array_join(
                                new_val_array[:i] + [val_post_comma]))
                    self.populate_table()
                    self.set_focus_index(focus_index)
        return False

    def _adjust_entry_length(self):
        for widget in self.entries:
            widget.set_width_chars(self.chars_width)
            widget.set_max_length(self.chars_width)
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


def python_array_join(values):
    """Create a Python-compliant list value from values."""
    return "[" + ", ".join(values) + "]"


def python_array_split(value):
    """Split the value into elements with appropriate string values."""
    try:
        value_array = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        value_no_brackets = value.lstrip("[").rstrip("]")
        value_array = metomi.rose.variable.array_split(value_no_brackets)
        return value_array
    cast_value_array = []
    for value in value_array:
        if isinstance(value, str):
            cast_value_array.append('"' + value + '"')
        else:
            cast_value_array.append(str(value))
    return cast_value_array
