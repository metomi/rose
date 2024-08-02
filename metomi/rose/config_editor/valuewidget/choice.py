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

import ast
import shlex

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import rose.config_editor
import rose.gtk.choice
import rose.gtk.dialog
import rose.opt_parse
import rose.variable


class ChoicesValueWidget(Gtk.HBox):

    """This represents a value as actual/available choices.

    Arguments are standard, except for the custom arg_str argument,
    set in the metadata. In this case we take a shell command-like
    syntax:

    # NAME
    #     rose.config_editor.valuewidget.choice.ChoicesValueWidget
    #
    # SYNOPSIS
    #     rose...Widget [OPTIONS] [CUSTOM_CHOICE_HINT ...]
    #
    # DESCRIPTION
    #     Represent available choices as a widget.
    #
    # OPTIONS
    #     --all-group=CHOICE
    #         The CHOICE that includes all other choices.
    #         For example: ALL, STANDARD
    #     --choices=CHOICE1[,CHOICE2,CHOICE3...]
    #         Add a comma-delimited list of choice(s) to the list of
    #         available choices for the widget.
    #         This option can be used repeatedly.
    #     --editable
    #         Allow custom choices to be entered that are not in choices
    #     --format=FORMAT
    #         Specify a different format to convert the list of included
    #         choices into the variable value.
    #         The only supported format is "python" which outputs the
    #         result of repr(my_list) - e.g. VARIABLE=["A", "B"].
    #         If not specified, the format will default to rose array
    #         standard e.g. VARIABLE=A, B.
    #     --guess-groups
    #         Extrapolate inter-choice dependencies from their names.
    #         For example, this would guess that "LINUX" would trigger
    #         "LINUX_QUICK".
    #
    # CUSTOM_CHOICE_HINT
    #     Optional custom choice hints for the user, valid with --editable.
    """

    OPTIONS = {
        "all_group": [
            ["--all-group"],
            {"action": "store",
             "metavar": "CHOICE"}],
        "choices": [
            ["--choices"],
            {"action": "append",
             "default": None,
             "metavar": "CHOICE"}],
        "editable": [
            ["--editable"],
            {"action": "store_true",
             "default": False}],
        "format": [
            ["--format"],
            {"action": "store",
             "metavar": "FORMAT"}],
        "guess_groups": [
            ["--guess-groups"],
            {"action": "store_true",
             "default": False}]}

    def __init__(self, value, metadata, set_value, hook, arg_str=None):
        super(ChoicesValueWidget, self).__init__(homogeneous=False,
                                                 spacing=0)
        self.value = value
        self.metadata = metadata
        self.set_value = set_value
        self.hook = hook

        self.opt_parser = rose.opt_parse.RoseOptionParser()
        self.opt_parser.OPTIONS = self.OPTIONS
        self.opt_parser.add_my_options(*list(self.OPTIONS.keys()))
        opts, args = self.opt_parser.parse_args(shlex.split(arg_str))
        self.all_group = opts.all_group
        self.groups = []
        if opts.choices is not None:
            for choices in opts.choices:
                self.groups.extend(rose.variable.array_split(choices))
        self.should_edit = opts.editable
        self.value_format = opts.format
        self.should_guess_groups = opts.guess_groups
        self.hints = list(args)

        self.should_show_kinship = self._calc_should_show_kinship()
        list_vbox = Gtk.VBox()
        list_vbox.show()
        self._listview = rose.gtk.choice.ChoicesListView(
            self._set_value_listview,
            self._get_value_values,
            self._handle_search)
        self._listview.show()
        list_frame = Gtk.Frame()
        list_frame.show()
        list_frame.add(self._listview)
        list_vbox.pack_start(list_frame, expand=False, fill=False)
        self.pack_start(list_vbox, expand=True, fill=True)
        tree_vbox = Gtk.VBox()
        tree_vbox.show()
        self._treeview = rose.gtk.choice.ChoicesTreeView(
            self._set_value_treeview,
            self._get_value_values,
            self._get_available_values,
            self._get_groups,
            self._get_is_implicit)
        self._treeview.show()
        tree_frame = Gtk.Frame()
        tree_frame.show()
        tree_frame.add(self._treeview)
        tree_vbox.pack_start(tree_frame, expand=True, fill=True)
        if self.should_edit:
            add_widget = self._get_add_widget()
            tree_vbox.pack_end(add_widget, expand=False, fill=False)
        self.pack_start(tree_vbox, expand=True, fill=True)
        self._listview.connect('focus-in-event',
                               self.hook.trigger_scroll)
        self._treeview.connect('focus-in-event',
                               self.hook.trigger_scroll)
        self.grab_focus = lambda: self.hook.get_focus(self._listview)

    def _handle_search(self, name):
        return False

    def _get_add_widget(self):
        add_hbox = Gtk.HBox()
        add_entry = Gtk.ComboBoxEntry()
        add_entry.connect("changed", self._handle_combo_choice)
        add_entry.get_child().connect(
            "key-press-event",
            lambda w, e: self._handle_text_choice(add_entry, e))
        add_entry.set_tooltip_text(rose.config_editor.CHOICE_TIP_ENTER_CUSTOM)
        add_entry.show()
        self._set_available_hints(add_entry)
        add_hbox.pack_end(add_entry, expand=True, fill=True)
        add_hbox.show()
        return add_hbox

    def _set_available_hints(self, comboboxentry):
        model = Gtk.ListStore(str)
        values = self._get_value_values()
        for hint in self.hints:
            if hint not in values:
                model.append([hint])
        comboboxentry.set_model(model)
        comboboxentry.set_text_column(0)

    def _handle_combo_choice(self, comboboxentry):
        iter_ = comboboxentry.get_active_iter()
        if iter_ is None:
            return False
        self._add_custom_choice(comboboxentry, comboboxentry.get_active_text())

    def _handle_text_choice(self, comboboxentry, event):
        if Gdk.keyval_name(event.keyval) in ["Return", "KP_Enter"]:
            self._add_custom_choice(comboboxentry,
                                    comboboxentry.get_child().get_text())
        return False

    def _add_custom_choice(self, comboboxentry, new_name):
        entry = comboboxentry.get_child()
        if not new_name:
            text = rose.config_editor.ERROR_BAD_NAME.format("''")
            title = rose.config_editor.DIALOG_TITLE_ERROR
            rose.gtk.dialog.run_dialog(rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                       text, title)
            return False
        new_values = self._get_value_values() + [entry.get_text()]
        entry.set_text("")
        self._format_and_set_value(" ".join(new_values))
        self._set_available_hints(comboboxentry)
        self._listview.refresh()
        self._treeview.refresh()

    def _get_value_values(self):
        if self.value_format == "python":
            try:
                values = list(ast.literal_eval(self.value))
            except (SyntaxError, TypeError, ValueError):
                values = []
            return values
        return rose.variable.array_split(self.value)

    def _get_available_values(self):
        return self.groups

    def _calc_should_show_kinship(self):
        """Calculate whether to show parent-child relationships.

        Do not show any if any group has more than one parent group.

        """
        for group in self.groups:
            grpset = set(group)
            if len([g for g in self.groups if set(g).issubset(grpset)]) > 1:
                return False
        return True

    def _get_groups(self, name, names):
        if self.all_group is not None:
            default_groups = [self.all_group]
        default_groups = []
        if not self.should_guess_groups or not self.should_show_kinship:
            return default_groups
        ok_groups = [n for n in names if set(n).issubset(name) and n != name]
        ok_groups.sort(lambda x, y: set(x).issubset(y) - set(y).issubset(x))
        for group in default_groups:
            if group in ok_groups:
                ok_groups.remove(group)
        return default_groups + ok_groups

    def _get_is_implicit(self, name):
        if not self.should_guess_groups:
            return False
        values = self._get_value_values()
        if self.all_group in values:
            return True
        for group in self.groups:
            if group in values and set(group).issubset(name) and group != name:
                return True
        return False

    def _set_value_listview(self, new_value):
        if new_value != self.value:
            self._format_and_set_value(new_value)
        self._treeview.refresh()

    def _set_value_treeview(self, new_value):
        if new_value != self.value:
            self._format_and_set_value(new_value)
        self._listview.refresh()

    def _format_and_set_value(self, new_value):
        if self.value_format == "python":
            new_value = repr(shlex.split(new_value))
        else:
            new_value = rose.variable.array_join(shlex.split(new_value))
        self.value = new_value
        self.set_value(new_value)
