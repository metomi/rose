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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import rose.config_editor
import rose.external
import rose.gtk.dialog
import rose.gtk.util


class FileSystemPanel(Gtk.ScrolledWindow):

    """A class to show underlying files and directories in a Gtk.TreeView."""

    def __init__(self, directory):
        super(FileSystemPanel, self).__init__()
        self.directory = directory
        view = Gtk.TreeView()
        store = Gtk.TreeStore(str, str)
        dirpath_iters = {self.directory: None}
        for dirpath, dirnames, filenames in os.walk(self.directory):
            if dirpath not in dirpath_iters:
                known_path = os.path.dirname(dirpath)
                new_iter = store.append(dirpath_iters[known_path],
                                        [os.path.basename(dirpath),
                                         os.path.abspath(dirpath)])
                dirpath_iters.update({dirpath: new_iter})
            this_iter = dirpath_iters[dirpath]
            filenames.sort()
            for name in filenames:
                if name in rose.CONFIG_NAMES:
                    continue
                filepath = os.path.join(dirpath, name)
                store.append(this_iter, [name, os.path.abspath(filepath)])
            for dirname in list(dirnames):
                if (dirname.startswith(".") or dirname in [
                        rose.SUB_CONFIGS_DIR, rose.CONFIG_META_DIR]):
                    dirnames.remove(dirname)
            dirnames.sort()
        view.set_model(store)
        col = Gtk.TreeViewColumn()
        col.set_title(rose.config_editor.TITLE_FILE_PANEL)
        cell = Gtk.CellRendererText()
        col.pack_start(cell, True, True, 0)
        col.set_cell_data_func(cell,
                               self._set_path_markup, store)
        view.append_column(col)
        view.expand_all()
        view.show()
        view.connect("row-activated", self._handle_activation)
        view.connect("button-press-event", self._handle_click)
        self.add(view)
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.show()

    def _set_path_markup(self, column, cell, model, r_iter, treestore):
        title = model.get_value(r_iter, 0)
        title = rose.gtk.util.safe_str(title)
        cell.set_property("markup", title)

    def _handle_activation(self, view=None, path=None, col=None):
        target_func = rose.external.launch_fs_browser
        if path is None:
            target = self.directory
        else:
            model = view.get_model()
            row_iter = model.get_iter(path)
            fs_path = model.get_value(row_iter, 1)
            target = fs_path
            if not os.path.isdir(target):
                target_func = rose.external.launch_geditor
        try:
            target_func(target)
        except Exception as exc:
            rose.gtk.dialog.run_exception_dialog(exc)

    def _handle_click(self, view, event):
        pathinfo = view.get_path_at_pos(int(event.x), int(event.y))
        if (event.button == 1 and event.type == Gdk._2BUTTON_PRESS and
                pathinfo is None):
            self._handle_activation()
        if event.button == 3:
            ui_string = """<ui><popup name='Popup'>
                           <menuitem action='Open'/>
                           </popup> </ui>"""
            actions = [('Open', Gtk.STOCK_OPEN,
                        rose.config_editor.FILE_PANEL_MENU_OPEN)]
            uimanager = Gtk.UIManager()
            actiongroup = Gtk.ActionGroup('Popup')
            actiongroup.add_actions(actions)
            uimanager.insert_action_group(actiongroup, pos=0)
            uimanager.add_ui_from_string(ui_string)
            if pathinfo is None:
                path = None
                col = None
            else:
                path, col = pathinfo[:2]
            open_item = uimanager.get_widget('/Popup/Open')
            open_item.connect(
                "activate",
                lambda m: self._handle_activation(view, path, col))
            this_menu = uimanager.get_widget('/Popup')
            this_menu.popup(None, None, None, event.button, event.time)
