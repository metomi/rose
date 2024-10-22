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

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import metomi.rose.config_editor


class StackItem(object):
    """A dictionary containing stack information."""

    def __init__(
        self,
        page_label,
        action_text,
        node,
        undo_function,
        undo_args=None,
        group=None,
        custom_name=None,
    ):
        self.page_label = page_label
        self.action = action_text
        self.node = node
        if custom_name is None:
            self.name = self.node.name
        else:
            self.name = custom_name
        self.group = group
        if hasattr(self.node, "value"):
            self.value = self.node.value
            self.old_value = self.node.old_value
        else:
            self.value = ""
            self.old_value = ""
        self.undo_func = undo_function
        if undo_args is None:
            undo_args = []
        self.undo_args = undo_args

    def __repr__(self):
        return (
            self.action[0].lower()
            + self.action[1:]
            + " "
            + self.name
            + ", ".join([str(u) for u in self.undo_args])
        )


class StackViewer(Gtk.Window):
    """Window to dynamically display the internal stack."""

    def __init__(self, undo_stack, redo_stack, undo_func):
        """Load a view of the stack."""
        super(StackViewer, self).__init__()
        self.set_title(metomi.rose.config_editor.STACK_VIEW_TITLE)
        self.action_colour_map = {
            metomi.rose.config_editor.STACK_ACTION_ADDED: (
                metomi.rose.config_editor.COLOUR_STACK_ADDED
            ),
            metomi.rose.config_editor.STACK_ACTION_APPLIED: (
                metomi.rose.config_editor.COLOUR_STACK_APPLIED
            ),
            metomi.rose.config_editor.STACK_ACTION_CHANGED: (
                metomi.rose.config_editor.COLOUR_STACK_CHANGED
            ),
            metomi.rose.config_editor.STACK_ACTION_CHANGED_COMMENTS: (
                metomi.rose.config_editor.COLOUR_STACK_CHANGED_COMMENTS
            ),
            metomi.rose.config_editor.STACK_ACTION_ENABLED: (
                metomi.rose.config_editor.COLOUR_STACK_ENABLED
            ),
            metomi.rose.config_editor.STACK_ACTION_IGNORED: (
                metomi.rose.config_editor.COLOUR_STACK_IGNORED
            ),
            metomi.rose.config_editor.STACK_ACTION_REMOVED: (
                metomi.rose.config_editor.COLOUR_STACK_REMOVED
            ),
            metomi.rose.config_editor.STACK_ACTION_REVERSED: (
                metomi.rose.config_editor.COLOUR_STACK_REVERSED
            ),
        }
        self.undo_func = undo_func
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.set_border_width(metomi.rose.config_editor.SPACING_SUB_PAGE)
        self.main_vbox = Gtk.VPaned()
        accelerators = Gtk.AccelGroup()
        accel_key, accel_mods = Gtk.accelerator_parse("<Ctrl>Z")
        accelerators.connect(
            accel_key,
            accel_mods,
            Gtk.AccelFlags.VISIBLE,
            lambda a, b, c, d: self.undo_from_log(),
        )
        accel_key, accel_mods = Gtk.accelerator_parse("<Ctrl><Shift>Z")
        accelerators.connect(
            accel_key,
            accel_mods,
            Gtk.AccelFlags.VISIBLE,
            lambda a, b, c, d: self.undo_from_log(redo_mode_on=True),
        )
        self.add_accel_group(accelerators)
        self.set_default_size(*metomi.rose.config_editor.SIZE_STACK)
        self.undo_view = self.get_stack_view(redo_mode_on=False)
        self.redo_view = self.get_stack_view(redo_mode_on=True)
        undo_vbox = self.get_stack_view_box(self.undo_view, redo_mode_on=False)
        redo_vbox = self.get_stack_view_box(self.redo_view, redo_mode_on=True)
        self.main_vbox.pack1(undo_vbox, resize=True, shrink=True)
        self.main_vbox.show()
        self.main_vbox.pack2(redo_vbox, resize=False, shrink=True)
        self.main_vbox.show()
        self.undo_view.connect("size-allocate", self.scroll_view)
        self.redo_view.connect("size-allocate", self.scroll_view)
        self.add(self.main_vbox)
        self.show()

    def get_stack_view_box(self, log_buffer, redo_mode_on=False):
        """Return a frame containing a scrolled text view."""
        text_view = log_buffer
        text_scroller = Gtk.ScrolledWindow()
        text_scroller.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS
        )
        text_scroller.set_shadow_type(Gtk.ShadowType.IN)
        text_scroller.add(text_view)
        vadj = text_scroller.get_vadjustment()
        vadj.set_value(vadj.get_upper() - 0.9 * vadj.get_page_size())
        text_scroller.show()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        if redo_mode_on:
            label.set_text("REDO STACK")
            self.redo_text_view = text_view
        else:
            label.set_text("UNDO STACK")
            self.undo_text_view = text_view
        label.show()
        vbox.set_border_width(metomi.rose.config_editor.SPACING_SUB_PAGE)
        vbox.pack_start(
            label,
            expand=False,
            fill=True,
            padding=metomi.rose.config_editor.SPACING_SUB_PAGE,
        )
        vbox.pack_start(text_scroller, expand=True, fill=True, padding=0)
        vbox.show()
        return vbox

    def undo_from_log(self, redo_mode_on=False):
        """Drive the main program undo function and update."""
        self.undo_func(redo_mode_on)
        self.update()

    def get_stack_view(self, redo_mode_on=False):
        """Return a tree view with information from a stack."""
        stack_model = self.get_stack_model(redo_mode_on, make_new_model=True)
        stack_view = Gtk.TreeView(stack_model)
        columns = {}
        cell_text = {}
        for title in [
            metomi.rose.config_editor.STACK_COL_NS,
            metomi.rose.config_editor.STACK_COL_ACT,
            metomi.rose.config_editor.STACK_COL_NAME,
            metomi.rose.config_editor.STACK_COL_VALUE,
            metomi.rose.config_editor.STACK_COL_OLD_VALUE,
        ]:
            columns[title] = Gtk.TreeViewColumn()
            columns[title].set_title(title)
            cell_text[title] = Gtk.CellRendererText()
            columns[title].pack_start(cell_text[title], True)
            columns[title].add_attribute(
                cell_text[title],
                attribute="markup",
                column=len(list(columns.keys())) - 1,
            )
            stack_view.append_column(columns[title])
        stack_view.show()
        return stack_view

    def get_stack_model(self, redo_mode_on=False, make_new_model=False):
        """Return a Gtk.ListStore generated from a stack."""
        stack = [self.undo_stack, self.redo_stack][redo_mode_on]
        if make_new_model:
            model = Gtk.ListStore(str, str, str, str, str, bool)
        else:
            model = [self.undo_view.get_model(), self.redo_view.get_model()][
                redo_mode_on
            ]
        model.clear()
        for stack_item in stack:
            marked_up_action = stack_item.action
            if stack_item.action in self.action_colour_map:
                colour = self.action_colour_map[stack_item.action]
                marked_up_action = (
                    "<span foreground='"
                    + colour
                    + "'>"
                    + stack_item.action
                    + "</span>"
                )
            if stack_item.page_label is None:
                short_label = "None"
            else:
                short_label = re.sub("^/[^/]+/", "", stack_item.page_label)
            model.append(
                (
                    short_label,
                    marked_up_action,
                    stack_item.name,
                    repr(stack_item.value),
                    repr(stack_item.old_value),
                    False,
                )
            )
        return model

    def scroll_view(self, tree_view, event=None):
        """Scroll the parent scrolled window to the bottom."""
        vadj = tree_view.get_parent().get_vadjustment()
        if vadj.get_upper() > vadj.get_lower() + vadj.get_page_size():
            vadj.set_value(vadj.get_upper() - 0.95 * vadj.get_page_size())

    def update(self):
        """Reload text views from the undo and redo stacks."""
        if self.undo_text_view.get_parent() is None:
            return
        self.get_stack_model(redo_mode_on=False)
        self.get_stack_model(redo_mode_on=True)
