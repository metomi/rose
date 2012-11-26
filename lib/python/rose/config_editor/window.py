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

import os
import re
import sys
import tempfile
import webbrowser

import pygtk
pygtk.require('2.0')
import gtk
import pango

import rose.config
import rose.resource


REC_SPLIT_MACRO_TEXT = re.compile(
       '(.{' + str(rose.config_editor.DIALOG_BODY_MACRO_CHANGES_MAX_LENGTH) +
       '})')


class MainWindow(object):

    """Generate the main window and dialog handling for this example."""

    def load(self, name='Untitled', menu=None, accelerators=None, toolbar=None,
             hyper_panel=None, notebook=None,
             page_change_func=rose.config_editor.false_function,
             save_func=rose.config_editor.false_function):
        self.window = gtk.Window()
        self.window.set_title(name + ' - ' + rose.config_editor.LAUNCH_COMMAND)
        self.util = rose.config_editor.util.Lookup()
        locator = rose.resource.ResourceLocator(paths=sys.path)
        icon_path = locator.locate('etc/images/rose-icon-trim.png')
        self.window.set_icon_from_file(icon_path)
        gtk.window_set_default_icon_list(self.window.get_icon())
        self.window.set_default_size(*rose.config_editor.SIZE_WINDOW)
        self.window.set_destroy_with_parent(False)
        self.save_func = save_func
        self.top_vbox = gtk.VBox()
        self.log_window = None  # The stack viewer.
        self.window.add(self.top_vbox)
        # Load the menu bar
        if menu is not None:
            menu.show()
            self.top_vbox.pack_start(menu, expand=False)
        if accelerators is not None:
            self.window.add_accel_group(accelerators)
        if toolbar is not None:
            toolbar.show()
            self.top_vbox.pack_start(toolbar, expand=False)
        # Load the hyper_panel and notebook
        for signal in ['switch-page', 'focus-tab', 'select-page',
                       'change-current-page']:
            notebook.connect_after(signal, page_change_func)
        self.generate_main_hbox(hyper_panel, notebook)
        self.top_vbox.pack_start(self.main_hbox, expand=True)
        self.top_vbox.show()
        self.window.show()
        hyper_panel.tree.columns_autosize()
        hyper_panel.grab_focus()

    def generate_main_hbox(self, hyper_panel, notebook):
        """Create the main container of the GUI window.

        This contains the tree panel and notebook.

        """
        self.main_hbox = gtk.HPaned()
        self.main_hbox.pack1(hyper_panel, resize=False, shrink=False)
        self.main_hbox.show()
        self.main_hbox.pack2(notebook, resize=True, shrink=True)
        self.main_hbox.show()
        self.main_hbox.set_position(rose.config_editor.WIDTH_TREE_PANEL)

    def launch_about_dialog(self, somewidget=None):
        """Create a dialog showing the 'About' information."""
        rose.gtk.util.run_about_dialog(name=rose.config_editor.PROGRAM_NAME,
                                       copyright=rose.config_editor.COPYRIGHT,
                                       logo_path="etc/images/rose-logo.png",
                                       website=rose.config_editor.PROJECT_URL)

    def _reload_choices(self, liststore, top_name, add_choices):
        liststore.clear()
        for full_section_id in add_choices:
            section_top_name, section_id = full_section_id.split(':', 1)
            if section_top_name == top_name:
                liststore.append([section_id])

    def launch_add_dialog(self, names, add_choices, section_help):
        """Launch a dialog asking for a section name."""
        add_dialog = gtk.Dialog(title=rose.config_editor.DIALOG_TITLE_ADD,
                                parent=self.window,
                                buttons=(gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_REJECT,
                                         gtk.STOCK_OK,
                                         gtk.RESPONSE_ACCEPT))
        config_label = gtk.Label(rose.config_editor.DIALOG_BODY_ADD_CONFIG)
        config_label.show()
        label = gtk.Label(rose.config_editor.DIALOG_BODY_ADD_SECTION)
        label.show()
        config_name_box = gtk.combo_box_new_text()
        for name in names:
            config_name_box.append_text(name.lstrip("/"))
        config_name_box.show()
        config_name_box.set_active(0)
        section_box = gtk.Entry()
        if section_help is not None:
            section_box.set_text(section_help)
        section_completion = gtk.EntryCompletion()
        liststore = gtk.ListStore(str)
        section_completion.set_model(liststore)
        section_box.set_completion(section_completion)
        section_completion.set_text_column(0)
        choices = []
        self._reload_choices(liststore, names[0], add_choices)
        section_box.show()
        config_name_box.connect('changed',
                                lambda c: self._reload_choices(
                                           liststore,
                                           names[c.get_active()]),
                                           add_choices)
        section_box.connect('activate',
                            lambda s: add_dialog.response(gtk.RESPONSE_OK))
        vbox = gtk.VBox(spacing=10)
        vbox.pack_start(config_label, expand=False, fill=False, padding=5)
        vbox.pack_start(config_name_box, expand=False, fill=False, padding=5)
        vbox.pack_start(label, expand=False, fill=False, padding=5)
        vbox.pack_start(section_box, expand=False, fill=False, padding=5)
        vbox.show()
        hbox = gtk.HBox(spacing=10)
        hbox.pack_start(vbox, expand=True, fill=True, padding=10)
        hbox.show()
        add_dialog.vbox.pack_start(hbox)
        section_box.grab_focus()
        section_box.set_position(-1)
        section_completion.complete()
        response = add_dialog.run()
        if response in [gtk.RESPONSE_OK, gtk.RESPONSE_YES,
                        gtk.RESPONSE_ACCEPT]:
            config_name_entered = names[config_name_box.get_active()]
            section_name_entered = section_box.get_text()
            add_dialog.destroy()
            return config_name_entered, section_name_entered
        add_dialog.destroy()
        return None, None

    def launch_exit_warning_dialog(self):
        """Launch a 'really want to quit' dialog."""
        text = 'Save changes before closing?'
        exit_dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_NONE,
                                        message_format=text,
                                        parent=self.window)
        exit_dialog.add_buttons(gtk.STOCK_NO, gtk.RESPONSE_REJECT,
                                gtk.STOCK_CANCEL, gtk.RESPONSE_CLOSE,
                                gtk.STOCK_YES, gtk.RESPONSE_ACCEPT)
        exit_dialog.set_title(rose.config_editor.DIALOG_TITLE_SAVE_CHANGES)
        exit_dialog.set_modal(True)
        exit_dialog.set_keep_above(True)
        exit_dialog.action_area.get_children()[1].grab_focus()
        response = exit_dialog.run()
        exit_dialog.destroy()
        if response == gtk.RESPONSE_REJECT:
            gtk.main_quit()
        elif response == gtk.RESPONSE_ACCEPT:
            self.save_func()
            gtk.main_quit()
        return False

    def launch_help_dialog(self, somewidget=None):
        """Launch a browser to open the help url."""
        webbrowser.open(rose.resource.ResourceLocator.default().get_doc_url() +
                        rose.config_editor.HELP_FILE, new=True, autoraise=True)
        return False

    def launch_ignore_dialog(self, name_section_dict, prefs, is_ignored):
        """Launch a dialog asking for a section name to ignore or enable.
        
        name_section_dict is a dictionary containing config names
        as keys, and lists of available sections as values.
        prefs is in the same format, but indicates preferred values.
        is_ignored is a bool that controls whether this is an ignore
        section dialog or an enable section dialog.
        
        """
        if is_ignored:
            dialog_title = rose.config_editor.DIALOG_TITLE_IGNORE
        else:
            dialog_title = rose.config_editor.DIALOG_TITLE_ENABLE
        add_dialog = gtk.Dialog(title=dialog_title,
                                parent=self.window,
                                buttons=(gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_REJECT,
                                         gtk.STOCK_OK,
                                         gtk.RESPONSE_ACCEPT))
        config_label = gtk.Label(
                         rose.config_editor.DIALOG_BODY_IGNORE_ENABLE_CONFIG)
        config_label.show()
        if is_ignored:
            label = gtk.Label(
                         rose.config_editor.DIALOG_BODY_IGNORE_SECTION)
        else:
            label = gtk.Label(
                         rose.config_editor.DIALOG_BODY_ENABLE_SECTION)
        label.show()
        config_name_box = gtk.combo_box_new_text()
        name_keys = name_section_dict.keys()
        name_keys.sort()
        for k, name in enumerate(name_keys):
            config_name_box.append_text(name)
            if name in prefs:
                config_name_box.set_active(k)
        if config_name_box.get_active() == -1:
            config_name_box.set_active(0)
        config_name_box.show()
        section_box = gtk.VBox()
        section_box.show()
        index = config_name_box.get_active()
        self._reload_section_choices(
                             section_box,
                             name_section_dict[name_keys[index]],
                             prefs.get(name_keys[index], []))
        config_name_box.connect(
                        'changed',
                        lambda c: self._reload_section_choices(
                                        section_box,
                                        name_section_dict[name_keys[
                                                          c.get_active()]],
                                        prefs.get(name_keys[c.get_active()],
                                                  [])))
        vbox = gtk.VBox(spacing=rose.config_editor.SPACING_PAGE)
        vbox.pack_start(config_label, expand=False, fill=False)
        vbox.pack_start(config_name_box, expand=False, fill=False)
        vbox.pack_start(label, expand=False, fill=False)
        vbox.pack_start(section_box, expand=False, fill=False)
        vbox.show()
        hbox = gtk.HBox()
        hbox.pack_start(vbox, expand=True, fill=True,
                        padding=rose.config_editor.SPACING_PAGE)
        hbox.show()
        add_dialog.vbox.pack_start(hbox,
                                   padding=rose.config_editor.SPACING_PAGE)
        section_box.grab_focus()
        response = add_dialog.run()
        if response in [gtk.RESPONSE_OK, gtk.RESPONSE_YES,
                        gtk.RESPONSE_ACCEPT]:
            config_name_entered = name_keys[config_name_box.get_active()]
            for widget in section_box.get_children():
                if hasattr(widget, 'get_active'):
                    index = widget.get_active()
                    sections = name_section_dict[config_name_entered]
                    section_name = sections[index]
                    add_dialog.destroy()
                    return config_name_entered, section_name
        add_dialog.destroy()
        return None, None

    def _reload_section_choices(self, vbox, sections, prefs):
        for child in vbox.get_children():
            vbox.remove(child)
        sections.sort(rose.config.sort_settings)
        section_chooser = gtk.combo_box_new_text()
        for k, section in enumerate(sections):
            section_chooser.append_text(section)
            if section in prefs:
                section_chooser.set_active(k)
        if section_chooser.get_active() == -1 and sections:
            section_chooser.set_active(0)
        section_chooser.show()
        vbox.pack_start(section_chooser, expand=False, fill=False)
        return vbox

    def launch_macro_changes_dialog(
               self, config_name, macro_name, changes_list,
               mode="transform",
               search_func=rose.config_editor.false_function):
        """Launch a dialog explaining macro changes."""
        dialog = MacroChangesDialog(self.window, config_name, macro_name,
                                    mode, search_func)
        return dialog.display(changes_list)

    def launch_new_config_dialog(self, root_directory):
        """Launch a dialog allowing naming of a new configuration."""
        existing_apps = os.listdir(root_directory)
        checker_function = lambda t: t not in existing_apps
        label = rose.config_editor.DIALOG_LABEL_CONFIG_CHOOSE_NAME
        ok_tip_text = rose.config_editor.TIP_CONFIG_CHOOSE_NAME
        err_tip_text = rose.config_editor.TIP_CONFIG_CHOOSE_NAME_ERROR
        dialog, container, name_entry = rose.gtk.util._get_naming_dialog(
                                                           label,
                                                           checker_function,
                                                           ok_tip_text,
                                                           err_tip_text)
        dialog.set_title(rose.config_editor.DIALOG_TITLE_CONFIG_CREATE)
        meta_hbox = gtk.HBox()
        meta_label = gtk.Label(
                         rose.config_editor.DIALOG_LABEL_CONFIG_CHOOSE_META)
        meta_label.show()
        meta_entry = gtk.Entry()
        tip_text = rose.config_editor.TIP_CONFIG_CHOOSE_META
        meta_entry.set_tooltip_text(tip_text)
        meta_entry.connect("activate", lambda b: dialog.response(gtk.RESPONSE_ACCEPT))
        meta_entry.show()
        meta_hbox.pack_start(meta_label, expand=False, fill=False,
                             padding=rose.config_editor.SPACING_SUB_PAGE)
        meta_hbox.pack_start(meta_entry, expand=False, fill=True,
                             padding=rose.config_editor.SPACING_SUB_PAGE)
        meta_hbox.show()
        container.pack_start(meta_hbox, expand=False, fill=True,
                             padding=rose.config_editor.SPACING_PAGE)
        response = dialog.run()
        name = None
        meta = None
        if name_entry.get_text():
            name = name_entry.get_text().strip().strip('/')
        if meta_entry.get_text():
            meta = meta_entry.get_text().strip()
        dialog.destroy()
        if response == gtk.RESPONSE_ACCEPT:
            return name, meta
        return None, None

    def launch_open_dirname_dialog(self):
        """Launch a FileChooserDialog and return a directory, or None."""
        open_dialog = gtk.FileChooserDialog(
                                title=rose.config_editor.DIALOG_TITLE_OPEN,
                                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                buttons=(gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN,
                                         gtk.RESPONSE_OK))
        open_dialog.set_transient_for(self.window)
        open_dialog.set_icon(self.window.get_icon())
        open_dialog.set_default_response(gtk.RESPONSE_OK)
        config_filter = gtk.FileFilter()
        config_filter.add_pattern(rose.TOP_CONFIG_NAME)
        config_filter.add_pattern(rose.SUB_CONFIG_NAME)
        config_filter.add_pattern(rose.INFO_CONFIG_NAME)
        open_dialog.set_filter(config_filter)
        response = open_dialog.run()
        if response in [gtk.RESPONSE_OK, gtk.RESPONSE_ACCEPT,
                        gtk.RESPONSE_YES]:
            config_directory = os.path.dirname(open_dialog.get_filename())
            open_dialog.destroy()
            return config_directory
        open_dialog.destroy()
        return None

    def launch_prefs(self, somewidget=None):
        """Launch a dialog explaining preferences."""
        text = rose.config_editor.DIALOG_LABEL_PREFERENCES
        title = rose.config_editor.DIALOG_TITLE_PREFERENCES
        rose.gtk.util.run_dialog(gtk.MESSAGE_INFO, text, title)
        return False

    def launch_view_stack(self, undo_stack, redo_stack, undo_func):
        """Load a view of the stack."""
        self.log_window = rose.config_editor.stack.StackViewer(
                                      undo_stack, redo_stack, undo_func)
        self.log_window.set_transient_for(self.window)


