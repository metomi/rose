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

import re

import rose
from . import array.entry
from . import array.mixed
from . import array.logical
from . import array.python_list
from . import array.spaced_list
from . import booltoggle
from . import character
from . import combobox
from . import files
from . import intspin
from . import meta
from . import radiobuttons
from . import text
from . import valuehints


NON_TEXT_TYPES = ('boolean', 'integer', 'logical', 'python_boolean',
                  'python_list', 'real', 'spaced_list')


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
    """Select an appropriate widget class based on the arguments.

    Note: rose edit overrides this logic if a widget is hard coded.

    """
    m_type = metadata.get(metomi.rose.META_PROP_TYPE)
    m_values = metadata.get(metomi.rose.META_PROP_VALUES)
    m_length = metadata.get(metomi.rose.META_PROP_LENGTH)
    m_hint = metadata.get(metomi.rose.META_PROP_VALUE_HINTS)
    contains_env = metomi.rose.env.contains_env_var(value)
    is_list = m_length is not None or isinstance(m_type, list)

    # determine widget by presence of environment variables
    if contains_env and (not m_type or m_type in NON_TEXT_TYPES or is_list):
        # it is not safe to display the widget as intended due to an env var
        if '\n' in value:
            return text.TextMultilineValueWidget
        else:
            return text.RawValueWidget

    # determine widget by metadata length
    if is_list:
        if isinstance(m_type, list):
            # irregular array
            return array.mixed.MixedArrayValueWidget
        elif m_type in ['logical', 'boolean', 'python_boolean']:
            # regular array (boolean)
            return array.logical.LogicalArrayValueWidget
        else:
            # regular array (generic)
            return array.entry.EntryArrayValueWidget

    # determine widget by metadata values
    if m_values is not None:
        if len(m_values) <= 4:
            # short list
            return radiobuttons.RadioButtonsValueWidget
        else:
            # long list
            return combobox.ComboBoxValueWidget

    # determine widget by metadata type
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
    if m_type in ['logical', 'boolean', 'python_boolean']:
        return booltoggle.BoolToggleValueWidget

    # determine widget by metadata hint
    if m_hint is not None:
        return valuehints.HintsValueWidget

    # fall back to a text widget
    if '\n' in value:
        return text.TextMultilineValueWidget
    else:
        return text.RawValueWidget
