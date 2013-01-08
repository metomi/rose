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

import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor


class ComboBoxValueWidget(gtk.HBox):

    """This is a class to add a combo box for a set of variable values.

    It needs to have some allowed values set in the variable metadata.

    """

    FRAC_X_ALIGN = 0.9
    MAX_COLS = 5

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(ComboBoxValueWidget, self).__init__(homogeneous=False,
                                                  spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        comboboxentry = gtk.ComboBox()
        liststore = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        cell.xalign = self.FRAC_X_ALIGN
        comboboxentry.pack_start(cell)
        comboboxentry.set_wrap_width(self.MAX_COLS)
        comboboxentry.add_attribute(cell, 'text', 0)
        for entry in self.metadata[rose.META_PROP_VALUES]:
            liststore.append([entry])
        comboboxentry.set_model(liststore)
        if self.value not in self.metadata[rose.META_PROP_VALUES]:
            pass #comboboxentry.set_active(0)
        else:
            index = self.metadata['values'].index(self.value)
            comboboxentry.set_active(index)
        comboboxentry.connect('changed', self.setter)
        comboboxentry.connect('button-press-event',
                              lambda b: comboboxentry.grab_focus())
        comboboxentry.show()
        self.pack_start(comboboxentry, False, False, 0)
        self.grab_focus = lambda : self.hook.get_focus(comboboxentry)
        self.set_contains_error = (lambda e:
                                   comboboxentry.modify_bg(gtk.STATE_NORMAL,
                                                           self.bad_colour))

    def setter(self, widget):
        index = widget.get_active()
        self.value = self.metadata[rose.META_PROP_VALUES][index]
        self.set_value(self.value)
        return False
