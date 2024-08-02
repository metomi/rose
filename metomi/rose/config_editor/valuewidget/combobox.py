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

import metomi.rose.config_editor


class ComboBoxValueWidget(Gtk.HBox):

    """This is a class to add a combo box for a set of variable values.

    It needs to have some allowed values set in the variable metadata.

    """

    FRAC_X_ALIGN = 0.9

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(ComboBoxValueWidget, self).__init__(homogeneous=False,
                                                  spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        comboboxentry = Gtk.ComboBox()
        liststore = Gtk.ListStore(str)
        cell = Gtk.CellRendererText()
        cell.xalign = self.FRAC_X_ALIGN
        comboboxentry.pack_start(cell, True, True, 0)
        comboboxentry.add_attribute(cell, 'text', 0)

        var_values = self.metadata[metomi.rose.META_PROP_VALUES]
        var_titles = self.metadata.get(metomi.rose.META_PROP_VALUE_TITLES)
        for k, entry in enumerate(var_values):
            if var_titles is not None and var_titles[k]:
                liststore.append([var_titles[k] + " (" + entry + ")"])
            else:
                liststore.append([entry])
        comboboxentry.set_model(liststore)
        if self.value in var_values:
            index = self.metadata['values'].index(self.value)
            comboboxentry.set_active(index)
        comboboxentry.connect('changed', self.setter)
        comboboxentry.connect('button-press-event',
                              lambda b: comboboxentry.grab_focus())
        comboboxentry.show()
        self.pack_start(comboboxentry, False, False, 0)
        self.grab_focus = lambda: self.hook.get_focus(comboboxentry)
        self.set_contains_error = (lambda e:
                                   comboboxentry.modify_bg(Gtk.StateType.NORMAL,
                                                           self.bad_colour))

    def setter(self, widget):
        index = widget.get_active()
        self.value = self.metadata[metomi.rose.META_PROP_VALUES][index]
        self.set_value(self.value)
        return False
