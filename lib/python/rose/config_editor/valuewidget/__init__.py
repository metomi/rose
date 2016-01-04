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

import re

import rose
import array.entry
import array.mixed
import array.logical
import array.python_list
import array.spaced_list
import booltoggle
import character
import combobox
import files
import intspin
import meta
import radiobuttons
import text
import valuehints


class ValueWidgetHook(object):

    """Provides hook functions for valuewidgets."""

    def __init__(self, scroll_func=None, focus_func=None):
        """Set up commonly used valuewidget hook functions."""
        self._scroll_func = scroll_func
        self._focus_func = focus_func

    def trigger_scroll(self, widget, event):
        """Set up top-level scrolling on a widget event."""
        if self._scroll_func is None:
            return False
        return self._scroll_func(widget, event)

    def get_focus(self, widget):
        """Set up a trigger based on focusing for a widget."""
        if self._focus_func is None:
            return widget.grab_focus()
        return self._focus_func(widget)

    def copy(self):
        """Return a copy of this instance."""
        return ValueWidgetHook(self.trigger_scroll, self.get_focus)


def chooser(value, metadata, error):
    """Select an appropriate widget class based on the arguments."""
    if rose.env.contains_env_var(value):
        return text.RawValueWidget
    m_type = metadata.get(rose.META_PROP_TYPE)
    m_values = metadata.get(rose.META_PROP_VALUES)
    m_length = metadata.get(rose.META_PROP_LENGTH)
    m_hint = metadata.get(rose.META_PROP_VALUE_HINTS)
    if (m_type is None and m_values is None and m_length is None and
       m_hint is None):
        return text.RawValueWidget
    if (m_values is None and m_length is None and m_hint is None and
       m_type in ['logical', 'boolean', 'python_boolean']):
        return booltoggle.BoolToggleValueWidget
    if m_length is None:
        if m_values is not None and len(m_values) <= 4:
            return radiobuttons.RadioButtonsValueWidget
        if m_values is not None and len(m_values) > 4:
            return combobox.ComboBoxValueWidget
    elif type(m_type) is not list:
        if m_type in ['logical', 'boolean']:
            return array.logical.LogicalArrayValueWidget
        return array.entry.EntryArrayValueWidget
    if m_type == 'integer':
        return intspin.IntSpinButtonValueWidget
    if m_type == 'meta':
        return meta.MetaValueWidget
    if m_type == 'str_multi':
        return text.TextMultilineValueWidget
    if m_type in ["character", "quoted"]:
        return character.QuotedTextValueWidget
    if m_type == "python_list" and not error:
        return array.python_list.PythonListValueWidget
    if m_type == "spaced_list" and not error:
        return array.spaced_list.SpacedListValueWidget
    if type(m_type) is list:
        return array.mixed.MixedArrayValueWidget
    if m_hint is not None:
        return valuehints.HintsValueWidget
    return text.RawValueWidget
