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

import metomi.rose


class BoolToggleValueWidget(Gtk.Box):

    """Produces a 'true' and 'false' labelled toggle button."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(BoolToggleValueWidget, self).__init__(homogeneous=False,
                                                    spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.allowed_values = []
        self.label_dict = {}
        if metadata.get(metomi.rose.META_PROP_TYPE) == "boolean":
            self.allowed_values = [metomi.rose.TYPE_BOOLEAN_VALUE_FALSE,
                                   metomi.rose.TYPE_BOOLEAN_VALUE_TRUE]
            self.label_dict = dict(list(zip(self.allowed_values,
                                       self.allowed_values)))
        elif metadata.get(metomi.rose.META_PROP_TYPE) == "python_boolean":
            self.allowed_values = [metomi.rose.TYPE_PYTHON_BOOLEAN_VALUE_FALSE,
                                   metomi.rose.TYPE_PYTHON_BOOLEAN_VALUE_TRUE]
            self.label_dict = dict(list(zip(self.allowed_values,
                                       self.allowed_values)))
        else:
            self.allowed_values = [metomi.rose.TYPE_LOGICAL_VALUE_FALSE,
                                   metomi.rose.TYPE_LOGICAL_VALUE_TRUE]
            self.label_dict = {
                metomi.rose.TYPE_LOGICAL_VALUE_FALSE:
                metomi.rose.TYPE_LOGICAL_FALSE_TITLE,
                metomi.rose.TYPE_LOGICAL_VALUE_TRUE:
                metomi.rose.TYPE_LOGICAL_TRUE_TITLE}

        imgs = [Gtk.Image.new_from_stock(Gtk.STOCK_MEDIA_STOP,
                                         Gtk.IconSize.MENU),
                Gtk.Image.new_from_stock(Gtk.STOCK_APPLY, Gtk.IconSize.MENU)]
        self.image_dict = dict(list(zip(self.allowed_values, imgs)))
        bad_img = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_WARNING,
                                           Gtk.IconSize.MENU)
        self.button = Gtk.ToggleButton(label=self.value)
        if self.value in self.allowed_values:
            self.button.set_active(self.allowed_values.index(self.value))
            self.button.set_label(self.label_dict[self.value])
            self.button.set_image(self.image_dict[self.value])
        else:
            self.button.set_inconsistent(True)
            self.button.set_image(bad_img)
        self.button.connect('toggled', self._switch_state_and_set)
        self.button.show()
        self.pack_start(self.button, expand=False, fill=False)
        self.grab_focus = lambda: self.hook.get_focus(self.button)
        self.button.connect('focus-in-event', self.hook.trigger_scroll)

    def _switch_state_and_set(self, widget):
        state = self.allowed_values[int(widget.get_active())]
        title = self.label_dict[state]
        image = self.image_dict[state]
        widget.set_label(title)
        widget.set_image(image)
        self.setter(widget)

    def setter(self, widget):
        label_value = widget.get_label()
        for real_item, label in list(self.label_dict.items()):
            if label == label_value:
                chosen_value = real_item
                break
        self.value = chosen_value
        self.set_value(chosen_value)
        return False