class MacroChangesDialog(gtk.Dialog):

    """Class to hold a dialog summarising macro results."""

    COLUMNS = ["Section", "Option", "Type", "Value", "Info"]
    MODE_COLOURS = {"transform": rose.config_editor.COLOUR_MACRO_CHANGED,
                    "validate": rose.config_editor.COLOUR_MACRO_ERROR,
                    "warn": rose.config_editor.COLOUR_MACRO_WARNING}
    MODE_TEXT = {"transform": rose.config_editor.DIALOG_TEXT_MACRO_CHANGED,
                 "validate": rose.config_editor.DIALOG_TEXT_MACRO_ERROR,
                 "warn": rose.config_editor.DIALOG_TEXT_MACRO_WARNING}

    def __init__(self, window, config_name, macro_name, mode, search_func):
        self.util = rose.config_editor.util.Lookup()
        self.short_config_name = config_name.rstrip('/').split('/')[-1]
        self.top_config_name = config_name.lstrip('/').split('/')[0]
        self.short_macro_name = macro_name.split('.')[-1]
        self.for_transform = (mode == "transform")
        self.for_validate = (mode == "validate")
        self.macro_name = macro_name
        self.mode = mode
        self.search_func = search_func
        if self.for_validate:
            title = rose.config_editor.DIALOG_TITLE_MACRO_VALIDATE
            button_list = [gtk.STOCK_OK, gtk.RESPONSE_ACCEPT]
        else:
            title = rose.config_editor.DIALOG_TITLE_MACRO_TRANSFORM
            button_list = [gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                           gtk.STOCK_OK, gtk.RESPONSE_ACCEPT]
        title = title.format(self.short_macro_name, self.short_config_name)
        button_list = tuple(button_list)
        super(MacroChangesDialog, self).__init__(buttons=button_list,
                                                 parent=window)
        if not self.for_transform :
            self.set_modal(False)
        self.set_title(title.format(macro_name))
        self.label = gtk.Label()
        self.label.show()
        if self.for_validate:
            stock_id = gtk.STOCK_DIALOG_WARNING
        else:
            stock_id = gtk.STOCK_CONVERT
        image = gtk.image_new_from_stock(stock_id,
                                         gtk.ICON_SIZE_LARGE_TOOLBAR)
        image.show()
        hbox = gtk.HBox()
        hbox.pack_start(image, expand=False, fill=False,
                        padding=rose.config_editor.SPACING_PAGE)
        hbox.pack_start(self.label, expand=False, fill=False,
                        padding=rose.config_editor.SPACING_PAGE)
        hbox.show()
        self.treewindow = gtk.ScrolledWindow()
        self.treewindow.show()
        self.treewindow.set_policy(gtk.POLICY_NEVER,
                                   gtk.POLICY_NEVER)
        self.treeview = rose.gtk.util.TooltipTreeView(
                                      get_tooltip_func=self._get_tooltip)
        self.treeview.show()
        self.treemodel = gtk.TreeStore(str, str, str, str, str)

        self.treeview.set_model(self.treemodel)
        for i, title in enumerate(self.COLUMNS):
            column = gtk.TreeViewColumn()
            column.set_title(title)
            cell = gtk.CellRendererText()
            if i == len(self.COLUMNS) - 1:
                column.pack_start(cell, expand=True)
            else:
                column.pack_start(cell, expand=False)
            if title == "Type":
                column.set_cell_data_func(cell, self._set_type_markup, i)
            else:
                column.set_cell_data_func(cell, self._set_markup, i)
            self.treeview.append_column(column)

        self.treeview.connect("row-activated", self._handle_treeview_activation)
        self.treewindow.add(self.treeview)
        self.vbox.pack_end(self.treewindow, expand=True, fill=True,
                           padding=rose.config_editor.SPACING_PAGE)
        self.vbox.pack_end(hbox, expand=False, fill=True,
                             padding=rose.config_editor.SPACING_PAGE)
        self.set_focus(self.action_area.get_children()[0])
        
    def display(self, changes):
        if not changes:
            # Shortcut, no changes.
            if self.for_validate:
                title = rose.config_editor.DIALOG_TITLE_MACRO_VALIDATE_NONE
                text = rose.config_editor.DIALOG_LABEL_MACRO_VALIDATE_NONE
            else:
                title = rose.config_editor.DIALOG_TITLE_MACRO_TRANSFORM_NONE
                text = rose.config_editor.DIALOG_LABEL_MACRO_TRANSFORM_NONE
            title = title.format(self.short_macro_name)
            text = rose.gtk.util.safe_str(text)
            return rose.gtk.util.run_dialog(
                        rose.gtk.util.DIALOG_TYPE_INFO, text, title)
        if self.for_validate:
            text = rose.config_editor.DIALOG_LABEL_MACRO_VALIDATE_ISSUES
        else:
            text = rose.config_editor.DIALOG_LABEL_MACRO_TRANSFORM_CHANGES
        nums_is_warning = {True: 0, False: 0}
        for item in changes:
            nums_is_warning[item.is_warning] += 1
        text = text.format(self.short_macro_name, self.short_config_name,
                           nums_is_warning[False])
        if nums_is_warning[True]:
            extra_text = rose.config_editor.DIALOG_LABEL_MACRO_WARN_ISSUES
            text = (text.rstrip() + " " +
                    extra_text.format(nums_is_warning[True]))
        self.label.set_markup(text)
        changes.sort(lambda x, y: cmp(x.option, y.option))
        changes.sort(lambda x, y: cmp(x.section, y.section))
        changes.sort(lambda x, y: cmp(x.is_warning, y.is_warning))
        last_section = None
        last_section_iter = None
        for item in changes:
            item_mode = self.mode
            if item.is_warning:
                item_mode = "warn"
            item_att_list = [item.section, item.option, item_mode, 
                             item.value, item.info]
            if item.section == last_section:
                self.treemodel.append(last_section_iter, item_att_list)
            else:
                sect_att_list = [item.section, None, None, None, None]
                last_section_iter = self.treemodel.append(None, sect_att_list)
                last_section = item.section
                self.treemodel.append(last_section_iter, item_att_list)
        self.treeview.expand_all()
        max_size = rose.config_editor.SIZE_MACRO_DIALOG_MAX
        my_size = self.size_request()
        new_size = [-1, -1]
        for i in [0, 1]:
            new_size[i] = min([my_size[i], max_size[i]])
        self.treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_default_size(*new_size)
        if self.for_transform:
            response = self.run()
            self.destroy()
            return (response == gtk.RESPONSE_ACCEPT)
        else:
            self.show()
            self.action_area.get_children()[0].connect(
                               "clicked", lambda b: self.destroy())

    def _get_tooltip(self, view, row_iter, col_index, tip):
        tip.set_text(view.get_model().get_value(row_iter, col_index))
        return True

    def _set_type_markup(self, column, cell, model, r_iter, col_index):
        macro_mode = model.get_value(r_iter, col_index)
        if macro_mode is None:
            cell.set_property("markup", None)
        else:
            cell.set_property("markup", self._get_type_markup(macro_mode))

    def _get_type_markup(self, macro_mode):
        colour = self.MODE_COLOURS[macro_mode]
        text = self.MODE_TEXT[macro_mode]
        return '<span foreground="{0}">{1}</span>'.format(colour, text)

    def _set_markup(self, column, cell, model, r_iter, col_index):
        text = model.get_value(r_iter, col_index)
        if text is None:
            cell.set_property("markup", None)
        else:
            cell.set_property("markup", rose.gtk.util.safe_str(text))
        if col_index == 0:
            cell.set_property("visible", (len(model.get_path(r_iter)) == 1))

    def _handle_treeview_activation(self, view, path, column):
        r_iter = view.get_model().get_iter(path)
        section = view.get_model().get_value(r_iter, 0)
        option = view.get_model().get_value(r_iter, 1)
        id_ = self.util.get_id_from_section_option(section, option)
        self.search_func(id_)
