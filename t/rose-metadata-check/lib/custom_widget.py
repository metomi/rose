# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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


class SpinnerValueWidget(gtk.HBox):

    """This is a class to represent an integer with a spin button."""

    WARNING_MESSAGE = 'Warning:\n  variable value: {0}\n  widget value: {1}'

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(IntSpinButtonValueWidget, self).__init__(homogeneous=False,
                                                       spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        tooltip_text = None
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            int_value = 0
            tooltip_text = self.WARNING_MESSAGE.format(value,
                                                       int_value)
        my_adj = gtk.Adjustment(value=int_value,
                                upper=sys.maxsize,
                                lower=-sys.maxsize - 1,
                                step_incr=1)
        spin_button = gtk.SpinButton(adjustment=my_adj, digits=0)
        spin_button.connect('focus-in-event',
                            self.hook.trigger_scroll)
        spin_button.set_numeric(True)
        spin_button.set_tooltip_text(tooltip_text)
        spin_button.show()
        self.change_id = spin_button.connect('value-changed', self.setter)
        self.pack_start(spin_button, False, False, 0)
        self.grab_focus = lambda: self.hook.get_focus(spin_button)

    def setter(self, widget):
        if str(widget.get_value_as_int()) != self.value:
            self.value = str(widget.get_value_as_int())
            self.set_value(self.value)
            widget.set_tooltip_text(None)
        return False
