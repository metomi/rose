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

import os
import re
import webbrowser

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import metomi.rose.config
import metomi.rose.gtk.dialog
import metomi.rose.gtk.util
import metomi.rose.resource


REC_SPLIT_MACRO_TEXT = re.compile(
    '(.{' + str(metomi.rose.config_editor.DIALOG_BODY_MACRO_CHANGES_MAX_LENGTH) +
    '})')


class MetadataTable(object):
    """
    Creates a table from the provided list of paths appending it to the
    provided parent.
    The current state of the table can be obtained using '.paths'.
    """
    def __init__(self, paths, parent):
        self.paths = paths
        self.parent = parent
        self.previous = None
        self.draw_table()

    def draw_table(self):
        """ Draws the table. """
        # destroy previous table if present
        if self.previous:
            self.previous.destroy()

        # rows, cols
        table = Gtk.Table(len(self.paths), 2)

        # table rows
        for i, path in enumerate(self.paths):
            label = Gtk.Label(label=path)
            label.set_alignment(xalign=0., yalign=0.5)
            # component, col_from, col_to, row_from, row_to
            table.attach(label, 0, 1, i, i + 1, xoptions=Gtk.AttachOptions.FILL, xpadding=15)
            label.show()
            button = Gtk.Button('Remove')
            button.data = path
            # component, col_from, col_to, row_from, row_to
            table.attach(button, 1, 2, i, i + 1)
            button.connect('clicked', self.remove_row)
            button.show()

        # append table
        self.parent.pack_start(table, True, True, 0)
        self.parent.reorder_child(table, 2)
        table.show()

        self.previous = table

    def remove_row(self, widget):
        """ To be called upon 'remove' button press. """
        self.paths.remove(widget.data)
        self.draw_table()

    def add_row(self, path):
        """ Creates a new table row from the provided path (as a string). """
        self.paths.append(path)
        self.draw_table()


