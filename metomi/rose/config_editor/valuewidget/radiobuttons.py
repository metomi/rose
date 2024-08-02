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


class RadioButtonsValueWidget(Gtk.HBox):

    """This is a class to represent a value as radio buttons."""

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(RadioButtonsValueWidget, self).__init__(homogeneous=False,
                                                      spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        var_values = metadata[rose.META_PROP_VALUES]
        var_titles = metadata.get(rose.META_PROP_VALUE_TITLES)

        if var_titles:
            vbox = Gtk.VBox()
            self.pack_start(vbox, False, True, 0)
            vbox.show()

        for k, item in enumerate(var_values):
            button_label = str(item)
            if var_titles is not None and var_titles[k]:
                button_label = var_titles[k]
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
            if var_titles is not None and var_titles[k]:
                radio_button.set_tooltip_text("(" + item + ")")
            radio_button.set_active(False)
            if item == self.value:
                radio_button.set_active(True)
            radio_button.connect('toggled', self.setter)
            radio_button.connect('button-press-event', self.setter)
            radio_button.connect('activate', self.setter)

            if var_titles:
                vbox.pack_start(radio_button, False, False, 2)
            else:
                self.pack_start(radio_button, False, False, 10)
            radio_button.show()
            radio_button.connect('focus-in-event',
                                 self.hook.trigger_scroll)

        self.grab_focus = lambda: self.hook.get_focus(radio_button)
        if len(var_values) == 1 and self.value == var_values[0]:
            radio_button.set_sensitive(False)

    def setter(self, widget, event=None):
        if widget.get_active():
            self.value = widget.real_value
            self.set_value(self.value)
        return False
