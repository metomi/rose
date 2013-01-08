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

import os
import shlex
import subprocess
import sys
import webbrowser

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import rose.config
import rose.config_editor
import rose.config_editor.util
import rose.external
import rose.gtk.util
import rose.resource


class HyperLinkTreePanel(gtk.ScrolledWindow):

    """Generate the page launcher panel.

    This contains the namespace groupings as child rows.
    Icons denoting changes in the attribute internal data are displayed
    next to the attributes.

    """

    def __init__(self, namespace_tree):
        super(HyperLinkTreePanel, self).__init__()
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.panel_top = gtk.TreeViewColumn()
        self.panel_top.set_title(rose.config_editor.TREE_PANEL_TITLE)
        self.cell_error_icon = gtk.CellRendererPixbuf()
        self.cell_changed_icon = gtk.CellRendererPixbuf()
        self.cell_title = gtk.CellRendererText()
        self.panel_top.pack_start(self.cell_error_icon, expand=False)
        self.panel_top.pack_start(self.cell_changed_icon, expand=False)
        self.panel_top.pack_start(self.cell_title, expand=False)
        self.panel_top.add_attribute(self.cell_error_icon,
                                     attribute='pixbuf',
                                     column=0)
        self.panel_top.add_attribute(self.cell_changed_icon,
                                     attribute='pixbuf',
                                     column=1)
        self.panel_top.set_cell_data_func(self.cell_title,
                                          self._set_title_markup, 2)
        self.data_store = gtk.TreeStore(gtk.gdk.Pixbuf, gtk.gdk.Pixbuf,
                                        str, str, int, int, int, int,
                                        str, str, str, str, str, str)
        # Data: name, title, error and change numbers,
        #       main tip, description, help, url, comment, change
        resource_loc = rose.resource.ResourceLocator(paths=sys.path)
        image_path = resource_loc.locate('etc/images/rose-config-edit')
        self.null_icon = gtk.gdk.pixbuf_new_from_file(image_path +
                                                      '/null_icon.xpm')
        self.changed_icon = gtk.gdk.pixbuf_new_from_file(image_path +
                                                         '/change_icon.xpm')
        self.error_icon = gtk.gdk.pixbuf_new_from_file(image_path +
                                                       '/error_icon.xpm')
        self.tree = rose.gtk.util.TooltipTreeView(
                             get_tooltip_func=self.get_treeview_tooltip)
        self.tree.append_column(self.panel_top)
        self.tree.set_model(self.data_store)
        self.tree.show()
        self.add(self.tree)
        self.load_tree(None, namespace_tree)
        self.tree.connect('button_press_event',
                          self.handle_activation)
        self._last_tree_activation_path = None
        self.tree.connect('row_activated',
                          self.handle_activation)
        self.tree.connect_after('move-cursor', self._handle_cursor_change)
        self.tree.connect('key-press-event', self.add_cursor_extra)
        self.panel_top.set_clickable(True)
        self.panel_top.connect('clicked',
                               lambda c: self.collapse_reset())
        self.show()
        self.tree.columns_autosize()
        self.tree.connect('enter-notify-event',
                          lambda t, e: self.update_row_tooltips())
        self.name_iter_map = {}

    def get_treeview_tooltip(self, view, row_iter, col_index, tip):
        """Handle creating a tooltip for the treeview."""
        tip.set_text(view.get_model().get_value(row_iter, 8))
        return True

    def add_cursor_extra(self, widget, event):
        left = (event.keyval == gtk.keysyms.Left)
        right = (event.keyval == gtk.keysyms.Right)
        if left or right:
            path, col = widget.get_cursor()
            if path is not None:
                if right:
                    widget.expand_row(path, open_all=False)
                elif left:
                    widget.collapse_row(path)
        return False

    def _handle_cursor_change(self, *args):
        current_path = self.tree.get_cursor()[0]
        if current_path != self._last_tree_activation_path:
            gobject.timeout_add(rose.config_editor.TREE_PANEL_KBD_TIMEOUT,
                                self._timeout_launch, current_path)

    def _timeout_launch(self, timeout_path):
        current_path = self.tree.get_cursor()[0]
        if (current_path == timeout_path and
            self._last_tree_activation_path != timeout_path):
            self.send_launch_request(self.get_name(timeout_path),
                                     as_new=False)
        return False
        
    def load_tree(self, row, namespace_subtree):
        expanded_rows = []
        self.name_iter_map = {}
        self.tree.map_expanded_rows(lambda r, d: expanded_rows.append(d))
        self.recursively_load_tree(row, namespace_subtree)
        self.set_expansion()
        for this_row in expanded_rows:
            self.tree.expand_to_path(this_row)

    def set_expansion(self):
        """Set the default expanded rows."""
        top_rows = self.tree.get_model().iter_n_children(None)
        if top_rows > rose.config_editor.TREE_PANEL_MAX_EXPANDED:
            return False
        if top_rows == 1:
            return self.tree.expand_all()
        r_iter = self.tree.get_model().get_iter_first()
        while r_iter is not None:
            path = self.tree.get_model().get_path(r_iter)
            self.tree.expand_to_path(path)
            r_iter = self.tree.get_model().iter_next(r_iter)

    def recursively_load_tree(self, row, namespace_subtree):
        """Update the tree store recursively using namespace_subtree."""
        self.name_iter_map = {}
        if row is None:
            self.data_store.clear()
        initials = namespace_subtree.items()
        initials.sort(self.sort_tree_items)
        stack = [[row] + list(i) for i in initials]
        while stack:
            row, key, value_meta_tuple = stack[0]
            value, meta, comment, change = value_meta_tuple
            description = meta.get(rose.META_PROP_DESCRIPTION, '')
            help = meta.get(rose.META_PROP_HELP, '')
            url = meta.get(rose.META_PROP_URL, '')
            title = meta[rose.META_PROP_TITLE]
            new_row = self.data_store.append(row, [self.null_icon,
                                                   self.null_icon,
                                                   title,
                                                   key,
                                                   0, 0, 0, 0,
                                                   '',
                                                   description,
                                                   help,
                                                   url,
                                                   comment,
                                                   change])
            if type(value) is dict:
                newer_initials = value.items()
                newer_initials.sort(self.sort_tree_items)
                for x in newer_initials:
                    stack.append([new_row] + list(x))
            stack.pop(0)

    def _set_title_markup(self, column, cell, model, r_iter, index):
        title = model.get_value(r_iter, index)
        title = rose.gtk.util.safe_str(title)
        if len(model.get_path(r_iter)) == 1:
            title = rose.config_editor.TITLE_PAGE_MARKUP.format(title)
        cell.set_property("markup", title)

    def sort_tree_items(self, row_item_1, row_item_2):
        """Sort tree items according to name and sort key."""
        main_sort_func = rose.config.sort_settings
        sort_key_1 = row_item_1[1][1].get(rose.META_PROP_SORT_KEY, '')
        sort_key_2 = row_item_2[1][1].get(rose.META_PROP_SORT_KEY, '')
        sort_key_1 = sort_key_1 + '~' + row_item_1[0]
        sort_key_2 = sort_key_2 + '~' + row_item_2[0]
        return main_sort_func(sort_key_1, sort_key_2)

    def get_rows(self, path=None):
        """Return all row paths under path in the tree model."""
        tree_model = self.tree.get_model()
        if path is None:
            my_iter = tree_model.get_iter_first()
        else:
            my_iter = tree_model.get_iter(path)
        rows = []
        while my_iter is not None:
            rows.append(tree_model.get_path(my_iter))
            next_iter = tree_model.iter_children(my_iter)
            if next_iter is None:
                next_iter = tree_model.iter_next(my_iter)
                if next_iter is None:
                    next_iter = tree_model.iter_parent(my_iter)
                    next_iter = tree_model.iter_next(next_iter)
            my_iter = next_iter
        return rows

    def set_row_icon(self, names, ind_count=0, ind_type='changed'):
        """Set the icons for row status on or off. Check parent icons.

        After updating the row which is specified by a list of namespace
        pieces (names), go up through the tree and update parent row icons
        according to the status of their child row icons.

        """
        ind_map = {'changed': {'icon_col': 1,
                               'icon': self.changed_icon,
                               'int_col': 6,
                               'total_col': 7},
                   'error': {'icon_col': 0,
                             'icon': self.error_icon,
                             'int_col': 4,
                             'total_col': 5}}
        int_col = ind_map[ind_type]['int_col']
        total_col = ind_map[ind_type]['total_col']
        row_path = self.get_path_from_names(names)
        tree_model = self.tree.get_model()
        if row_path is None:
            return False
        row_iter = tree_model.get_iter(row_path)
        old_total = tree_model.get_value(row_iter, total_col)
        old_int = tree_model.get_value(row_iter, int_col)
        diff_int_count = ind_count - old_int
        new_total = old_total + diff_int_count
        tree_model.set_value(row_iter, int_col, ind_count)
        tree_model.set_value(row_iter, total_col, new_total)
        if new_total > 0:
            tree_model.set_value(row_iter, ind_map[ind_type]['icon_col'],
                                 ind_map[ind_type]['icon'])
        else:
            tree_model.set_value(row_iter, ind_map[ind_type]['icon_col'],
                                 self.null_icon)

        # Now pass information up the tree
        for parent in [row_path[:i] for i in range(len(row_path) - 1, 0, -1)]:
            parent_iter = tree_model.get_iter(parent)
            old_parent_total = tree_model.get_value(parent_iter, total_col)
            new_parent_total = old_parent_total + diff_int_count
            tree_model.set_value(parent_iter, total_col, new_parent_total)
            if new_parent_total > 0:
                tree_model.set_value(parent_iter,
                                     ind_map[ind_type]['icon_col'],
                                     ind_map[ind_type]['icon'])
            else:
                tree_model.set_value(parent_iter,
                                     ind_map[ind_type]['icon_col'],
                                     self.null_icon)

    def update_row_tooltips(self):
        """Synchronise the icon information with the hover-over text."""
        tree_model = self.tree.get_model()
        my_iter = tree_model.get_iter_first()
        if my_iter is None:
            return
        paths = []
        iter_stack = [my_iter]
        while iter_stack:
            my_iter = iter_stack.pop(0)
            paths.append(tree_model.get_path(my_iter))
            next_iter = tree_model.iter_next(my_iter)
            if next_iter is not None:
                iter_stack.append(next_iter)
            if tree_model.iter_has_child(my_iter):
                iter_stack.append(tree_model.iter_children(my_iter))
        for path in paths:
            path_iter = tree_model.get_iter(path)
            name = tree_model.get_value(path_iter, 3)
            num_errors = tree_model.get_value(path_iter, 4)
            mods = tree_model.get_value(path_iter, 6)
            description = tree_model.get_value(path_iter, 9)
            comment = tree_model.get_value(path_iter, 12)
            change = tree_model.get_value(path_iter, 13)
            if description != '':
                text = description
            else:
                text = name
            if mods > 0:
                text += rose.config_editor.TREE_PANEL_MODIFIED
            if num_errors > 0:
                if num_errors == 1:
                    text += rose.config_editor.TREE_PANEL_ERROR
                else:
                    text += rose.config_editor.TREE_PANEL_ERRORS.format(
                                                          num_errors)
            if description != '':
                text += "\n(" + name + ")"
            if comment:
                text += "\n" + comment
            if change:
                text += "\n" + change
            tree_model.set_value(path_iter, 8, text)

    def update_change(self, row_names, new_change):
        """Update 'changed' text."""
        self._set_row_names_value(row_names, 13, new_change)

    def update_comment(self, row_names, new_comment):
        """Update 'comment' text."""
        self._set_row_names_value(row_names, 12, new_comment)

    def _set_row_names_value(self, row_names, index, value):
        path = self.get_path_from_names(row_names)
        if path is not None:
            model = self.tree.get_model()
            row_iter = model.get_iter(path)
            model.set_value(row_iter, index, value)

    def select_row(self, row_names):
        """Highlight one particular row, but only this one."""
        if row_names is None:
            return
        path = self.get_path_from_names(row_names)
        if path is not None:
            i = 1
            while self.tree.row_expanded(path[:i]) and i <= len(path):
                i += 1
            self.tree.set_cursor(path[:i])
        if path is None:
            self.tree.set_cursor((0,))

    def get_path_from_name(self, row_name):
        """Return a row path corresponding to the row name, or None."""
        tree_model = self.tree.get_model()
        my_iter = tree_model.get_iter_first()
        this_name = tree_model.get_value(my_iter, 3)
        while my_iter is not None and this_name != row_name:
            my_iter = tree_model.iter_next(my_iter)
            if my_iter is not None:
                this_name = tree_model.get_value(my_iter, 3)
            else:
                my_iter = tree_model.iter_children(my_iter)
                my_iter = tree_model.iter_children(my_iter)
                if my_iter is not None:
                    this_name = tree_model.get_value(my_iter, 3)
        if my_iter is not None:
            path = tree_model.get_path(my_iter)
            return path
        return None

    def get_path_from_names(self, row_names):
        """Return a row path corresponding to the list of branch names."""
        tree_model = self.tree.get_model()
        key = tuple(row_names)
        if key in self.name_iter_map:
            return tree_model.get_path(self.name_iter_map[key])
        my_iter = tree_model.get_iter_first()
        these_names = []
        good_paths = [row_names[:i] for i in range(len(row_names) + 1)]
        for names in reversed(good_paths):
            subkey = tuple(names)
            if subkey in self.name_iter_map:
                my_iter = self.name_iter_map[subkey]
                these_names = names[:-1]
                break
        while my_iter is not None:
            branch_name = tree_model.get_value(my_iter, 3)
            my_names = these_names + [branch_name]
            self.name_iter_map.update({tuple(my_names): my_iter})
            if my_names in good_paths:
                if my_names == row_names:
                    return tree_model.get_path(my_iter)
                else:
                    these_names.append(branch_name)
                    my_iter = tree_model.iter_children(my_iter)
            else:
                my_iter = tree_model.iter_next(my_iter)
        return None

    def handle_activation(self, treeview=None, event=None, somewidget=None):
        """Send a page launch request based on left or middle clicks."""
        if event is not None and treeview is not None:
            if hasattr(event, 'button'):
                pathinfo = treeview.get_path_at_pos(int(event.x),
                                                    int(event.y))
                if pathinfo is not None:
                    path, col, cell_x, cell_y = pathinfo
                    if (treeview.get_expander_column() == col and
                        cell_x < 1 + 18 * len(path)):  # Hardwired, bad.
                        if event.button != 3:
                            return False
                        else:
                            return treeview.expand_row(path, open_all=True)
                    if event.button == 3:
                        self.popup_menu(path, event)
                    else:
                        treeview.grab_focus()
                        treeview.set_cursor( pathinfo[0], col, 0)
                elif event.button == 3: # Right clicked outside the rows
                    self.popup_menu(None, event)
                else: # Clicked outside the rows
                    return False
                if event.button == 1:  # Left click event, replace old tab
                    self._last_tree_activation_path = path
                    self.send_launch_request(self.get_name(path),
                                             as_new=False)
                elif event.button == 2:  # Middle click event, make new tab
                    self._last_tree_activation_path = path
                    self.send_launch_request(self.get_name(path),
                                             as_new=True)
            else:
                path = event
                self.send_launch_request(self.get_name(path), as_new=False)
        return False

    def get_name(self, path=None):
        """Return the row name (text) corresponding to the treeview path."""
        if path is None:
            tree_selection = self.tree.get_selection()
            (tree_model, tree_iter) = tree_selection.get_selected()
            path = tree_model.get_path(tree_iter)
        else:
            tree_model = self.tree.get_model()
            tree_iter = tree_model.get_iter(path)
        row_name = str(tree_model.get_value(tree_iter, 3))
        full_name = row_name
        for parent in [path[:i] for i in range(len(path) - 1, 0, -1)]:
            parent_iter = tree_model.get_iter(parent)
            full_name = (str(tree_model.get_value(parent_iter, 3) +
                         "/" + full_name))
        return full_name

    def get_subtree_names(self, path=None):
        """Return all names that exist in a subtree of path."""
        tree_model = self.tree.get_model()
        root_iter = tree_model.get_iter(path)
        sub_iters = []
        for n in range(tree_model.iter_n_children(root_iter)):
            sub_iters.append(tree_model.iter_nth_child(root_iter, n))
        sub_names = []
        while sub_iters:
            if sub_iters[0] is not None:
                path = tree_model.get_path(sub_iters[0])
                sub_names.append(self.get_name(path))
                for n in range(tree_model.iter_n_children(sub_iters[0])):
                    sub_iters.append(tree_model.iter_nth_child(sub_iters[0],
                                                               n))
            sub_iters.pop(0)
        return sub_names

    def popup_menu(self, path, event):
        """Launch a popup menu for add/clone/remove."""
        if path is None or len(path) <= 1:
            add_name = None
        else:
            add_name = "/" + self.get_name(path)
        tree_model = self.tree.get_model()
        tree_iter = None
        if path is not None:
            tree_iter = tree_model.get_iter(path)
        ui_config_string = """<ui> <popup name='Popup'>
                              <menuitem action="New"/>
                              <separator name="newconfigsep"/>
                              <menuitem action="Add"/>"""
        actions = [('New', gtk.STOCK_NEW,
                    rose.config_editor.TREE_PANEL_NEW_CONFIG),
                   ('Add', gtk.STOCK_ADD,
                    rose.config_editor.TREE_PANEL_ADD_SECTION),
                   ('Autofix', gtk.STOCK_CONVERT,
                    rose.config_editor.TREE_PANEL_AUTOFIX_CONFIG),
                   ('Clone', gtk.STOCK_COPY,
                    rose.config_editor.TREE_PANEL_CLONE_SECTION),
                   ('Edit', gtk.STOCK_EDIT,
                    rose.config_editor.TREE_PANEL_EDIT_SECTION),
                   ('Enable', gtk.STOCK_YES,
                    rose.config_editor.TREE_PANEL_ENABLE_SECTION),
                   ('Ignore', gtk.STOCK_NO,
                    rose.config_editor.TREE_PANEL_IGNORE_SECTION),
                   ('Info', gtk.STOCK_INFO,
                    rose.config_editor.TREE_PANEL_INFO_SECTION),
                   ('Help', gtk.STOCK_HELP,
                    rose.config_editor.TREE_PANEL_HELP_SECTION),
                   ('URL', gtk.STOCK_HOME,
                    rose.config_editor.TREE_PANEL_URL_SECTION),
                   ('Remove', gtk.STOCK_DELETE,
                    rose.config_editor.TREE_PANEL_REMOVE)]
        if path is not None:
            name = self.get_name(path)
            cloneable = self.ask_can_clone(name)
            is_top = self.ask_is_top(name)
            is_fixable = (is_top and tree_iter is not None and
                          tree_model.get_value(tree_iter, 5) > 0)
            has_content = self.ask_has_content(name)
            if is_fixable:
                ui_config_string = ui_config_string.replace(
                          """<separator name="newconfigsep"/>""",
                          """<separator name="newconfigsep"/>
                             <menuitem action="Autofix"/>
                             <separator name="sepauto"/>""", 1)
            if cloneable:
                ui_config_string += '<separator name="clonesep"/>'
                ui_config_string += '<menuitem action="Clone"/>'
            ui_config_string += '<separator name="ignoresep"/>'
            ui_config_string += '<menuitem action="Enable"/>'
            ui_config_string += '<menuitem action="Ignore"/>'
            ui_config_string += '<separator name="infosep"/>'
            if has_content:
                ui_config_string += '<menuitem action="Info"/>'
                ui_config_string += '<menuitem action="Edit"/>'
            url = self.get_url(path)
            help = self.get_help(path)
            if url is not None or help is not None:
                ui_config_string += '<separator name="helpsep"/>'
                if url is not None:
                    ui_config_string += '<menuitem action="URL"/>'
                if help is not None:
                    ui_config_string += '<menuitem action="Help"/>'
            if not is_top:
                ui_config_string += """<separator name="sep1"/>
                                       <menuitem action="Remove"/>"""
        else:
            ui_config_string += '<separator name="ignoresep"/>'
            ui_config_string += '<menuitem action="Enable"/>'
            ui_config_string += '<menuitem action="Ignore"/>'
        ui_config_string += """</popup> </ui>"""
        uimanager = gtk.UIManager()
        actiongroup = gtk.ActionGroup('Popup')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, pos=0)
        uimanager.add_ui_from_string(ui_config_string)
        is_empty = (self.tree.get_model().get_iter_first() is None)
        new_item = uimanager.get_widget('/Popup/New')
        new_item.connect("activate",
                         lambda b: self.send_create_request())
        new_item.set_sensitive(not is_empty)
        add_item = uimanager.get_widget('/Popup/Add')
        add_item.connect("activate",
                         lambda b: self.send_add_dialog_request(add_name))
        add_item.set_sensitive(not is_empty)
        enable_item = uimanager.get_widget('/Popup/Enable')
        enable_item.connect(
                    "activate",
                    lambda b: self.send_ignore_request(add_name, False))
        enable_item.set_sensitive(not is_empty)
        ignore_item = uimanager.get_widget('/Popup/Ignore')
        ignore_item.connect(
                    "activate",
                    lambda b: self.send_ignore_request(add_name, True))
        ignore_item.set_sensitive(not is_empty)
        if path is not None:
            if cloneable:
                clone_item = uimanager.get_widget('/Popup/Clone')
                clone_item.connect("activate",
                                   lambda b: self.send_clone_request(name))
            if has_content:
                edit_item = uimanager.get_widget('/Popup/Edit')
                edit_item.connect("activate",
                                    lambda b: self.send_edit_request(name))
                info_item = uimanager.get_widget('/Popup/Info')
                info_item.connect("activate",
                                    lambda b: self.send_info_request(name))
            if self.get_help(path) is not None:
                help_item = uimanager.get_widget('/Popup/Help')
                help_title = name.split('/')[1:]
                help_title = rose.config_editor.DIALOG_HELP_TITLE.format(
                                                                  help_title)
                ns = "/" + name
                search_function = lambda i: self.send_search_request(ns, i)
                help_item.connect(
                          "activate",
                          lambda b: rose.gtk.util.run_hyperlink_dialog(
                                         gtk.STOCK_DIALOG_INFO,
                                         self.get_help(path),
                                         help_title,
                                         search_function))
            if self.get_url(path) is not None:
                url_item = uimanager.get_widget('/Popup/URL')
                url_item.connect(
                            "activate",
                            lambda b: webbrowser.open(self.get_url(path)))
            if is_fixable:
                autofix_item = uimanager.get_widget('/Popup/Autofix')
                autofix_item.connect("activate",
                                     lambda b: self.send_fix_request(name))
            if not is_top:
                del_names = self.get_subtree_names(path) + [name]
                del_names = ['/' + d for d in del_names]
                remove_item = uimanager.get_widget('/Popup/Remove')
                remove_item.connect("activate",
                                    lambda b: self.send_delete_request(
                                                               del_names))
        menu = uimanager.get_widget('/Popup')
        menu.popup(None, None, None, event.button, event.time)
        return False

    def collapse_reset(self):
        """Return the tree view to the basic startup state."""
        self.tree.collapse_all()
        self.set_expansion()
        self.tree.grab_focus()
        return False

    def get_help(self, path):
        h_iter = self.tree.get_model().get_iter(path)
        help = self.tree.get_model().get_value(h_iter, 10)
        if help == '':
            return None
        return help

    def get_url(self, path):
        u_iter = self.tree.get_model().get_iter(path)
        help = self.tree.get_model().get_value(u_iter, 11)
        if help == '':
            return None
        return help

    def ask_can_clone(self, name):
        """Connect this at a higher level for section clone menu options."""
        pass

    def ask_is_top(self, name):
        """Connect this at a higher level to test parenthood."""
        pass

    def ask_has_content(self, name):
        """Connect this at a higher level to test for any data here."""
        pass

    def send_add_dialog_request(self, name):
        """Connect this at a higher level for section add requests."""
        pass

    def send_clone_request(self, name):
        """Connect this at a higher level for section clone requests."""
        pass

    def send_create_request(self):
        """Connect this at a higher level for config creation requests."""
        pass

    def send_delete_request(self, name):
        """Connect this at a higher level for namespace delete requests."""
        pass

    def send_edit_request(self, name):
        """Connect this at a higher level for comment edit requests."""
        pass

    def send_fix_request(self, name):
        """Connect this at a higher level for auto-fix requests."""

    def send_ignore_request(self, name, is_ignored):
        """Connect this at a higher level for section ignore/enable."""
        pass

    def send_info_request(self, name):
        """Connect this at a higher level for section info."""

    def send_launch_request(self, path, as_new=False):
        """Connect this at a higher level for page creation requests."""
        pass

    def send_search_request(self, name, variable_id):
        """Connect this at a higher level for hyperlink connection."""
        pass


