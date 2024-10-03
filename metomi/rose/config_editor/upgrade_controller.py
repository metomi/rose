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

import copy
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

import metomi.rose.gtk.util
import metomi.rose.macro
import metomi.rose.upgrade


class UpgradeController(object):

    """Configure the upgrade of configurations."""

    def __init__(self, app_config_dict, handle_transform_func,
                 parent_window=None, upgrade_inspector=None):
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                   Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)
        self.window = Gtk.Dialog(buttons=buttons)
        self.set_transient_for(parent_window)
        self.window.set_title(metomi.rose.config_editor.DIALOG_TITLE_UPGRADE)
        self.config_dict = {}
        self.config_directory_dict = {}
        self.config_manager_dict = {}
        config_names = sorted(app_config_dict.keys())
        self._config_version_model_dict = {}
        self.use_all_versions = False
        self.treemodel = Gtk.TreeStore(str, str, str, bool)
        self.treeview = metomi.rose.gtk.util.TooltipTreeView(
            get_tooltip_func=self._get_tooltip)
        self.treeview.show()
        old_pwd = os.getcwd()
        for config_name in config_names:
            app_config = app_config_dict[config_name]["config"]
            app_directory = app_config_dict[config_name]["directory"]
            meta_value = app_config.get_value([metomi.rose.CONFIG_SECT_TOP,
                                               metomi.rose.CONFIG_OPT_META_TYPE], "")
            if len(meta_value.split("/")) < 2:
                continue
            try:
                os.chdir(app_directory)
                manager = metomi.rose.upgrade.MacroUpgradeManager(app_config)
            except OSError:
                # This can occur when access is not allowed to metadata files.
                continue
            self.config_dict[config_name] = app_config
            self.config_directory_dict[config_name] = app_directory
            self.config_manager_dict[config_name] = manager
            self._update_treemodel_data(config_name)
        os.chdir(old_pwd)
        self.treeview.set_model(self.treemodel)
        self.treeview.set_rules_hint(True)
        self.treewindow = Gtk.ScrolledWindow()
        self.treewindow.show()
        self.treewindow.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.NEVER)
        columns = metomi.rose.config_editor.DIALOG_COLUMNS_UPGRADE
        for i, title in enumerate(columns):
            column = Gtk.TreeViewColumn()
            column.set_title(title)
            if self.treemodel.get_column_type(i) == GObject.TYPE_BOOLEAN:
                cell = Gtk.CellRendererToggle()
                cell.connect("toggled", self._handle_toggle_upgrade, i)
                cell.set_property("activatable", True)
            elif i == 2:
                self._combo_cell = Gtk.CellRendererCombo()
                self._combo_cell.set_property("has-entry", False)
                self._combo_cell.set_property("editable", True)
                self._combo_cell.connect("changed",
                                         self._handle_change_version, 2)
                cell = self._combo_cell
            else:
                cell = Gtk.CellRendererText()
            if i == len(columns) - 1:
                column.pack_start(cell, True, True, 0)
            else:
                column.pack_start(cell, False, True, 0)
            column.set_cell_data_func(cell, self._set_cell_data, i)
            self.treeview.append_column(column)
        self.treeview.connect("cursor-changed", self._handle_change_cursor)
        self.treewindow.add(self.treeview)
        self.window.vbox.pack_start(
            self.treewindow, expand=True, fill=True,
            padding=metomi.rose.config_editor.SPACING_PAGE)
        label = Gtk.Label(label=metomi.rose.config_editor.DIALOG_LABEL_UPGRADE)
        label.show()
        self.window.vbox.pack_start(
            label, True, True, metomi.rose.config_editor.SPACING_PAGE)
        button_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_hbox.show()
        all_versions_toggle_button = Gtk.CheckButton(
            label=metomi.rose.config_editor.DIALOG_LABEL_UPGRADE_ALL,
            use_underline=False)
        all_versions_toggle_button.set_active(self.use_all_versions)
        all_versions_toggle_button.connect("toggled",
                                           self._handle_toggle_all_versions)
        all_versions_toggle_button.show()
        button_hbox.pack_start(all_versions_toggle_button, expand=False,
                               fill=False,
                               padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        self.window.vbox.pack_end(button_hbox, expand=False, fill=False, padding=0)
        self.ok_button = self.window.action_area.get_children()[0]
        self.window.set_focus(all_versions_toggle_button)
        self.window.set_focus(self.ok_button)
        self._set_ok_to_upgrade()
        max_size = metomi.rose.config_editor.SIZE_MACRO_DIALOG_MAX
        my_size = self.window.size_request()
        new_size = [-1, -1]
        extra = 2 * metomi.rose.config_editor.SPACING_PAGE
        for i in [0, 1]:
            new_size[i] = min([my_size[i] + extra, max_size[i]])
        self.treewindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.window.set_default_size(*new_size)
        response = self.window.run()
        old_pwd = os.getcwd()
        if response == Gtk.ResponseType.ACCEPT:
            iter_ = self.treemodel.get_iter_first()
            while iter_ is not None:
                config_name = self.treemodel.get_value(iter_, 0)
                curr_version = self.treemodel.get_value(iter_, 1)
                next_version = self.treemodel.get_value(iter_, 2)
                ok_to_upgrade = self.treemodel.get_value(iter_, 3)
                config = self.config_dict[config_name]
                manager = self.config_manager_dict[config_name]
                directory = self.config_directory_dict[config_name]
                if not ok_to_upgrade or next_version == curr_version:
                    iter_ = self.treemodel.iter_next(iter_)
                    continue
                os.chdir(directory)
                manager.set_new_tag(next_version)
                macro_config = copy.deepcopy(config)
                try:
                    new_config, change_list = manager.transform(
                        macro_config, custom_inspector=upgrade_inspector)
                except Exception as exc:
                    metomi.rose.gtk.dialog.run_dialog(
                        metomi.rose.gtk.dialog.DIALOG_TYPE_ERROR,
                        type(exc).__name__ + ": " + str(exc),
                        metomi.rose.config_editor.ERROR_UPGRADE.format(
                            config_name.lstrip("/"))
                    )
                    iter_ = self.treemodel.iter_next(iter_)
                    continue
                macro_id = (type(manager).__name__ + "." +
                            metomi.rose.macro.TRANSFORM_METHOD)
                if handle_transform_func(config_name, macro_id,
                                         new_config, change_list,
                                         triggers_ok=True):
                    meta_config = metomi.rose.macro.load_meta_config(
                        new_config, config_type=metomi.rose.SUB_CONFIG_NAME,
                        ignore_meta_error=True
                    )
                    trig_macro = metomi.rose.macros.trigger.TriggerMacro()
                    macro_config = copy.deepcopy(new_config)
                    macro_id = (
                        metomi.rose.upgrade.MACRO_UPGRADE_TRIGGER_NAME + "." +
                        metomi.rose.macro.TRANSFORM_METHOD
                    )
                    if not trig_macro.validate_dependencies(macro_config,
                                                            meta_config):
                        new_trig_config, trig_change_list = (
                            metomi.rose.macros.trigger.TriggerMacro().transform(
                                macro_config, meta_config)
                        )
                        handle_transform_func(config_name, macro_id,
                                              new_trig_config,
                                              trig_change_list,
                                              triggers_ok=True)
                iter_ = self.treemodel.iter_next(iter_)
        os.chdir(old_pwd)
        self.window.destroy()

    def _get_tooltip(self, view, row_iter, col_index, tip):
        name = self.treeview.get_column(col_index).get_title()
        value = str(self.treemodel.get_value(row_iter, col_index))
        tip.set_text(name + ": " + value)
        return True

    def _handle_change_cursor(self, view):
        path = self.treeview.get_cursor()[0]
        iter_ = self.treemodel.get_iter(path)
        config_name = self.treemodel.get_value(iter_, 0)
        listmodel = self._config_version_model_dict[config_name]
        self._combo_cell.set_property("model", listmodel)
        self._combo_cell.set_property("text-column", 0)

    def _handle_change_version(self, cell, path, new, col_index):
        iter_ = self.treemodel.get_iter(path)
        if isinstance(new, str):
            new_value = new
        else:
            new_value = cell.get_property("model").get_value(new, 0)
        self.treemodel.set_value(iter_, col_index, new_value)

    def _handle_toggle_all_versions(self, button):
        self.use_all_versions = button.get_active()
        self.treemodel = Gtk.TreeStore(str, str, str, bool)
        self._config_version_model_dict.clear()
        for config_name in sorted(self.config_dict.keys()):
            self._update_treemodel_data(config_name)
        self.treeview.set_model(self.treemodel)
        self._set_ok_to_upgrade()

    def _handle_toggle_upgrade(self, cell, path, col_index):
        iter_ = self.treemodel.get_iter(path)
        value = self.treemodel.get_value(iter_, col_index)
        if (self.treemodel.get_value(iter_, 1) ==
                self.treemodel.get_value(iter_, 2)):
            self.treemodel.set_value(iter_, col_index, False)
        else:
            self.treemodel.set_value(iter_, col_index, not value)
        self._set_ok_to_upgrade()

    def _set_ok_to_upgrade(self, *args):
        any_upgrades_toggled = False
        iter_ = self.treemodel.get_iter_first()
        while iter_ is not None:
            if self.treemodel.get_value(iter_, 3):
                any_upgrades_toggled = True
                break
            iter_ = self.treemodel.iter_next(iter_)
        self.ok_button.set_sensitive(any_upgrades_toggled)

    def _set_cell_data(self, column, cell, model, r_iter, col_index):
        if model.get_column_type(col_index) == GObject.TYPE_BOOLEAN:
            cell.set_property("active", model.get_value(r_iter, col_index))
            if model.get_value(r_iter, 1) == model.get_value(r_iter, 2):
                model.set_value(r_iter, col_index, False)
                cell.set_property("inconsistent", True)
                cell.set_property("sensitive", False)
            else:
                cell.set_property("inconsistent", False)
                cell.set_property("sensitive", True)
        elif col_index == 2:
            cell.set_property("text", model.get_value(r_iter, 2))
        else:
            text = model.get_value(r_iter, col_index)
            if col_index == 0:
                text = text.lstrip("/")
            cell.set_property("text", text)

    def _update_treemodel_data(self, config_name):
        manager = self.config_manager_dict[config_name]
        current_tag = manager.tag
        next_tag = manager.get_new_tag(only_named=not self.use_all_versions)
        if next_tag is None:
            self.treemodel.append(
                None, [config_name, current_tag, current_tag, False])
        else:
            self.treemodel.append(
                None, [config_name, current_tag, next_tag, True])
        listmodel = Gtk.ListStore(str)
        tags = manager.get_tags(only_named=not self.use_all_versions)
        if not tags:
            tags = [manager.tag]
        for tag in tags:
            listmodel.append([tag])
        self._config_version_model_dict[config_name] = listmodel
