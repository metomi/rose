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
import rose.gtk.util
import rose.resource


class PageNavigationPanel(gtk.ScrolledWindow):

    """Generate the page launcher panel.

    This contains the namespace groupings as child rows.
    Icons denoting changes in the attribute internal data are displayed
    next to the attributes.

    """

    def __init__(self, namespace_tree, launch_ns_func,
                 get_metadata_comments_func,
                 popup_menu_func, ask_can_show_func):
        super(PageNavigationPanel, self).__init__()
        self._launch_ns_func = launch_ns_func
        self._get_metadata_comments_func = get_metadata_comments_func
        self._popup_menu_func = popup_menu_func
        self._ask_can_show_func = ask_can_show_func
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
        # The columns in self.data_store correspond to: error_icon,
        # change_icon, name, title, error and change totals (4),
        # latent and ignored statuses, main tip text, and change text.
        self.data_store = gtk.TreeStore(gtk.gdk.Pixbuf, gtk.gdk.Pixbuf,
                                        str, str, int, int, int, int,
                                        bool, str, str, str)
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
        self.filter_model = self.data_store.filter_new()
        self.filter_model.set_visible_func(self._get_should_show)
        self.tree.set_model(self.filter_model)
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
        self.visible_iter_map = {}

    def get_treeview_tooltip(self, view, row_iter, col_index, tip):
        """Handle creating a tooltip for the treeview."""
        tip.set_text(self.filter_model.get_value(row_iter, 10))
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
            self._launch_ns_func(self.get_name(timeout_path),
                                 as_new=False)
        return False
        
    def load_tree(self, row, namespace_subtree):
        expanded_rows = []
        self.tree.map_expanded_rows(lambda r, d: expanded_rows.append(d))
        self.recursively_load_tree(row, namespace_subtree)
        self.set_expansion()
        for this_row in expanded_rows:
            self.tree.expand_to_path(this_row)

    def set_expansion(self):
        """Set the default expanded rows."""
        top_rows = self.filter_model.iter_n_children(None)
        if top_rows > rose.config_editor.TREE_PANEL_MAX_EXPANDED:
            return False
        if top_rows == 1:
            return self.expand_recursive(no_duplicates=True)
        r_iter = self.filter_model.get_iter_first()
        while r_iter is not None:
            path = self.filter_model.get_path(r_iter)
            self.tree.expand_to_path(path)
            r_iter = self.filter_model.iter_next(r_iter)

    def recursively_load_tree(self, row, namespace_subtree):
        """Update the tree store recursively using namespace_subtree."""
        self.name_iter_map = {}
        self.visible_iter_map = {}
        if row is None:
            self.data_store.clear()
        initials = namespace_subtree.items()
        initials.sort(self.sort_tree_items)
        stack = [[row] + list(i) for i in initials]
        while stack:
            row, key, value_meta_tuple = stack[0]
            value, meta, statuses, change = value_meta_tuple
            title = meta[rose.META_PROP_TITLE]
            latent_status = statuses[rose.config_editor.SHOW_MODE_LATENT]
            ignored_status = statuses[rose.config_editor.SHOW_MODE_IGNORED]
            new_row = self.data_store.append(row, [self.null_icon,
                                                   self.null_icon,
                                                   title,
                                                   key,
                                                   0, 0, 0, 0,
                                                   latent_status,
                                                   ignored_status,
                                                   '',
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
            title = rose.config_editor.TITLE_PAGE_ROOT_MARKUP.format(title)
        latent_status = model.get_value(r_iter, 8)
        ignored_status = model.get_value(r_iter, 9)
        if latent_status:
            title = rose.config_editor.TITLE_PAGE_LATENT_MARKUP.format(title)
        if ignored_status:
            title = rose.config_editor.TITLE_PAGE_IGNORED_MARKUP.format(
                                                  ignored_status, title)
        cell.set_property("markup", title)

    def sort_tree_items(self, row_item_1, row_item_2):
        """Sort tree items according to name and sort key."""
        main_sort_func = rose.config.sort_settings
        sort_key_1 = row_item_1[1][1].get(rose.META_PROP_SORT_KEY, '')
        sort_key_2 = row_item_2[1][1].get(rose.META_PROP_SORT_KEY, '')
        sort_key_1 = sort_key_1 + '~' + row_item_1[0]
        sort_key_2 = sort_key_2 + '~' + row_item_2[0]
        return main_sort_func(sort_key_1, sort_key_2)

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
        row_path = self.get_path_from_names(names, unfiltered=True)
        if row_path is None:
            return False
        row_iter = self.data_store.get_iter(row_path)
        old_total = self.data_store.get_value(row_iter, total_col)
        old_int = self.data_store.get_value(row_iter, int_col)
        diff_int_count = ind_count - old_int
        new_total = old_total + diff_int_count
        self.data_store.set_value(row_iter, int_col, ind_count)
        self.data_store.set_value(row_iter, total_col, new_total)
        if new_total > 0:
            self.data_store.set_value(row_iter, ind_map[ind_type]['icon_col'],
                                      ind_map[ind_type]['icon'])
        else:
            self.data_store.set_value(row_iter, ind_map[ind_type]['icon_col'],
                                      self.null_icon)

        # Now pass information up the tree
        for parent in [row_path[:i] for i in range(len(row_path) - 1, 0, -1)]:
            parent_iter = self.data_store.get_iter(parent)
            old_parent_total = self.data_store.get_value(parent_iter,
                                                         total_col)
            new_parent_total = old_parent_total + diff_int_count
            self.data_store.set_value(parent_iter,
                                      total_col,
                                      new_parent_total)
            if new_parent_total > 0:
                self.data_store.set_value(parent_iter,
                                          ind_map[ind_type]['icon_col'],
                                          ind_map[ind_type]['icon'])
            else:
                self.data_store.set_value(parent_iter,
                                          ind_map[ind_type]['icon_col'],
                                          self.null_icon)

    def update_row_tooltips(self):
        """Synchronise the icon information with the hover-over text."""
        my_iter = self.data_store.get_iter_first()
        if my_iter is None:
            return
        paths = []
        iter_stack = [my_iter]
        while iter_stack:
            my_iter = iter_stack.pop(0)
            paths.append(self.data_store.get_path(my_iter))
            next_iter = self.data_store.iter_next(my_iter)
            if next_iter is not None:
                iter_stack.append(next_iter)
            if self.data_store.iter_has_child(my_iter):
                iter_stack.append(self.data_store.iter_children(my_iter))
        for path in paths:
            path_iter = self.data_store.get_iter(path)
            name = self.data_store.get_value(path_iter, 3)
            num_errors = self.data_store.get_value(path_iter, 4)
            mods = self.data_store.get_value(path_iter, 6)
            proper_name = self.get_name(path, unfiltered=True)
            metadata, comment = self._get_metadata_comments_func(proper_name)
            description = metadata.get(rose.META_PROP_DESCRIPTION, "")
            change = self.data_store.get_value(path_iter, 11)
            if description:
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
            if description:
                text += "\n(" + name + ")"
            if comment:
                text += "\n" + comment
            if change:
                text += "\n" + change
            self.data_store.set_value(path_iter, 10, text)

    def update_change(self, row_names, new_change):
        """Update 'changed' text."""
        self._set_row_names_value(row_names, 11, new_change)

    def update_statuses(self, row_names, latent_status, ignored_status):
        """Update latent and ignored statuses."""
        self._set_row_names_value(row_names, 8, latent_status)
        self._set_row_names_value(row_names, 9, ignored_status)

    def _set_row_names_value(self, row_names, index, value):
        path = self.get_path_from_names(row_names, unfiltered=True)
        if path is not None:
            row_iter = self.data_store.get_iter(path)
            self.data_store.set_value(row_iter, index, value)

    def select_row(self, row_names):
        """Highlight one particular row, but only this one."""
        if row_names is None:
            return
        path = self.get_path_from_names(row_names, unfiltered=True)
        path = self.filter_model.convert_child_path_to_path(path)
        if path is not None:
            i = 1
            while self.tree.row_expanded(path[:i]) and i <= len(path):
                i += 1
            self.tree.set_cursor(path[:i])
        if path is None:
            self.tree.set_cursor((0,))

    def get_path_from_names(self, row_names, unfiltered=False):
        """Return a row path corresponding to the list of branch names."""
        if unfiltered:
            tree_model = self.data_store
        else:
            tree_model = self.filter_model
        self.name_iter_map.setdefault(unfiltered, {})
        name_iter_map = self.name_iter_map[unfiltered]
        key = tuple(row_names)
        if key in name_iter_map:
            return tree_model.get_path(name_iter_map[key])
        my_iter = tree_model.get_iter_first()
        these_names = []
        good_paths = [row_names[:i] for i in range(len(row_names) + 1)]
        for names in reversed(good_paths):
            subkey = tuple(names)
            if subkey in name_iter_map:
                my_iter = name_iter_map[subkey]
                these_names = names[:-1]
                break
        while my_iter is not None:
            branch_name = tree_model.get_value(my_iter, 3)
            my_names = these_names + [branch_name]
            name_iter_map.update({tuple(my_names): my_iter})
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
                            return self.expand_recursive(start_path=path,
                                                         no_duplicates=True)
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
                    self._launch_ns_func(self.get_name(path), as_new=False)
                elif event.button == 2:  # Middle click event, make new tab
                    self._last_tree_activation_path = path
                    self._launch_ns_func(self.get_name(path), as_new=True)
            else:
                path = event
                self._launch_ns_func(self.get_name(path), as_new=False)
        return False

    def get_name(self, path=None, unfiltered=False):
        """Return the row name (text) corresponding to the treeview path."""
        if path is None:
            tree_selection = self.tree.get_selection()
            (tree_model, tree_iter) = tree_selection.get_selected()
            path = tree_model.get_path(tree_iter)
        else:
            tree_model = self.tree.get_model()
            if unfiltered:
                tree_model = tree_model.get_model()
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
        namespace = self.get_name(path)
        return self._popup_menu_func(namespace, event)

    def collapse_reset(self):
        """Return the tree view to the basic startup state."""
        self.tree.collapse_all()
        self.set_expansion()
        self.tree.grab_focus()
        return False

    def expand_recursive(self, start_path=None, no_duplicates=False):
        """Expand the tree starting at start_path."""
        treemodel = self.tree.get_model()
        if start_path is None:
            start_iter = treemodel.get_iter_first()
            start_path = treemodel.get_path(start_iter)
        if not no_duplicates:
            return self.tree.expand_row(start_path, open_all=True)
        stack = [treemodel.get_iter(start_path)]
        while stack:
            iter_ = stack.pop(0)
            if iter_ is None:
                continue
            path = treemodel.get_path(iter_)
            child_iter = treemodel.iter_children(iter_)
            child_dups = []
            while child_iter is not None:
                child_name = self.get_name(treemodel.get_path(child_iter))
                metadata, comment = self._get_metadata_comments_func(
                                                                child_name)
                dupl = metadata.get(rose.META_PROP_DUPLICATE)
                child_dups.append(dupl == rose.META_PROP_VALUE_TRUE)
                child_iter = treemodel.iter_next(child_iter)
            if not all(child_dups):
                self.tree.expand_row(path, open_all=False)
                stack.append(treemodel.iter_children(iter_))
            if path != start_path:
                stack.append(treemodel.iter_next(iter_))

    def _get_should_show(self, model, iter_):
        # Determine whether to show a row.
        latent_status = model.get_value(iter_, 8)
        ignored_status = model.get_value(iter_, 9)
        child_iter = model.iter_children(iter_)
        is_visible = self._ask_can_show_func(latent_status, ignored_status)
        if is_visible:
            return True
        while child_iter is not None:
            if self._get_should_show(model, child_iter):
                return True
            child_iter = model.iter_next(child_iter)
        return False