class FileSystemPanel(gtk.ScrolledWindow):

    """A class to show underlying files and directories in a gtk.TreeView."""

    def __init__(self, directory):
        super(FileSystemPanel, self).__init__()
        self.directory = directory
        view = gtk.TreeView()
        store = gtk.TreeStore(str, str)
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
                if (dirname.startswith(".") or
                    dirname in [rose.SUB_CONFIGS_DIR, rose.CONFIG_META_DIR]):
                    dirnames.remove(dirname)
            dirnames.sort()
        view.set_model(store)
        col = gtk.TreeViewColumn()
        col.set_title(rose.config_editor.TITLE_FILE_PANEL)
        cell = gtk.CellRendererText()
        col.pack_start(cell, expand=True)
        col.set_cell_data_func(cell,
                               self._set_path_markup, store)
        view.append_column(col)
        view.expand_all()
        view.show()
        view.connect("row-activated", self._handle_activation)
        view.connect("button-press-event", self._handle_click)
        self.add(view)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
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
            if not model.iter_has_child(row_iter):
                target_func = rose.external.launch_geditor
        try:
            target_func(target)
        except Exception as e:
            title = rose.config_editor.DIALOG_TITLE_CRITICAL_ERROR
            rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                                     str(e), title)

    def _handle_click(self, view, event):
        pathinfo = view.get_path_at_pos(int(event.x), int(event.y))
        if (event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS and
            pathinfo is None):
            self._handle_activation()
        if event.button == 3:
            ui_string = """<ui><popup name='Popup'>
                           <menuitem action='Open'/>
                           </popup> </ui>"""
            actions = [('Open', gtk.STOCK_OPEN,
                         rose.config_editor.FILE_PANEL_MENU_OPEN)]
            uimanager = gtk.UIManager()
            actiongroup = gtk.ActionGroup('Popup')
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


