# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
#-----------------------------------------------------------------------------

import ast
import inspect
import os
import shlex
import subprocess
import sys

import pygtk
pygtk.require('2.0')
import gtk

import rose.config
import rose.config_editor
import rose.config_editor.upgrade_controller
import rose.external
import rose.gtk.dialog
import rose.gtk.run
import rose.macro
import rose.macros
import rose.popen
import rose.suite_control
import rose.suite_engine_proc


class MenuBar(object):

    """Generate the menu bar, using the GTK UIManager.

    Parses the settings in 'ui_config_string'. Connection of buttons is done
    at a higher level.

    """

    ui_config_string = """<ui>
    <menubar name="TopMenuBar">
      <menu action="File">
        <menuitem action="Open..."/>
        <menuitem action="Save"/>
        <menuitem action="Check and save"/>
        <menuitem action="Load All Apps"/>
        <separator name="sep_save"/>
        <menuitem action="Quit"/>
      </menu>
      <menu action="Edit">
        <menuitem action="Undo"/>
        <menuitem action="Redo"/>
        <menuitem action="Stack"/>
        <separator name="sep_undo_redo"/>
        <menuitem action="Find"/>
        <menuitem action="Find Next"/>
        <separator name="sep_find"/>
        <menuitem action="Preferences"/>
      </menu>
      <menu action="View">
        <menuitem action="View fixed vars"/>
        <menuitem action="View ignored vars"/>
        <menuitem action="View user-ignored vars"/>
        <menuitem action="View latent vars"/>
        <separator name="sep_view_vars"/>
        <menuitem action="View ignored pages"/>
        <menuitem action="View user-ignored pages"/>
        <menuitem action="View latent pages"/>
        <separator name="sep_view_flags"/>
        <menuitem action="Flag no-metadata vars"/>
        <menuitem action="Flag optional vars"/>
        <menuitem action="Flag opt config vars"/>
        <separator name="sep_view_widgets"/>
        <menuitem action="View status bar"/>
      </menu>
      <menu action="Metadata">
        <menuitem action="Reload metadata"/>
        <menuitem action="Switch off metadata"/>
        <separator name="sep_view_generic"/>
        <menu action="Prefs">
          <menuitem action="View without descriptions"/>
          <menuitem action="View without help"/>
          <menuitem action="View without titles"/>
        </menu>
        <separator name="sep_upgrade"/>
        <menuitem action="Upgrade"/>
        <separator name="sep graph"/>
        <menuitem action="Graph"/>
        <separator name="sep_checking"/>
        <menuitem action="Extra checks"/>
        <separator name="sep macro"/>
        <menuitem action="All V"/>
        <menuitem action="Autofix"/>
      </menu>
      <menu action="Tools">
        <menu action="Run Suite">
          <menuitem action="Run Suite default"/>
          <menuitem action="Run Suite custom"/>
        </menu>
        <separator name="sep_run_action"/>
        <menuitem action="Browser"/>
        <menuitem action="Terminal"/>
        <menuitem action="View Output"/>
        <menuitem action="Open Suite GControl"/>
      </menu>
      <menu action="Page">
        <menuitem action="Add variable"/>
        <menuitem action="Revert"/>
        <separator name="info"/>
        <menuitem action="Page Info"/>
        <separator name="help"/>
        <menuitem action="Page Help"/>
        <menuitem action="Page Web Help"/>
      </menu>
      <menu action="Help">
        <menuitem action="GUI Help"/>
        <menuitem action="About"/>
      </menu>
    </menubar>
    </ui>"""

    action_details = [('File', None,
                       rose.config_editor.TOP_MENU_FILE),
                      ('Open...', gtk.STOCK_OPEN,
                       rose.config_editor.TOP_MENU_FILE_OPEN,
                       rose.config_editor.ACCEL_OPEN),
                      ('Save', gtk.STOCK_SAVE,
                       rose.config_editor.TOP_MENU_FILE_SAVE,
                       rose.config_editor.ACCEL_SAVE),
                      ('Check and save', gtk.STOCK_SPELL_CHECK,
                       rose.config_editor.TOP_MENU_FILE_CHECK_AND_SAVE),
                      ('Load All Apps', gtk.STOCK_CDROM,
                       rose.config_editor.TOP_MENU_FILE_LOAD_APPS),
                      ('Quit', gtk.STOCK_QUIT,
                       rose.config_editor.TOP_MENU_FILE_QUIT,
                       rose.config_editor.ACCEL_QUIT),
                      ('Edit', None,
                       rose.config_editor.TOP_MENU_EDIT),
                      ('Undo', gtk.STOCK_UNDO,
                       rose.config_editor.TOP_MENU_EDIT_UNDO,
                       rose.config_editor.ACCEL_UNDO),
                      ('Redo', gtk.STOCK_REDO,
                       rose.config_editor.TOP_MENU_EDIT_REDO,
                       rose.config_editor.ACCEL_REDO),
                      ('Stack', gtk.STOCK_INFO,
                       rose.config_editor.TOP_MENU_EDIT_STACK),
                      ('Find', gtk.STOCK_FIND,
                       rose.config_editor.TOP_MENU_EDIT_FIND,
                       rose.config_editor.ACCEL_FIND),
                      ('Find Next', gtk.STOCK_FIND,
                       rose.config_editor.TOP_MENU_EDIT_FIND_NEXT,
                       rose.config_editor.ACCEL_FIND_NEXT),
                      ('Preferences', gtk.STOCK_PREFERENCES,
                       rose.config_editor.TOP_MENU_EDIT_PREFERENCES),
                      ('View', None,
                       rose.config_editor.TOP_MENU_VIEW),
                      ('Page', None,
                       rose.config_editor.TOP_MENU_PAGE),
                      ('Add variable', gtk.STOCK_ADD,
                       rose.config_editor.TOP_MENU_PAGE_ADD),
                      ('Revert', gtk.STOCK_REVERT_TO_SAVED,
                       rose.config_editor.TOP_MENU_PAGE_REVERT),
                      ('Page Info', gtk.STOCK_INFO,
                       rose.config_editor.TOP_MENU_PAGE_INFO),
                      ('Page Help', gtk.STOCK_HELP,
                       rose.config_editor.TOP_MENU_PAGE_HELP),
                      ('Page Web Help', gtk.STOCK_HOME,
                       rose.config_editor.TOP_MENU_PAGE_WEB_HELP),
                      ('Metadata', None,
                       rose.config_editor.TOP_MENU_METADATA),
                      ('Reload metadata', gtk.STOCK_REFRESH,
                       rose.config_editor.TOP_MENU_METADATA_REFRESH,
                       rose.config_editor.ACCEL_METADATA_REFRESH),
                      ('Prefs', gtk.STOCK_PREFERENCES,
                       rose.config_editor.TOP_MENU_METADATA_PREFERENCES),
                      ('Upgrade', gtk.STOCK_GO_UP,
                       rose.config_editor.TOP_MENU_METADATA_UPGRADE),
                      ('All V', gtk.STOCK_DIALOG_QUESTION,
                       rose.config_editor.TOP_MENU_METADATA_MACRO_ALL_V),
                      ('Autofix', gtk.STOCK_CONVERT,
                       rose.config_editor.TOP_MENU_METADATA_MACRO_AUTOFIX),
                      ('Extra checks', gtk.STOCK_DIALOG_QUESTION,
                       rose.config_editor.TOP_MENU_METADATA_CHECK),
                      ('Graph', gtk.STOCK_SORT_ASCENDING,
                       rose.config_editor.TOP_MENU_METADATA_GRAPH),
                      ('Tools', None,
                       rose.config_editor.TOP_MENU_TOOLS),
                      ('Run Suite', gtk.STOCK_MEDIA_PLAY,
                       rose.config_editor.TOP_MENU_TOOLS_SUITE_RUN),
                      ('Run Suite default', gtk.STOCK_MEDIA_PLAY,
                       rose.config_editor.TOP_MENU_TOOLS_SUITE_RUN_DEFAULT,
                       rose.config_editor.ACCEL_SUITE_RUN),
                      ('Run Suite custom', gtk.STOCK_EDIT,
                       rose.config_editor.TOP_MENU_TOOLS_SUITE_RUN_CUSTOM),
                      ('Browser', gtk.STOCK_DIRECTORY,
                       rose.config_editor.TOP_MENU_TOOLS_BROWSER,
                       rose.config_editor.ACCEL_BROWSER),
                      ('Terminal', gtk.STOCK_EXECUTE,
                       rose.config_editor.TOP_MENU_TOOLS_TERMINAL,
                       rose.config_editor.ACCEL_TERMINAL),
                      ('View Output', gtk.STOCK_DIRECTORY,
                       rose.config_editor.TOP_MENU_TOOLS_VIEW_OUTPUT),
                      ('Open Suite GControl', "rose-gtk-scheduler",
                       rose.config_editor.TOP_MENU_TOOLS_OPEN_SUITE_GCONTROL),
                      ('Help', None,
                       rose.config_editor.TOP_MENU_HELP),
                      ('GUI Help', gtk.STOCK_HELP,
                       rose.config_editor.TOP_MENU_HELP_GUI,
                       rose.config_editor.ACCEL_HELP_GUI),
                      ('About', gtk.STOCK_DIALOG_INFO,
                       rose.config_editor.TOP_MENU_HELP_ABOUT)]

    toggle_action_details = [
                      ('View latent vars', None,
                       rose.config_editor.TOP_MENU_VIEW_LATENT_VARS),
                      ('View fixed vars', None,
                       rose.config_editor.TOP_MENU_VIEW_FIXED_VARS),
                      ('View ignored vars', None,
                       rose.config_editor.TOP_MENU_VIEW_IGNORED_VARS),
                      ('View user-ignored vars', None,
                       rose.config_editor.TOP_MENU_VIEW_USER_IGNORED_VARS),
                      ('View without descriptions', None,
                       rose.config_editor.TOP_MENU_VIEW_WITHOUT_DESCRIPTIONS),
                      ('View without help', None,
                       rose.config_editor.TOP_MENU_VIEW_WITHOUT_HELP),
                      ('View without titles', None,
                       rose.config_editor.TOP_MENU_VIEW_WITHOUT_TITLES),
                      ('View ignored pages', None,
                       rose.config_editor.TOP_MENU_VIEW_IGNORED_PAGES),
                      ('View user-ignored pages', None,
                       rose.config_editor.TOP_MENU_VIEW_USER_IGNORED_PAGES),
                      ('View latent pages', None,
                       rose.config_editor.TOP_MENU_VIEW_LATENT_PAGES),
                      ('Flag opt config vars', None,
                       rose.config_editor.TOP_MENU_VIEW_FLAG_OPT_CONF_VARS),
                      ('Flag optional vars', None,
                       rose.config_editor.TOP_MENU_VIEW_FLAG_OPTIONAL_VARS),
                      ('Flag no-metadata vars', None,
                       rose.config_editor.TOP_MENU_VIEW_FLAG_NO_METADATA_VARS),
                      ('View status bar', None,
                       rose.config_editor.TOP_MENU_VIEW_STATUS_BAR),
                      ('Switch off metadata', None,
                       rose.config_editor.TOP_MENU_METADATA_SWITCH_OFF)]

    def __init__(self):
        self.uimanager = gtk.UIManager()
        self.actiongroup = gtk.ActionGroup('MenuBar')
        self.actiongroup.add_actions(self.action_details)
        self.actiongroup.add_toggle_actions(self.toggle_action_details)
        self.uimanager.insert_action_group(self.actiongroup, pos=0)
        self.uimanager.add_ui_from_string(self.ui_config_string)
        self.macro_ids = []

    def set_accelerators(self, accel_dict):
        """Add the keyboard accelerators."""
        self.accelerators = gtk.AccelGroup()
        self.accelerators.lookup = {}  # Unfortunately, this is necessary.
        key_list = []
        mod_list = []
        action_list = []
        for key_press, accel_func in accel_dict.items():
            key, mod = gtk.accelerator_parse(key_press)
            self.accelerators.lookup[str(key) + str(mod)] = accel_func
            self.accelerators.connect_group(
                              key, mod,
                              gtk.ACCEL_VISIBLE,
                              lambda a, c, k, m:
                                self.accelerators.lookup[str(k) + str(m)]())

    def clear_macros(self):
        """Reset menu to original configuration and clear macros."""
        for merge_id in self.macro_ids:
            self.uimanager.remove_ui(merge_id)
        self.macro_ids = []
        all_v_item = self.uimanager.get_widget("/TopMenuBar/Metadata/All V")
        all_v_item.set_sensitive(False)

    def add_macro(self, config_name, modulename, classname, methodname,
                  help, image_path, run_macro):
        """Add a macro to the macro menu."""
        macro_address = '/TopMenuBar/Metadata'
        macro_menu = self.uimanager.get_widget(macro_address).get_submenu()
        if methodname == rose.macro.VALIDATE_METHOD:
            all_v_item = self.uimanager.get_widget(macro_address + "/All V")
            all_v_item.set_sensitive(True)
        config_menu_name = config_name.replace('/', ':').replace('_', '__')
        config_label_name = config_name.split('/')[-1].replace('_', '__')
        label = rose.config_editor.TOP_MENU_METADATA_MACRO_CONFIG.format(
                                                     config_label_name)
        config_address = macro_address + '/' + config_menu_name
        config_item = self.uimanager.get_widget(config_address)
        if config_item is None:
            actiongroup = self.uimanager.get_action_groups()[0]
            if actiongroup.get_action(config_menu_name) is None:
                actiongroup.add_action(gtk.Action(config_menu_name,
                                                  label,
                                                  None, None))
            new_ui = """<ui><menubar name="TopMenuBar">
                        <menu action="Metadata">
                        <menuitem action="{0}"/></menu></menubar>
                        </ui>""".format(config_menu_name)
            self.macro_ids.append(self.uimanager.add_ui_from_string(new_ui))
            config_item = self.uimanager.get_widget(config_address)
            if image_path is not None:
                image = gtk.image_new_from_file(image_path)
                config_item.set_image(image)
        if config_item.get_submenu() is None:
            config_item.set_submenu(gtk.Menu())
        macro_fullname = ".".join([modulename, classname, methodname])
        macro_fullname = macro_fullname.replace("_", "__")
        if methodname == rose.macro.VALIDATE_METHOD:
            stock_id = gtk.STOCK_DIALOG_QUESTION
        else:
            stock_id = gtk.STOCK_CONVERT
        macro_item = gtk.ImageMenuItem(stock_id=stock_id)
        macro_item.set_label(macro_fullname)
        macro_item.set_tooltip_text(help)
        macro_item.show()
        macro_item._run_data = [config_name, modulename, classname,
                                methodname]
        macro_item.connect("activate",
                           lambda i: run_macro(*i._run_data))
        config_item.get_submenu().append(macro_item)
        if (methodname == rose.macro.VALIDATE_METHOD):
            for item in config_item.get_submenu().get_children():
                if hasattr(item, "_rose_all_validators"):
                    return False
            all_item = gtk.ImageMenuItem(gtk.STOCK_DIALOG_QUESTION)
            all_item._rose_all_validators = True
            all_item.set_label(rose.config_editor.MACRO_MENU_ALL_VALIDATORS)
            all_item.set_tooltip_text(
                     rose.config_editor.MACRO_MENU_ALL_VALIDATORS_TIP)
            all_item.show()
            all_item._run_data = [config_name, None, None, methodname]
            all_item.connect("activate",
                             lambda i: run_macro(*i._run_data))
            config_item.get_submenu().prepend(all_item)