class MainWindow(object):

    """Generate the main window and dialog handling for this example."""

    def load(self, name='Untitled', menu=None, accelerators=None, toolbar=None,
             nav_panel=None, status_bar=None, notebook=None,
             page_change_func=metomi.rose.config_editor.false_function,
             save_func=metomi.rose.config_editor.false_function):
        self.window = Gtk.Window()
        self.window.set_title(name + ' - ' +
                              metomi.rose.config_editor.LAUNCH_COMMAND)
        self.util = metomi.rose.config_editor.util.Lookup()
        self.window.set_icon(metomi.rose.gtk.util.get_icon())
        Gtk.Window.set_default_icon_list([self.window.get_icon()])
        self.window.set_default_size(*metomi.rose.config_editor.SIZE_WINDOW)
        self.window.set_destroy_with_parent(False)
        self.save_func = save_func
        self.top_vbox = Gtk.VBox()
        self.log_window = None  # The stack viewer.
        self.window.add(self.top_vbox)
        # Load the menu bar
        if menu is not None:
            menu.show()
            self.top_vbox.pack_start(menu, False, True, 0)
        if accelerators is not None:
            self.window.add_accel_group(accelerators)
        if toolbar is not None:
            toolbar.show()
            self.top_vbox.pack_start(toolbar, False, True, 0)
        # Load the nav_panel and notebook
        for signal in ['switch-page', 'focus-tab', 'select-page',
                       'change-current-page']:
            notebook.connect_after(signal, page_change_func)
        self.generate_main_hbox(nav_panel, notebook)
        self.top_vbox.pack_start(self.main_hbox, True, True, 0)
        self.top_vbox.pack_start(status_bar, expand=False, fill=False, padding=0)
        self.top_vbox.show()
        self.window.show()
        nav_panel.tree.columns_autosize()
        nav_panel.grab_focus()

    def generate_main_hbox(self, nav_panel, notebook):
        """Create the main container of the GUI window.

        This contains the tree panel and notebook.

        """
        self.main_hbox = Gtk.HPaned()
        self.main_hbox.pack1(nav_panel, resize=False, shrink=False)
        self.main_hbox.show()
        self.main_hbox.pack2(notebook, resize=True, shrink=True)
        self.main_hbox.show()
        self.main_hbox.set_position(metomi.rose.config_editor.WIDTH_TREE_PANEL)

    def launch_about_dialog(self, somewidget=None):
        """Create a dialog showing the 'About' information."""
        metomi.rose.gtk.dialog.run_about_dialog(
            name=metomi.rose.config_editor.PROGRAM_NAME,
            copyright_=metomi.rose.config_editor.COPYRIGHT,
            logo_path="etc/images/rose-logo.png",
            website=metomi.rose.config_editor.PROJECT_URL)

    def _reload_choices(self, liststore, top_name, add_choices):
        liststore.clear()
        for full_section_id in add_choices:
            section_top_name, section_id = full_section_id.split(':', 1)
            if section_top_name == top_name:
                liststore.append([section_id])

    def launch_add_dialog(self, names, add_choices, section_help):
        """Launch a dialog asking for a section name."""
        add_dialog = Gtk.Dialog(title=metomi.rose.config_editor.DIALOG_TITLE_ADD,
                                parent=self.window,
                                buttons=(Gtk.STOCK_CANCEL,
                                         Gtk.ResponseType.REJECT,
                                         Gtk.STOCK_OK,
                                         Gtk.ResponseType.ACCEPT))
        ok_button = add_dialog.action_area.get_children()[0]
        config_label = Gtk.Label(label=metomi.rose.config_editor.DIALOG_BODY_ADD_CONFIG)
        config_label.show()
        label = Gtk.Label(label=metomi.rose.config_editor.DIALOG_BODY_ADD_SECTION)
        label.show()
        config_name_box = Gtk.ComboBoxText()
        for name in names:
            config_name_box.append_text(name.lstrip("/"))
        config_name_box.show()
        config_name_box.set_active(0)
        section_box = Gtk.Entry()
        if section_help is not None:
            section_box.set_text(section_help)
        section_completion = Gtk.EntryCompletion()
        liststore = Gtk.ListStore(str)
        section_completion.set_model(liststore)
        section_box.set_completion(section_completion)
        section_completion.set_text_column(0)
        self._reload_choices(liststore, names[0], add_choices)
        section_box.show()
        config_name_box.connect(
            "changed",
            lambda c: self._reload_choices(
                liststore, names[c.get_active()], add_choices))
        section_box.connect("activate",
                            lambda s: add_dialog.response(Gtk.ResponseType.OK))
        section_box.connect(
            "changed",
            lambda s: ok_button.set_sensitive(bool(s.get_text())))
        vbox = Gtk.VBox(spacing=10)
        vbox.pack_start(config_label, expand=False, fill=False, padding=5)
        vbox.pack_start(config_name_box, expand=False, fill=False, padding=5)
        vbox.pack_start(label, expand=False, fill=False, padding=5)
        vbox.pack_start(section_box, expand=False, fill=False, padding=5)
        vbox.show()
        hbox = Gtk.HBox(spacing=10)
        hbox.pack_start(vbox, expand=True, fill=True, padding=10)
        hbox.show()
        add_dialog.vbox.pack_start(hbox, True, True, 0)
        section_box.grab_focus()
        section_box.set_position(-1)
        section_completion.complete()
        ok_button.set_sensitive(bool(section_box.get_text()))
        response = add_dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.YES,
                        Gtk.ResponseType.ACCEPT]:
            config_name_entered = names[config_name_box.get_active()]
            section_name_entered = section_box.get_text()
            add_dialog.destroy()
            return config_name_entered, section_name_entered
        add_dialog.destroy()
        return None, None

    def launch_exit_warning_dialog(self):
        """Launch a 'really want to quit' dialog."""
        text = 'Save changes before closing?'
        exit_dialog = Gtk.MessageDialog(buttons=Gtk.ButtonsType.NONE,
                                        message_format=text,
                                        parent=self.window)
        exit_dialog.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.REJECT,
                                Gtk.STOCK_CANCEL, Gtk.ResponseType.CLOSE,
                                Gtk.STOCK_YES, Gtk.ResponseType.ACCEPT)
        exit_dialog.set_title(metomi.rose.config_editor.DIALOG_TITLE_SAVE_CHANGES)
        exit_dialog.set_modal(True)
        exit_dialog.set_keep_above(True)
        exit_dialog.action_area.get_children()[1].grab_focus()
        response = exit_dialog.run()
        exit_dialog.destroy()
        if response == Gtk.ResponseType.REJECT:
            Gtk.main_quit()
        elif response == Gtk.ResponseType.ACCEPT:
            save_ok = self.save_func()
            if save_ok:
                Gtk.main_quit()
        return False

    def launch_graph_dialog(self, name_section_dict):
        """Launch a dialog asking for a config and section to graph.

        name_section_dict is a dictionary containing config names
        as keys, and lists of available sections as values.

        """
        prefs = {}
        return self._launch_choose_section_dialog(
            name_section_dict, prefs,
            metomi.rose.config_editor.DIALOG_TITLE_GRAPH,
            metomi.rose.config_editor.DIALOG_BODY_GRAPH_CONFIG,
            metomi.rose.config_editor.DIALOG_BODY_GRAPH_SECTION,
            null_section_choice=True
        )

    def launch_help_dialog(self, somewidget=None):
        """Launch a browser to open the help url."""
        webbrowser.open(
            'https://metomi.github.io/rose/doc/html/index.html',
            new=True,
            autoraise=True
        )
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
            dialog_title = metomi.rose.config_editor.DIALOG_TITLE_IGNORE
        else:
            dialog_title = metomi.rose.config_editor.DIALOG_TITLE_ENABLE
        config_title = metomi.rose.config_editor.DIALOG_BODY_IGNORE_ENABLE_CONFIG
        if is_ignored:
            section_title = metomi.rose.config_editor.DIALOG_BODY_IGNORE_SECTION
        else:
            section_title = metomi.rose.config_editor.DIALOG_BODY_ENABLE_SECTION
        return self._launch_choose_section_dialog(
            name_section_dict, prefs,
            dialog_title, config_title,
            section_title)

    def _launch_choose_section_dialog(
            self, name_section_dict, prefs, dialog_title, config_title,
            section_title, null_section_choice=False, do_target_section=False):
        chooser_dialog = Gtk.Dialog(
            title=dialog_title,
            parent=self.window,
            buttons=(Gtk.STOCK_CANCEL,
                     Gtk.ResponseType.REJECT,
                     Gtk.STOCK_OK,
                     Gtk.ResponseType.ACCEPT))
        config_label = Gtk.Label(label=config_title)
        config_label.show()
        section_label = Gtk.Label(label=section_title)
        section_label.show()
        config_name_box = Gtk.ComboBoxText()
        name_keys = sorted(list(name_section_dict.keys()))
        for k, name in enumerate(name_keys):
            config_name_box.append_text(name)
            if name in prefs:
                config_name_box.set_active(k)
        if config_name_box.get_active() == -1:
            config_name_box.set_active(0)
        config_name_box.show()
        section_box = Gtk.VBox()
        section_box.show()
        null_section_checkbutton = Gtk.CheckButton(
            metomi.rose.config_editor.DIALOG_LABEL_NULL_SECTION)
        null_section_checkbutton.connect(
            "toggled",
            lambda b: section_box.set_sensitive(not b.get_active())
        )
        if null_section_choice:
            null_section_checkbutton.show()
            null_section_checkbutton.set_active(True)
        index = config_name_box.get_active()
        section_combo = self._reload_section_choices(
            section_box,
            name_section_dict[name_keys[index]],
            prefs.get(name_keys[index], []))
        config_name_box.connect(
            'changed',
            lambda c: self._reload_section_choices(
                section_box,
                name_section_dict[name_keys[c.get_active()]],
                prefs.get(name_keys[c.get_active()], [])))
        vbox = Gtk.VBox(spacing=metomi.rose.config_editor.SPACING_PAGE)
        vbox.pack_start(config_label, expand=False, fill=False, padding=0)
        vbox.pack_start(config_name_box, expand=False, fill=False, padding=0)
        vbox.pack_start(section_label, expand=False, fill=False, padding=0)
        vbox.pack_start(null_section_checkbutton, expand=False, fill=False, padding=0)
        vbox.pack_start(section_box, expand=False, fill=False, padding=0)
        if do_target_section:
            target_section_entry = Gtk.Entry()
            self._reload_target_section_entry(
                section_combo, target_section_entry,
                name_keys[config_name_box.get_active()], name_section_dict
            )
            section_combo.connect(
                "changed",
                lambda combo: self._reload_target_section_entry(
                    combo, target_section_entry,
                    name_keys[config_name_box.get_active()],
                    name_section_dict
                )
            )
            target_section_entry.show()
            vbox.pack_start(target_section_entry, expand=False, fill=False, padding=0)
        vbox.show()
        hbox = Gtk.HBox()
        hbox.pack_start(vbox, expand=True, fill=True,
                        padding=metomi.rose.config_editor.SPACING_PAGE)
        hbox.show()
        chooser_dialog.vbox.pack_start(
            hbox, True, True, metomi.rose.config_editor.SPACING_PAGE)
        section_box.grab_focus()
        response = chooser_dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.YES,
                        Gtk.ResponseType.ACCEPT]:
            config_name_entered = name_keys[config_name_box.get_active()]
            if null_section_checkbutton.get_active():
                chooser_dialog.destroy()
                if do_target_section:
                    return config_name_entered, None, None
                return config_name_entered, None

            for widget in section_box.get_children():
                if hasattr(widget, 'get_active'):
                    index = widget.get_active()
                    sections = name_section_dict[config_name_entered]
                    section_name = sections[index]
                    if do_target_section:
                        target_section_name = target_section_entry.get_text()
                    chooser_dialog.destroy()
                    if do_target_section:
                        return (config_name_entered, section_name,
                                target_section_name)
                    return config_name_entered, section_name
        chooser_dialog.destroy()
        if do_target_section:
            return None, None, None
        return None, None

    def _reload_section_choices(self, vbox, sections, prefs):
        for child in vbox.get_children():
            vbox.remove(child)
        sections.sort(metomi.rose.config.sort_settings)
        section_chooser = Gtk.ComboBoxText()
        for k, section in enumerate(sections):
            section_chooser.append_text(section)
            if section in prefs:
                section_chooser.set_active(k)
        if section_chooser.get_active() == -1 and sections:
            section_chooser.set_active(0)
        section_chooser.show()
        vbox.pack_start(section_chooser, expand=False, fill=False, padding=0)
        return section_chooser

    def _reload_target_section_entry(self, section_combo_box, target_entry,
                                     config_name_entered, name_section_dict):
        index = section_combo_box.get_active()
        sections = name_section_dict[config_name_entered]
        section_name = sections[index]
        target_entry.set_text(section_name)

    def launch_macro_changes_dialog(
            self, config_name, macro_name, changes_list, mode="transform",
            search_func=metomi.rose.config_editor.false_function):
        """Launch a dialog explaining macro changes."""
        dialog = MacroChangesDialog(self.window, config_name, macro_name,
                                    mode, search_func)
        return dialog.display(changes_list)

    def launch_new_config_dialog(self, root_directory):
        """Launch a dialog allowing naming of a new configuration."""
        existing_apps = os.listdir(root_directory)
        checker_function = lambda t: t not in existing_apps
        label = metomi.rose.config_editor.DIALOG_LABEL_CONFIG_CHOOSE_NAME
        ok_tip_text = metomi.rose.config_editor.TIP_CONFIG_CHOOSE_NAME
        err_tip_text = metomi.rose.config_editor.TIP_CONFIG_CHOOSE_NAME_ERROR
        dialog, container, name_entry = metomi.rose.gtk.dialog.get_naming_dialog(
            label, checker_function, ok_tip_text, err_tip_text)
        dialog.set_title(metomi.rose.config_editor.DIALOG_TITLE_CONFIG_CREATE)
        meta_hbox = Gtk.HBox()
        meta_label = Gtk.Label(label=
            metomi.rose.config_editor.DIALOG_LABEL_CONFIG_CHOOSE_META)
        meta_label.show()
        meta_entry = Gtk.Entry()
        tip_text = metomi.rose.config_editor.TIP_CONFIG_CHOOSE_META
        meta_entry.set_tooltip_text(tip_text)
        meta_entry.connect(
            "activate", lambda b: dialog.response(Gtk.ResponseType.ACCEPT))
        meta_entry.show()
        meta_hbox.pack_start(meta_label, expand=False, fill=False,
                             padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        meta_hbox.pack_start(meta_entry, expand=False, fill=True,
                             padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        meta_hbox.show()
        container.pack_start(meta_hbox, expand=False, fill=True,
                             padding=metomi.rose.config_editor.SPACING_PAGE)
        response = dialog.run()
        name = None
        meta = None
        if name_entry.get_text():
            name = name_entry.get_text().strip().strip('/')
        if meta_entry.get_text():
            meta = meta_entry.get_text().strip()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            return name, meta
        return None, None

    def launch_open_dirname_dialog(self):
        """Launch a FileChooserDialog and return a directory, or None."""
        open_dialog = Gtk.FileChooserDialog(
            title=metomi.rose.config_editor.DIALOG_TITLE_OPEN,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL,
                     Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_OPEN,
                     Gtk.ResponseType.OK))
        open_dialog.set_transient_for(self.window)
        open_dialog.set_icon(self.window.get_icon())
        open_dialog.set_default_response(Gtk.ResponseType.OK)
        config_filter = Gtk.FileFilter()
        config_filter.add_pattern(metomi.rose.TOP_CONFIG_NAME)
        config_filter.add_pattern(metomi.rose.SUB_CONFIG_NAME)
        config_filter.add_pattern(metomi.rose.INFO_CONFIG_NAME)
        open_dialog.set_filter(config_filter)
        response = open_dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT,
                        Gtk.ResponseType.YES]:
            config_directory = os.path.dirname(open_dialog.get_filename())
            open_dialog.destroy()
            return config_directory
        open_dialog.destroy()
        return None

    def launch_load_metadata_dialog(self):
        """ Launches a dialoge for selecting a metadata path. """
        open_dialog = Gtk.FileChooserDialog(
            title=metomi.rose.config_editor.DIALOG_TITLE_LOAD_METADATA,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(Gtk.STOCK_CLOSE,
                     Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_ADD,
                     Gtk.ResponseType.OK))
        open_dialog.set_transient_for(self.window)
        open_dialog.set_icon(self.window.get_icon())
        open_dialog.set_default_response(Gtk.ResponseType.OK)
        response = open_dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT,
                        Gtk.ResponseType.YES]:
            config_directory = open_dialog.get_filename()
            open_dialog.destroy()
            return config_directory
        open_dialog.destroy()
        return None

    def launch_metadata_manager(self, paths):
        """
        Launches a dialogue where users may add or remove custom meta data
        paths.
        """
        dialog = Gtk.Dialog(
            title=metomi.rose.config_editor.DIALOG_TITLE_MANAGE_METADATA,
            buttons=(Gtk.STOCK_CANCEL,
                     Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_OK,
                     Gtk.ResponseType.OK)
        )

        # add description
        label = Gtk.Label(label='Specify metadata paths to override the default '
                          'metadata.\n')
        dialog.vbox.pack_start(label, True, True, 0)
        label.show()

        # create table of paths
        table = MetadataTable(paths, dialog.vbox)

        # create add path button
        button = Gtk.Button('Add Path')

        def add_path():
            _path = self.launch_load_metadata_dialog()
            if _path:
                table.add_row(_path)
        button.connect('clicked', lambda b: add_path())
        dialog.vbox.pack_start(button, True, True, 0)
        button.show()

        # open the dialogue
        response = dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT,
                        Gtk.ResponseType.YES]:
            # if user clicked 'ok'
            dialog.destroy()
            return table.paths
        else:
            dialog.destroy()
            return None

    def launch_prefs(self, somewidget=None):
        """Launch a dialog explaining preferences."""
        text = metomi.rose.config_editor.DIALOG_LABEL_PREFERENCES
        title = metomi.rose.config_editor.DIALOG_TITLE_PREFERENCES
        metomi.rose.gtk.dialog.run_dialog(metomi.rose.gtk.dialog.DIALOG_TYPE_INFO, text,
                                   title)
        return False

    def launch_remove_dialog(self, name_section_dict, prefs):
        """Launch a dialog asking for a section name to remove.

        name_section_dict is a dictionary containing config names
        as keys, and lists of available sections as values.
        prefs is in the same format, but indicates preferred values.

        """
        return self._launch_choose_section_dialog(
            name_section_dict, prefs,
            metomi.rose.config_editor.DIALOG_TITLE_REMOVE,
            metomi.rose.config_editor.DIALOG_BODY_REMOVE_CONFIG,
            metomi.rose.config_editor.DIALOG_BODY_REMOVE_SECTION
        )

    def launch_rename_dialog(self, name_section_dict, prefs):
        """Launch a dialog asking for a section name to rename.

        name_section_dict is a dictionary containing config names
        as keys, and lists of available sections as values.
        prefs is in the same format, but indicates preferred values.

        """
        return self._launch_choose_section_dialog(
            name_section_dict, prefs,
            metomi.rose.config_editor.DIALOG_TITLE_RENAME,
            metomi.rose.config_editor.DIALOG_BODY_RENAME_CONFIG,
            metomi.rose.config_editor.DIALOG_BODY_RENAME_SECTION,
            do_target_section=True
        )

    def launch_view_stack(self, undo_stack, redo_stack, undo_func):
        """Load a view of the stack."""
        self.log_window = metomi.rose.config_editor.stack.StackViewer(
            undo_stack, redo_stack, undo_func)
        self.log_window.set_transient_for(self.window)


