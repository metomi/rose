#!/bin/bash
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
# Test "rose metadata-check".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Check widget reference checking.
TEST_KEY=$TEST_KEY_BASE-simple-ok
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spin.SpinnerValueWidget
__META_CONFIG__
init_widget spin.py <<'__WIDGET__'
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
                                upper=sys.maxint,
                                lower=-sys.maxint - 1,
                                step_incr=1)
        spin_button = gtk.SpinButton(adjustment=my_adj, digits=0)
        spin_button.connect('focus-in-event',
                            self.hook.trigger_scroll)
        spin_button.set_numeric(True)
        spin_button.set_tooltip_text(tooltip_text)
        spin_button.show()
        self.change_id = spin_button.connect(
                            'value-changed',
                            self.setter)
        self.pack_start(spin_button, False, False, 0)
        self.grab_focus = lambda : self.hook.get_focus(spin_button)

    def setter(self, widget):
        if str(widget.get_value_as_int()) != self.value:
            self.value = str(widget.get_value_as_int())
            self.set_value(self.value)
            widget.set_tooltip_text(None)
        return False
__WIDGET__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check widget reference checking with arguments.
TEST_KEY=$TEST_KEY_BASE-args-ok
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spin.SpinnerValueWidget something1 something2
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check widget reference checking with arguments.
TEST_KEY=$TEST_KEY_BASE-import-builtin-ok
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=rose.config_editor.valuewidget.intspin.IntSpinButtonValueWidget
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check widget not found checking.
TEST_KEY=$TEST_KEY_BASE-import-find-fail
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spinner.SpinnerValueWidget

[namelist:widget_nl=my_widget_var2]
widget[rose-config-edit]=spin.SpinnerSpinValueWidget
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 2
    namelist:widget_nl=my_widget_var1=widget[rose-config-edit]=spinner.SpinnerValueWidget
        Not found: spinner.SpinnerValueWidget
    namelist:widget_nl=my_widget_var2=widget[rose-config-edit]=spin.SpinnerSpinValueWidget
        Not found: spin.SpinnerSpinValueWidget
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check widget broken Python code checking.
TEST_KEY=$TEST_KEY_BASE-import-code-fail
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spin.SpinnerValueWidget
__META_CONFIG__
init_widget spin.py <<'__WIDGET__'
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
upper=sys.maxint,
lower=-sys.maxint - 1,
step_incr=1)
spin_button = gtk.SpinButton(adjustment=my_adj, digits=0)
spin_button.connect('focus-in-event',
self.hook.trigger_scroll)
spin_button.set_numeric(True)
spin_button.set_tooltip_text(tooltip_text)
spin_button.show()
self.change_id = spin_button.connect(
'value-changed',
self.setter)
self.pack_start(spin_button, False, False, 0)
self.grab_focus = lambda : self.hook.get_focus(spin_button)

def setter(self, widget):
if str(widget.get_value_as_int()) != self.value:
self.value = str(widget.get_value_as_int())
self.set_value(self.value)
widget.set_tooltip_text(None)
return False
__WIDGET__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:widget_nl=my_widget_var1=widget[rose-config-edit]=spin.SpinnerValueWidget
        Could not import spin.SpinnerValueWidget: IndentationError: expected an indented block (envswitch.py, line 37)
teardown
#-------------------------------------------------------------------------------
exit
