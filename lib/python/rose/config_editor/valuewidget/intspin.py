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

import sys

import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor


class IntSpinButtonValueWidget(gtk.HBox):

    """This is a class to represent an integer with a spin button."""

    WARNING_MESSAGE = 'Warning:\n  variable value: {0}\n  widget value: {1}'

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(IntSpinButtonValueWidget, self).__init__(homogeneous=False,
                                                       spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.upper = sys.maxint
        self.lower = -sys.maxint - 1

        tooltip_text = None
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            int_value = 0
            tooltip_text = self.WARNING_MESSAGE.format(value,
                                                       int_value)

        if int_value > self.upper or int_value < self.lower:
            acceptable = False
        else:
            acceptable = True

        if acceptable:
            entry = self.make_spinner(int_value)
            signal = 'value-changed'
        else:
            entry = gtk.Entry()
            entry.set_text(self.value)
            signal = 'activate'

        self.change_id = entry.connect(signal, self.setter)

        entry.set_tooltip_text(tooltip_text)
        entry.show()

        self.pack_start(entry, False, False, 0)

        self.warning_img = gtk.Image()
        if not acceptable:
            self.warning_img = gtk.Image()
            self.warning_img.set_from_stock(gtk.STOCK_DIALOG_WARNING,
                                            gtk.ICON_SIZE_MENU)
            self.warning_img.set_tooltip_text(
                rose.config_editor.WARNING_INTEGER_OUT_OF_BOUNDS)
            self.warning_img.show()
            self.pack_start(self.warning_img, False, False, 0)

        self.grab_focus = lambda: self.hook.get_focus(entry)

    def make_spinner(self, int_value):
        my_adj = gtk.Adjustment(value=int_value,
                                upper=self.upper,
                                lower=self.lower,
                                step_incr=1)

        spin_button = gtk.SpinButton(adjustment=my_adj, digits=0)
        spin_button.connect('focus-in-event',
                            self.hook.trigger_scroll)

        spin_button.set_numeric(True)

        return spin_button

    def setter(self, widget):
        if isinstance(widget, gtk.Entry):
            if widget.get_text != self.value:
                self.value = widget.get_text()
                self.set_value(self.value)
                if (not widget.get_text().isdigit() or
                        int(widget.get_text()) > self.upper or
                        int(widget.get_text()) < self.lower):
                    self.warning_img.show()
                else:
                    self.warning_img.hide()
        else:
            if str(widget.get_value_as_int()) != self.value:
                self.value = str(widget.get_value_as_int())
                self.set_value(self.value)
                widget.set_tooltip_text(None)

        return False
