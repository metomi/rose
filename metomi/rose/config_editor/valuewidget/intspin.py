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

import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import metomi.rose.config_editor


class IntSpinButtonValueWidget(Gtk.Box):

    """This is a class to represent an integer with a spin button."""

    WARNING_MESSAGE = 'Warning:\n  variable value: {0}\n  widget value: {1}'

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(IntSpinButtonValueWidget, self).__init__(homogeneous=False,
                                                       spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook
        self.upper = sys.maxsize
        self.lower = -sys.maxsize - 1

        tooltip_text = None
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            int_value = 0
            tooltip_text = self.WARNING_MESSAGE.format(value, int_value)

        value_ok = self.lower <= int_value <= self.upper

        if value_ok:
            entry = self.make_spinner(int_value)
            signal = 'changed'
        else:
            entry = Gtk.Entry()
            entry.set_text(self.value)
            signal = 'activate'

        self.change_id = entry.connect(signal, self.setter)

        entry.set_tooltip_text(tooltip_text)
        entry.show()

        self.pack_start(entry, False, False, 0)

        self.warning_img = Gtk.Image()
        if not value_ok:
            self.warning_img = Gtk.Image()
            self.warning_img.set_from_stock(Gtk.STOCK_DIALOG_WARNING,
                                            Gtk.IconSize.MENU)
            self.warning_img.set_tooltip_text(
                metomi.rose.config_editor.WARNING_INTEGER_OUT_OF_BOUNDS)
            self.warning_img.show()
            self.pack_start(self.warning_img, False, False, 0)

        self.grab_focus = lambda: self.hook.get_focus(entry)

    def make_spinner(self, int_value):
        my_adj = Gtk.Adjustment(value=int_value,
                                upper=self.upper,
                                lower=self.lower,
                                step_incr=1)

        spin_button = Gtk.SpinButton(adjustment=my_adj, digits=0)
        spin_button.connect('focus-in-event',
                            self.hook.trigger_scroll)

        spin_button.set_numeric(True)

        return spin_button

    def setter(self, widget):
        """Callback on widget value change.

        Note: 1. SpinButton's `.get_value_as_int` method is not reliable. It
        returns the spin value but not the value of the text that is typed in
        manually. 2. Calling `self.set_value` method with a value that cannot
        be cast into an `int` may cause `Segmentation fault` on some version of
        GTK, so we'll only call `self.set_value` for a value that can be cast
        into an in-range `int` value.
        """
        text = widget.get_text()
        if text != self.value:
            self.value = text
            try:
                value_ok = self.lower <= int(text) <= self.upper
            except ValueError:
                value_ok = False
            if value_ok:
                self.set_value(self.value)
                self.warning_img.hide()
            else:
                self.warning_img.show()
        return False
