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
import time
import webbrowser

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import metomi.rose.config_editor.panelwidget
import metomi.rose.config_editor.pagewidget
import metomi.rose.config_editor.stack
import metomi.rose.config_editor.util
import metomi.rose.config_editor.variable
import metomi.rose.formats
import metomi.rose.gtk.dialog
import metomi.rose.gtk.util
import metomi.rose.resource
import metomi.rose.variable

from functools import cmp_to_key


class ConfigPage(Gtk.Box):

    """Returns a container for a tab."""

    def __init__(self, page_metadata, config_data, ghost_data, section_ops,
                 variable_ops, sections, latent_sections, get_formats_func,
                 reporter, directory=None, sub_data=None, sub_ops=None,
                 launch_info_func=None, launch_edit_func=None,
                 launch_macro_func=None):
        super(ConfigPage, self).__init__(homogeneous=False)
        self.namespace = page_metadata.get('namespace')
        self.ns_is_default = page_metadata.get('ns_is_default')
        self.config_name = page_metadata.get('config_name')
        self.label = page_metadata.get('label')
        self.description = page_metadata.get('description')
        self.help = page_metadata.get('help')
        self.url = page_metadata.get('url')
        self.see_also = page_metadata.get('see_also')
        self.custom_macros = page_metadata.get('macro', {})
        self.custom_widget = page_metadata.get('widget')
        self.custom_sub_widget = page_metadata.get('widget_sub_ns')
        self.show_modes = page_metadata.get('show_modes')
        self.is_duplicate = (page_metadata.get('duplicate') ==
                             metomi.rose.META_PROP_VALUE_TRUE)
        self.section = None
        if sections:
            self.section = sections[0]
        self.sections = sections
        self.latent_sections = latent_sections
        self.icon_path = page_metadata.get('icon')
        self.reporter = reporter
        self.directory = directory
        self.sub_data = sub_data
        self.sub_ops = sub_ops
        self.launch_info = launch_info_func
        self.launch_edit = launch_edit_func
        self._launch_macro_func = launch_macro_func
        namespaces = self.namespace.strip('/').split('/')
        namespaces.reverse()
        self.info = ""
        if self.description is None:
            self.info = " - ".join(namespaces[:-1])
        else:
            if self.description != '':
                self.info = self.description + '\n'
            self.info += " - ".join(namespaces[:-1])
        if self.see_also != '':
            self.info += '\n => ' + self.see_also
        self.panel_data = config_data
        self.ghost_data = ghost_data
        self.section_ops = section_ops
        self.variable_ops = variable_ops
        self.trigger_ask_for_config_keys = (
            lambda: get_formats_func(self.config_name))
        self.sort_data()
        self.sort_data(ghost=True)
        self._last_info_labels = None
        self.generate_main_container()
        self.get_page()
        self.update_ignored(no_refresh=True)

    def get_page(self):
        """Generate a container of widgets for page content and a label."""
        self.labelwidget = self.get_label_widget()
        self.scrolled_main_window = Gtk.ScrolledWindow()
        self.scrolled_main_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                             Gtk.PolicyType.AUTOMATIC)
        self.scrolled_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scrolled_vbox.show()
        self.scrolled_main_window.add_with_viewport(self.scrolled_vbox)
        self.scrolled_main_window.get_child().set_shadow_type(Gtk.ShadowType.NONE)
        self.scrolled_main_window.set_border_width(
            metomi.rose.config_editor.SPACING_SUB_PAGE)
        self.scrolled_vbox.pack_start(self.main_container,
                                      expand=False, fill=True, padding=0)
        self.scrolled_main_window.show()
        self.main_vpaned = Gtk.VPaned()
        self.info_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False)
        self.info_panel.show()
        self.update_info()
        second_panel = None
        if self.namespace == self.config_name and self.directory is not None:
            self.generate_filesystem_panel()
            second_panel = self.filesystem_panel
        elif self.sub_data is not None:
            self.generate_sub_data_panel()
            second_panel = self.sub_data_panel
        self.vpaned = Gtk.VPaned()
        if self.panel_data:
            self.vpaned.pack1(self.scrolled_main_window, resize=True,
                              shrink=True)
            if second_panel is not None:
                self.vpaned.pack2(second_panel, resize=False, shrink=True)
        elif second_panel is not None:
            self.vpaned.pack1(self.scrolled_main_window, resize=False,
                              shrink=True)
            self.vpaned.pack2(second_panel, resize=True, shrink=True)
            self.vpaned.set_position(metomi.rose.config_editor.FILE_PANEL_EXPAND)
        else:
            self.vpaned.pack1(self.scrolled_main_window, resize=True,
                              shrink=True)
        self.vpaned.show()
        self.main_vpaned.pack2(self.vpaned)
        self.main_vpaned.show()
        self.pack_start(self.main_vpaned, expand=True, fill=True)
        self.show()
        self.scroll_vadj = self.scrolled_main_window.get_vadjustment()
        self.scrolled_main_window.connect(
            "button-press-event",
            self._handle_click_main_window)

    def _handle_click_main_window(self, widget, event):
        if event.button != 3:
            return False
        self.launch_add_menu(event.button, event.time)
        return False

    def get_label_widget(self, is_detached=False):
        """Return a container of widgets for the notebook tab label."""
        if is_detached:
            location = self.config_name.lstrip('/').split('/')
            location.reverse()
            label = Gtk.Label(label=' - '.join([self.label] + location))
            self.is_detached = True
        else:
            label = Gtk.Label(label=self.label)
            self.is_detached = False
        label.show()
        label_event_box = Gtk.EventBox()
        label_event_box.add(label)
        label_event_box.show()
        if self.help or self.url:
            label_event_box.connect("enter-notify-event",
                                    self._handle_enter_label)
            label_event_box.connect("leave-notify-event",
                                    self._handle_leave_label)
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False)
        if self.icon_path is not None:
            self.label_icon = Gtk.Image()
            self.label_icon.set_from_file(self.icon_path)
            self.label_icon.show()
            label_box.pack_start(self.label_icon, expand=False, fill=False,
                                 padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        close_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_CLOSE, size=Gtk.IconSize.MENU, as_tool=True)
        style = Gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        setattr(style, "inner-border", [0, 0, 0, 0])
        close_button.modify_style(style)

        label_box.pack_start(label_event_box, expand=False, fill=False,
                             padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        if not is_detached:
            label_box.pack_end(close_button, expand=False, fill=False, padding=0)
        label_box.show()
        event_box = Gtk.EventBox()
        event_box.add(label_box)
        close_button.connect('released', lambda b: self.close_self())
        event_box.connect('button_press_event', self._handle_click_tab)
        event_box.show()
        if self.info is not None:
            event_box.connect("enter-notify-event", self._set_tab_tooltip)
        return event_box

    def _handle_enter_label(self, label_event_box, event=None):
        label = label_event_box.get_child()
        att_list = label.get_attributes()
        if att_list is None:
            att_list = Pango.AttrList()
        att_list.insert(Pango.AttrUnderline(Pango.Underline.SINGLE,
                                            start_index=0,
                                            end_index=-1))
        label.set_attributes(att_list)

    def _handle_leave_label(self, label_event_box, event=None):
        label = label_event_box.get_child()
        att_list = label.get_attributes()
        if att_list is None:
            att_list = Pango.AttrList()
        att_list = att_list.filter(lambda a:
                                   a.type != Pango.ATTR_UNDERLINE)
        if att_list is None:
            # This is messy but necessary.
            att_list = Pango.AttrList()
        label.set_attributes(att_list)

    def _set_tab_tooltip(self, event_box, event):
        tip_text = ""
        if self.info is not None:
            tip_text += self.info
        if self.section is not None:
            comment_format = metomi.rose.config_editor.VAR_COMMENT_TIP.format
            for comment_line in self.section.comments:
                tip_text += "\n" + comment_format(comment_line)
        event_box.set_tooltip_text(tip_text)

    def _handle_click_tab(self, event_widget, event):
        if event.button == 3:
            return self.launch_tab_menu(event)
        if self.main_vpaned.get_mapped():
            if self.help:
                return self.launch_help()
            if self.url:
                return self.launch_url()

    def launch_tab_menu(self, event):
        """Open a popup menu for the tab, if right clicked."""
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
            ('Open', Gtk.STOCK_NEW, metomi.rose.config_editor.TAB_MENU_OPEN_NEW),
            ('Info', Gtk.STOCK_INFO, metomi.rose.config_editor.TAB_MENU_INFO),
            ('Edit', Gtk.STOCK_EDIT, metomi.rose.config_editor.TAB_MENU_EDIT),
            ('Help', Gtk.STOCK_HELP, metomi.rose.config_editor.TAB_MENU_HELP),
            ('Web_Help', Gtk.STOCK_HOME,
             metomi.rose.config_editor.TAB_MENU_WEB_HELP),
            ('Close', Gtk.STOCK_CLOSE, metomi.rose.config_editor.TAB_MENU_CLOSE)]
        if self.help is not None:
            help_string = """<separator name="helpsep"/>
                             <menuitem action="Help"/>"""
            ui_config_string_end = help_string + ui_config_string_end
        if self.url is not None:
            url_string = """<separator name="urlsep"/>
                             <menuitem action="Web_Help"/>"""
            ui_config_string_end = url_string + ui_config_string_end

        uimanager = Gtk.UIManager()
        actiongroup = Gtk.ActionGroup('Popup')
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
        button_hbox = Gtk.Box(homogeneous=False, spacing=0)
        self.tool_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=0)
        sep = Gtk.VSeparator()
        sep.show()
        sep_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sep_vbox.pack_start(sep, expand=True, fill=True, padding=0)
        sep_vbox.set_border_width(metomi.rose.config_editor.SPACING_SUB_PAGE)
        sep_vbox.show()
        info_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_INFO,
            as_tool=True,
            tip_text=metomi.rose.config_editor.TAB_MENU_INFO)
        info_button.connect("clicked", lambda m: self.launch_info())
        help_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_HELP,
            as_tool=True,
            tip_text=metomi.rose.config_editor.TAB_MENU_HELP)
        help_button.connect("clicked", self.launch_help)
        url_button = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_HOME,
            as_tool=True,
            tip_text=metomi.rose.config_editor.TAB_MENU_WEB_HELP)
        url_button.connect("clicked", self.launch_url)
        button_hbox.pack_start(add_button, expand=False, fill=False, padding=0)
        button_hbox.pack_start(revert_button, expand=False, fill=False, padding=0)
        button_hbox.pack_start(sep_vbox, expand=False, fill=False, padding=0)
        button_hbox.pack_start(info_button, expand=False, fill=False, padding=0)
        if self.help is not None:
            button_hbox.pack_start(help_button, expand=False, fill=False, padding=0)
        if self.url is not None:
            button_hbox.pack_start(url_button, expand=False, fill=False, padding=0)
        button_hbox.show()
        button_frame = Gtk.Frame()
        button_frame.set_shadow_type(Gtk.ShadowType.NONE)
        button_frame.add(button_hbox)
        button_frame.show()
        self.tool_hbox.pack_start(button_frame, expand=False, fill=False, padding=0)
        label_box = Gtk.Box(homogeneous=False,
                             spacing=metomi.rose.config_editor.SPACING_PAGE)
        # Had to remove True, True, 0 in below like Ben F
        label_box.pack_start(self.get_label_widget(is_detached=True))
        label_box.show()
        self.tool_hbox.pack_start(
            label_box, expand=True, fill=True, padding=10)
        self.tool_hbox.show()
        self.pack_start(self.tool_hbox, expand=False, fill=False)
        self.reorder_child(self.tool_hbox, 0)
        if isinstance(parent, Gtk.Window):
            if parent.get_child() is not None:
                parent.remove(parent.get_child())
        else:
            self.close_self()
        if focus_child is not None:
            focus_child.grab_focus()

    def close_self(self):
        """Delete this instance from a metomi.rose.gtk.util.Notebook."""
        parent = self.get_parent()
        my_index = parent.get_page_ids().index(self.namespace)
        parent.remove_page(my_index)
        parent.emit('select-page', False)

    def launch_help(self, *args):
        """Launch the page help."""
        title = metomi.rose.config_editor.DIALOG_HELP_TITLE.format(self.label)
        metomi.rose.gtk.dialog.run_hyperlink_dialog(
            Gtk.STOCK_DIALOG_INFO, str(self.help), title)

    def launch_url(self, *args):
        """Launch the page url help."""
        webbrowser.open(str(self.url))

    def update_info(self):
        """Driver routine to update non-variable information."""
        button_list, label_list, _ = self._get_page_info_widgets()
        if [l.get_text() for l in label_list] == self._last_info_labels:
            # No change - do not redraw.
            return False
        self.generate_page_info(button_list, label_list)
        has_content = (self.info_panel.get_children() and
                       self.info_panel.get_children()[0].get_children())
        if self.info_panel in self.main_vpaned.get_children():
            if not has_content:
                self.main_vpaned.remove(self.info_panel)
        elif has_content:
            self.main_vpaned.pack1(self.info_panel)

    def generate_page_info(self, button_list=None, label_list=None, info=None):
        """Generate a widget giving information about sections."""
        info_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False)
        info_container.show()
        if button_list is None or label_list is None or info is None:
            button_list, label_list, info = self._get_page_info_widgets()
        self._last_info_labels = [l.get_text() for l in label_list]
        for button, label in zip(button_list, label_list):
            var_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False)
            var_hbox.pack_start(button, expand=False, fill=False, padding=0)
            var_hbox.pack_start(label, expand=False, fill=True,
                                padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
            var_hbox.show()
            info_container.pack_start(var_hbox, expand=False, fill=True)
        # Add page help.
        if self.description:
            help_label = metomi.rose.gtk.util.get_hyperlink_label(
                self.description, search_func=self.search_for_id)
            help_label_window = Gtk.ScrolledWindow()
            help_label_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                         Gtk.PolicyType.AUTOMATIC)
            help_label_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            help_label_hbox.pack_start(help_label, expand=False, fill=False, padding=0)
            help_label_hbox.show()
            help_label_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            help_label_vbox.pack_start(
                help_label_hbox, expand=False, fill=False, padding=0)
            help_label_vbox.show()
            help_label_window.add_with_viewport(help_label_vbox)
            help_label_window.get_child().set_shadow_type(Gtk.ShadowType.NONE)
            help_label_window.show()
            width, height = help_label_window.size_request()
            if info == "Blank page - no data":
                self.main_vpaned.set_position(
                    metomi.rose.config_editor.SIZE_WINDOW[1] * 100)
            else:
                height = min([metomi.rose.config_editor.SIZE_WINDOW[1] / 3,
                              help_label.size_request()[1]])
            help_label_window.set_size_request(width, height)
            help_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            help_hbox.pack_start(help_label_window, expand=True, fill=True,
                                 padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
            help_hbox.show()
            info_container.pack_start(
                help_hbox, expand=True, fill=True,
                padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        for child in self.info_panel.get_children():
            self.info_panel.remove(child)
        self.info_panel.pack_start(info_container, expand=True, fill=True)

    def generate_filesystem_panel(self):
        """Generate a widget to view the file hierarchy."""
        self.filesystem_panel = (
            metomi.rose.config_editor.panelwidget.filesystem.FileSystemPanel(
                self.directory))

    def generate_sub_data_panel(self, override_custom=False):
        """Generate a panel giving a summary of other page data."""
        args = (self.sub_data["sections"],
                self.sub_data["variables"],
                self.section_ops,
                self.variable_ops,
                self.search_for_id,
                self.sub_ops,
                self.is_duplicate)
        if self.custom_sub_widget is not None and not override_custom:
            widget_name_args = self.custom_sub_widget.split(None, 1)
            if len(widget_name_args) > 1:
                widget_path, widget_args = widget_name_args
            else:
                widget_path, widget_args = widget_name_args[0], None
            metadata_files = self.section_ops.get_ns_metadata_files(
                self.namespace)
            widget_dir = metomi.rose.META_DIR_WIDGET
            metadata_files.sort(
                lambda x, y: (widget_dir in y) - (widget_dir in x))
            prefix = re.sub(r"[^\w]", "_", self.config_name.strip("/"))
            prefix += "/" + metomi.rose.META_DIR_WIDGET + "/"
            custom_widget = metomi.rose.resource.import_object(
                widget_path,
                metadata_files,
                self.handle_bad_custom_sub_widget,
                module_prefix=prefix)
            if custom_widget is None:
                text = metomi.rose.config_editor.ERROR_IMPORT_CLASS.format(
                    self.custom_sub_widget)
                self.handle_bad_custom_sub_widget(text)
                return False
            try:
                self.sub_data_panel = custom_widget(*args, arg_str=widget_args)
            except Exception as exc:
                self.handle_bad_custom_sub_widget(str(exc))
        else:
            panel_module = metomi.rose.config_editor.panelwidget.summary_data
            self.sub_data_panel = (
                panel_module.StandardSummaryDataPanel(*args))

    def handle_bad_custom_sub_widget(self, error_info):
        text = metomi.rose.config_editor.ERROR_IMPORT_WIDGET.format(
            error_info)
        self.reporter(
            metomi.rose.config_editor.util.ImportWidgetError(text))
        self.generate_sub_data_panel(override_custom=True)

    def update_sub_data(self):
        """Update the sub (summary) data panel."""
        if self.sub_data is None:
            if (hasattr(self, "sub_data_panel") and
                    self.sub_data_panel is not None):
                self.vpaned.remove(self.sub_data_panel)
                self.sub_data_panel.destroy()
                self.sub_data_panel = None
        else:
            if (hasattr(self, "sub_data_panel") and
                    self.sub_data_panel is not None):
                self.sub_data_panel.update(self.sub_data["sections"],
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
        add_ui_start = """<ui> <popup name='Popup'>
                         <menu action="Add meta">"""
        add_ui_end = """</menu> </popup> </ui>"""
        actions = [('Add meta', Gtk.STOCK_DIRECTORY,
                    metomi.rose.config_editor.ADD_MENU_META)]
        section_choices = []
        for sect_data in self.sections:
            if not sect_data.ignored_reason:
                section_choices.append(sect_data.name)
        section_choices.sort(key=cmp_to_key(metomi.rose.config.sort_settings))
        if self.ns_is_default and section_choices:
            add_ui_start = add_ui_start.replace(
                "'Popup'>",
                """'Popup'><menuitem action="Add blank"/>""")
            text = metomi.rose.config_editor.ADD_MENU_BLANK
            if len(section_choices) > 1:
                text = metomi.rose.config_editor.ADD_MENU_BLANK_MULTIPLE
            actions.insert(0, ('Add blank', Gtk.STOCK_NEW, text))
        ghost_list = [v for v in self.ghost_data]
        sorter = metomi.rose.config.sort_settings
        ghost_list.sort(lambda v, w: sorter(v.metadata['id'],
                                            w.metadata['id']))
        for variable in ghost_list:
            label_text = variable.name
            if (not self.show_modes[metomi.rose.config_editor.SHOW_MODE_NO_TITLE] and
                    metomi.rose.META_PROP_TITLE in variable.metadata):
                label_text = variable.metadata[metomi.rose.META_PROP_TITLE]
            label_text = label_text.replace("_", "__")
            add_ui_start += ('<menuitem action="' +
                             variable.metadata['id'] + '"/>')
            actions.append((variable.metadata['id'], None,
                            "_" + label_text))
        add_ui = add_ui_start + add_ui_end
        uimanager = Gtk.UIManager()
        actiongroup = Gtk.ActionGroup('Popup')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(add_ui)
        if 'Add blank' in add_ui:
            blank_item = uimanager.get_widget('/Popup/Add blank')
            if len(section_choices) > 1:
                blank_item.connect(
                    "activate",
                    lambda b: self._launch_section_chooser(section_choices))
            else:
                blank_item.connect("activate", lambda b: self.add_row())
        for variable in ghost_list:
            named_item = uimanager.get_widget(
                '/Popup/Add meta/' + variable.metadata['id'])
            if not named_item:
                return None
            named_item.var_id = variable.metadata['id']
            tooltip_text = ""
            description = variable.metadata.get(metomi.rose.META_PROP_DESCRIPTION)
            if description:
                tooltip_text += description + "\n"
            tooltip_text += "(" + variable.metadata["id"] + ")"
            named_item.set_tooltip_text(tooltip_text)
            named_item.connect("activate", _add_var_from_item)
        if 'Add blank' in add_ui or self.ghost_data:
            return uimanager.get_widget('/Popup')
        return None

    def _launch_section_chooser(self, section_choices):
        """Choose a section to add a blank variable to."""
        section = metomi.rose.gtk.dialog.run_choices_dialog(
            metomi.rose.config_editor.DIALOG_LABEL_CHOOSE_SECTION_ADD_VAR,
            section_choices,
            metomi.rose.config_editor.DIALOG_TITLE_CHOOSE_SECTION)
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
            variable = metomi.rose.variable.Variable('', '',
                                              {'id': v_id,
                                               'full_ns': self.namespace})
            if section is None and self.section.ignored_reason:
                # Cannot add to an ignored section.
                return False
        self.variable_ops.add_var(variable)
        if hasattr(self.main_container, 'add_variable_widget'):
            self.main_container.add_variable_widget(variable)
            self.trigger_update_status()
            self.update_ignored()
        else:
            self.refresh()
            self.update_ignored(no_refresh=True)
        self.set_main_focus(variable.metadata.get('id'))

    def generate_main_container(self, override_custom=False):
        """Choose a container to interface with variables in panel_data."""
        if self.custom_widget is not None and not override_custom:
            widget_name_args = self.custom_widget.split(None, 1)
            if len(widget_name_args) > 1:
                widget_path, widget_args = widget_name_args
            else:
                widget_path, widget_args = widget_name_args[0], None
            metadata_files = self.section_ops.get_ns_metadata_files(
                self.namespace)
            custom_widget = metomi.rose.resource.import_object(
                widget_path,
                metadata_files,
                self.handle_bad_custom_main_widget)
            if custom_widget is None:
                text = metomi.rose.config_editor.ERROR_IMPORT_CLASS.format(
                    widget_path)
                self.handle_bad_custom_main_widget(text)
                return
            try:
                self.main_container = custom_widget(self.panel_data,
                                                    self.ghost_data,
                                                    self.variable_ops,
                                                    self.show_modes,
                                                    arg_str=widget_args)
            except Exception as exc:
                self.handle_bad_custom_main_widget(exc)
            else:
                return
        std_table = metomi.rose.config_editor.pagewidget.table.PageTable
        disc_table = metomi.rose.config_editor.pagewidget.table.PageLatentTable
        if self.namespace == "/discovery":
            self.main_container = disc_table(self.panel_data,
                                             self.ghost_data,
                                             self.variable_ops,
                                             self.show_modes)
        else:
            self.main_container = std_table(self.panel_data,
                                            self.ghost_data,
                                            self.variable_ops,
                                            self.show_modes)

    def handle_bad_custom_main_widget(self, error_info):
        """Handle a bad custom page widget import."""
        text = metomi.rose.config_editor.ERROR_IMPORT_WIDGET.format(
            error_info)
        self.reporter.report(
            metomi.rose.config_editor.util.ImportWidgetError(text))
        self.generate_main_container(override_custom=True)

    def validate_errors(self, variable_id=None):
        """Check if there are there errors in variables on this page."""
        if variable_id is None:
            bad_list = []
            for variable in self.panel_data + self.ghost_data:
                bad_list += list(variable.error.items())
            return bad_list
        else:
            for variable in self.panel_data + self.ghost_data:
                if variable.metadata.get('id') == variable_id:
                    if variable.error == {}:
                        return None
                    return list(variable.error.items())
        return None

    def choose_focus(self, focus_variable=None):
        """Select a widget to have the focus on page generation."""
        if self.custom_widget is not None:
            return
        if self.show_modes[metomi.rose.config_editor.SHOW_MODE_LATENT]:
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
            self.generate_page_info()
            return self.sort_main(remake_forced=True)
        variable = None
        for variable in self.panel_data + self.ghost_data:
            if variable.metadata['id'] == only_this_var_id:
                break
        else:
            return self.sort_main(remake_forced=True)
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
                if ((metomi.rose.META_PROP_TYPE in widget.errors) !=
                        (metomi.rose.META_PROP_TYPE in variable.error) and
                        hasattr(widget, "needs_type_error_refresh") and
                        not widget.needs_type_error_refresh()):
                    return widget.type_error_refresh(variable)
                else:
                    return self.handle_reload_var_widget(variable)
            # Then there were no widgets for this variable. Insert it.
            return self.handle_add_var_widget(variable)
        else:
            if var_id in widget_for_var and widget_for_var[var_id].is_ghost:
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
                                          fill=True, padding=0)
            self.choose_focus(focus_var)
            self.update_ignored(no_refresh=True)
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

    def get_main_focus(self):
        """Retrieve the focus variable widget id."""
        widget_list = self.get_main_variable_widgets()
        focus_child = getattr(self.main_container, "focus_child")
        for widget in widget_list:
            if focus_child == widget:
                if hasattr(widget.get_parent(), 'variable'):
                    return widget.get_parent().variable.metadata['id']
                elif hasattr(widget, 'variable'):
                    return widget.variable.metadata['id']
        return None

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

    def set_sub_focus(self, node_id):
        if (self.sub_data is not None and
                hasattr(self, "sub_data_panel") and
                hasattr(self.sub_data_panel, "set_focus_node_id")):
            self.sub_data_panel.set_focus_node_id(node_id)

    def react_to_show_modes(self, mode_key, is_mode_on):
        self.show_modes[mode_key] = is_mode_on
        if hasattr(self.main_container, 'show_mode_change'):
            self.update_ignored()
            react_func = getattr(self.main_container, 'show_mode_change')
            react_func(mode_key, is_mode_on)
        elif mode_key in [metomi.rose.config_editor.SHOW_MODE_IGNORED,
                          metomi.rose.config_editor.SHOW_MODE_USER_IGNORED]:
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

    def update_ignored(self, no_refresh=False):
        """Set variable widgets to 'ignored' or 'enabled' status."""
        new_tuples = []
        for variable in self.panel_data + self.ghost_data:
            if variable.ignored_reason:
                new_tuples.append((variable.metadata['id'],
                                   variable.ignored_reason.copy()))
        target_widgets_done = []
        refresh_list = []
        relevant_errs = metomi.rose.config_editor.WARNING_TYPES_IGNORE
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
            if (any(e in target.errors for e in relevant_errs) or
                    any(e in target.variable.error for e in relevant_errs)):
                if ([e in target.errors for e in relevant_errs] !=
                        [e in target.variable.error for e in relevant_errs]):
                    refresh_list.append(target.variable.metadata['id'])
                    target.errors = list(target.variable.error.keys())
            target_widgets_done.append(target)
        if hasattr(self.main_container, "update_ignored"):
            self.main_container.update_ignored()
        elif not no_refresh:
            self.refresh()
        for variable_id in refresh_list:
            self.refresh(variable_id)

    def _check_show_ignored_reason(self, ignored_reason):
        """Return whether we should show this state."""
        mode = self.show_modes
        if list(ignored_reason.keys()) == [metomi.rose.variable.IGNORED_BY_USER]:
            return (mode[metomi.rose.config_editor.SHOW_MODE_IGNORED] or
                    mode[metomi.rose.config_editor.SHOW_MODE_USER_IGNORED])
        return mode[metomi.rose.config_editor.SHOW_MODE_IGNORED]

    def _set_widget_ignored(self, widget, help_text, enabled=False):
        if self._check_show_ignored_reason(widget.variable.ignored_reason):
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

    def reload_from_data(self, new_config_data, new_ghost_data):
        """Load the new data into the page as gracefully as possible."""
        for variable in [v for v in self.panel_data]:
            # Remove redundant existing variables
            var_id = variable.metadata.get('id')
            new_id_list = [x.metadata['id'] for x in new_config_data]
            if var_id not in new_id_list or var_id is None:
                self.variable_ops.remove_var(variable)
        for variable in [v for v in self.ghost_data]:
            # Remove redundant metadata variables.
            var_id = variable.metadata.get('id')
            new_id_list = [x.metadata['id'] for x in new_ghost_data]
            if var_id not in new_id_list:
                self.variable_ops.remove_var(variable)  # From the ghost list.
        for variable in new_config_data:
            # Update or add variables
            var_id = variable.metadata['id']
            old_id_list = [x.metadata.get('id') for x in self.panel_data]
            if var_id in old_id_list:
                old_variable = self.panel_data[old_id_list.index(var_id)]
                old_variable.metadata = variable.metadata
                if old_variable.value != variable.value:
                    # Reset the value.
                    self.variable_ops.set_var_value(old_variable,
                                                    variable.value)
                if old_variable.comments != variable.comments:
                    self.variable_ops.set_var_comments(old_variable,
                                                       variable.comments)
                old_ign_set = set(old_variable.ignored_reason.keys())
                new_ign_set = set(variable.ignored_reason.keys())
                if old_ign_set != new_ign_set:
                    # Reset the ignored state.
                    self.variable_ops.set_var_ignored(
                        old_variable,
                        variable.ignored_reason.copy(),
                        override=True)
                else:
                    # The types are the same, but pass on the info.
                    old_variable.ignored_reason = (
                        variable.ignored_reason.copy())
                old_variable.error = variable.error.copy()
                old_variable.warning = variable.warning.copy()
            else:
                self.variable_ops.add_var(variable.copy())
        for variable in new_ghost_data:
            # Update or remove variables
            var_id = variable.metadata['id']
            old_id_list = [x.metadata.get('id')
                           for x in self.ghost_data]
            if var_id in old_id_list:
                index = old_id_list.index(var_id)
                old_variable = self.ghost_data[index]
                old_variable.metadata = variable.metadata.copy()
                old_variable.ignored_reason = variable.ignored_reason.copy()
                if old_variable.value != variable.value:
                    old_variable.value = variable.value
                old_variable.error = variable.error.copy()
                old_variable.warning = variable.warning.copy()
            else:
                self.ghost_data.append(variable.copy())
        self.refresh()
        self.trigger_update_status()
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
            title = variable.metadata.get(metomi.rose.META_PROP_TITLE, variable.name)
            var_id = variable.metadata.get('id', variable.name)
            key = (
                variable.metadata.get(metomi.rose.META_PROP_SORT_KEY, '~'),
                var_id
            )
            if variable.name == '':
                key = ('~', '')
            sorted_data.append((key, title, variable.name,
                                variable.value, variable))
        ascending_cmp = lambda x, y: metomi.rose.config_editor.util.null_cmp(
            x[0], y[0])
        descending_cmp = lambda x, y: metomi.rose.config_editor.util.null_cmp(
            x[0], y[0])
        if ascending:
            sorted_data.sort(key=cmp_to_key(ascending_cmp))
        else:
            sorted_data.sort(key=cmp_to_key(descending_cmp))
        if [x[4] for x in sorted_data] == datavars:
            return False
        for i, datum in enumerate(sorted_data):
            datavars[i] = datum[4]  # variable
        return True

    def _macro_menu_launch(self, widget, event):
        # Create a menu below the widget for macro actions.
        menu = Gtk.Menu()
        for macro_name, info in sorted(self.custom_macros.items()):
            method, description = info
            if method == metomi.rose.macro.TRANSFORM_METHOD:
                stock_id = Gtk.STOCK_CONVERT
            else:
                stock_id = Gtk.STOCK_DIALOG_QUESTION
            macro_menuitem = Gtk.ImageMenuItem(stock_id=stock_id)
            macro_menuitem.set_label(macro_name)
            macro_menuitem.set_tooltip_text(description)
            macro_menuitem.show()
            macro_menuitem._macro = macro_name
            macro_menuitem.connect(
                "button-release-event",
                lambda m, e: self.launch_macro(m._macro))
            menu.append(macro_menuitem)
        menu.popup(None, None, widget.position_menu, event.button,
                   event.time, widget)

    def launch_macro(self, macro_name_string):
        """Launch a macro, if possible."""
        class_name = None
        method_name = None
        if "." in macro_name_string:
            module_name, class_name = macro_name_string.split(".", 1)
            if "." in class_name:
                class_name, method_name = class_name.split(".", 1)
        else:
            module_name = macro_name_string
        self._launch_macro_func(
            config_name=self.config_name,
            module_name=module_name,
            class_name=class_name,
            method_name=method_name)

    def search_for_id(self, id_):
        """Launch a search for variable or section id."""
        return self.variable_ops.search_for_var(self.namespace, id_)

    def trigger_update_status(self):
        """Connect this at a higher level to allow changed data signals."""
        pass

    def _get_page_info_widgets(self):
        button_list = []
        label_list = []
        info = ""
        # No content warning, if applicable.
        has_no_content = (self.section is None and
                          not self.ghost_data and
                          self.sub_data is None and
                          not self.latent_sections)
        if has_no_content:
            info = metomi.rose.config_editor.PAGE_WARNING_NO_CONTENT
            tip = metomi.rose.config_editor.PAGE_WARNING_NO_CONTENT_TIP
            error_button = metomi.rose.gtk.util.CustomButton(
                stock_id=Gtk.STOCK_INFO,
                as_tool=True,
                tip_text=tip)
            error_label = Gtk.Label()
            error_label.set_text(info)
            error_label.show()
            button_list.append(error_button)
            label_list.append(error_label)
        if self.section is not None and self.section.ignored_reason:
            # This adds an ignored warning.
            info = metomi.rose.config_editor.PAGE_WARNING_IGNORED_SECTION.format(
                self.section.name)
            tip = metomi.rose.config_editor.PAGE_WARNING_IGNORED_SECTION_TIP
            error_button = metomi.rose.gtk.util.CustomButton(
                stock_id=Gtk.STOCK_NO,
                as_tool=True,
                tip_text=tip)
            error_label = Gtk.Label()
            error_label.set_text(info)
            error_label.show()
            button_list.append(error_button)
            label_list.append(error_label)
        elif self.see_also == '' or metomi.rose.FILE_VAR_SOURCE not in self.see_also:
            # This adds an 'orphaned' warning, only if the section is enabled.
            if (self.section is not None and
                    self.section.name.startswith('namelist:')):
                error_button = metomi.rose.gtk.util.CustomButton(
                    stock_id=Gtk.STOCK_DIALOG_WARNING,
                    as_tool=True,
                    tip_text=metomi.rose.config_editor.ERROR_ORPHAN_SECTION_TIP)
                error_label = Gtk.Label()
                info = metomi.rose.config_editor.ERROR_ORPHAN_SECTION.format(
                    self.section.name)
                error_label.set_text(info)
                error_label.show()
                button_list.append(error_button)
                label_list.append(error_label)
        has_data = (has_no_content or
                    self.sub_data is not None or
                    bool(self.panel_data))
        if not has_data:
            for section in self.sections:
                if section.metadata["full_ns"] == self.namespace:
                    has_data = True
                    break
        if not has_data:
            # This is a latent namespace page.
            latent_button = metomi.rose.gtk.util.CustomButton(
                stock_id=Gtk.STOCK_INFO,
                as_tool=True,
                tip_text=metomi.rose.config_editor.TIP_LATENT_PAGE)
            latent_label = Gtk.Label()
            latent_label.set_text(metomi.rose.config_editor.PAGE_WARNING_LATENT)
            latent_label.show()
            button_list.append(latent_button)
            label_list.append(latent_label)
        # This adds error notification for sections.
        for sect_data in self.sections + self.latent_sections:
            for err, info in list(sect_data.error.items()):
                error_button = metomi.rose.gtk.util.CustomButton(
                    stock_id=Gtk.STOCK_DIALOG_ERROR,
                    as_tool=True,
                    tip_text=info)
                error_label = Gtk.Label()
                error_label.set_text(metomi.rose.config_editor.PAGE_WARNING.format(
                    err, sect_data.name))
                error_label.show()
                button_list.append(error_button)
                label_list.append(error_label)
        if list(self.custom_macros.items()):
            macro_button = metomi.rose.gtk.util.CustomButton(
                label=metomi.rose.config_editor.LABEL_PAGE_MACRO_BUTTON,
                stock_id=Gtk.STOCK_EXECUTE,
                tip_text=metomi.rose.config_editor.TIP_MACRO_RUN_PAGE,
                as_tool=True, icon_at_start=True,
                has_menu=True)
            macro_button.connect("button-press-event",
                                 self._macro_menu_launch)
            macro_label = Gtk.Label()
            macro_label.show()
            button_list.append(macro_button)
            label_list.append(macro_label)
        return button_list, label_list, info
