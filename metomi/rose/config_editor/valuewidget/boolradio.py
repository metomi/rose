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

import rose.config_editor
from . import radiobuttons


class BoolValueWidget(radiobuttons.RadioButtonsValueWidget):

    """Produces 'true' and 'false' labelled radio buttons."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(BoolValueWidget, self).__init__(homogeneous=False,
                                              spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.allowed_values = []
        self.label_dict = {}
        if metadata.get(rose.META_PROP_TYPE) == "boolean":
            self.allowed_values = [rose.TYPE_BOOLEAN_VALUE_TRUE,
                                   rose.TYPE_BOOLEAN_VALUE_FALSE]
        else:
            self.allowed_values = [rose.TYPE_LOGICAL_VALUE_TRUE,
                                   rose.TYPE_LOGICAL_VALUE_FALSE]
            self.label_dict = {
                rose.TYPE_LOGICAL_VALUE_TRUE:
                rose.TYPE_LOGICAL_TRUE_TITLE,
                rose.TYPE_LOGICAL_VALUE_FALSE:
                rose.TYPE_LOGICAL_FALSE_TITLE}

        for k, item in enumerate(self.allowed_values):
            if item in self.label_dict:
                button_label = str(self.label_dict[item])
            else:
                button_label = str(item)
                self.label_dict.update({item: button_label})
            if k == 0:
                radio_button = Gtk.RadioButton(group=None,
                                               label=button_label,
                                               use_underline=False)
                radio_button.real_value = item
            else:
                radio_button = Gtk.RadioButton(group=radio_button,
                                               label=button_label,
                                               use_underline=False)
                radio_button.real_value = item
            radio_button.set_active(False)
            if item == str(value):
                radio_button.set_active(True)
            radio_button.connect('toggled', self.setter)
            self.pack_start(radio_button, False, False, 10)
            radio_button.show()
            radio_button.connect('focus-in-event', self.hook.trigger_scroll)
        self.grab_focus = lambda: self.hook.get_focus(radio_button)

    def setter(self, widget, variable):
        if widget.get_active():
            label_value = widget.get_label()
            for real_item, label in list(self.label_dict.items()):
                if label == label_value:
                    chosen_value = real_item
                    break
            self.value = chosen_value
            self.set_value(chosen_value)
        return False
