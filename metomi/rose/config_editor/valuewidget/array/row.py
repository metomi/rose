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

import re
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import entry
import metomi.rose.gtk.util
import metomi.rose.variable


class RowArrayValueWidget(Gtk.Box):

    """This is a class to represent a value as part of a row."""

    BAD_COLOUR = metomi.rose.gtk.util.color_parse(
        metomi.rose.config_editor.COLOUR_VARIABLE_TEXT_ERROR)
    CHECK_NAME_IS_ELEMENT = re.compile(r'.*\(\d+\)$').match
    TIP_ADD = 'Add array element'
    TIP_DELETE = 'Remove last array element'
    TIP_INVALID_ENTRY = "Invalid entry - not {0}"
    MIN_WIDTH_CHARS = 7

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(RowArrayValueWidget, self).__init__(homogeneous=False,
                                                  spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.value_array = metomi.rose.variable.array_split(value)
        self.extra_array = []  # For new rows
        self.element_values = []
        self.rows = []
        self.widgets = []
        self.has_length_error = False
        self.length = metadata.get(metomi.rose.META_PROP_LENGTH)
        self.type = metadata.get(metomi.rose.META_PROP_TYPE, "raw")
        self.num_cols = len(self.value_array)
        if arg_str is None:
            if isinstance(self.type, list):
                self.num_cols = len(self.type)
            elif self.length is not None and self.length.isdigit():
                self.num_cols = int(self.length)
        else:
            self.num_cols = int(arg_str)
        self.unlimited = (self.length == ':')
        if self.unlimited:
            self.array_length = 1
        else:
            self.array_length = metadata.get(metomi.rose.META_PROP_LENGTH, 1)
        log_imgs = [(Gtk.STOCK_MEDIA_STOP, Gtk.IconSize.MENU),
                    (Gtk.STOCK_APPLY, Gtk.IconSize.MENU),
                    (Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.MENU)]
        self.make_log_image = lambda i: Gtk.Image.new_from_stock(*log_imgs[i])
        self.set_num_rows()
        self.entry_table = Gtk.Table(rows=self.num_rows,
                                     columns=self.num_cols,
                                     homogeneous=True)
        self.entry_table.connect('focus-in-event',
                                 self.hook.trigger_scroll)
        self.entry_table.show()
        for i in range(self.num_rows):
            self.insert_row(i)
        self.normalise_width_widgets()
        self.generate_buttons(is_for_elements=not isinstance(self.type, list))
        self.pack_start(self.add_del_button_box, expand=False, fill=False)
        self.pack_start(self.entry_table, expand=True, fill=True)
        self.show()

    def set_num_rows(self):
        """Derive the number of columns and rows."""
        if not isinstance(self.type, list):
            self.num_rows = 1
            self.max_rows = 1
            self.unlimited = False
            return
        columns = len(self.type)
        if self.CHECK_NAME_IS_ELEMENT(self.metadata['id']):
            self.unlimited = False
        if self.unlimited:
            self.num_rows, rem = divmod(len(self.value_array), columns)
            self.num_rows += [1, 0][rem == 0]
            self.max_rows = sys.maxsize
        else:
            self.num_rows = int(self.array_length)
            rem = divmod(len(self.value_array), columns)[1]
            if self.num_rows == 0:
                self.num_rows = 1
            self.max_rows = self.num_rows
        if rem != 0:
            # Then there is an incorrect number of entries.
            # Display as entry box.
            self.num_rows = 1
            self.max_rows = 1
            self.unlimited = False
            self.has_length_error = True
            self.value_array = [self.value]
        if self.num_rows == 0:
            self.num_rows = 1
        if self.max_rows == 0:
            self.max_rows = 1

    def get_type(self, index):
        """Get the metadata type for this value index."""
        return self.get_types()[index]

    def get_types(self):
        """Get a list of metadata types for the value."""
        if isinstance(self.type, list):
            return self.type
        return [self.type] * self.num_cols

    def grab_focus(self):
        if self.entry_table.focus_child is None:
            self.hook.get_focus(self.rows[-1][-1])
        else:
            self.hook.get_focus(self.entry_table.focus_child)

    def add_element(self, *args):
        """Create a new element (non-derived types)."""
        w_value = metomi.rose.variable.get_value_from_metadata(
            {metomi.rose.META_PROP_TYPE: self.type})
        self.value_array = self.value_array + [w_value]
        self.value = metomi.rose.variable.array_join(self.value_array)
        self.set_value(self.value)
        for child in self.entry_table.get_children():
            self.entry_table.remove(child)
        for i in range(self.num_rows):
            self.insert_row(i)
        self.normalise_width_widgets()
        self._decide_show_buttons()

    def add_row(self, *args):
        """Create a new row of widgets."""
        nrows = self.entry_table.child_get_property(
            self.rows[-1][-1], 'top-attach')
        self.entry_table.resize(nrows + 2, self.num_cols)
        new_values = self.insert_row(nrows + 1)
        if any(new_values):
            self.value_array = self.value_array + new_values
            self.value = metomi.rose.variable.array_join(self.value_array)
            self.set_value(self.value)
            self.set_num_rows()
        self.normalise_width_widgets()
        self._decide_show_buttons()
        return False

    def get_focus_index(self):
        text = ''
        for i, widget_list in enumerate(self.rows):
            for j, widget in enumerate(widget_list):
                value_index = i * self.num_cols + j
                if value_index > len(self.value_array) - 1:
                    return len(text)
                val = self.value_array[i * self.num_cols + j]
                prefix_text = entry.get_next_delimiter(self.value[len(text):],
                                                       val)
                if prefix_text is None:
                    return
                if widget == self.entry_table.focus_child:
                    if hasattr(widget, "get_focus_index"):
                        position = widget.get_focus_index()
                        return len(text + prefix_text) + position
                    else:
                        for child in widget.get_children():
                            if not hasattr(child, "get_position"):
                                continue
                            position = child.get_position()
                            if self.get_type(j) in ["character", "quoted"]:
                                position += 1
                            return len(text + prefix_text) + position
                    return len(text + prefix_text) + len(val)
                text += prefix_text + val
        return None

    def set_focus_index(self, focus_index=None):
        """Set the focus and position within the table."""
        if focus_index is None:
            return
        value_array = metomi.rose.variable.array_split(self.value)
        text = ''
        widgets = []
        for widget_list in self.rows:
            widgets.extend(widget_list)
        if self.has_length_error:  # Special invalid length widget
            widgets[0].grab_focus()
            if hasattr(widgets[0], "set_focus_index"):
                widgets[0].set_focus_index(focus_index)
            return
        for i, val in enumerate(value_array):
            prefix = entry.get_next_delimiter(self.value[len(text):], val)
            if prefix is None:
                return
            if len(text + prefix + val) >= focus_index:
                if len(widgets) > i:
                    widgets[i].grab_focus()
                    val_offset = focus_index - len(text + prefix)
                    if hasattr(widgets[i], "set_focus_index"):
                        widgets[i].set_focus_index(val_offset)
                    return
            text += prefix + val

    def del_element(self, *args):
        """Create a new element (non-derived types)."""
        self.value_array.pop()
        self.value = metomi.rose.variable.array_join(self.value_array)
        self.set_value(self.value)
        for child in self.entry_table.get_children():
            self.entry_table.remove(child)
        for i in range(self.num_rows):
            self.insert_row(i)
        self.normalise_width_widgets()
        self._decide_show_buttons()

    def del_row(self, *args):
        """Delete the last row of widgets."""
        nrows = self.entry_table.child_get_property(
            self.rows[-1][-1], 'top-attach')
        for _ in enumerate(self.get_types()):
            widget = self.rows[-1][-1]
            self.rows[-1].pop(-1)
            self.entry_table.remove(widget)
        self.rows.pop(-1)
        self.entry_table.resize(nrows, self.num_cols)

        chop_index = len(self.value_array) - len(self.get_types())
        self.value_array = self.value_array[:chop_index]
        self.value = metomi.rose.variable.array_join(self.value_array)
        self.set_value(self.value)
        self.set_num_rows()
        self.normalise_width_widgets()
        self._decide_show_buttons()
        return False

    def _decide_show_buttons(self):
        # Show or hide the add row and delete row buttons.
        if isinstance(self.type, list):
            if len(self.rows) >= self.max_rows and not self.unlimited:
                self.add_button.hide()
                self.del_button.show()
            else:
                self.add_button.show()
                self.del_button.show()
            if len(self.rows) == 1:
                self.del_button.hide()
            else:
                self.add_button.show()
        else:
            if (self.length is not None and self.length.isdigit() and
                    len(self.value_array) >= int(self.length)):
                self.add_button.hide()
                self.del_button.show()
            else:
                self.add_button.show()
                self.del_button.show()
            if len(self.value_array) == 1:
                self.del_button.hide()

    def insert_row(self, row_index):
        """Create a row of widgets from type_list."""
        widget_list = []
        new_values = []
        actual_num_cols = len(self.get_types())
        for i, el_piece_type in enumerate(self.get_types()):
            unwrapped_index = row_index * actual_num_cols + i
            value_index = unwrapped_index
            if (not isinstance(self.type, list) and
                    value_index >= len(self.value_array)):
                widget = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                eb0 = Gtk.EventBox()
                eb0.show()
                widget.pack_start(eb0, expand=True, fill=True)
                widget.show()
                self.entry_table.attach(widget,
                                        i, i + 1,
                                        row_index, row_index + 1,
                                        xoptions=(Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL),
                                        yoptions=Gtk.AttachOptions.SHRINK)
                widget_list.append(widget)
                continue
            while value_index > len(self.value_array) - 1:
                value_index -= actual_num_cols
            if value_index < 0:
                w_value = metomi.rose.variable.get_value_from_metadata(
                    {metomi.rose.META_PROP_TYPE: el_piece_type})
            else:
                w_value = self.value_array[value_index]
            new_values.append(w_value)
            hover_text = ''
            w_error = {}
            if el_piece_type in ['integer', 'real']:
                try:
                    [int, float][el_piece_type == 'real'](w_value)
                except (TypeError, ValueError):
                    if w_value != '':
                        hover_text = self.TIP_INVALID_ENTRY.format(
                            el_piece_type)
                        w_error = {metomi.rose.META_PROP_TYPE: hover_text}
            w_meta = {metomi.rose.META_PROP_TYPE: el_piece_type}
            widget_cls = metomi.rose.config_editor.valuewidget.chooser(
                w_value, w_meta, w_error)
            hook = self.hook
            setter = ArrayElementSetter(self.setter, unwrapped_index)
            widget = widget_cls(w_value, w_meta, setter.set_value, hook)
            if hover_text:
                widget.set_tooltip_text(hover_text)
            widget.show()
            self.entry_table.attach(widget,
                                    i, i + 1,
                                    row_index, row_index + 1,
                                    xoptions=(Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL),
                                    yoptions=Gtk.AttachOptions.SHRINK)
            widget_list.append(widget)
        self.rows.append(widget_list)
        self.widgets.extend(widget_list)
        return new_values

    def normalise_width_widgets(self):
        if not self.rows:
            return
        for widget in self.rows[0]:
            self._normalise_width_chars(widget)

    def _normalise_width_chars(self, widget):
        index = self.widgets.index(widget)
        element = index % self.num_cols
        max_width = {}
        # Get max width
        for widgets in self.rows:
            if element >= len(widgets):
                continue
            e_widget = widgets[element]
            i = 0
            child_list = e_widget.get_children()
            while child_list:
                child = child_list.pop()
                if isinstance(child, Gtk.Entry) and hasattr(child, 'get_text'):
                    width = len(child.get_text())
                    if width > max_width.get(i, -1):
                        max_width.update({i: width})
                if hasattr(child, 'get_children'):
                    child_list.extend(child.get_children())
                elif hasattr(child, 'get_child'):
                    child_list.append(child.get_child())
                i += 1
        for key, value in list(max_width.items()):
            if value < self.MIN_WIDTH_CHARS:
                max_width[key] = self.MIN_WIDTH_CHARS
        # Set max width
        for widgets in self.rows:
            if element >= len(widgets):
                continue
            e_widget = widgets[element]
            i = 0
            child_list = e_widget.get_children()
            while child_list:
                child = child_list.pop()
                if (isinstance(child, Gtk.Entry) and
                        hasattr(child, 'set_width_chars')):
                    child.set_width_chars(max_width[i])
                if hasattr(child, 'get_children'):
                    child_list.extend(child.get_children())
                elif hasattr(child, 'get_child'):
                    child_list.append(child.get_child())
                i += 1

    def generate_buttons(self, is_for_elements=False):
        """Insert an add row and delete row button."""
        del_image = Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE,
                                             Gtk.IconSize.MENU)
        del_image.show()
        self.del_button = Gtk.EventBox()
        self.del_button.set_tooltip_text(self.TIP_DELETE)
        self.del_button.add(del_image)
        self.del_button.show()
        if is_for_elements:
            delete_func = self.del_element
        else:
            delete_func = self.del_row
        self.del_button.connect('button-release-event', delete_func)
        self.del_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.ACTIVE))
        self.del_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.NORMAL))
        add_image = Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.MENU)
        add_image.show()
        self.add_button = Gtk.EventBox()
        self.add_button.set_tooltip_text(self.TIP_ADD)
        self.add_button.add(add_image)
        self.add_button.show()
        if is_for_elements:
            add_func = self.add_element
        else:
            add_func = self.add_row
        self.add_button.connect('button-release-event', add_func)
        self.add_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.ACTIVE))
        self.add_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(Gtk.StateType.NORMAL))
        self.add_del_button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add_del_button_box.pack_start(
            self.add_button, expand=False, fill=False)
        self.add_del_button_box.pack_start(
            self.del_button, expand=False, fill=False)
        self.add_del_button_box.show()
        self._decide_show_buttons()

    def setter(self, array_index, element_value):
        """Update the value."""
        actual_num_cols = len(self.get_types())
        widget_row = self.rows[array_index / actual_num_cols]
        widget = widget_row[array_index % actual_num_cols]
        self._normalise_width_chars(widget)
        i = array_index - len(self.value_array)
        if i >= 0:
            while len(self.extra_array) <= i:
                self.extra_array.append("")
            self.extra_array[i] = element_value
            ok_index = 0
            j = self.num_cols
            while j <= len(self.extra_array):
                if (len(self.extra_array[:j]) % self.num_cols == 0 and
                        all(self.extra_array[:j])):
                    ok_index = j
                else:
                    break
                j += self.num_cols
            self.value_array.extend(self.extra_array[:ok_index])
            self.extra_array = self.extra_array[ok_index:]
        else:
            self.value_array[array_index] = element_value
        new_val = metomi.rose.variable.array_join(self.value_array)
        if new_val != self.value:
            self.value = new_val
            self.set_value(new_val)


class ArrayElementSetter(object):

    """Element widget setter class."""

    def __init__(self, setter_function, index):
        self.setter_function = setter_function
        self.index = index

    def set_value(self, value):
        self.setter_function(self.index, value)
