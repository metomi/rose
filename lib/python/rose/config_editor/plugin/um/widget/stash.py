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

import ast
import os
import re
import sys

import pango
import pygtk
pygtk.require("2.0")
import gtk

import rose.config
import rose.config_editor.panelwidget.standard
import rose.gtk.util
import rose.config_editor.plugin.um.widget.stash_add


class BaseStashSummaryDataPanelv1(
          rose.config_editor.panelwidget.standard.BaseSummaryDataPanel):

    """This is a base class for displaying and editing STASH requests.
    
    It adds editing capability for option values, displays metadata
    fetched from the STASHmaster file, and can launch a custom dialog
    for adding/removing STASH requests.

    Subclasses *must* provide the following method:
    def get_stashmaster_lookup_dict(self):
    which should return a nested dictionary containing STASHmaster file
    information.

    Subclasses *must* override the STASH_PACKAGE_PATH attribute with an
    absolute path to a directory containing a rose-app.conf file with
    STASH request package information.
    
    Subclasses should override the STASHMASTER_PATH attribute with an
    absolute path to a directory containing e.g. the STASHmaster_A
    file. An argument to the widget metadata option can also be used to
    provide this information.

    """

    # These attributes must/should be overridden:
    STASH_PACKAGE_PATH = None
    STASHMASTER_PATH = None

    # These attributes are generic titles.
    ADD_NEW_STASH_LABEL = "New"
    ADD_NEW_STASH_TIP = "Launch a window for adding new STASH requests"
    ADD_NEW_STASH_WINDOW_TITLE = "Add new STASH requests"
    DESCRIPTION_TITLE = "Info"
    INCLUDED_TITLE = "Incl?"
    PACKAGE_MANAGER_LABEL = "Packages"
    PACKAGE_MANAGER_TIP = "Launch a menu for managing groups of requests"
    SECTION_INDEX_TITLE = "Index"
    VIEW_MANAGER_LABEL = "View"
    VIEW_MANAGER_TIP = "Change view options"

    # The title property name for a request (must match the parser's one).
    STASH_PARSE_DESC_OPT = "name"

    # These attributes are namelist/UM-input specific.
    STREQ_NL_BASE = "namelist:streq"
    STREQ_NL_SECT_OPT = "isec"
    STREQ_NL_ITEM_OPT = "item"
    OPTION_NL_MAP = {"dom_name": "namelist:domain",
                     "tim_name": "namelist:time",
                     "use_name": "namelist:use"}

    def __init__(self, *args, **kwargs):
        self.stashmaster_directory_path = kwargs.get("arg_str", "")
        if not self.stashmaster_directory_path:
            self.stashmaster_directory_path = self.STASHMASTER_PATH
        self.load_stash()
        super(BaseStashSummaryDataPanelv1, self).__init__(*args, **kwargs)
        self._add_new_diagnostic_launcher()

    def add_cell_renderer_for_value(self, col, col_title):
        """Add a cell renderer type based on the column."""
        self._update_available_profiles()
        if col_title in self.OPTION_NL_MAP:
            cell_for_value = gtk.CellRendererCombo()
            listmodel = gtk.ListStore(str)
            values = sorted(self._available_profile_map[col_title])
            for possible_value in values:
                listmodel.append([possible_value])
            cell_for_value.set_property("has-entry", False)
            cell_for_value.set_property("editable", True)
            cell_for_value.set_property("model", listmodel)
            cell_for_value.set_property("text-column", 0)
            cell_for_value.connect("changed",
                                   self._handle_cell_combo_change,
                                   col_title)
            col.pack_start(cell_for_value, expand=True)
            col.set_cell_data_func(cell_for_value,
                                   self._set_tree_cell_value_combo)
        elif col_title == self.INCLUDED_TITLE:
            cell_for_value = gtk.CellRendererToggle()
            col.pack_start(cell_for_value, expand=False)
            cell_for_value.set_property("activatable", True)
            cell_for_value.connect("toggled",
                                   self._handle_cell_toggle_change)
            col.set_cell_data_func(cell_for_value,
                                   self._set_tree_cell_value_toggle)
        else:
            cell_for_value = gtk.CellRendererText()
            col.pack_start(cell_for_value, expand=True)
            if (col_title not in [self.SECTION_INDEX_TITLE,
                                  self.DESCRIPTION_TITLE]):
                cell_for_value.set_property("editable", True)
                cell_for_value.connect("edited",
                                       self._handle_cell_text_change,
                                       col_title)
            col.set_cell_data_func(cell_for_value,
                                   self._set_tree_cell_value)

    def get_stashmaster_lookup_dict(self):
        """Return a nested dictionary with STASHmaster info.

        Record properties are stored under section_number =>
        item_number => property_name.
        
        For example, if the nested dictionary is called 'stash_dict':
        stash_dict[section_number][item_number]['name']
        would be something like:
        "U COMPNT OF WIND AFTER TIMESTEP"

        Subclasses must provide (override) this method.
        The attribute self.stashmaster_directory_path may be used.

        """
        raise NotImplementedError()

    def load_stash(self):
        """Load a STASHmaster file into data structures for later use."""
        self._stash_lookup = self.get_stashmaster_lookup_dict()
        package_config_file = os.path.join(self.STASH_PACKAGE_PATH,
                                           rose.SUB_CONFIG_NAME)
        self.package_config = rose.config.ConfigLoader().load_with_opts(
                                          package_config_file)
        self.generate_package_lookup()

    def generate_package_lookup(self):
        """Store a dictionary of package requests and domains."""
        self._package_lookup = {}
        self._package_profile_lookup = {}
        package_profiles = {}
        for sect, node in self.package_config.value.items():
            if not isinstance(node.value, dict) or node.is_ignored():
                continue
            base_sect = sect.rsplit("(", 1)[0]
            if base_sect == self.STREQ_NL_BASE:
                package_node = node.get(["package"], no_ignore=True)
                if package_node is not None:
                    package = package_node.value
                    self._package_lookup.setdefault(package, {})
                    self._package_lookup[package].setdefault(base_sect, [])
                    self._package_lookup[package][base_sect].append(sect)
                    for prof in self.OPTION_NL_MAP:
                        prof_node = node.get([prof], no_ignore=True)
                        if prof_node is not None:
                            self._package_lookup[package].setdefault(prof, [])
                            self._package_lookup[package][prof].append(
                                                          prof_node.value)
                continue
            for prof, prof_nl in self.OPTION_NL_MAP.items():
                if base_sect == prof_nl:
                    name_node = node.get([prof], no_ignore=True)
                    if name_node is not None:
                        name = name_node.value
                        self._package_profile_lookup.setdefault(prof, {})
                        self._package_profile_lookup[prof][name] = sect
                    break

    def get_model_data(self):
        """Construct a data model of other page data."""
        sub_sect_names = self.sections.keys()
        sub_var_names = []
        self.var_id_map = {}
        section_sect_item = {}
        for section, variables in self.variables.items():
            for variable in variables:
                self.var_id_map[variable.metadata["id"]] = variable
                if variable.name not in sub_var_names:
                    sub_var_names.append(variable.name)
                if variable.name == self.STREQ_NL_SECT_OPT:
                    section_sect_item.setdefault(section, [])
                    try:
                        value = int(variable.value)
                    except (TypeError, ValueError):
                        value = variable.value
                    if len(section_sect_item[section]) < 1:
                        section_sect_item[section].append(None)
                    section_sect_item[section][0] = value
                if variable.name == self.STREQ_NL_ITEM_OPT:
                    section_sect_item.setdefault(section, [])
                    try:
                        value = int(variable.value)
                    except (TypeError, ValueError):
                        value = variable.value
                    if len(section_sect_item[section]) < 2:
                        section_sect_item[section].append(None)
                    section_sect_item[section].append(value)
        sub_sect_names.sort(lambda x, y: cmp(section_sect_item.get(x),
                                             section_sect_item.get(y)))
        sub_var_names.sort(rose.config.sort_settings)
        sub_var_names.sort(lambda x, y: (y != "package") -
                                        (x != "package"))
        sub_var_names.sort(lambda x, y: (y == self.STREQ_NL_ITEM_OPT) -
                                        (x == self.STREQ_NL_ITEM_OPT))
        sub_var_names.sort(lambda x, y: (y == self.STREQ_NL_SECT_OPT) -
                                        (x == self.STREQ_NL_SECT_OPT))
        data_rows = []
        for section in sub_sect_names:
            row_data = []
            stash_sect_id = self.util.get_id_from_section_option(
                                             section, self.STREQ_NL_SECT_OPT)
            stash_item_id = self.util.get_id_from_section_option(
                                             section, self.STREQ_NL_ITEM_OPT)
            sect_var = self.var_id_map.get(stash_sect_id)
            item_var = self.var_id_map.get(stash_item_id)
            stash_props = None
            if sect_var is not None and item_var is not None:
                stash_props = self._stash_lookup.get(sect_var.value, {}).get(
                                                     item_var.value)
            if stash_props is None:
                row_data.append(None)
            else:
                desc = stash_props[self.STASH_PARSE_DESC_OPT].strip()
                row_data.append(desc)
            is_enabled = (rose.variable.IGNORED_BY_USER not in
                          self.sections[section].ignored_reason)
            row_data.append(str(is_enabled))
            for opt in sub_var_names:
                id_ = self.util.get_id_from_section_option(section, opt)
                var = self.var_id_map.get(id_)
                if var is None:
                    row_data.append(None)
                else:
                    row_data.append(rose.gtk.util.safe_str(var.value))
            row_data.append(section)
            data_rows.append(row_data)
        column_names = [self.DESCRIPTION_TITLE, self.INCLUDED_TITLE]
        column_names += sub_var_names + [self.SECTION_INDEX_TITLE]
        return data_rows, column_names
 
    def set_tree_cell_status(self, col, cell, model, row_iter):
        # Set the status-related markup for a cell.
        col_index = self._view.get_columns().index(col)
        sect_index = self.get_section_column_index()
        section = model.get_value(row_iter, sect_index)
        if section is None:
            return cell.set_property("markup", None)
        if col_index == sect_index:
            node_data = self.sections.get(section)
        else:
            option = self.column_names[col_index]
            if option is None:
                return cell.set_property("markup", None)
            id_ = self.util.get_id_from_section_option(section, option)
            node_data = self.var_id_map.get(id_)
        cell.set_property("markup",
                          self._get_status_from_data(node_data))

    def set_tree_tip(self, view, row_iter, col_index, tip):
        """Set the TreeView Tooltip."""
        sect_index = self.get_section_column_index()
        section = view.get_model().get_value(row_iter, sect_index)
        if section is None:
            return False
        if col_index == sect_index:
            option = None
            if section not in self.sections:
                return False
            id_data = self.sections[section]
            tip_text = section
        else:
            option = self.column_names[col_index]
            id_ = self.util.get_id_from_section_option(section, option)
            if (id_ not in self.var_id_map and
                option in [self.DESCRIPTION_TITLE, self.INCLUDED_TITLE]):
                tip.set_text(
                        str(view.get_model().get_value(row_iter, col_index)))
                return True
            id_data = self.var_id_map[id_]
            value = str(view.get_model().get_value(row_iter, col_index))
            tip_text = rose.CONFIG_DELIMITER.join([section, option, value]) + "\n"
            if option in self.OPTION_NL_MAP:
                prof_id = self._profile_location_map[option].get(value)
                if prof_id is not None:
                    prof_sect = self.util.get_section_option_from_id(prof_id)[0]
                    tip_text += "See " + prof_sect
        tip_text += id_data.metadata.get(rose.META_PROP_DESCRIPTION, "")
        if tip_text:
            tip_text += "\n"
        for key, value in id_data.error.items():
            tip_text += (
                    rose.config_editor.SUMMARY_DATA_PANEL_ERROR_TIP.format(
                                                                key, value))
        for key in id_data.ignored_reason:
            tip_text += key + "\n"
        if option is not None:
            change_text = self.var_ops.get_var_changes(id_data)
            tip_text += change_text + "\n"
        tip.set_text(tip_text.rstrip())
        return True

    def _add_new_diagnostic_launcher(self):
        # Create a button for launching the Add new STASH dialog.
        add_button = rose.gtk.util.CustomButton(
                                   label=self.ADD_NEW_STASH_LABEL,
                                   stock_id=gtk.STOCK_ADD,
                                   tip_text=self.ADD_NEW_STASH_TIP)
        package_button = rose.gtk.util.CustomButton(
                                       label=self.PACKAGE_MANAGER_LABEL,
                                       tip_text=self.PACKAGE_MANAGER_TIP)
        arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
        arrow.show()
        package_button.hbox.pack_start(arrow, expand=False, fill=False)
        eb = gtk.EventBox()
        eb.show()
        self.control_widget_hbox.pack_start(eb, expand=True, fill=True)
        self.control_widget_hbox.pack_start(add_button, expand=False, fill=False)
        self.control_widget_hbox.pack_start(package_button, expand=False,
                                            fill=False)
        eb = gtk.EventBox()
        eb.show()
        self.control_widget_hbox.pack_start(eb, expand=True, fill=True)
        add_button.connect("clicked", self._launch_new_diagnostic_window)
        package_button.connect("button-press-event",
                               self._launch_package_menu)

    def _handle_cell_combo_change(self, combo_cell, path_string, combo_iter,
                                  col_title):
        # Handle a gtk.CellRendererCombo (variable) value change.
        new_value = combo_cell.get_property("model").get_value(combo_iter, 0)
        row_iter = self._view.get_model().get_iter(path_string)
        sect_index = self.get_section_column_index()
        section = self._view.get_model().get_value(row_iter, sect_index)
        option = col_title
        id_ = self.util.get_id_from_section_option(section, option)
        var = self.var_id_map[id_]
        self.var_ops.set_var_value(var, new_value)
        return False

    def _handle_cell_text_change(self, text_cell, path_string, new_text,
                                 col_title):
        # Handle a gtk.CellRendererText (variable) value change.
        row_iter = self._view.get_model().get_iter(path_string)
        sect_index = self.get_section_column_index()
        section = self._view.get_model().get_value(row_iter, sect_index)
        option = col_title
        id_ = self.util.get_id_from_section_option(section, option)
        var = self.var_id_map[id_]
        self.var_ops.set_var_value(var, new_text)
        return False

    def _handle_cell_toggle_change(self, combo_cell, path_string):
        # Handle a gtk.CellRendererToggle value change.
        was_active = combo_cell.get_property("active")
        row_iter = self._view.get_model().get_iter(path_string)
        sect_index = self.get_section_column_index()
        section = self._view.get_model().get_value(row_iter, sect_index)
        if section is None:
            return False
        is_active = not was_active
        combo_cell.set_property("active", is_active)
        self.sub_ops.ignore_section(section, not is_active)
        return False

    def _set_tree_cell_value_combo(self, column, cell, treemodel, iter_):
        cell.set_property("visible", True)
        cell.set_property("editable", True)
        col_index = self._view.get_columns().index(column)
        value = self._view.get_model().get_value(iter_, col_index)
        if value is None:
            cell.set_property("editable", False)
            cell.set_property("text", None)
            cell.set_property("visible", False)
        max_len = rose.config_editor.SUMMARY_DATA_PANEL_MAX_LEN
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        cell.set_property("text", value)

    def _set_tree_cell_value_toggle(self, column, cell, treemodel, iter_):
        cell.set_property("visible", True)
        col_index = self._view.get_columns().index(column)
        value = self._view.get_model().get_value(iter_, col_index)
        if value is None:
            cell.set_property("visible", False)
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        try:
            value = ast.literal_eval(value)
        except ValueError:
            return False
        cell.set_property("active", value)

    def _set_tree_cell_value(self, column, cell, treemodel, iter_):
        cell.set_property("visible", True)
        col_index = self._view.get_columns().index(column)
        value = self._view.get_model().get_value(iter_, col_index)
        if value is None:
            cell.set_property("markup", None)
            cell.set_property("visible", False)
        max_len = rose.config_editor.SUMMARY_DATA_PANEL_MAX_LEN
        if (value is not None and len(value) > max_len
            and col_index != 0):
            cell.set_property("width-chars", max_len)
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        sect_index = self.get_section_column_index()
        if (value is not None and col_index == sect_index and
            self.is_duplicate):
            value = value.split("(")[-1].rstrip(")")
        if col_index == 0 and treemodel.iter_parent(iter_) is not None:
            cell.set_property("visible", False)
        cell.set_property("markup", rose.gtk.util.safe_str(value))

    def _update_available_profiles(self):
        # Retrieve which profiles (namelists like domain) are available.
        self._available_profile_map = {}
        self._profile_location_map = {}
        ok_var_names = self.OPTION_NL_MAP.keys()
        ok_sect_names = self.OPTION_NL_MAP.values()
        for name in ok_var_names:
            self._available_profile_map[name] = []
        for id_, value in self.sub_ops.get_var_id_values().items():
            section, option = self.util.get_section_option_from_id(id_)
            if (option in ok_var_names and
                any([section.startswith(n) for n in ok_sect_names])):
                self._profile_location_map.setdefault(option, {})
                self._profile_location_map[option].update({value: id_})
                self._available_profile_map.setdefault(option, [])
                self._available_profile_map[option].append(value)
        for profile_names in self._available_profile_map.values():
            profile_names.sort()

    def _get_custom_menu_items(self, path, col, event):
        # Add some custom menu items to the TreeView rightclick menu.
        menuitems = []
        model = self._view.get_model()
        col_index = self._view.get_columns().index(col)
        col_title = self.column_names[col_index]
        if col_title not in self.OPTION_NL_MAP:
            return []
        iter_ = model.get_iter(path)
        value = model.get_value(iter_, col_index)
        location = self._profile_location_map[col_title][value]
        profile_id = self._profile_location_map[col_title][value]
        profile_string = ""
        profile_actions = []
        profile_action_location_map = {}
        menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
        menuitem.set_label(label="View " + value.strip("'"))
        menuitem._loc_id = location
        menuitem.connect("activate",
                         lambda i: self.search_function(i._loc_id))
        menuitem.show()
        menuitems.append(menuitem)
        profiles_menuitems = []
        for profile in self._available_profile_map[col_title]:
            label = "View " + profile.strip("'")
            menuitem = gtk.MenuItem(label=label)
            menuitem._loc_id = self._profile_location_map[col_title][profile]
            menuitem.connect("button-release-event",
                             lambda i, e: self.search_function(i._loc_id))
            menuitem.show()
            profiles_menuitems.append(menuitem)
        if profiles_menuitems:
            profiles_menu = gtk.Menu()
            profiles_menu.show()
            profiles_root_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
            profiles_root_menuitem.set_label("View...")
            profiles_root_menuitem.show()
            profiles_root_menuitem.set_submenu(profiles_menu)
            for profiles_menuitem in profiles_menuitems:
                profiles_menu.append(profiles_menuitem)
            menuitems.append(profiles_root_menuitem)
        return menuitems

    def _handle_activation(self, view, path, column):
        # React to row activation in the TreeView.
        if path is None:
            return False
        model = view.get_model()
        row_iter = model.get_iter(path)
        col_index = view.get_columns().index(column)
        col_title = self.column_names[col_index]
        if col_title in self.OPTION_NL_MAP:
            return False 
        cell_data = model.get_value(row_iter, col_index)
        sect_index = self.get_section_column_index()
        section = model.get_value(row_iter, sect_index)
        if section is None:
            return False
        option = None
        if col_index != sect_index and cell_data is not None:
            option = self.column_names[col_index]
            if option == self.DESCRIPTION_TITLE:
                option = None
        id_ = self.util.get_id_from_section_option(section, option)
        self.search_function(id_)

    def get_section_column_index(self):
        """Return the column index for the section (Rose section)."""
        return self.column_names.index(self.SECTION_INDEX_TITLE)

    def add_new_stash_request(self, section, item):
        """Add a new streq namelist."""
        new_opt_map = {self.STREQ_NL_SECT_OPT: section,
                       self.STREQ_NL_ITEM_OPT: item}
        new_section = self.add_section(None, opt_map=new_opt_map,
                                       no_page_launch=True)

    def _launch_new_diagnostic_window(self, widget=None):
        # Launch the new STASH request dialog.
        window = gtk.Window()
        window.set_title(self.ADD_NEW_STASH_WINDOW_TITLE)
        add_module = rose.config_editor.plugin.um.widget.stash_add
        self._diag_panel = add_module.AddStashDiagnosticsPanelv1(
                                              self._stash_lookup,
                                              self.sections,
                                              self.variables,
                                              self.add_new_stash_request)
        window.add(self._diag_panel)
        window.set_default_size(900, 800)
        window.show()

    def _launch_package_menu(self, widget, event):
        # Create a menu below the widget for package actions.
        menu = gtk.Menu()
        packages = {}
        for section, vars_ in self.variables.items():
            for var in vars_:
                if var.name == "package":
                    is_ignored = (rose.variable.IGNORED_BY_USER in
                                  self.sections[section].ignored_reason)
                    packages.setdefault(var.value, [])
                    packages[var.value].append(is_ignored)
        for package in sorted(packages.keys()):
            ignored_list = packages[package]
            package_title = "Package: " + package
            package_menuitem = gtk.MenuItem(package_title)
            package_menuitem.show()
            package_menu = gtk.Menu()
            enable_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_YES)
            enable_menuitem.set_label(label="Enable all")
            enable_menuitem._connect_args = (package, True)
            enable_menuitem.connect(
                   "button-release-event",
                   lambda m, e: self._enable_packages(*m._connect_args))
            enable_menuitem.show()
            enable_menuitem.set_sensitive(any(ignored_list))
            package_menu.append(enable_menuitem)
            ignore_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_NO)
            ignore_menuitem.set_label(label="Ignore all")
            ignore_menuitem._connect_args = (package, False)
            ignore_menuitem.connect(
                   "button-release-event",
                   lambda m, e: self._enable_packages(*m._connect_args))
            ignore_menuitem.set_sensitive(any([not i for i in ignored_list]))
            ignore_menuitem.show()
            package_menu.append(ignore_menuitem)
            remove_menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_REMOVE)
            remove_menuitem.set_label(label="Remove all")
            remove_menuitem._connect_args = (package,)
            remove_menuitem.connect(
                   "button-release-event",
                   lambda m, e: self._remove_packages(*m._connect_args))
            remove_menuitem.show()
            package_menu.append(remove_menuitem)
            package_menuitem.set_submenu(package_menu)
            menu.append(package_menuitem)
        menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_ADD)
        menuitem.set_label(label="Import")
        import_menu = gtk.Menu()
        new_packages = set(self._package_lookup.keys()) - set(packages.keys())
        for new_package in sorted(new_packages):
            new_pack_menuitem = gtk.MenuItem(label=new_package)
            new_pack_menuitem._connect_args = (new_package,)
            new_pack_menuitem.connect(
                     "button-release-event",
                     lambda m, e: self._add_package(*m._connect_args))
            new_pack_menuitem.show()
            import_menu.append(new_pack_menuitem)
        if not new_packages:
            menuitem.set_sensitive(False)
        menuitem.set_submenu(import_menu)
        menuitem.show()
        menu.append(menuitem)
        menuitem = gtk.ImageMenuItem(stock_id=gtk.STOCK_NO)
        menuitem.set_label(label="Disable all packages")
        menuitem.connect("activate",
                         lambda i: self._enable_packages(disable=True))
        menuitem.show()
        menu.append(menuitem)
        menu.popup(None, None, self._position_menu, event.button,
                   event.time, widget)

    def _position_menu(self, menu, widget):
        # Place the menu carefully below the button.
        x, y = widget.get_window().get_origin()
        allocated_rectangle = widget.get_allocation()
        x += allocated_rectangle.x
        y += allocated_rectangle.y + allocated_rectangle.height
        return x, y, False

    def _add_package(self, package):
        # Handle package addition - new requests and/or profiles.
        sections_for_adding = []
        for sect_type, values in self._package_lookup[package].items():
            if sect_type == "namelist:streq":
                sections_for_adding.extend(values)
            else:
                for prof_name in values:
                    sect = self._package_profile_lookup[sect_type][prof_name]
                    sections_for_adding.append(sect)
        for section in sections_for_adding:
            opt_name_values = {}
            node = self.package_config.get([section], no_ignore=True)
            if node is None or not isinstance(node.value, dict):
                continue
            for opt, node in node.value.items():
                opt_name_values.update({opt: node.value})
            if section not in self.sections:
                self.sub_ops.add_section(section, opt_map=opt_name_values)

    def _remove_packages(self, just_this_package=None):
        # Remove requests and/or profiles for packages.
        self._update_available_profiles()
        sections_for_removing = []
        profile_streqs = {}
        for section, vars_ in self.variables.items():
            for var in vars_:
                if var.name == "package":
                    if (just_this_package is None or
                        var.value == just_this_package):
                        sect, opt = self.util.get_section_option_from_id(
                                                    var.metadata["id"])
                        if sect not in sections_for_removing:
                            sections_for_removing.append(sect)
                elif var.name in self.OPTION_NL_MAP:
                    profile_streqs.setdefault(var.name, {})
                    profile_streqs[var.name].setdefault(var.value, [])
                    profile_streqs[var.name][var.value].append(section)
        streq_remove_list = list(sections_for_removing)
        for profile_type in profile_streqs:
            for name, streq_list in profile_streqs[profile_type].items():
                if all([s in streq_remove_list for s in streq_list]):
                    # This is only referenced by sections about to be removed.
                    profile_id = self._profile_location_map.get(
                                               profile_type, {}).get(name)
                    if profile_id is None:
                        continue
                    profile_section = self.util.get_section_option_from_id(
                                                            profile_id)[0]
                    sections_for_removing.append(profile_section)
        self.sub_ops.remove_sections(sections_for_removing)
  
    def _enable_packages(self, just_this_package=None, disable=False):
        # Enable or user-ignore requests matching these packages.
        sections_for_changing = []
        for section, vars_ in self.variables.items():
            for var in vars_:
                if var.name == "package":
                    if (just_this_package is None or
                        var.value == just_this_package):
                        sect, opt = self.util.get_section_option_from_id(
                                                  var.metadata["id"])
                        if sect not in sections_for_changing:
                            sections_for_changing.append(sect)
        for sect in sections_for_changing:
            is_ignored = (rose.variable.IGNORED_BY_USER in
                          self.sections[sect].ignored_reason)
            if is_ignored != disable:
                continue
            self.sub_ops.ignore_section(sect, not disable)
