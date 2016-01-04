# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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

import re
import sys

import pygtk
pygtk.require('2.0')
import gtk
import pango

import rose.gtk.util
import rose.variable


class LogicalArrayValueWidget(gtk.HBox):

    """This is a class to represent an array of logical or boolean types."""

    TIP_ADD = 'Add array element'
    TIP_DEL = 'Delete array element'

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(LogicalArrayValueWidget, self).__init__(homogeneous=False,
                                                      spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.max_length = metadata[rose.META_PROP_LENGTH]
        value_array = rose.variable.array_split(value)
        if metadata.get(rose.META_PROP_TYPE) == "boolean":
            self.allowed_values = [rose.TYPE_BOOLEAN_VALUE_FALSE,
                                   rose.TYPE_BOOLEAN_VALUE_TRUE]
            self.label_dict = dict(zip(self.allowed_values,
                                       self.allowed_values))
        else:
            self.allowed_values = [rose.TYPE_LOGICAL_VALUE_FALSE,
                                   rose.TYPE_LOGICAL_VALUE_TRUE]
            self.label_dict = {
                rose.TYPE_LOGICAL_VALUE_FALSE:
                rose.TYPE_LOGICAL_FALSE_TITLE,
                rose.TYPE_LOGICAL_VALUE_TRUE:
                rose.TYPE_LOGICAL_TRUE_TITLE}

        imgs = [(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_MENU),
                (gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU)]
        self.make_log_image = lambda i: gtk.image_new_from_stock(*imgs[i])
        self.chars_width = max([len(v) for v in value_array] + [1]) + 1
        self.num_allowed_columns = 3
        self.entry_table = gtk.Table(rows=1,
                                     columns=self.num_allowed_columns,
                                     homogeneous=True)
        self.entry_table.connect('focus-in-event',
                                 self.hook.trigger_scroll)
        self.entry_table.show()

        self.entries = []
        for value_item in value_array:
            entry = self.get_entry(value_item)
            self.entries.append(entry)
        self.generate_buttons()
        self.populate_table()
        self.pack_start(self.button_box, expand=False, fill=False)
        self.pack_start(self.entry_table, expand=True, fill=True)
        self.entry_table.connect_after('size-allocate',
                                       lambda w, e: self.reshape_table())
        self.connect('focus-in-event',
                     lambda w, e: self.hook.get_focus(self.get_focus_entry()))

    def get_focus_entry(self):
        """Get either the last selected button or the last one."""
        return self.entries[-1]

    def generate_buttons(self):
        """Create the add button."""
        add_image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
        add_image.show()
        self.add_button = gtk.EventBox()
        self.add_button.set_tooltip_text(self.TIP_ADD)
        self.add_button.add(add_image)
        self.add_button.connect('button-release-event',
                                lambda b, e: self.add_entry())
        self.add_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_ACTIVE))
        self.add_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_NORMAL))
        del_image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,
                                             gtk.ICON_SIZE_MENU)
        del_image.show()
        self.del_button = gtk.EventBox()
        self.del_button.set_tooltip_text(self.TIP_ADD)
        self.del_button.add(del_image)
        self.del_button.show()
        self.del_button.connect('button-release-event',
                                self.remove_entry)
        self.del_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_ACTIVE))
        self.del_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_NORMAL))
        self.button_box = gtk.VBox()
        self.button_box.show()
        self.button_box.pack_start(self.add_button, expand=False, fill=False)
        self.button_box.pack_start(self.del_button, expand=False, fill=False)

    def get_entry(self, value_item):
        """Create a widget for this array element."""
        bad_img = gtk.image_new_from_stock(gtk.STOCK_DIALOG_WARNING,
                                           gtk.ICON_SIZE_MENU)
        button = gtk.ToggleButton()
        button.options = [rose.TYPE_LOGICAL_VALUE_FALSE,
                          rose.TYPE_LOGICAL_VALUE_TRUE]
        button.labels = [rose.TYPE_LOGICAL_FALSE_TITLE,
                         rose.TYPE_LOGICAL_TRUE_TITLE]
        button.set_tooltip_text(value_item)
        if value_item in self.allowed_values:
            index = self.allowed_values.index(value_item)
            button.set_active(index)
            button.set_image(self.make_log_image(index))
            button.set_label(button.labels[index])
        else:
            button.set_inconsistent(True)
            button.set_image(bad_img)
        button.connect('toggled', self._switch_state_and_set)
        button.show()
        return button

    def _switch_state_and_set(self, widget):
        state = self.allowed_values[widget.get_active()]
        title = self.label_dict[state]
        image = self.make_log_image(widget.get_active())
        widget.set_tooltip_text(state)
        widget.set_label(title)
        widget.set_image(image)
        self.setter(widget)

    def populate_table(self):
        """Populate a table with the array elements, dynamically."""
        focus = None
        table_widgets = self.entries
        for child in self.entry_table.get_children():
            if child.is_focus():
                focus = child
        if len(self.entry_table.get_children()) < len(table_widgets):
            # Newly added widget, set focus to the end
            focus = self.entries[-1]
        for child in self.entry_table.get_children():
            self.entry_table.remove(child)
        if (focus is None and self.entry_table.is_focus()
                and len(self.entries) > 0):
            focus = self.entries[-1]
        num_fields = len(self.entries)
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
        else:
            self.del_button.show()
        for i, widget in enumerate(table_widgets):
            row = i // self.num_allowed_columns
            column = i % self.num_allowed_columns
            self.entry_table.attach(widget,
                                    column, column + 1,
                                    row, row + 1,
                                    xoptions=gtk.FILL,
                                    yoptions=gtk.SHRINK)
        self.grab_focus = lambda: self.hook.get_focus(self.entries[-1])
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
        """Add a new button to the array."""
        entry = self.get_entry(self.allowed_values[0])
        self.entries.append(entry)
        self.populate_table()
        self.setter()

    def remove_entry(self, *args):
        """Remove a button."""
        if len(self.entries) > 1:
            self.entries.pop()
            self.populate_table()
            self.setter()

    def setter(self, *args):
        """Update the value."""
        val_array = []
        for widget in self.entries:
            value = widget.get_tooltip_text()
            if value is None:
                value = ''
            val_array.append(value)
        new_val = rose.variable.array_join(val_array)
        self.value = new_val
        self.set_value(new_val)
        self.value_array = rose.variable.array_split(self.value)
        return False
