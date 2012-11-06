# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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

import pango
import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor
import rose.config_editor.util


class MenuWidget(gtk.HBox):

    """This class generates a button with a menu for variable actions."""

    MENU_ICON_ERRORS = 'rose-gtk-gnome-package-system-errors'
    MENU_ICON_FILE = 'gtk-harddisk'
    MENU_ICON_WARNINGS = 'rose-gtk-gnome-package-system-warnings'
    MENU_ICON_LATENT = 'rose-gtk-gnome-add'
    MENU_ICON_LATENT_ERRORS = 'rose-gtk-gnome-add-errors'
    MENU_ICON_LATENT_WARNINGS = 'rose-gtk-gnome-add-warnings'
    MENU_ICON_NORMAL = 'rose-gtk-gnome-package-system-normal'

    def __init__(self, variable, var_ops, remove_func, update_func,
                 launch_help_func):
        super(MenuWidget, self).__init__(homogeneous=False, spacing=0)
        self.my_variable = variable
        self.var_ops = var_ops
        self.trigger_remove = remove_func
        self.update_status = update_func
        self.launch_help = launch_help_func
        self.is_ghost = self.var_ops.is_var_ghost(variable)
        self.load_contents()

    def load_contents(self):
        """Load the GTK, including menu."""
        variable = self.my_variable
        option_ui_start = """<ui>
                             <popup action='Options'> """
        option_ui_middle = """<menuitem action="Info"/>
                              <menuitem action="Help"/>"""
        option_ui_end = """<separator name="sepEdit"/>
                           <menuitem action="Edit"/>
                           <menuitem action="Ignore"/>
                           <separator name="sepRemove"/>
                           <menuitem action="Remove"/>
                           </popup> </ui>"""
        actions = [('Options', 'rose-gtk-gnome-package-system', ''),
                   ('Info', gtk.STOCK_INFO,
                    rose.config_editor.VAR_MENU_INFO),
                   ('Help',  gtk.STOCK_HELP,
                    rose.config_editor.VAR_MENU_HELP),
                   ('Edit', gtk.STOCK_EDIT,
                    rose.config_editor.VAR_MENU_EDIT_COMMENTS),
                   ('Ignore', gtk.STOCK_NO,
                    rose.config_editor.VAR_MENU_IGNORE),
                   ('Remove', gtk.STOCK_DELETE, 
                    rose.config_editor.VAR_MENU_REMOVE)]
        menu_icon_id = 'rose-gtk-gnome-package-system'
        if self.is_ghost:
            option_ui_middle = (
                   option_ui_middle.replace('<menuitem action="Ignore"/>',
                                            ''))
        var_type = variable.metadata.get(rose.META_PROP_TYPE, '')
        var_values = variable.metadata.get(rose.META_PROP_VALUES, range(2))
        if (isinstance(var_type, basestring)
            and var_type.startswith('file')):
            menu_icon_id = self.MENU_ICON_FILE
        if variable.warning:
            if self.is_ghost:
                menu_icon_id = self.MENU_ICON_LATENT_WARNINGS
            else:
                menu_icon_id = self.MENU_ICON_WARNINGS
            old_middle = option_ui_middle
            option_ui_middle = ''
            for warn, warn_info in variable.warning.items():
                option_ui_middle += "<menuitem action='Warn_" + warn + "'/>"
                w_string = "(" + warn + "): " + warn_info.replace("_", "__")
                actions.append(("Warn_" + warn, gtk.STOCK_DIALOG_INFO,
                                w_string))
            option_ui_middle += "<separator name='sepWarning'/>" + old_middle
        if variable.error:
            if self.is_ghost:
                menu_icon_id = self.MENU_ICON_LATENT_ERRORS
            else:
                menu_icon_id = self.MENU_ICON_ERRORS
            old_middle = option_ui_middle
            option_ui_middle = ''
            for err, err_info in variable.error.items():
                option_ui_middle += "<menuitem action='Error_" + err + "'/>"
                e_string = "(" + err + "): " + err_info.replace("_", "__")
                actions.append(("Error_" + err, gtk.STOCK_DIALOG_WARNING,
                                e_string))
            option_ui_middle += "<separator name='sepError'/>" + old_middle
        if self.is_ghost:
            if not variable.error and not variable.warning:
                menu_icon_id = self.MENU_ICON_LATENT
            old_middle = option_ui_middle
            option_ui_middle = "<menuitem action='Add'/>"
            option_ui_middle += "<separator name='sepAdd'/>" + old_middle
            actions.append(('Add', gtk.STOCK_ADD,
                            rose.config_editor.VAR_MENU_ADD))
        if 'url' in variable.metadata:
            url_ui = "<separator name='sepWeb'/><menuitem action='Web Help'/>"
            actions.append(('Web Help', gtk.STOCK_HOME,
                            rose.config_editor.VAR_MENU_URL))
            option_ui_middle += url_ui
        option_ui = option_ui_start + option_ui_middle + option_ui_end
        self.button = rose.gtk.util.CustomButton(
                                    stock_id=menu_icon_id,
                                    size=gtk.ICON_SIZE_MENU,
                                    as_tool=True)
        self._set_hover_over(variable)
        self.option_ui = option_ui
        self.actions = actions
        self.pack_start(self.button, expand=False, fill=False, padding=0)
        self.button.connect(
                "button-press-event",
                lambda b, e: self._popup_option_menu(
                                                self.option_ui,
                                                self.actions,
                                                e.button,
                                                e.time))
        # FIXME: Try to popup the menu at the button, instead of the cursor.
        self.button.connect(
                "activate",
                lambda b: _popup_option_menu(
                              self.option_ui,
                              self.actions,
                              1,
                              gtk.gdk.Event(gtk.gdk.KEY_PRESS).time))
        self.button.connect(
                "enter-notify-event",
                lambda b, e: self._set_hover_over(variable))
        self._set_hover_over(variable)
        self.button.show()

    def refresh(self, variable=None):
        """Reload the contents."""
        if variable is not None:
            self.my_variable = variable
        for widget in self.get_children():
            self.remove(widget)
        self.load_contents()

    def _set_hover_over(self, variable):
        hover_string = 'Variable options'
        if variable.warning:
            hover_string = rose.config_editor.VAR_MENU_TIP_WARNING
            for warn, warn_info in variable.warning.items():
                hover_string += "(" + warn + "): " + warn_info + '\n'
            hover_string = hover_string.rstrip('\n')
        if variable.error:
            hover_string = rose.config_editor.VAR_MENU_TIP_ERROR
            for err, err_info in variable.error.items():
                hover_string += "(" + err + "): " + err_info + '\n'
            hover_string = hover_string.rstrip('\n')
        if self.is_ghost:
            if not variable.error:
                hover_string = rose.config_editor.VAR_MENU_TIP_LATENT
        self.hover_text = hover_string
        self.button.set_tooltip_text(self.hover_text)
        self.button.show()

    def _perform_add(self):
        self.var_ops.add_var(self.my_variable)

    def _popup_option_menu(self, option_ui, actions, button, time):
        actiongroup = gtk.ActionGroup('Popup')
        actiongroup.set_translation_domain('')
        actiongroup.add_actions(actions)
        uimanager = gtk.UIManager()
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(option_ui)
        remove_item = uimanager.get_widget('/Options/Remove')
        remove_item.connect("activate",
                            lambda b: self.trigger_remove())
        edit_item = uimanager.get_widget('/Options/Edit')
        edit_item.connect("activate", self.launch_edit)
        errors = self.my_variable.error.keys()
        warnings = self.my_variable.warning.keys()
        ns = self.my_variable.metadata["full_ns"]
        search_function = lambda i: self.var_ops.search_for_var(ns, i)
        dialog_func = rose.gtk.util.run_hyperlink_dialog
        for error in errors:
            action_name = "Error_" + error
            if "action='" + action_name + "'" not in option_ui:
                continue
            err_item = uimanager.get_widget('/Options/' + action_name)
            title = rose.config_editor.DIALOG_VARIABLE_ERROR_TITLE.format(
                                error, self.my_variable.metadata["id"])
            err_item.connect("activate",
                             lambda e: dialog_func(
                                              gtk.STOCK_DIALOG_WARNING,
                                              self.my_variable.error[error],
                                              title, search_function))
        for warning in warnings:
            action_name = "Warn_" + warning
            if "action='" + action_name + "'" not in option_ui:
                continue
            warn_item = uimanager.get_widget('/Options/' + action_name)
            title = rose.config_editor.DIALOG_VARIABLE_WARNING_TITLE.format(
                                warning, self.my_variable.metadata["id"])
            warn_item.connect("activate",
                              lambda e: dialog_func(
                                          gtk.STOCK_DIALOG_INFO,
                                          self.my_variable.warning[warning],
                                          title, search_function))
        if 'action="Ignore"' in option_ui:
            ignore_item = uimanager.get_widget('/Options/Ignore')
            if rose.config_editor.WARNING_TYPE_IGNORED in errors:
                # It is an enabled variable that should be trigger-ignored.
                new_reason = {rose.variable.IGNORED_BY_SYSTEM:
                              rose.config_editor.IGNORED_STATUS_MANUAL}
            else:
                # It is a standard enabled variable.
                new_reason = {rose.variable.IGNORED_BY_USER:
                              rose.config_editor.IGNORED_STATUS_MANUAL}
                if (self.my_variable.metadata.get(
                         rose.META_PROP_COMPULSORY) == 
                    rose.META_PROP_VALUE_TRUE):
                    # Only optional enabled variables can be user-ignored.
                    ignore_item.set_sensitive(False)
            ignore_item.connect(
                    "activate",
                    lambda b: self.var_ops.set_var_ignored(
                                 self.my_variable, new_reason))
        elif 'action="Enable"' in option_ui:
            enable_item = uimanager.get_widget('/Options/Enable')
            if (rose.variable.IGNORED_BY_USER in 
                self.my_variable.ignored_reason):
                # It is a user-ignored variable
                if rose.config_editor.WARNING_TYPE_IGNORED in errors:
                    # It is a user-ignored variable that should be
                    # trigger-ignored.
                    enable_item.set_sensitive(False)
            elif (rose.config_editor.WARNING_TYPE_ENABLED not in errors and
                  rose.config_editor.WARNING_TYPE_NOT_TRIGGER not in errors
                  and self.my_variable.metadata.get(rose.META_PROP_COMPULSORY)
                  == rose.META_PROP_VALUE_TRUE):
                # It is a correctly trigger-ignored, compulsory variable.
                enable_item.set_sensitive(False)
            enable_item.connect(
                        "activate",
                        lambda b: self.var_ops.set_var_ignored(
                                       self.my_variable, {}))
        info_item = uimanager.get_widget('/Options/Info')
        info_item.connect("activate", self._launch_info_dialog)
        if (self.my_variable.metadata.get(rose.META_PROP_COMPULSORY) == 
            rose.META_PROP_VALUE_TRUE or self.is_ghost):
            remove_item.set_sensitive(False)
        help_item = uimanager.get_widget('/Options/Help')
        help_item.connect("activate",
                          lambda b: self.launch_help(
                                         self.my_variable.metadata['help']))
        if 'help' not in self.my_variable.metadata:
            help_item.set_sensitive(False)
        url_item = uimanager.get_widget('/Options/Web Help')
        if url_item is not None and 'url' in self.my_variable.metadata:
            url_item.connect("activate",
                             lambda b: self.launch_help(
                                            self.my_variable.metadata['url']))
        if self.is_ghost:
            add_item = uimanager.get_widget('/Options/Add')
            add_item.connect("activate",
                            lambda b: self._perform_add())
        option_menu = uimanager.get_widget('/Options')
        option_menu.attach_to_widget(self.button,
                                     lambda m, w: False)
        option_menu.show()
        option_menu.popup(None, None, None, button, time)
        return False

    def _launch_info_dialog(self, *args):
        changes = self.var_ops.get_var_changes(self.my_variable)
        ns = self.my_variable.metadata["full_ns"]
        search_function = lambda i: self.var_ops.search_for_var(ns, i)
        rose.config_editor.util.launch_node_info_dialog(self.my_variable,
                                                        changes,
                                                        search_function)

    def launch_edit(self, *args):
        text = "\n".join(self.my_variable.comments)
        title = rose.config_editor.DIALOG_TITLE_EDIT_COMMENTS.format(
                                   self.my_variable.metadata['id'])
        rose.gtk.util.run_edit_dialog(text,
                                      finish_hook=self._edit_finish_hook,
                                      title=title)

    def _edit_finish_hook(self, text):
        self.var_ops.set_var_comments(self.my_variable, text.splitlines())
        self.update_status()


class CheckedMenuWidget(MenuWidget):

    """Represent the menu button with a check box instead."""

    def __init__(self, *args):
        super(CheckedMenuWidget, self).__init__(*args)
        self.remove(self.button)
        for string in ["<menuitem action='Add'/>",
                       "<separator name='sepAdd'/>",
                       '<menuitem action="Remove"/>']:
            self.option_ui = self.option_ui.replace(string, "")
        self.checkbutton = gtk.CheckButton()
        self.checkbutton.set_active(not self.is_ghost)
        meta = self.my_variable.metadata
        if (not self.is_ghost and
            meta.get(rose.META_PROP_COMPULSORY) == rose.META_PROP_VALUE_TRUE):
            self.checkbutton.set_sensitive(False)
        self.pack_start(self.checkbutton, expand=False, fill=False, padding=0)
        self.pack_start(self.button, expand=False, fill=False, padding=0)
        self.checkbutton.connect("toggled", self.on_toggle)
        self.checkbutton.show()

    def on_toggle(self, widget):
        """Handle a toggle."""
        if self.is_ghost:
            self._perform_add()
        else:
            self.trigger_remove()
