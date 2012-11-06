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

import time
import webbrowser

import pygtk
pygtk.require('2.0')
import gtk
import pango

import rose.config_editor.pagewidget
import rose.config_editor.stack
import rose.config_editor.util
import rose.config_editor.variable
import rose.formats
import rose.gtk.util
import rose.variable


class ConfigPage(gtk.VBox):

    """Returns a container for a tab."""

    def __init__(self, page_metadata, config_data, ghost_data,
                 variable_ops, sections, get_formats_func, directory=None,
                 sub_data=None, launch_info_func=None, launch_edit_func=None):
        super(ConfigPage, self).__init__(homogeneous=False)
        self.namespace = page_metadata.get('namespace')
        self.ns_is_default = page_metadata.get('ns_is_default')
        self.config_name = page_metadata.get('config_name')
        self.label = page_metadata.get('label')
        self.description = page_metadata.get('description')
        self.help = page_metadata.get('help')
        self.url = page_metadata.get('url')
        self.see_also = page_metadata.get('see_also')
        self.custom_widget = page_metadata.get('widget')
        self.show_modes = page_metadata.get('show_modes')
        self.is_duplicate = (page_metadata.get('duplicate') ==
                             rose.META_PROP_VALUE_TRUE)
        self.section = None
        if sections:
            self.section = sections[0]
        self.sections = sections
        self.icon_path = page_metadata.get('icon')
        self.directory = directory
        self.sub_data = sub_data
        self.launch_info = launch_info_func
        self.launch_edit = launch_edit_func
        namespaces = self.namespace.strip('/').split('/')
        namespaces.reverse()
        if self.description is None:
            self.description = " - ".join(namespaces[:-1])
        else:
            if self.description != '':
                self.description += '\n'
            self.description += " - ".join(namespaces[:-1])
        if self.see_also != '':
            self.description += '\n => ' + self.see_also
        self.panel_data = config_data
        self.ghost_data = ghost_data
        self.variable_ops = variable_ops
        self.trigger_ask_for_config_keys = lambda: get_formats_func(
                                                       self.config_name)
        self.sort_data()
        self.sort_data(ghost=True)
        self.generate_main_container()
        self.get_page()
        self.update_ignored()

    def get_page(self):
        """Generate a container of widgets for page content and a label."""
        self.labelwidget = self.get_label_widget()
        self.scrolled_main_window = gtk.ScrolledWindow()
        self.scrolled_main_window.set_policy(gtk.POLICY_AUTOMATIC,
                                             gtk.POLICY_AUTOMATIC)
        self.scrolled_vbox = gtk.VBox()
        self.scrolled_vbox.show()
        self.scrolled_main_window.add_with_viewport(self.scrolled_vbox)
        self.scrolled_main_window.get_child().set_shadow_type(gtk.SHADOW_NONE)
        self.scrolled_main_window.set_border_width(
                           rose.config_editor.SPACING_SUB_PAGE)
        self.scrolled_vbox.pack_start(self.main_container,
                                      expand=False, fill=True)
        self.scrolled_main_window.show()
        self.info_panel = gtk.VBox(homogeneous=False)
        self.info_panel.show()
        self.generate_page_info_widget()
        self.pack_start(self.info_panel, expand=False, fill=False)
        second_panel = None
        if self.namespace == self.config_name and self.directory is not None:
            self.generate_filesystem_panel()
            second_panel = self.filesystem_panel
        elif self.sub_data is not None:
            self.generate_sub_data_panel()
            second_panel = self.sub_data_panel
        if second_panel is None:
            self.pack_start(self.scrolled_main_window, expand=True, fill=True)
        else:
            self.paned = gtk.VPaned()
            self.paned.pack1(self.scrolled_main_window, resize=True,
                             shrink=True)
            self.paned.pack2(second_panel, resize=True, shrink=True)
            if not self.panel_data:
                self.paned.set_position(rose.config_editor.FILE_PANEL_EXPAND)
            self.paned.show()
            self.pack_start(self.paned, expand=True, fill=True)
        self.show()
        self.scroll_vadj = self.scrolled_main_window.get_vadjustment()
        self.scrolled_main_window.connect(
                     "button-press-event",
                     lambda b, e: e.button == 3 and 
                                  self.launch_add_menu(e.button, e.time))

    def get_label_widget(self, is_detached=False):
        """Return a container of widgets for the notebook tab label."""
        if is_detached:
            location = self.config_name.lstrip('/').split('/')
            location.reverse()
            label = gtk.Label(' - '.join([self.label] + location))
            self.is_detached = True
        else:
            label = gtk.Label(self.label)
            self.is_detached = False
        label.show()
        label_box = gtk.HBox(homogeneous=False)
        if self.icon_path is not None:
            self.label_icon = gtk.Image()
            self.label_icon.set_from_file(self.icon_path)
            self.label_icon.show()
            label_box.pack_start(self.label_icon, expand=False, fill=False,
                                 padding=rose.config_editor.SPACING_SUB_PAGE)
        close_button = rose.gtk.util.CustomButton(
                            stock_id=gtk.STOCK_CLOSE,
                            size=gtk.ICON_SIZE_MENU,
                            as_tool=True)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        setattr(style, "inner-border", [0, 0, 0, 0] )
        close_button.modify_style(style)
        
        label_box.pack_start(label, expand=False, fill=False,
                             padding=rose.config_editor.SPACING_SUB_PAGE)
        if not is_detached:
            label_box.pack_end(close_button, expand=False, fill=False)
        label_box.show()
        event_box = gtk.EventBox()
        event_box.add(label_box)
        close_button.connect('released', lambda b: self.close_self())
        event_box.connect('button_press_event', self.launch_tab_menu)
        event_box.show()
        if self.description is not None:
            event_box.connect("enter-notify-event", self._set_tab_tooltip)
        return event_box

    def _set_tab_tooltip(self, event_box, event):
        tip_text = ""
        if self.description is not None:
            tip_text += self.description
        if self.section is not None:
            comment_format = rose.config_editor.VAR_COMMENT_TIP.format
            for comment_line in self.section.comments:
                tip_text += "\n" + comment_format(comment_line)
        event_box.set_tooltip_text(tip_text)

    def launch_tab_menu(self, event_widget=None, event=None, somewidget=None):
        """Open a popup menu for the tab, if right clicked."""
        if event.button != 3:
            return False
        ui_config_string_start = """<ui> <popup name='Popup'>"""
        ui_config_string_end = """</popup> </ui>"""
        if not self.is_detached:
            ui_config_string_start += """<menuitem action="Open"/>
                                         <separator name="sep1"/>"""
            close_string = """<separator name="close"/>
                              <menuitem action="Close"/>"""
            ui_config_string_end = close_string + ui_config_string_end
        ui_config_string_start += """<menuitem action="Info"/>
                                     <menuitem action="Edit"/>"""
        actions = [
               ('Open', gtk.STOCK_NEW, rose.config_editor.TAB_MENU_OPEN_NEW),
               ('Info', gtk.STOCK_INFO, rose.config_editor.TAB_MENU_INFO),
               ('Edit', gtk.STOCK_EDIT, rose.config_editor.TAB_MENU_EDIT),
               ('Help', gtk.STOCK_HELP, rose.config_editor.TAB_MENU_HELP),
               ('Web_Help', gtk.STOCK_HOME,
                rose.config_editor.TAB_MENU_WEB_HELP),
               ('Close', gtk.STOCK_CLOSE, rose.config_editor.TAB_MENU_CLOSE)]
        if self.help is not None:
            help_string = """<separator name="helpsep"/>
                             <menuitem action="Help"/>"""
            ui_config_string_end = help_string + ui_config_string_end
        if self.url is not None:
            url_string = """<separator name="urlsep"/>
                             <menuitem action="Web_Help"/>"""
            ui_config_string_end = url_string + ui_config_string_end
        
        uimanager = gtk.UIManager()
        actiongroup = gtk.ActionGroup('Popup')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(ui_config_string_start +
                                     ui_config_string_end)
        if not self.is_detached:
            window_item = uimanager.get_widget('/Popup/Open')
            window_item.connect("activate", self.trigger_tab_detach)
            close_item = uimanager.get_widget('/Popup/Close')
            close_item.connect("activate", lambda b: self.close_self())
        edit_item = uimanager.get_widget('/Popup/Edit')
        edit_item.connect("activate", lambda b: self.launch_edit())
        info_item = uimanager.get_widget('/Popup/Info')
        info_item.connect("activate", lambda b: self.launch_info())
        if self.help is not None:
            help_item = uimanager.get_widget('/Popup/Help')
            help_item.connect("activate", lambda b: self.launch_help())
        if self.url is not None:
            url_item = uimanager.get_widget('/Popup/Web_Help')
            url_item.connect("activate", lambda b: self.launch_url())
        tab_menu = uimanager.get_widget('/Popup')
        tab_menu.popup(None, None, None, event.button, event.time)
        return False

    def trigger_tab_detach(self, widget=None):
        """Connect this at a higher level to manage tab detachment."""
        pass

    def reshuffle_for_detached(self, add_button, revert_button, parent):
        """Reshuffle widgets for detached view."""
        focus_child = getattr(self, 'focus_child')
        if hasattr(self, "paned"):
            self.remove(self.paned)
        else:
            self.remove(self.scrolled_main_window)
        self.remove(self.info_panel)
        if hasattr(self, 'tool_hbox'):
            self.remove(self.tool_hbox)
        button_hbox = gtk.HBox(homogeneous=False, spacing=0)
        self.tool_hbox = gtk.HBox(homogeneous=False, spacing=0)
        sep = gtk.VSeparator()
        sep.show()
        sep_vbox = gtk.VBox()
        sep_vbox.pack_start(sep, expand=True, fill=True)
        sep_vbox.set_border_width(rose.config_editor.SPACING_SUB_PAGE)
        sep_vbox.show()
        info_button = rose.gtk.util.CustomButton(
                               stock_id=gtk.STOCK_INFO,
                               as_tool=True,
                               tip_text=rose.config_editor.TAB_MENU_INFO)
        info_button.connect("clicked", lambda m: self.launch_info())
        help_button = rose.gtk.util.CustomButton(
                               stock_id=gtk.STOCK_HELP,
                               as_tool=True,
                               tip_text=rose.config_editor.TAB_MENU_HELP)
        help_button.connect("clicked", self.launch_help)
        url_button = rose.gtk.util.CustomButton(
                              stock_id=gtk.STOCK_HOME,
                              as_tool=True,
                              tip_text=rose.config_editor.TAB_MENU_WEB_HELP)
        url_button.connect("clicked", self.launch_url)
        button_hbox.pack_start(add_button, expand=False, fill=False)
        button_hbox.pack_start(revert_button, expand=False, fill=False)
        button_hbox.pack_start(sep_vbox, expand=False, fill=False)
        button_hbox.pack_start(info_button, expand=False, fill=False)
        if self.help is not None:
            button_hbox.pack_start(help_button, expand=False, fill=False)
        if self.url is not None:
            button_hbox.pack_start(url_button, expand=False, fill=False)
        button_hbox.show()
        button_frame = gtk.Frame()
        button_frame.set_shadow_type(gtk.SHADOW_NONE)
        button_frame.add(button_hbox)
        button_frame.show()
        self.tool_hbox.pack_start(button_frame, expand=False, fill=False)
        label_box = gtk.HBox(homogeneous=False,
                             spacing=rose.config_editor.SPACING_PAGE)
        label_box.pack_start(self.get_label_widget(is_detached=True))
        label_box.show()
        self.tool_hbox.pack_start(label_box, expand=True, fill=True, padding=10)
        self.tool_hbox.show()
        self.pack_start(self.tool_hbox, expand=False, fill=False)
        self.pack_start(self.info_panel, expand=False, fill=True)
        if hasattr(self, "paned"):
            self.pack_start(self.paned, expand=True, fill=True)
        else:
            self.pack_start(self.scrolled_main_window, expand=True, fill=True)
        if isinstance(parent, gtk.Window):
            if parent.get_child() is not None:
                parent.remove(parent.get_child())
        else:
            self.close_self()
        if focus_child is not None:
            focus_child.grab_focus()

    def close_self(self):
        """Delete this instance from a rose.gtk.util.Notebook."""
        parent = self.get_parent()
        my_index = parent.get_page_ids().index(self.namespace)
        parent.remove_page(my_index)
        parent.emit('select-page', False)

    def launch_help(self, *args):
        """Launch the page help."""
        title = rose.config_editor.DIALOG_HELP_TITLE.format(self.label)
        rose.gtk.util.run_hyperlink_dialog(
                                 gtk.STOCK_DIALOG_INFO,
                                 str(self.help),
                                 title)

    def launch_url(self, *args):
        """Launch the page url help."""
        webbrowser.open(str(self.url))

    def update_info(self):
        """Driver routine to update non-variable information."""
        self.generate_page_info_widget()

    def generate_page_info_widget(self):
        """Generates a widget giving information about sections."""
        info_container = gtk.VBox(homogeneous=False)
        info_container.show()
        button_list = []
        label_list = []
        if self.section is None and self.sub_data is None:
            info = rose.config_editor.PAGE_WARNING_NO_CONTENT
            tip = rose.config_editor.PAGE_WARNING_NO_CONTENT_TIP
            error_button = rose.gtk.util.CustomButton(
                                stock_id=gtk.STOCK_DIALOG_WARNING,
                                as_tool=True,
                                tip_text=tip)
            error_label = gtk.Label()
            error_label.set_text(info)
            error_label.show()
            button_list.append(error_button)
            label_list.append(error_label)
        if self.section is not None and self.section.ignored_reason:
            info = rose.config_editor.PAGE_WARNING_IGNORED_SECTION.format(
                        self.section.name)
            tip = rose.config_editor.PAGE_WARNING_IGNORED_SECTION_TIP
            error_button = rose.gtk.util.CustomButton(
                  stock_id=gtk.STOCK_NO,
                  as_tool=True,
                  tip_text=tip)
            error_label = gtk.Label()
            error_label.set_text(info)
            error_label.show()
            button_list.append(error_button)
            label_list.append(error_label)
        elif (self.see_also == '' or
              rose.FILE_VAR_CONTENT not in self.see_also):
            if (self.section is not None and 
                self.section.name.startswith('namelist:')):
                error_button = rose.gtk.util.CustomButton(
                      stock_id=gtk.STOCK_DIALOG_WARNING,
                      as_tool=True,
                      tip_text=rose.config_editor.ERROR_ORPHAN_SECTION_TIP)
                error_label = gtk.Label()
                error_label.set_text(rose.config_editor.ERROR_ORPHAN_SECTION)
                error_label.show()
                button_list.append(error_button)
                label_list.append(error_label)
        for sect_data in self.sections:
            for err, info in sect_data.error.items():
                error_button = rose.gtk.util.CustomButton(
                      stock_id=gtk.STOCK_DIALOG_ERROR,
                      as_tool=True,
                      tip_text=info)
                error_label = gtk.Label()
                error_label.set_text(
                            rose.config_editor.PAGE_WARNING.format(
                                 err, sect_data.name))
                error_label.show()
                button_list.append(error_button)
                label_list.append(error_label)
        for button, label in zip(button_list, label_list):
            var_hbox = gtk.HBox(homogeneous=False)
            var_hbox.pack_start(button, expand=False, fill=False)
            var_hbox.pack_start(label, expand=False, fill=True,
                                padding=rose.config_editor.SPACING_SUB_PAGE)
            var_hbox.show()
            info_container.pack_start(var_hbox, expand=False, fill=True)
        if button_list:
            sep = gtk.HSeparator()
            sep.show()
            info_container.pack_end(
                                sep, expand=True, fill=True,
                                padding=rose.config_editor.SPACING_SUB_PAGE)
        for child in self.info_panel.get_children():
            self.info_panel.remove(child)
        self.info_panel.pack_start(info_container, expand=False, fill=True)

    def generate_filesystem_panel(self):
        """Generate a widget to view the file hierarchy."""
        self.filesystem_panel = rose.config_editor.panel.FileSystemPanel(
                                                         self.directory)

    def generate_sub_data_panel(self):
        """Generate a panel giving a summary of other page data."""
        s_func = lambda i: self.variable_ops.search_for_var(self.namespace, i)
        self.sub_data_panel = rose.config_editor.panel.SummaryDataPanel(
                                          self.sub_data["sections"],
                                          self.sub_data["variables"],
                                          s_func, self.is_duplicate)

    def update_sub_data(self):
        """Update the sub (summary) data panel."""
        if self.sub_data is not None:
            self.sub_data_panel.update_tree_model(self.sub_data["sections"],
                                                  self.sub_data["variables"])

    def launch_add_menu(self, button, my_time):
        """Pop up a contextual add variable menu."""
        add_menu = self.get_add_menu()
        if add_menu is None:
            return False
        add_menu.popup(None, None, None, button, my_time)
        return False

    def get_add_menu(self):
        def _add_var_from_item(item):
            for variable in self.ghost_data:
                if variable.metadata['id'] == item.var_id:
                    self.add_row(variable)
                    return
        if "/file/" in self.namespace:  # Don't like this.
            return None
        add_ui_start = """<ui> <popup name='Popup'>
                         <menu action="Add meta">"""
        add_ui_end = """</menu> </popup> </ui>"""
        actions =  [('Add meta',  gtk.STOCK_DIRECTORY,
                     rose.config_editor.ADD_MENU_META)]
        missing_variables = []
        section_choices = []
        for sect_data in self.sections:
            if not sect_data.ignored_reason:
                section_choices.append(sect_data.name)
        section_choices.sort(rose.config.sort_settings)
        if self.ns_is_default and section_choices:
            add_ui_start = add_ui_start.replace(
                            "'Popup'>",
                            """'Popup'><menuitem action="Add blank"/>""")
            text = rose.config_editor.ADD_MENU_BLANK
            if len(section_choices) > 1:
                text = rose.config_editor.ADD_MENU_BLANK_MULTIPLE
            actions.insert(0, ('Add blank', gtk.STOCK_NEW, text))
        ghost_list = [v for v in self.ghost_data]
        sorter = rose.config.sort_settings
        ghost_list.sort(lambda v, w: sorter(v.metadata['id'],
                                            w.metadata['id']))
        for variable in ghost_list:
            add_ui_start += ('<menuitem action="' +
                             variable.metadata['id'] + '"/>')
            actions.append((variable.metadata['id'], None,
                            "_" + variable.name.replace('_', ' ')))
        add_ui = add_ui_start + add_ui_end
        uimanager = gtk.UIManager()
        actiongroup = gtk.ActionGroup('Popup')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(add_ui)
        if 'Add blank' in add_ui:
            blank_item = uimanager.get_widget('/Popup/Add blank')
            if len(section_choices) > 1:
                blank_item.connect("activate", 
                                   lambda b: self._launch_section_chooser(
                                                   section_choices))
            else:
                blank_item.connect("activate", lambda b: self.add_row())
        for variable in ghost_list:
            named_item = uimanager.get_widget('/Popup/Add meta/'
                                              + variable.metadata['id'])
            named_item.var_id = variable.metadata['id']
            named_item.set_tooltip_text(variable.metadata['id'])
            named_item.connect("activate", _add_var_from_item)
        if 'Add blank' in add_ui or self.ghost_data:
            return uimanager.get_widget('/Popup')
        return None

    def _launch_section_chooser(self, section_choices):
        """Choose a section to add a blank variable to."""
        section = rose.gtk.util.run_choices_dialog(
                       rose.config_editor.DIALOG_LABEL_CHOOSE_SECTION_ADD_VAR,
                       section_choices,
                       rose.config_editor.DIALOG_TITLE_CHOOSE_SECTION)
        if section is not None:
            self.add_row(section=section)

    def add_row(self, variable=None, section=None):
        """Append a new variable to the page's main variable list.

        If variable is None, a blank name/value/metadata variable is added.
        This is only allowed where there are not multiple config sections
        represented in the namespace, as otherwise the location of the
        variable in the configuration data is badly defined.

        """
        if variable is None:
            if self.section is None and section is None:
                return False
            creation_time = str(time.time()).replace('.', '_')
            if section is None:
                sect = self.section.name
            else:
                sect = section
            v_id = sect + '=null' + creation_time
            variable = rose.variable.Variable('', '', 
                                              {'id': v_id, 
                                               'full_ns': self.namespace})
            if section is None and self.section.ignored_reason:
                # Cannot add to an ignored section.
                return False
        self.variable_ops.add_var(variable)
        if hasattr(self.main_container, 'add_variable_widget'):
            self.main_container.add_variable_widget(variable)
            self.trigger_update_status()
        else:
            self.refresh()
        self.update_ignored()
        self.set_main_focus(variable.metadata.get('id'))

    def generate_main_container(self):
        """Choose a container to interface with variables in panel_data."""
        if self.custom_widget is not None:
            self.main_container = self.custom_widget(
                                   self.panel_data,
                                   self.ghost_data,
                                   self.variable_ops,
                                   self.show_modes)
        std_table = rose.config_editor.pagewidget.standard.PageTable
        file_chooser = rose.config_editor.pagewidget.chooser.PageFormatTree
        disc_table = rose.config_editor.pagewidget.standard.PageLatentTable
        if "/file/" in self.namespace:  # Don't like this!
            self.main_container = file_chooser(
                                       self.panel_data,
                                       self.ghost_data,
                                       self.variable_ops,
                                       self.show_modes,
                                       self.trigger_ask_for_config_keys)
        elif self.namespace == "/discovery":
            self.main_container = disc_table(self.panel_data,
                                             self.ghost_data,
                                             self.variable_ops,
                                             self.show_modes)
        else:
            self.main_container = std_table(self.panel_data,
                                            self.ghost_data,
                                            self.variable_ops,
                                            self.show_modes)

    def validate_errors(self, variable_id=None):
        """Check if there are there errors in variables on this page."""
        if variable_id is None:
            bad_list = []
            for variable in self.panel_data + self.ghost_data:
                bad_list += variable.error.items()
            return bad_list
        else:
            for variable in self.panel_data + self.ghost_data:
                if variable.metadata.get('id') == variable_id:
                    if variable.error == {}:
                        return None
                    return variable.error.items()
        return None

    def choose_focus(self, focus_variable=None):
        """Select a widget to have the focus on page generation."""
        if self.custom_widget is not None:
            return
        if self.show_modes['latent']:
            for widget in self.get_main_variable_widgets():
                if hasattr(widget.get_parent(), 'variable'):
                    if widget.get_parent().variable.name == '':
                        widget.get_parent().grab_focus()
                        return
        names = [v.name for v in (self.panel_data + self.ghost_data)]
        if focus_variable is None or focus_variable.name not in names:
            return
        if self.panel_data:
            for widget in self.get_main_variable_widgets():
                if hasattr(widget.get_parent(), 'variable'):
                    var = widget.get_parent().variable
                    if var.name == focus_variable.name:
                        if (var.metadata.get('id') ==
                            focus_variable.metadata.get('id')):
                            widget.get_parent().grab_focus()
                            return

    def refresh(self, only_this_var_id=None):
        """Reload the page or selectively refresh widgets for one variable."""
        if only_this_var_id is None:
            self.generate_page_info_widget()
            return self.sort_main(remake_forced=True)
        variable = None
        for variable in self.panel_data + self.ghost_data:
            if variable.metadata['id'] == only_this_var_id:
                break
        else:
            return self.sort_main(remake_forced=True)
        var_name = variable.name
        var_id = variable.metadata['id']
        widget_for_var = {}
        for widget in self.get_main_variable_widgets():
            if hasattr(widget, 'variable'):
                target_id = widget.variable.metadata['id']
                target_widget = widget
            else:
                target_id = widget.get_parent().variable.metadata['id']
                target_widget = widget.get_parent()
            widget_for_var.update({target_id: target_widget})
        if variable in self.panel_data:
            if var_id in widget_for_var:
                widget = widget_for_var[var_id]
                if widget.is_ghost:
                    # Then it is an added ghost variable.
                    return self.handle_add_var_widget(variable)
                # Then it has an existing variable widget.
                if ((rose.META_PROP_TYPE in widget.errors) != 
                    (rose.META_PROP_TYPE in variable.error) and
                    hasattr(widget, "needs_type_error_refresh") and
                    not widget.needs_type_error_refresh()):
                    return widget.type_error_refresh(variable)
                else:
                    return self.handle_reload_var_widget(variable)
            # Then there were no widgets for this variable. Insert it.
            return self.handle_add_var_widget(variable)
        else:
            if (var_id in widget_for_var and
                widget_for_var[var_id].is_ghost):
                # It is a latent variable that needs a refresh.
                return self.handle_reload_var_widget(variable)
            # It is a normal variable that has been removed.
            return self.handle_remove_var_widget(variable)

    def handle_add_var_widget(self, variable):
        if hasattr(self.main_container, 'add_variable_widget'):
            self.main_container.add_variable_widget(variable)
            self.update_ignored()
        else:
            self.refresh()
        self.set_main_focus(variable.metadata.get('id'))

    def handle_reload_var_widget(self, variable):
        if hasattr(self.main_container, 'reload_variable_widget'):
            self.main_container.reload_variable_widget(variable)
            self.update_ignored()
        else:
            self.refresh()

    def handle_remove_var_widget(self, variable):
        if hasattr(self.main_container, 'remove_variable_widget'):
            self.main_container.remove_variable_widget(variable)
            self.update_ignored()
        else:
            self.refresh()

    def sort_main(self, column_index=0, ascending=True,
                  remake_forced=False):
        """Regenerate a sorted table, according to the arguments.

        column_index maps as {0: index, 1: title, 2: key, 3: value}.
        ascending specifies whether to use 'normal' cmp or 'reversed' cmp
        arguments.

        """
        if self.sort_data(column_index, ascending) or remake_forced:
            focus_var = None
            focus_widget = self.get_toplevel().focus_child
            if (focus_widget is not None and
                hasattr(focus_widget.get_parent(), 'variable')):
                focus_var = focus_widget.get_parent().variable
            self.main_container.destroy()
            self.generate_main_container()
            self.scrolled_vbox.pack_start(self.main_container, expand=False,
                                          fill=True)
            self.choose_focus(focus_var)
            self.update_ignored()
            self.trigger_update_status()

    def get_main_variable_widgets(self):
        """Return the widgets within the main_container."""
        return self.get_widgets_with_attribute('variable')

    def get_widgets_with_attribute(self, att_name, parent_widget=None):
        """Return widgets with a certain named attribute."""
        if parent_widget is None:
            widget_list = self.main_container.get_children()
        else:
            widget_list = parent_widget.get_children()
        i = 0
        while i < len(widget_list):
            widget = widget_list[i]
            if not (hasattr(widget.get_parent(), att_name) or
                    hasattr(widget, att_name)):
                widget_list.pop(i)
                i -= 1
                if hasattr(widget, 'get_children'):
                    widget_list.extend(widget.get_children())
                elif hasattr(widget, 'get_child'):
                    widget_list.append(widget.get_child())
            i += 1
        return widget_list

    def set_main_focus(self, var_id):
        """Set the main focus on the key-matched variable widget."""
        widget_list = self.get_main_variable_widgets()
        for widget in widget_list:
            if (hasattr(widget.get_parent(), 'variable') and
                widget.get_parent().variable.metadata['id'] == var_id):
                widget.get_parent().grab_focus(self.main_container)
                return True
        for widget in widget_list:
            if (hasattr(widget, 'variable') and
                widget.variable.metadata['id'] == var_id):
                widget.grab_focus()
                return True
        return False

    def react_to_show_modes(self, mode_key, is_mode_on):
        self.show_modes[mode_key] = is_mode_on
        if hasattr(self.main_container, 'show_mode_change'):
            react_func = getattr(self.main_container, 'show_mode_change')
            react_func(mode_key, is_mode_on)
            self.update_ignored()
        elif mode_key in [rose.config_editor.SHOW_MODE_IGNORED,
                          rose.config_editor.SHOW_MODE_USER_IGNORED]:
            self.update_ignored()
        else:
            self.refresh()

    def refresh_widget_status(self):
        """Refresh the status of all variable widgets."""
        for widget in self.get_widgets_with_attribute('update_status'):
            if hasattr(widget.get_parent(), 'update_status'):
                widget.get_parent().update_status()
            else:
                widget.update_status()

    def update_ignored(self):
        """Set variable widgets to 'ignored' or 'enabled' status."""
        new_tuples = []
        for variable in self.panel_data + self.ghost_data:
            if variable.ignored_reason:
                new_tuples.append((variable.metadata['id'],
                                   variable.ignored_reason.copy()))
        target_widgets_done = []
        refresh_list = []
        relevant_errs = [rose.config_editor.WARNING_TYPE_ENABLED,
                         rose.config_editor.WARNING_TYPE_IGNORED]
        for widget in self.get_main_variable_widgets():
            if hasattr(widget.get_parent(), 'variable'):
                target = widget.get_parent()
            elif hasattr(widget, 'variable'):
                target = widget
            else:
                continue
            if target in target_widgets_done:
                continue
            for var_id, help_text in [x for x in new_tuples]:
                if target.variable.metadata.get('id') == var_id:
                    self._set_widget_ignored(target, help_text)
                    new_tuples.remove((var_id, help_text))
                    break
            else:
                if hasattr(target, 'is_ignored') and target.is_ignored:
                    self._set_widget_ignored(target, '', enabled=True)
            if (any([e in target.errors for e in relevant_errs]) or
                any([e in target.variable.error for e in relevant_errs])):
                if ([e in target.errors for e in relevant_errs] !=
                    [e in target.variable.error for e in relevant_errs]):
                        refresh_list.append(
                                        target.variable.metadata['id'])
                        target.errors = target.variable.error.keys()
            target_widgets_done.append(target)
        for variable_id in refresh_list:
            self.refresh(variable_id)

    def _check_show_ignored_reason(self, ignored_reason):
        """Return whether we should show this state."""
        mode = self.show_modes
        if ignored_reason.keys() == [rose.variable.IGNORED_BY_USER]:
            return (mode[rose.config_editor.SHOW_MODE_IGNORED] or
                    mode[rose.config_editor.SHOW_MODE_USER_IGNORED])
        return mode[rose.config_editor.SHOW_MODE_IGNORED]

    def _set_widget_ignored(self, widget, help_text, enabled=False):
        if self._check_show_ignored_reason(widget.variable.ignored_reason):
            if hasattr(widget, 'show'):
                widget.show()
            if hasattr(widget, 'set_ignored'):
                widget.set_ignored()
            elif hasattr(widget, 'set_sensitive'):
                widget.set_sensitive(enabled)
        else:
            if hasattr(widget, 'hide') and hasattr(widget, 'show'):
                if hasattr(widget, 'set_ignored'):
                    widget.set_ignored()
                elif hasattr(widget, 'set_sensitive'):
                    widget.set_sensitive(enabled)
                if enabled:
                    widget.show()
                elif not widget.variable.error:
                    widget.hide()

    def reload_from_data(self, new_config_data, new_ghost_data):
        """Load the new data into the page as gracefully as possible."""
        for variable in [v for v in self.panel_data]:
            # Remove redundant existing variables
            var_id = variable.metadata.get('id')
            var_name = variable.name
            new_id_list = [x.metadata['id'] for x in new_config_data]
            if var_id not in new_id_list or var_id is None:
                self.variable_ops.remove_var(variable)
        for variable in [v for v in self.ghost_data]:
            # Remove redundant metadata variables.
            var_id = variable.metadata.get('id')
            var_name = variable.name
            new_id_list = [x.metadata['id'] for x in new_ghost_data]
            if var_id not in new_id_list:
                self.variable_ops.remove_var(variable)  # From the ghost list.
        for variable in new_config_data:
            # Update or add variables
            var_id = variable.metadata['id']
            var_name = variable.name
            old_id_list = [x.metadata.get('id') for x in self.panel_data]
            if var_id in old_id_list:
                old_variable = self.panel_data[old_id_list.index(var_id)]
                old_variable.metadata = variable.metadata
                if old_variable.value != variable.value:
                    self.variable_ops.set_var_value(old_variable, 
                                                    variable.value)
                old_ign_set = set(old_variable.ignored_reason.keys())
                new_ign_set = set(variable.ignored_reason.keys())
                if old_ign_set != new_ign_set:
                    self.variable_ops.set_var_ignored(
                                      old_variable,
                                      variable.ignored_reason.copy(),
                                      override=True)
                else:
                    # The types are the same, but pass on the info.
                    old_variable.ignored_reason = (
                                         variable.ignored_reason.copy())
            else:
                self.variable_ops.add_var(variable)
        for variable in new_ghost_data:
            # Update or remove variables
            var_id = variable.metadata['id']
            var_name = variable.name
            old_id_list = [x.metadata.get('id')
                           for x in self.ghost_data]
            if var_id in old_id_list:
                index = old_id_list.index(var_id)
                old_variable = self.ghost_data[index]
                old_variable.metadata = variable.metadata
                old_variable.ignored_reason = variable.ignored_reason.copy()
                if old_variable.value != variable.value:
                    old_variable.value = variable.value
            else:
                self.ghost_data.append(variable)
        self.refresh()
        self.trigger_update_status()
       # if self.sort_data is not None:
       #    self.update_sort_data()
        return False

    def sort_data(self, column_index=0, ascending=True, ghost=False):
        """Sort page data by an attribute specified with column_index.

        The column_index maps to attributes like this -
        {0: index, 1:title, 2:key, 3:value}, where index is the metadata
        index (or null string if there isn't one) plus the key. Sorting
        does not affect the undo stack.

        """
        sorted_data = []
        if ghost:
            datavars = self.ghost_data
        else:
            datavars = self.panel_data
        for variable in datavars:
            title = variable.metadata.get(rose.META_PROP_TITLE, variable.name)
            var_id = variable.metadata.get('id', variable.name)
            key = (variable.metadata.get(rose.META_PROP_SORT_KEY, '') +
                   '~' + var_id)
            if variable.name == '':
                key = ''
            sorted_data.append((key, title, variable.name,
                                variable.value, variable))
        ascending_cmp = lambda x, y: self._null_cmp(x[column_index], x[2],
                                                    y[column_index], y[2])
        descending_cmp = lambda x, y: self._null_cmp(y[column_index], x[2],
                                                     x[column_index], y[2])
        if ascending:
            sorted_data.sort(ascending_cmp)
        else:
            sorted_data.sort(descending_cmp)
        if [x[4] for x in sorted_data] == datavars:
            return False
        for i, (key, title, name, value, variable) in enumerate(sorted_data):
            datavars[i] = variable
        return True

    def _null_cmp(self, x, x_name, y, y_name):
        if x_name == '' or y_name == '':
            return (x_name == '') - (y_name == '')
        return rose.config.sort_settings(x, y)

    def trigger_update_status(self):
        """Connect this at a higher level to allow changed data signals."""
        pass