class MacroChangesDialog(Gtk.Dialog):

    """Class to hold a dialog summarising macro results."""

    COLUMNS = ["Section", "Option", "Type", "Value", "Info"]
    MODE_COLOURS = {"transform": metomi.rose.config_editor.COLOUR_MACRO_CHANGED,
                    "validate": metomi.rose.config_editor.COLOUR_MACRO_ERROR,
                    "warn": metomi.rose.config_editor.COLOUR_MACRO_WARNING}
    MODE_TEXT = {"transform": metomi.rose.config_editor.DIALOG_TEXT_MACRO_CHANGED,
                 "validate": metomi.rose.config_editor.DIALOG_TEXT_MACRO_ERROR,
                 "warn": metomi.rose.config_editor.DIALOG_TEXT_MACRO_WARNING}

    def __init__(self, window, config_name, macro_name, mode, search_func):
        self.util = metomi.rose.config_editor.util.Lookup()
        self.short_config_name = config_name.rstrip('/').split('/')[-1]
        self.top_config_name = config_name.lstrip('/').split('/')[0]
        self.short_macro_name = macro_name.split('.')[-1]
        self.for_transform = (mode == "transform")
        self.for_validate = (mode == "validate")
        self.macro_name = macro_name
        self.mode = mode
        self.search_func = search_func
        if self.for_validate:
            title = metomi.rose.config_editor.DIALOG_TITLE_MACRO_VALIDATE
            button_list = [Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT]
        else:
            title = metomi.rose.config_editor.DIALOG_TITLE_MACRO_TRANSFORM
            button_list = [Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                           Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT]
        title = title.format(self.short_macro_name, self.short_config_name)
        button_list = tuple(button_list)
        super(MacroChangesDialog, self).__init__(buttons=button_list,
                                                 parent=window)
        if not self.for_transform:
            self.set_modal(False)
        self.set_title(title.format(macro_name))
        self.label = Gtk.Label()
        self.label.show()
        if self.for_validate:
            stock_id = Gtk.STOCK_DIALOG_WARNING
        else:
            stock_id = Gtk.STOCK_CONVERT
        image = Gtk.Image.new_from_stock(stock_id, Gtk.IconSize.LARGE_TOOLBAR)
        image.show()
        hbox = Gtk.HBox()
        hbox.pack_start(image, expand=False, fill=False,
                        padding=metomi.rose.config_editor.SPACING_PAGE)
        hbox.pack_start(self.label, expand=False, fill=False,
                        padding=metomi.rose.config_editor.SPACING_PAGE)
        hbox.show()
        self.treewindow = Gtk.ScrolledWindow()
        self.treewindow.show()
        self.treewindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.treeview = metomi.rose.gtk.util.TooltipTreeView(
            get_tooltip_func=self._get_tooltip)
        self.treeview.show()
        self.treemodel = Gtk.TreeStore(str, str, str, str, str)

        self.treeview.set_model(self.treemodel)
        for i, title in enumerate(self.COLUMNS):
            column = Gtk.TreeViewColumn()
            column.set_title(title)
            cell = Gtk.CellRendererText()
            if i == len(self.COLUMNS) - 1:
                column.pack_start(cell, True, True, 0)
            else:
                column.pack_start(cell, False, True, 0)
            if title == "Type":
                column.set_cell_data_func(cell, self._set_type_markup, i)
            else:
                column.set_cell_data_func(cell, self._set_markup, i)
            self.treeview.append_column(column)

        self.treeview.connect(
            "row-activated", self._handle_treeview_activation)
        self.treewindow.add(self.treeview)
        self.vbox.pack_end(self.treewindow, expand=True, fill=True,
                           padding=metomi.rose.config_editor.SPACING_PAGE)
        self.vbox.pack_end(hbox, expand=False, fill=True,
                           padding=metomi.rose.config_editor.SPACING_PAGE)
        self.set_focus(self.action_area.get_children()[0])

    def display(self, changes):
        if not changes:
            # Shortcut, no changes.
            if self.for_validate:
                title = metomi.rose.config_editor.DIALOG_TITLE_MACRO_VALIDATE_NONE
                text = metomi.rose.config_editor.DIALOG_LABEL_MACRO_VALIDATE_NONE
            else:
                title = metomi.rose.config_editor.DIALOG_TITLE_MACRO_TRANSFORM_NONE
                text = metomi.rose.config_editor.DIALOG_LABEL_MACRO_TRANSFORM_NONE
            title = title.format(self.short_macro_name)
            text = metomi.rose.gtk.util.safe_str(text)
            return metomi.rose.gtk.dialog.run_dialog(
                metomi.rose.gtk.dialog.DIALOG_TYPE_INFO, text, title)
        if self.for_validate:
            text = metomi.rose.config_editor.DIALOG_LABEL_MACRO_VALIDATE_ISSUES
        else:
            text = metomi.rose.config_editor.DIALOG_LABEL_MACRO_TRANSFORM_CHANGES
        nums_is_warning = {True: 0, False: 0}
        for item in changes:
            nums_is_warning[item.is_warning] += 1
        text = text.format(self.short_macro_name, self.short_config_name,
                           nums_is_warning[False])
        if nums_is_warning[True]:
            extra_text = metomi.rose.config_editor.DIALOG_LABEL_MACRO_WARN_ISSUES
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
        max_size = metomi.rose.config_editor.SIZE_MACRO_DIALOG_MAX
        my_size = self.size_request()
        new_size = [-1, -1]
        for i in [0, 1]:
            new_size[i] = min([my_size[i], max_size[i]])
        self.treewindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_default_size(*new_size)
        if self.for_transform:
            response = self.run()
            self.destroy()
            return (response == Gtk.ResponseType.ACCEPT)
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
            cell.set_property("markup", metomi.rose.gtk.util.safe_str(text))
        if col_index == 0:
            cell.set_property("visible", (len(model.get_path(r_iter)) == 1))

    def _handle_treeview_activation(self, view, path, column):
        r_iter = view.get_model().get_iter(path)
        section = view.get_model().get_value(r_iter, 0)
        option = view.get_model().get_value(r_iter, 1)
        id_ = self.util.get_id_from_section_option(section, option)
        self.search_func(id_)