class MainMenuHandler(object):

    """Handles signals from the main menu and tool bar."""

    def __init__(self, data, util, reporter, mainwindow,
                 undo_stack, redo_stack, undo_func,
                 update_config_func,
                 apply_macro_transform_func, apply_macro_validation_func,
                 section_ops_inst, variable_ops_inst, find_ns_id_func):
        self.data = data
        self.util = util
        self.reporter = reporter
        self.mainwindow = mainwindow
        self.undo_stack = undo_stack
        self.redo_stack = redo_stack
        self.perform_undo = undo_func
        self.update_config = update_config_func
        self.apply_macro_transform = apply_macro_transform_func
        self.apply_macro_validation = apply_macro_validation_func
        self.sect_ops = section_ops_inst
        self.var_ops = variable_ops_inst
        self.find_ns_id_func = find_ns_id_func
        self.bad_colour = rose.gtk.util.color_parse(
                          rose.config_editor.COLOUR_VARIABLE_TEXT_ERROR)

    def about_dialog(self, args):
        self.mainwindow.launch_about_dialog()

    def get_orphan_container(self, page):
        """Return a container with the page object inside."""
        box = gtk.VBox()
        box.pack_start(page, expand=True, fill=True)
        box.show()
        return box

    def view_stack(self, args):
        """Handle a View Stack request."""
        self.mainwindow.launch_view_stack(self.undo_stack, self.redo_stack,
                                          self.perform_undo)

    def destroy(self, *args):
        """Handle a destroy main program request."""
        for name in self.data.config:
            if self.data.helper.get_config_has_unsaved_changes(name):
                self.mainwindow.launch_exit_warning_dialog()
                return True
        try:
            gtk.main_quit()
        except RuntimeError:
            # This can occur before gtk.main() is called, during the load.
            sys.exit()

    def check_all_extra(self):
        """Check fail-if, warn-if, and run all validator macros."""
        for config_name in self.data.config.keys():
            if not self.data.config[config_name].is_preview:
                self.update_config(config_name)
        num_errors = self.check_fail_rules(configs_updated=True)
        num_errors += self.run_custom_macro(
            method_name=rose.macro.VALIDATE_METHOD,
            configs_updated=True)
        if num_errors:
            text = rose.config_editor.EVENT_MACRO_VALIDATE_CHECK_ALL.format(
                                                                 num_errors)
            kind = self.reporter.KIND_ERR
        else:
            text = rose.config_editor.EVENT_MACRO_VALIDATE_CHECK_ALL_OK
            kind = self.reporter.KIND_OUT
        self.reporter.report(text, kind=kind)

    def check_fail_rules(self, configs_updated=False):
        """Check the fail-if and warn-if conditions of the configurations."""
        if not configs_updated:
            for config_name in self.data.config.keys():
                if not self.data.config[config_name].is_preview:
                    self.update_config(config_name)
        macro = rose.macros.rule.FailureRuleChecker()
        macro_fullname = "rule.FailureRuleChecker.validate"
        error_count = 0
        config_names = sorted(self.data.config.keys())
        for config_name in sorted(self.data.config.keys()):
            config_data = self.data.config[config_name]
            if config_data.is_preview:
                continue
            config = config_data.config
            meta = config_data.meta
            try:
                return_value = macro.validate(config, meta)
                if return_value:
                    error_count += len(return_value)
            except Exception as e:
                rose.gtk.dialog.run_dialog(
                         rose.gtk.dialog.DIALOG_TYPE_ERROR,
                         str(e),
                         rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                            macro_fullname))
                continue
            sorter = rose.config.sort_settings
            to_id = lambda s: self.util.get_id_from_section_option(
                                                s.section, s.option)
            return_value.sort(lambda x, y: sorter(to_id(x), to_id(y)))
            self.handle_macro_validation(config_name, macro_fullname,
                                         config, return_value,
                                         no_display=(not return_value))
        if error_count > 0:
            msg = rose.config_editor.EVENT_MACRO_VALIDATE_RULE_PROBLEMS_FOUND
            info_text = msg.format(error_count)
            kind = self.reporter.KIND_ERR
        else:
            msg = rose.config_editor.EVENT_MACRO_VALIDATE_RULE_NO_PROBLEMS
            info_text = msg
            kind = self.reporter.KIND_OUT
        self.reporter.report(info_text, kind=kind)
        return error_count

    def clear_page_menu(self, menubar, add_menuitem):
        """Clear all page add variable items."""
        add_menuitem.remove_submenu()

    def load_page_menu(self, menubar, add_menuitem, current_page):
        """Load the page add variable items, if any."""
        if current_page is None:
            return False
        add_var_menu = current_page.get_add_menu()
        if add_var_menu is None or not add_var_menu.get_children():
            add_menuitem.set_sensitive(False)
            return False
        add_menuitem.set_sensitive(True)
        add_menuitem.set_submenu(add_var_menu)

    def load_macro_menu(self, menubar):
        """Refresh the menu dealing with custom macro launches."""
        menubar.clear_macros()
        config_keys = self.data.config.keys()
        config_keys.sort()
        tuple_sorter = lambda x, y: cmp(x[0], y[0])
        for config_name in config_keys:
            image = self.data.helper.get_icon_path_for_config(config_name)
            macros = self.data.config[config_name].macros
            macro_tuples = rose.macro.get_macro_class_methods(macros)
            macro_tuples.sort(tuple_sorter)
            for macro_mod, macro_cls, macro_func, help in macro_tuples:
                menubar.add_macro(config_name, macro_mod, macro_cls,
                                  macro_func, help, image,
                                  self.handle_run_custom_macro)

    def inspect_custom_macro(self, macro_meth):
        """Inspect a custom macro for kwargs and return any"""
        arglist = inspect.getargspec(macro_meth).args
        defaultlist = inspect.getargspec(macro_meth).defaults
        optionals = {}
        while defaultlist is not None and len(defaultlist) > 0:
            if arglist[-1] not in ["self", "config", "meta_config"]:
                optionals[arglist[-1]] = defaultlist[-1]
                arglist = arglist[0:-1]
                defaultlist = defaultlist[0:-1]
            else:
                break
        return optionals

    def handle_graph(self):
        """Handle a graph metadata request."""
        config_sect_dict = {}
        for config_name in self.data.config.keys():
            config_data = self.data.config[config_name]
            config_sect_dict[config_name] = config_data.sections.now.keys()
            config_sect_dict[config_name].sort(rose.config.sort_settings)
        config_name, section = self.mainwindow.launch_graph_dialog(
            config_sect_dict)
        if config_name is None:
            return False
        if section is None:
            allowed_sections = None
        else:
            allowed_sections = [section]
        self.launch_graph(config_name, allowed_sections=allowed_sections)

    def check_entry_value(self, entry_widget, dialog, entries,
                          labels, optionals):
        is_valid = True
        for k, entry in entries.items():
            this_is_valid = True
            try:
                new_val = ast.literal_eval(entry.get_text())
                entry.modify_text(gtk.STATE_NORMAL, None)
            except (ValueError, EOFError, SyntaxError):
                entry.modify_text(gtk.STATE_NORMAL, self.bad_colour)
                is_valid = False
                this_is_valid = False
            if not this_is_valid or new_val != optionals[k]:
                lab = '<span foreground="blue">{0}</span>'.format(str(k)+":")
                labels[k].set_markup(lab)
            else:
                labels[k].set_text(str(k) + ":")
        dialog.set_response_sensitive(gtk.RESPONSE_OK, is_valid)
        return

    def handle_macro_entry_activate(self, entry_widget, dialog, entries):
        for k, entry in entries.items():
            try:
                ast.literal_eval(entry.get_text())
            except (ValueError, EOFError, SyntaxError):
                break
        else:
            dialog.response(gtk.RESPONSE_OK)

    def override_macro_defaults(self, optionals, methname):
        """Launch a dialog to handle capture of any override args to macro"""
        res = {}
        #create the text input field
        entries = {}
        labels = {}
        errs = {}
        succeeded = False
        dialog = gtk.MessageDialog(
                None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_OK_CANCEL,
                None)
        dialog.set_markup('Specify overrides for macro arguments:')
        dialog.set_title(methname)
        table = gtk.Table(len(optionals.items()), 2, False)
        dialog.vbox.add(table)
        for i in range(len(optionals.items())):
            k, v = optionals.items()[i]
            label = gtk.Label(str(k) + ":")
            entry = gtk.Entry()
            if isinstance(v,str):
                entry.set_text("'" + v + "'")
            else:
                entry.set_text(str(v))
            entry.connect("changed", self.check_entry_value, dialog,
                          entries, labels, optionals)
            entry.connect("activate", self.handle_macro_entry_activate,
                          dialog, entries)
            entries[k] = entry
            labels[k] = label
            table.attach(entry, 1, 2, i, i+1)
            hbox = gtk.HBox()
            hbox.pack_start(label, expand=False)
            table.attach(hbox, 0, 1, i, i+1)
        dialog.show_all()
        response = dialog.run()
        if (response == gtk.RESPONSE_CANCEL or
            response == gtk.RESPONSE_CLOSE):
            res = optionals
            dialog.destroy()
        else:
            res = {}
            for k,box in entries.items():
                res[k] = ast.literal_eval(box.get_text())
        dialog.destroy()
        return res

    def handle_run_custom_macro(self, *args, **kwargs):
        """Wrap the method so that this returns False for GTK callbacks."""
        self.run_custom_macro(*args, **kwargs)
        return False

    def run_custom_macro(self, config_name=None, module_name=None,
                         class_name=None, method_name=None,
                         configs_updated=False):
        """Run the custom macro method and launch a dialog."""
        old_pwd = os.getcwd()
        macro_data = []
        if config_name is None:
            configs = sorted(self.data.config.keys())
        else:
            configs = [config_name]
        for name in list(configs):
            if self.data.config[name].is_preview:
                configs.remove(name)
                continue
            if not configs_updated:
                self.update_config(name)
        if method_name is None:
            method_names = [rose.macro.VALIDATE_METHOD,
                            rose.macro.TRANSFORM_METHOD]
        else:
            method_names = [method_name]
        if module_name is not None and config_name is not None:
            config_mod_prefix = self.data.helper.get_macro_module_prefix(config_name)
            if not module_name.startswith(config_mod_prefix):
                module_name = config_mod_prefix + module_name
        for config_name in configs:
            config_data = self.data.config[config_name]
            if config_data.directory is not None:
                os.chdir(config_data.directory)
            for module in config_data.macros:
                if module_name is not None and module.__name__ != module_name:
                    continue
                for obj_name, obj in inspect.getmembers(module):
                    for method_name in method_names:
                        if (not hasattr(obj, method_name) or
                            obj_name.startswith("_") or
                            not issubclass(obj, rose.macro.MacroBase)):
                            continue
                        if class_name is not None and obj_name != class_name:
                            continue
                        macro_fullname = ".".join([module.__name__,
                                                   obj_name,
                                                   method_name])
                        err_text = (
                              rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                           macro_fullname))
                        try:
                            macro_inst = obj()
                        except Exception as e:
                            rose.gtk.dialog.run_dialog(
                                 rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                 str(e), err_text)
                            continue
                        if hasattr(macro_inst, method_name):
                            macro_data.append((config_name, macro_inst,
                                               module.__name__, obj_name,
                                               method_name))
        os.chdir(old_pwd)
        if not macro_data:
            return 0
        sorter = rose.config.sort_settings
        to_id = lambda s: self.util.get_id_from_section_option(s.section,
                                                               s.option)
        config_macro_errors = []
        config_macro_changes = []
        for config_name, macro_inst, modname, objname, methname in macro_data:
            macro_fullname = '.'.join([modname, objname, methname])
            macro_config = self.data.dump_to_internal_config(config_name)
            config_data = self.data.config[config_name]
            meta_config = config_data.meta
            macro_method = getattr(macro_inst, methname)
            optionals = self.inspect_custom_macro(macro_method)
            if optionals:
                res = self.override_macro_defaults(optionals, objname)
            else:
                res = {}
            os.chdir(config_data.directory)
            try:
                return_value = macro_method(macro_config, meta_config, **res)
            except Exception as e:
                rose.gtk.dialog.run_dialog(
                         rose.gtk.dialog.DIALOG_TYPE_ERROR,
                         str(e),
                         rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
                                                            macro_fullname))
                continue
            if methname == rose.macro.TRANSFORM_METHOD:
                if (not isinstance(return_value, tuple) or
                    len(return_value) != 2 or
                    not isinstance(return_value[0], rose.config.ConfigNode) or
                    not isinstance(return_value[1], list)):
                    self._handle_bad_macro_return(macro_fullname, return_value)
                    continue
                integrity_exception = rose.macro.check_config_integrity(
                    return_value[0])
                if integrity_exception is not None:
                    self._handle_bad_macro_return(macro_fullname,
                                                  integrity_exception)
                    continue
                macro_config, change_list = return_value
                if not change_list:
                    continue
                change_list.sort(lambda x, y: sorter(to_id(x), to_id(y)))
                num_changes = len(change_list)
                self.handle_macro_transforms(config_name, macro_fullname,
                                             macro_config, change_list)
                config_macro_changes.append((config_name,
                                             macro_fullname,
                                             num_changes))
                continue
            elif methname == rose.macro.VALIDATE_METHOD:
                if not isinstance(return_value, list):
                    self._handle_bad_macro_return(macro_fullname,
                                                  return_value)
                    continue
                if return_value:
                    return_value.sort(lambda x, y: sorter(to_id(x), to_id(y)))
                config_macro_errors.append((config_name,
                                            macro_fullname,
                                            len(return_value)))
                self.handle_macro_validation(config_name, macro_fullname,
                                             macro_config, return_value)
        os.chdir(old_pwd)
        if class_name is None:
            # Construct a grouped report.
            config_macro_errors.sort()
            config_macro_changes.sort()
            if rose.macro.VALIDATE_METHOD in method_names:
                null_format = rose.config_editor.EVENT_MACRO_VALIDATE_ALL_OK
                change_format = rose.config_editor.EVENT_MACRO_VALIDATE_ALL
                num_issues = sum([e[2] for e in config_macro_errors])
                issue_confs = [e[0] for e in config_macro_errors if e[2]]
            else:
                null_format = rose.config_editor.EVENT_MACRO_TRANSFORM_ALL_OK
                change_format = rose.config_editor.EVENT_MACRO_TRANSFORM_ALL
                num_issues = sum([e[2] for e in config_macro_changes])
                issue_confs = [e[0] for e in config_macro_changes if e[2]]
            issue_confs = sorted(set(issue_confs))
            if num_issues:
                issue_conf_text = self._format_macro_config_names(issue_confs)
                self.reporter.report(change_format.format(issue_conf_text,
                                                          num_issues),
                                     kind=self.reporter.KIND_ERR)
            else:
                all_conf_text = self._format_macro_config_names(configs)
                self.reporter.report(null_format.format(all_conf_text),
                                     kind=self.reporter.KIND_OUT)
        num_errors = sum([e[2] for e in config_macro_errors])
        num_changes = sum([c[2] for c in config_macro_changes])
        return num_errors + num_changes

    def _format_macro_config_names(self, config_names):
        if len(config_names) > 5:
            return rose.config_editor.EVENT_MACRO_CONFIGS.format(
                                            len(config_names))
        config_names = [c.lstrip("/") for c in config_names]
        return ", ".join(config_names)

    def _handle_bad_macro_return(self, macro_fullname, info):
        if isinstance(info, Exception):
            text = rose.config_editor.ERROR_BAD_MACRO_EXCEPTION.format(
                type(info).__name__, str(info))
        else:
            text = rose.config_editor.ERROR_BAD_MACRO_RETURN.format(info)
        summary = rose.config_editor.ERROR_RUN_MACRO_TITLE.format(
            macro_fullname)
        self.reporter.report(summary,
                             kind=self.reporter.KIND_ERR)
        rose.gtk.dialog.run_dialog(
            rose.gtk.dialog.DIALOG_TYPE_ERROR,
            text, summary)

    def handle_macro_transforms(self, config_name, macro_name,
                                macro_config, change_list, no_display=False,
                                triggers_ok=False):
        """Calculate needed changes and apply them if prompted to.

        At the moment trigger-ignore of variables and sections is
        assumed to be the exclusive property of the Rose trigger
        macro and is not allowed for any other macro.

        """
        if not change_list:
            self._report_macro_transform(config_name, macro_name, 0)
            return
        macro_type = ".".join(macro_name.split(".")[:-1])
        var_changes = []
        sect_changes = []
        sect_removes = []
        for item in list(change_list):
            if item.option is None:
                sect_changes.append(item)
            else:
                var_changes.append(item)
        search = lambda i: self.find_ns_id_func(config_name, i)
        if not no_display:
            proceed_ok = self.mainwindow.launch_macro_changes_dialog(
                              config_name, macro_type, change_list,
                              search_func=search)
            if not proceed_ok:
                self._report_macro_transform(config_name, macro_name, 0)
                return 0
        changed_ids = []
        sections = self.data.config[config_name].sections
        for item in sect_changes:
            sect = item.section
            changed_ids.append(sect)
            macro_node = macro_config.get([sect])
            if macro_node is None:
                sect_removes.append(sect)
                continue
            if sect in sections.now:
                sect_data = sections.now[sect]
            else:
                self.sect_ops.add_section(config_name, sect)
                sect_data = sections.now[sect]
            if (rose.variable.IGNORED_BY_USER in sect_data.ignored_reason and
                macro_node.state !=
                rose.config.ConfigNode.STATE_USER_IGNORED):
                # Enable.
                self.sect_ops.ignore_section(config_name, sect, False,
                                             override=True)
            elif (macro_node.state ==
                  rose.config.ConfigNode.STATE_USER_IGNORED and
                  rose.variable.IGNORED_BY_USER not in
                  sect_data.ignored_reason):
                self.sect_ops.ignore_section(config_name, sect, True,
                                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_SYST_IGNORED and
                  rose.variable.IGNORED_BY_SYSTEM not in
                  sect_data.ignored_reason):
                sect_data.error.setdefault(
                          rose.config_editor.WARNING_TYPE_ENABLED,
                          rose.config_editor.IGNORED_STATUS_MACRO)
                self.sect_ops.ignore_section(config_name, sect, True,
                                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_NORMAL and
                  rose.variable.IGNORED_BY_SYSTEM in
                  sect_data.ignored_reason):
                sect_data.error.setdefault(
                          rose.config_editor.WARNING_TYPE_TRIGGER_IGNORED,
                          rose.config_editor.IGNORED_STATUS_MACRO)
                self.sect_ops.ignore_section(config_name, sect, False,
                                             override=True)
        for item in var_changes:
            sect = item.section
            opt = item.option
            val = item.value
            warning = item.info
            var_id = self.util.get_id_from_section_option(sect, opt)
            changed_ids.append(var_id)
            var = self.data.helper.get_variable_by_id(var_id, config_name)
            macro_node = macro_config.get([sect, opt])
            if macro_node is None:
                self.var_ops.remove_var(var)
                continue
            if var is None:
                value = macro_node.value
                metadata = self.data.helper.get_metadata_for_config_id(
                                            var_id, config_name)
                variable = rose.variable.Variable(opt, value, metadata)
                self.data.load_ns_for_node(variable, config_name)
                self.var_ops.add_var(variable)
                var = self.data.helper.get_variable_by_id(var_id, config_name)
                continue
            if var.value != macro_node.value:
                self.var_ops.set_var_value(var, macro_node.value)
            elif (rose.variable.IGNORED_BY_USER in var.ignored_reason and
                  macro_node.state !=
                  rose.config.ConfigNode.STATE_USER_IGNORED):
                # Enable.
                self.var_ops.set_var_ignored(var, {}, override=True)
            elif (macro_node.state ==
                  rose.config.ConfigNode.STATE_USER_IGNORED and
                  rose.variable.IGNORED_BY_USER not in var.ignored_reason):
                self.var_ops.set_var_ignored(
                             var,
                             {rose.variable.IGNORED_BY_USER:
                              rose.config_editor.IGNORED_STATUS_MACRO},
                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_SYST_IGNORED and
                  rose.variable.IGNORED_BY_SYSTEM not in var.ignored_reason):
                self.var_ops.set_var_ignored(
                             var,
                             {rose.variable.IGNORED_BY_SYSTEM:
                              rose.config_editor.IGNORED_STATUS_MACRO},
                             override=True)
            elif (triggers_ok and macro_node.state ==
                  rose.config.ConfigNode.STATE_NORMAL and
                  rose.variable.IGNORED_BY_SYSTEM in var.ignored_reason):
                self.var_ops.set_var_ignored(var, {}, override=True)
        for sect in sect_removes:
            self.sect_ops.remove_section(config_name, sect)
        self.apply_macro_transform(config_name, macro_type, changed_ids)
        self._report_macro_transform(config_name, macro_name, len(change_list))
        return len(change_list)

    def _report_macro_transform(self, config_name, macro_name, num_changes):
        name = config_name.lstrip("/")
        if macro_name.endswith(rose.macro.TRANSFORM_METHOD):
            macro = macro_name.split('.')[-2]
        else:
            macro = macro_name.split('.')[-1]
        kind = self.reporter.KIND_OUT
        if num_changes:
            info_text = rose.config_editor.EVENT_MACRO_TRANSFORM.format(
                                    name, macro, num_changes)
        else:
            info_text = rose.config_editor.EVENT_MACRO_TRANSFORM_OK.format(
                                    name, macro)
        self.reporter.report(info_text, kind=kind)

    def handle_macro_validation(self, config_name, macro_name,
                                macro_config, problem_list, no_display=False):
        """Apply errors and give information to the user."""
        macro_type = ".".join(macro_name.split(".")[:-1])
        self.apply_macro_validation(config_name, macro_type, problem_list)
        search = lambda i: self.find_ns_id_func(config_name, i)
        self._report_macro_validation(config_name, macro_name,
                                      len(problem_list))
        if not no_display:
            self.mainwindow.launch_macro_changes_dialog(
                            config_name, macro_type, problem_list,
                            mode="validate", search_func=search)

    def _report_macro_validation(self, config_name, macro_name, num_errors):
        name = config_name.lstrip("/")
        if macro_name.endswith(rose.macro.VALIDATE_METHOD):
            macro = macro_name.split('.')[-2]
        else:
            macro = macro_name.split('.')[-1]
        if num_errors:
            info_text = rose.config_editor.EVENT_MACRO_VALIDATE.format(
                                name, macro, num_errors)
            kind = self.reporter.KIND_ERR
        else:
            info_text = rose.config_editor.EVENT_MACRO_VALIDATE_OK.format(
                                name, macro)
            kind = self.reporter.KIND_OUT
        self.reporter.report(info_text, kind=kind)

    def handle_upgrade(self, only_this_config_name=None):
        """Run the upgrade manager for this suite."""
        config_dict = {}
        for config_name in self.data.config.keys():
            config_data = self.data.config[config_name]
            if config_data.is_preview:
                continue
            self.update_config(config_name)
            if (only_this_config_name is None or
                config_name == only_this_config_name):
                config_dict[config_name] = {
                    "config": config_data.config,
                    "directory": config_data.directory
                }
        rose.config_editor.upgrade_controller.UpgradeController(
                           config_dict, self.handle_macro_transforms,
                           parent_window=self.mainwindow.window)

    def help(self, *args):
        # Handle a GUI help request.
        self.mainwindow.launch_help_dialog()

    def prefs(self, args):
        # Handle a Preferences view request.
        self.mainwindow.launch_prefs()

    def launch_browser(self):
        if self.data.top_level_directory is None:
            rose.external.launch_fs_browser(os.getcwd())
        else:
            rose.external.launch_fs_browser(self.data.top_level_directory)

    def launch_graph(self, namespace, allowed_sections=None):
        try:
            import pygraphviz
        except ImportError as e:
            title = rose.config_editor.WARNING_CANNOT_GRAPH
            rose.gtk.dialog.run_dialog(rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                       str(e), title)
        config_name, subsp = self.util.split_full_ns(self.data, namespace)
        self.update_config(config_name)
        config_data = self.data.config[config_name]
        if config_data.directory is None:
            return False
        if allowed_sections is None:
            if config_name != namespace:
                allowed_sections = (
                    self.data.helper.get_sections_from_namespace(namespace))
            else:
                allowed_sections = []
        cmd = (shlex.split(rose.config_editor.LAUNCH_COMMAND_GRAPH) +
               [config_data.directory] + allowed_sections)
        rose.popen.RosePopener().run_bg(*cmd)

    def launch_scheduler(self, *args):
        """Run the scheduler for a suite open in config edit."""
        this_id = self.data.top_level_name
        scontrol = rose.suite_control.SuiteControl()
        if scontrol.suite_engine_proc.is_suite_registered(this_id):
            return scontrol.gcontrol(this_id)
        else:
            msg = rose.config_editor.DIALOG_TEXT_UNREGISTERED_SUITE.format(
                                                                       this_id)
            return rose.gtk.dialog.run_dialog(
                          rose.gtk.dialog.DIALOG_TYPE_ERROR,
                          msg,
                          rose.config_editor.DIALOG_TITLE_UNREGISTERED_SUITE)

    def launch_terminal(self):
        # Handle a launch terminal request.
        try:
            rose.external.launch_terminal()
        except rose.popen.RosePopenError as e:
            rose.gtk.dialog.run_dialog(
                                rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                str(e),
                                rose.config_editor.DIALOG_TITLE_ERROR)

    def launch_output_viewer(self):
        """View a suite's output, if any."""
        g = rose.suite_engine_proc.SuiteEngineProcessor.get_processor()
        try:
            g.launch_suite_log_browser(None, self.data.top_level_name)
        except rose.suite_engine_proc.NoSuiteLogError:
            rose.gtk.dialog.run_dialog(
                                rose.gtk.dialog.DIALOG_TYPE_ERROR,
                                rose.config_editor.ERROR_NO_OUTPUT.format(
                                            self.data.top_level_name),
                                rose.config_editor.DIALOG_TITLE_ERROR)

    def get_run_suite_args(self, *args):
        """Ask the user for custom arguments to suite run."""
        help_cmds = shlex.split(rose.config_editor.LAUNCH_SUITE_RUN_HELP)
        help_text = subprocess.Popen(help_cmds,
                                     stdout=subprocess.PIPE).communicate()[0]
        rose.gtk.dialog.run_command_arg_dialog(
                            rose.config_editor.LAUNCH_SUITE_RUN,
                            help_text, self.run_suite_check_args)

    def run_suite_check_args(self, args):
        if args is None:
            return False
        self.run_suite(args)

    def run_suite(self, args=None, **kwargs):
        """Run the suite, if possible."""
        if not isinstance(args, list):
            args = []
        for key, value in kwargs.items():
            args.extend([key, value])
        rose.gtk.run.run_suite(*args)
        return False

    def transform_default(self, only_this_config=None):
        """Run the Rose built-in transformer macros."""
        if (only_this_config is not None and
            only_this_config in self.data.config.keys()):
            config_keys = [only_this_config]
            text = rose.config_editor.DIALOG_LABEL_AUTOFIX
        else:
            config_keys = sorted(self.data.config.keys())
            text = rose.config_editor.DIALOG_LABEL_AUTOFIX_ALL
        proceed = rose.gtk.dialog.run_dialog(
                                  rose.gtk.dialog.DIALOG_TYPE_WARNING,
                                  text,
                                  rose.config_editor.DIALOG_TITLE_AUTOFIX,
                                  cancel=True)
        if not proceed:
            return False
        sorter = rose.config.sort_settings
        to_id = lambda s: self.util.get_id_from_section_option(s.section,
                                                               s.option)
        for config_name in config_keys:
            macro_config = self.data.dump_to_internal_config(config_name)
            meta_config = self.data.config[config_name].meta
            macro = rose.macros.DefaultTransforms()
            config, change_list = macro.transform(macro_config, meta_config)
            change_list.sort(lambda x, y: sorter(to_id(x), to_id(y)))
            self.handle_macro_transforms(
                        config_name, "Autofixer.transform",
                        macro_config, change_list, triggers_ok=True)