class SummaryDataPanel(gtk.ScrolledWindow):

    """A class to show rose sub-sections and variables in a gtk.TreeView."""

    def __init__(self, sections, variables, search_function, is_duplicate):
        super(SummaryDataPanel, self).__init__()
        self.sections = sections
        self.variables = variables
        self.search_function = search_function
        self.is_duplicate = is_duplicate
        self._view = rose.gtk.util.TooltipTreeView(
                                   get_tooltip_func=self._get_tree_tip)
        self._view.set_rules_hint(True)
        self._view.show()
        self._view.connect("row-activated",
                                    self._handle_activation)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.update_tree_model()
        self.add(self._view)
        self.show()

    def update_tree_model(self, sections=None, variables=None):
        """Update the summary of page data."""
        if sections is not None:
            self.sections = sections
        if variables is not None:
            self.variables = variables
        for column in list(self._view.get_columns()):
            self._view.remove_column(column)
        model, cols = self._get_tree_model_and_col_names()
        self._view.set_model(model)
        for i, col_name in enumerate(cols):
            col = gtk.TreeViewColumn()
            col.set_title(col_name.replace("_", "__"))
            cell = gtk.CellRendererText()
            col.pack_start(cell, expand=True)
            if i < len(cols) - 1:
                col.set_resizable(True)
            col.set_sort_column_id(i)
            col.set_cell_data_func(cell, self._get_tree_cell)
            self._view.append_column(col)

    def _get_tree_cell(self, col, cell, model, row_iter):
        col_index = self._view.get_columns().index(col)
        value = model.get_value(row_iter, col_index)
        max_len = rose.config_editor.SUMMARY_DATA_PANEL_MAX_LEN
        if (value is not None and len(value) > max_len
            and col_index != 0):
            cell.set_property("width-chars", max_len)
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        if col_index == 0 and self.is_duplicate:
            value = value.split("(")[-1].rstrip(")")
        cell.set_property("markup", value)

    def _get_tree_tip(self, view, row_iter, col_index, tip):
        cell_id = view.get_model().get_value(row_iter, 0)
        if col_index == 0:
            tip.set_text(cell_id)
        else:
            col_title = view.get_columns()[col_index].get_title()
            cell_id += rose.CONFIG_DELIMITER + col_title
            cell_data = view.get_model().get_value(row_iter, col_index)
            if cell_data is None:
                tip.set_text(cell_id)
            else:
                tip.set_text(cell_id + "\n" + cell_data)
        return True

    def _get_tree_model_and_col_names(self):
        # Construct a data model of other page data.
        sub_sect_names = [s.name for s in self.sections]
        sub_var_names = []
        var_id_map = {}
        for variable in self.variables:
            var_id_map[variable.metadata["id"]] = variable
            if variable.name not in sub_var_names:
                sub_var_names.append(variable.name)
        sub_sect_names.sort(rose.config.sort_settings)
        sub_var_names.sort(rose.config.sort_settings)
        col_types = [str] + [str] * len(sub_var_names)
        store = gtk.TreeStore(*col_types)
        i_format = rose.config_editor.SUMMARY_DATA_PANEL_IGNORED_MARKUP.format
        safe_str = rose.gtk.util.safe_str
        for section in sub_sect_names:
            row_data = [section]
            for opt in sub_var_names:
                var = var_id_map.get(section + rose.CONFIG_DELIMITER + opt)
                if var is None:
                    row_data.append(None)
                else:
                    if var.ignored_reason:
                        row_data.append(i_format(safe_str(var.value)))
                    else:
                        row_data.append(var.value)
            store.append(None, row_data)
        if self.is_duplicate:
            store.set_sort_func(0, self._sort_model_dupl)
        column_names = [rose.config_editor.SUMMARY_DATA_PANEL_SECTION_TITLE]
        column_names += sub_var_names
        return store, column_names

    def _sort_model_dupl(self, model, iter1, iter2):
        val1 = model.get_value(iter1, 0)
        val2 = model.get_value(iter2, 0)
        return rose.config.sort_settings(val1, val2)
            
    def _handle_activation(self, view, path, column):
        if path is None:
            return False
        model = view.get_model()
        row_iter = model.get_iter(path)
        col_index = view.get_columns().index(column)
        cell_data = model.get_value(row_iter, col_index)
        search_id = model.get_value(row_iter, 0)
        if cell_data != search_id and cell_data is not None:
            option = column.get_title().replace("__", "_")
            search_id += rose.CONFIG_DELIMITER + option
        self.search_function(search_id)
