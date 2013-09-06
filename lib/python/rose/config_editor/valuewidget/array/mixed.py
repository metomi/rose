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
import sys

import pygtk
pygtk.require('2.0')
import gtk
import pango

import rose.gtk.util
import rose.variable


class MixedArrayValueWidget(gtk.HBox):

    """This is a class to represent a derived type variable as a table.
    
    The type (variable.metadata['type']) should be a list, e.g.
    ['integer', 'real']. There can optionally be a length
    (variable.metadata['length'] for derived type arrays.
    
    This will create a table containing different types (horizontally)
    and different array elements (vertically).
    
    """

    BAD_COLOUR = rose.gtk.util.color_parse(
                        rose.config_editor.COLOUR_VARIABLE_TEXT_ERROR)
    CHECK_NAME_IS_ELEMENT = re.compile('.*\(\d+\)$').match
    TIP_ADD = 'Add array element'
    TIP_DELETE = 'Remove last array element'
    TIP_INVALID_ENTRY = "Invalid entry - not {0}"
    MIN_WIDTH_CHARS = 7

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(MixedArrayValueWidget, self).__init__(homogeneous=False,
                                                    spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.last_value = value
        self.value_array = rose.variable.array_split(value)
        self.extra_array = []  # For new rows
        self.element_values = []
        self.rows = []
        self.widgets = []
        self.unlimited = (metadata.get(rose.META_PROP_LENGTH) == ':')
        if self.unlimited:
            self.array_length = 1
        else:
            self.array_length = metadata.get(rose.META_PROP_LENGTH, 1)
        self.num_cols = len(metadata[rose.META_PROP_TYPE])
        self.types_row = [t for t in
                          metadata[rose.META_PROP_TYPE]]
        log_imgs = [(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_MENU),
                    (gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU),
                    (gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)]
        self.make_log_image = lambda i: gtk.image_new_from_stock(*log_imgs[i])
        self.set_num_rows()
        self.entry_table = gtk.Table(rows=self.num_rows,
                                     columns=self.num_cols,
                                     homogeneous=False)
        self.entry_table.connect('focus-in-event',
                                 self.hook.trigger_scroll)
        self.entry_table.show()
        r = 0
        for r in range(self.num_rows):
            self.insert_row(r)
        self.normalise_width_widgets()
        self.generate_buttons()
        self.pack_start(self.add_del_button_box, expand=False, fill=False)
        self.pack_start(self.entry_table, expand=True, fill=True)
        self.show()

    def set_num_rows(self):
        """Derive the number of columns and rows."""
        if self.CHECK_NAME_IS_ELEMENT(self.metadata['id']):
            self.unlimited = False
        if self.unlimited:
            self.num_rows, rem = divmod(len(self.value_array), self.num_cols)
            self.num_rows += [1, 0][rem == 0]
            self.max_rows = sys.maxint
        else:
            self.num_rows = int(self.array_length)
            num, rem = divmod(len(self.value_array), self.num_cols)
            if self.num_rows == 0:
               self.num_rows = 1
            self.max_rows = self.num_rows
        if rem != 0:
            # Then there is an incorrect number of entries.
            # Display as entry box.
            self.num_rows = 1
            self.max_rows = 1
            self.unlimited = False
            self.types_row = ['_error_']
            self.value_array = [self.value]
        if self.num_rows == 0:
            self.num_rows = 1
        if self.max_rows == 0:
            self.max_rows = 1
   
    def grab_focus(self):
        if self.entry_table.focus_child is None:
            self.hook.get_focus(self.rows[-1][-1])
        else:
            self.hook.get_focus(self.entry_table.focus_child)

    def add_row(self, *args):
        """Create a new row of widgets."""
        r = self.entry_table.child_get_property(self.rows[-1][-1],
                                                'top-attach')
        self.entry_table.resize(r + 2, self.num_cols) 
        new_values = self.insert_row(r + 1)
        if any(new_values):
            self.value_array = self.value_array + new_values
            self.value = rose.variable.array_join(self.value_array)
            self.last_value = self.value
            self.set_value(self.value)
            self.set_num_rows()
        self.normalise_width_widgets()
        self._decide_show_buttons()
        return False

    def get_focus_index(self):
        text = ''
        for r, widget_list in enumerate(self.rows):
            for i, widget in enumerate(widget_list):
                val = self.value_array[r * self.num_cols + i]
                prefix_text = get_next_delimiter(self.last_value[len(text):],
                                                 val)
                if widget == self.entry_table.focus_child:
                    if hasattr(widget, "get_focus_index"):
                        position = widget.get_focus_index()
                        return len(text + prefix_text) + position
                    else:
                        for child in widget.get_children():
                            if not hasattr(child, "get_position"):
                                continue
                            position = child.get_position()
                            if self.types_row[i] in ["character", "quoted"]:
                                position += 1
                            return len(text + prefix_text) + position
                    return len(text + prefix_text) + len(val)
                text += prefix_text + val
        return None

    def set_focus_index(self, focus_index=None):
        """Set the focus and position within the table."""
        if focus_index is None:
            return
        value_array = rose.variable.array_split(self.value)
        text = ''
        widgets = []
        for widget_list in self.rows:
            widgets.extend(widget_list)
        types = self.types_row * len(self.rows)
        if len(types) == 1:  # Special invalid length widget
            widgets[0].grab_focus()
            if hasattr(widgets[0], "set_focus_index"):
                widgets[0].set_focus_index(focus_index)
            return
        for i, val in enumerate(value_array):
            prefix = get_next_delimiter(self.value[len(text):],
                                        val)
            if len(text + prefix + val) >= focus_index:
                if len(widgets) > i:
                    widgets[i].grab_focus()
                    val_offset = focus_index - len(text + prefix)
                    if hasattr(widgets[i], "set_focus_index"):
                        widgets[i].set_focus_index(val_offset)
                    return
            text += prefix + val

    def del_row(self, *args):
        """Delete the last row of widgets."""
        r = self.entry_table.child_get_property(self.rows[-1][-1],
                                                'top-attach')
        for i in range(len(self.types_row)):
            entry = self.rows[-1][-1]
            self.rows[-1].pop(-1)
            self.entry_table.remove(entry)
        self.rows.pop(-1)
        self.entry_table.resize(r, self.num_cols)
        chop_index = len(self.value_array) - self.num_cols
        self.value_array = self.value_array[:chop_index]
        self.value = rose.variable.array_join(self.value_array)
        self.set_value(self.value)
        self.set_num_rows()
        self._decide_show_buttons()
        return False

    def _decide_show_buttons(self):
        # Show or hide the add row and delete row buttons.
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

    def insert_row(self, row_index):
        """Create a row of widgets from type_list."""
        widget_list = []
        new_values = []
        for c, el_piece_type in enumerate(self.types_row):
            unwrapped_index = row_index * self.num_cols + c
            value_index = unwrapped_index
            while value_index > len(self.value_array) - 1:
                value_index -= len(self.types_row)
            if value_index < 0:
                w_value = rose.variable.get_value_from_metadata(
                               {rose.META_PROP_TYPE: el_piece_type})
            else:
                w_value = self.value_array[value_index]
            new_values.append(w_value)
            hover_text = ''
            w_error = {}
            if el_piece_type in ['integer', 'real']:
                try:
                    test_value = [int, float][el_piece_type == 'real'](w_value)
                except (TypeError, ValueError):
                    if w_value != '':
                        hover_text = self.TIP_INVALID_ENTRY.format(
                                                            el_piece_type)
                        w_error = {rose.META_PROP_TYPE: hover_text}
            w_meta = {rose.META_PROP_TYPE: el_piece_type}
            widget_cls = rose.config_editor.valuewidget.chooser(
                                     w_value, w_meta, w_error)
            hook = self.hook
            setter = ArrayElementSetter(self.setter, unwrapped_index)
            widget = widget_cls(w_value, w_meta, setter.set_value, hook)
            if hover_text:
                widget.set_tooltip_text(hover_text)
            widget.show()
            self.entry_table.attach(widget,
                                    c, c + 1,
                                    row_index, row_index + 1,
                                    xoptions=gtk.SHRINK,
                                    yoptions=gtk.SHRINK)
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
            e_widget = widgets[element]
            i = 0
            child_list = e_widget.get_children()
            while child_list:
                child = child_list.pop()
                if (isinstance(child, gtk.Entry) and
                    hasattr(child, 'get_text')):
                    w = len(child.get_text())
                    if w > max_width.get(i, -1):
                        max_width.update({i: w})
                if hasattr(child, 'get_children'):
                    child_list.extend(child.get_children())
                elif hasattr(child, 'get_child'):
                    child_list.append(child.get_child())
                i += 1
        for key, value in max_width.items():
            if value < self.MIN_WIDTH_CHARS:
                max_width[key] = self.MIN_WIDTH_CHARS
        # Set max width
        for widgets in self.rows:
            e_widget = widgets[element]
            i = 0
            child_list = e_widget.get_children()
            while child_list:
                child = child_list.pop()
                if (isinstance(child, gtk.Entry) and
                    hasattr(child, 'set_width_chars')):
                    child.set_width_chars(max_width[i])
                if hasattr(child, 'get_children'):
                    child_list.extend(child.get_children())
                elif hasattr(child, 'get_child'):
                    child_list.append(child.get_child())
                i += 1

    def generate_buttons(self):
        """Insert an add row and delete row button."""
        del_image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,
                                             gtk.ICON_SIZE_MENU)
        del_image.show()
        self.del_button = gtk.EventBox()
        self.del_button.set_tooltip_text(self.TIP_ADD)
        self.del_button.add(del_image)
        self.del_button.show()
        self.del_button.connect('button-release-event', self.del_row)
        self.del_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_ACTIVE))
        self.del_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_NORMAL))
        add_image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
        add_image.show()
        self.add_button = gtk.EventBox()
        self.add_button.set_tooltip_text(self.TIP_ADD)
        self.add_button.add(add_image)
        self.add_button.show()
        self.add_button.connect('button-release-event', self.add_row)
        self.add_button.connect('enter-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_ACTIVE))
        self.add_button.connect('leave-notify-event',
                                lambda b, e: b.set_state(gtk.STATE_NORMAL))
        self.add_del_button_box = gtk.VBox()
        self.add_del_button_box.pack_start(self.add_button, expand=False, fill=False)
        self.add_del_button_box.pack_start(self.del_button, expand=False, fill=False)
        self.add_del_button_box.show()
        self._decide_show_buttons()

    def setter(self, array_index, element_value):
        """Update the value."""
        widget_row = self.rows[array_index / self.num_cols]
        widget = widget_row[array_index % self.num_cols]
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
        new_val = rose.variable.array_join(self.value_array)
        if new_val != self.value:
            self.last_value = new_val
            self.set_value(new_val)
            self.value = new_val


class ArrayElementSetter(object):

    """Element widget setter class."""

    def __init__(self, setter_function, index):
        self.setter_function = setter_function
        self.index = index

    def set_value(self, value):
        self.setter_function(self.index, value)


def get_next_delimiter(array_text, next_element):
    v = array_text.index(next_element)
    if v == 0 and len(array_text) > 1:  # Null or whitespace element.
        while array_text[v].isspace():
            v += 1
        if array_text[v] == ",":
            v += 1
    return array_text[:v]
