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
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
from gi.repository import GObject

import metomi.rose.config
import metomi.rose.config_editor
import metomi.rose.config_editor.util
import metomi.rose.gtk.util
import metomi.rose.resource


class PageNavigationPanel(Gtk.ScrolledWindow):

    """Generate the page launcher panel.

    This contains the namespace groupings as child rows.
    Icons denoting changes in the attribute internal data are displayed
    next to the attributes.

    """

    COLUMN_ERROR_ICON = 0
    COLUMN_CHANGE_ICON = 1
    COLUMN_TITLE = 2
    COLUMN_NAME = 3
    COLUMN_ERROR_INTERNAL = 4
    COLUMN_ERROR_TOTAL = 5
    COLUMN_CHANGE_INTERNAL = 6
    COLUMN_CHANGE_TOTAL = 7
    COLUMN_LATENT_STATUS = 8
    COLUMN_IGNORED_STATUS = 9
    COLUMN_TOOLTIP_TEXT = 10
    COLUMN_CHANGE_TEXT = 11

    def __init__(self, namespace_tree, launch_ns_func,
                 get_metadata_comments_func,
                 popup_menu_func, ask_can_show_func, ask_is_preview):
        super(PageNavigationPanel, self).__init__()
        self._launch_ns_func = launch_ns_func
        self._get_metadata_comments_func = get_metadata_comments_func
        self._popup_menu_func = popup_menu_func
        self._ask_can_show_func = ask_can_show_func
        self._ask_is_preview = ask_is_preview
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_shadow_type(Gtk.ShadowType.OUT)
        self._rec_no_expand_leaves = re.compile(
            metomi.rose.config_editor.TREE_PANEL_NO_EXPAND_LEAVES_REGEX)
        self.panel_top = Gtk.TreeViewColumn()
        self.panel_top.set_title(metomi.rose.config_editor.TREE_PANEL_TITLE)
        self.cell_error_icon = Gtk.CellRendererPixbuf()
        self.cell_changed_icon = Gtk.CellRendererPixbuf()
        self.cell_title = Gtk.CellRendererText()
        self.panel_top.pack_start(self.cell_error_icon, False, True, 0)
        self.panel_top.pack_start(self.cell_changed_icon, False, True, 0)
        self.panel_top.pack_start(self.cell_title, False, True, 0)
        self.panel_top.add_attribute(self.cell_error_icon,
                                     attribute='pixbuf',
                                     column=self.COLUMN_ERROR_ICON)
        self.panel_top.add_attribute(self.cell_changed_icon,
                                     attribute='pixbuf',
                                     column=self.COLUMN_CHANGE_ICON)
        self.panel_top.set_cell_data_func(self.cell_title,
                                          self._set_title_markup,
                                          self.COLUMN_TITLE)
        # The columns in self.data_store correspond to: error_icon,
        # change_icon, title, name, error and change totals (4),
        # latent and ignored statuses, main tip text, and change text.
        self.data_store = Gtk.TreeStore(GdkPixbuf.Pixbuf, GdkPixbuf.Pixbuf,
                                        str, str, int, int, int, int,
                                        bool, str, str, str)
        resource_loc = metomi.rose.resource.ResourceLocator(paths=sys.path)
        image_path = resource_loc.locate('etc/images/rose-config-edit')
        self.null_icon = GdkPixbuf.Pixbuf.new_from_file(image_path +
                                                      '/null_icon.xpm')
        self.changed_icon = GdkPixbuf.Pixbuf.new_from_file(image_path +
                                                         '/change_icon.xpm')
        self.error_icon = GdkPixbuf.Pixbuf.new_from_file(image_path +
                                                       '/error_icon.xpm')
        self.tree = metomi.rose.gtk.util.TooltipTreeView(
            get_tooltip_func=self.get_treeview_tooltip)
        self.tree.append_column(self.panel_top)
        self.filter_model = self.data_store.filter_new()
        self.filter_model.set_visible_func(self._get_should_show)
        self.tree.set_model(self.filter_model)
        self.tree.show()
        self.name_iter_map = {}
        self.add(self.tree)
        self.load_tree(None, namespace_tree)
        self.tree.connect('button-press-event',
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
        self.visible_iter_map = {}

    def get_treeview_tooltip(self, view, row_iter, col_index, tip):
        """Handle creating a tooltip for the treeview."""
        tip.set_text(self.filter_model.get_value(row_iter,
                                                 self.COLUMN_TOOLTIP_TEXT))
        return True

    def add_cursor_extra(self, widget, event):
        left = (event.keyval == Gdk.KEY_Left)
        right = (event.keyval == Gdk.KEY_Right)
        if left or right:
            path = widget.get_cursor()[0]
            if path is not None:
                if right:
                    widget.expand_row(path, open_all=False)
                elif left:
                    widget.collapse_row(path)
        return False

    def _handle_cursor_change(self, *args):
        current_path = self.tree.get_cursor()[0]
        if current_path != self._last_tree_activation_path:
            GObject.timeout_add(metomi.rose.config_editor.TREE_PANEL_KBD_TIMEOUT,
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
        self.load_tree_stack(row, namespace_subtree)
        self.set_expansion()
        for this_row in expanded_rows:
            self.tree.expand_to_path(this_row)

    def set_expansion(self):
        """Set the default expanded rows."""
        top_rows = self.filter_model.iter_n_children(None)
        if top_rows > metomi.rose.config_editor.TREE_PANEL_MAX_EXPANDED_ROOTS:
            return False
        if top_rows == 1:
            return self.expand_recursive(no_duplicates=True)
        r_iter = self.filter_model.get_iter_first()
        while r_iter is not None:
            path = self.filter_model.get_path(r_iter)
            self.tree.expand_to_path(path)
            r_iter = self.filter_model.iter_next(r_iter)

    def load_tree_stack(self, row, namespace_subtree):
        """Update the tree store recursively using namespace_subtree."""
        self.name_iter_map = {}
        self.visible_iter_map = {}
        if row is None:
            self.data_store.clear()
        initials = list(namespace_subtree.items())
        initials.sort(self.sort_tree_items)
        stack = []
        if row is None:
            start_keylist = []
        else:
            path = self.data_store.get_path(row)
            start_keylist = self.get_name(path, unfiltered=True).split("/")
        for item in initials:
            key, value_meta_tuple = item
            stack.append([row] + [list(start_keylist)] + list(item))
        self.name_iter_map.setdefault(True, {})  # True maps to unfiltered.
        name_iter_map = self.name_iter_map[True]
        while stack:
            row, keylist, key, value_meta_tuple = stack[0]
            value, meta, statuses, change = value_meta_tuple
            title = meta[metomi.rose.META_PROP_TITLE]
            latent_status = statuses[metomi.rose.config_editor.SHOW_MODE_LATENT]
            ignored_status = statuses[metomi.rose.config_editor.SHOW_MODE_IGNORED]
            new_row = self.data_store.append(row, [self.null_icon,
                                                   self.null_icon,
                                                   title,
                                                   key,
                                                   0, 0, 0, 0,
                                                   latent_status,
                                                   ignored_status,
                                                   '',
                                                   change])
            new_keylist = keylist + [key]
            name_iter_map["/".join(new_keylist)] = new_row
            if isinstance(value, dict):
                newer_initials = list(value.items())
                newer_initials.sort(self.sort_tree_items)
                for vals in newer_initials:
                    stack.append([new_row] + [list(new_keylist)] + list(vals))
            stack.pop(0)

    def _set_title_markup(self, column, cell, model, r_iter, index):
        title = model.get_value(r_iter, index)
        title = metomi.rose.gtk.util.safe_str(title)
        if len(model.get_path(r_iter)) == 1:
            title = metomi.rose.config_editor.TITLE_PAGE_ROOT_MARKUP.format(title)
        latent_status = model.get_value(r_iter, self.COLUMN_LATENT_STATUS)
        ignored_status = model.get_value(r_iter, self.COLUMN_IGNORED_STATUS)
        name = self.get_name(model.get_path(r_iter))
        preview_status = self._ask_is_preview(name)
        if preview_status:
            title = metomi.rose.config_editor.TITLE_PAGE_PREVIEW_MARKUP.format(title)
        if latent_status:
            if self._get_is_latent_sub_tree(model, r_iter):
                title = metomi.rose.config_editor.TITLE_PAGE_LATENT_MARKUP.format(
                    title)
        if ignored_status:
            title = metomi.rose.config_editor.TITLE_PAGE_IGNORED_MARKUP.format(
                ignored_status, title)
        cell.set_property("markup", title)

    def sort_tree_items(self, row_item_1, row_item_2):
        """Sort tree items according to name and sort key."""
        sort_key_1 = row_item_1[1][1].get(metomi.rose.META_PROP_SORT_KEY, '~')
        sort_key_2 = row_item_2[1][1].get(metomi.rose.META_PROP_SORT_KEY, '~')
        var_id_1 = row_item_1[0]
        var_id_2 = row_item_2[0]

        x_key = (sort_key_1, var_id_1)
        y_key = (sort_key_2, var_id_2)

        return metomi.rose.config_editor.util.null_cmp(x_key, y_key)

    def set_row_icon(self, names, ind_count=0, ind_type='changed'):
        """Set the icons for row status on or off. Check parent icons.

        After updating the row which is specified by a list of namespace
        pieces (names), go up through the tree and update parent row icons
        according to the status of their child row icons.

        """
        ind_map = {'changed': {'icon_col': self.COLUMN_CHANGE_ICON,
                               'icon': self.changed_icon,
                               'int_col': self.COLUMN_CHANGE_INTERNAL,
                               'total_col': self.COLUMN_CHANGE_TOTAL},
                   'error': {'icon_col': self.COLUMN_ERROR_ICON,
                             'icon': self.error_icon,
                             'int_col': self.COLUMN_ERROR_INTERNAL,
                             'total_col': self.COLUMN_ERROR_TOTAL}}
        int_col = ind_map[ind_type]['int_col']
        total_col = ind_map[ind_type]['total_col']
        row_path = self.get_path_from_names(names, unfiltered=True)
        if row_path is None:
            return False
        row_iter = self.data_store.get_iter(row_path)
        old_total = self.data_store.get_value(row_iter, total_col)
        old_int = self.data_store.get_value(row_iter, int_col)
        diff_int_count = ind_count - old_int
        if diff_int_count == 0:
            # No change.
            return False
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
            title = self.data_store.get_value(path_iter, self.COLUMN_TITLE)
            name = self.data_store.get_value(path_iter, self.COLUMN_NAME)
            num_errors = self.data_store.get_value(path_iter,
                                                   self.COLUMN_ERROR_INTERNAL)
            mods = self.data_store.get_value(path_iter,
                                             self.COLUMN_CHANGE_INTERNAL)
            proper_name = self.get_name(path, unfiltered=True)
            metadata, comment = self._get_metadata_comments_func(proper_name)
            description = metadata.get(metomi.rose.META_PROP_DESCRIPTION, "")
            change = self.data_store.get_value(
                path_iter, self.COLUMN_CHANGE_TEXT)
            text = title
            if name != title:
                text += " (" + name + ")"
            if mods > 0:
                text += " - " + metomi.rose.config_editor.TREE_PANEL_MODIFIED
            if description:
                text += ":\n" + description
            if num_errors > 0:
                if num_errors == 1:
                    text += metomi.rose.config_editor.TREE_PANEL_ERROR
                else:
                    text += metomi.rose.config_editor.TREE_PANEL_ERRORS.format(
                        num_errors)
            if comment:
                text += "\n" + comment
            if change:
                text += "\n\n" + change
            self.data_store.set_value(
                path_iter, self.COLUMN_TOOLTIP_TEXT, text)

    def update_change(self, row_names, new_change):
        """Update 'changed' text."""
        self._set_row_names_value(
            row_names, self.COLUMN_CHANGE_TEXT, new_change)

    def update_statuses(self, row_names, latent_status, ignored_status):
        """Update latent and ignored statuses."""
        self._set_row_names_value(
            row_names, self.COLUMN_LATENT_STATUS, latent_status)
        self._set_row_names_value(
            row_names, self.COLUMN_IGNORED_STATUS, ignored_status)

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
        try:
            path = self.filter_model.convert_child_path_to_path(path)
        except TypeError:
            path = None
        if path is None:
            dest_path = (0,)
        else:
            i = 1
            while self.tree.row_expanded(path[:i]) and i <= len(path):
                i += 1
            dest_path = path[:i]
        cursor_path = self.tree.get_cursor()[0]
        if cursor_path != dest_path:
            self.tree.set_cursor(dest_path)

    def get_path_from_names(self, row_names, unfiltered=False):
        """Return a row path corresponding to the list of branch names."""
        if unfiltered:
            tree_model = self.data_store
        else:
            tree_model = self.filter_model
        self.name_iter_map.setdefault(unfiltered, {})
        name_iter_map = self.name_iter_map[unfiltered]
        key = "/".join(row_names)
        if key in name_iter_map:
            return tree_model.get_path(name_iter_map[key])
        if unfiltered:
            # This would be cached in name_iter_map by load_tree_stack.
            return None
        my_iter = tree_model.get_iter_first()
        these_names = []
        good_paths = [row_names[:i] for i in range(len(row_names) + 1)]
        for names in reversed(good_paths):
            subkey = "/".join(names)
            if subkey in name_iter_map:
                my_iter = name_iter_map[subkey]
                these_names = names[:-1]
                break
        while my_iter is not None:
            branch_name = tree_model.get_value(my_iter, self.COLUMN_NAME)
            my_names = these_names + [branch_name]
            subkey = "/".join(my_names)
            name_iter_map[subkey] = my_iter
            if my_names in good_paths:
                if my_names == row_names:
                    return tree_model.get_path(my_iter)
                else:
                    these_names.append(branch_name)
                    my_iter = tree_model.iter_children(my_iter)
            else:
                my_iter = tree_model.iter_next(my_iter)
        return None

    def get_change_error_totals(self, config_name=None):
        """Return the number of changes and total errors for the root nodes."""
        if config_name:
            path = self.get_path_from_names([config_name], unfiltered=True)
            iter_ = self.data_store.get_iter(path)
        else:
            iter_ = self.data_store.get_iter_first()
        changes = 0
        errors = 0
        while iter_ is not None:
            iter_changes = self.data_store.get_value(
                iter_, self.COLUMN_CHANGE_TOTAL)
            iter_errors = self.data_store.get_value(
                iter_, self.COLUMN_ERROR_TOTAL)
            if iter_changes is not None:
                changes += iter_changes
            if iter_errors is not None:
                errors += iter_errors
            if config_name:
                break
            else:
                iter_ = self.data_store.iter_next(iter_)
        return changes, errors

    def handle_activation(self, treeview=None, event=None, somewidget=None):
        """Send a page launch request based on left or middle clicks."""
        if event is not None and treeview is not None:
            if hasattr(event, 'button'):
                pathinfo = treeview.get_path_at_pos(int(event.x),
                                                    int(event.y))
                if pathinfo is not None:
                    path, col, cell_x, _ = pathinfo
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
                        treeview.set_cursor(pathinfo[0], col, 0)
                elif event.button == 3:  # Right clicked outside the rows
                    self.popup_menu(None, event)
                else:  # Clicked outside the rows
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
        row_name = str(tree_model.get_value(tree_iter, self.COLUMN_NAME))
        full_name = row_name
        for parent in [path[:i] for i in range(len(path) - 1, 0, -1)]:
            parent_iter = tree_model.get_iter(parent)
            full_name = str(
                tree_model.get_value(parent_iter, self.COLUMN_NAME) +
                "/" + full_name)
        return full_name

    def get_subtree_names(self, path=None):
        """Return all names that exist in a subtree of path."""
        tree_model = self.tree.get_model()
        root_iter = tree_model.get_iter(path)
        sub_iters = []
        for i in range(tree_model.iter_n_children(root_iter)):
            sub_iters.append(tree_model.iter_nth_child(root_iter, i))
        sub_names = []
        while sub_iters:
            if sub_iters[0] is not None:
                path = tree_model.get_path(sub_iters[0])
                sub_names.append(self.get_name(path))
                for i in range(tree_model.iter_n_children(sub_iters[0])):
                    sub_iters.append(tree_model.iter_nth_child(sub_iters[0],
                                                               i))
            sub_iters.pop(0)
        return sub_names

    def popup_menu(self, path, event):
        """Launch a popup menu for add/clone/remove."""
        if path:
            path_name = "/" + self.get_name(path)
        else:
            path_name = None
        return self._popup_menu_func(path_name, event)

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
        max_depth = metomi.rose.config_editor.TREE_PANEL_MAX_EXPANDED_DEPTH
        stack = [treemodel.get_iter(start_path)]
        while stack:
            iter_ = stack.pop(0)
            if iter_ is None:
                continue
            path = treemodel.get_path(iter_)
            name = self.get_name(path)
            child_iter = treemodel.iter_children(iter_)
            child_dups = []
            while child_iter is not None:
                child_name = self.get_name(treemodel.get_path(child_iter))
                metadata = self._get_metadata_comments_func(child_name)[0]
                dupl = metadata.get(metomi.rose.META_PROP_DUPLICATE)
                child_dups.append(dupl == metomi.rose.META_PROP_VALUE_TRUE)
                child_iter = treemodel.iter_next(child_iter)
            if path != start_path:
                stack.append(treemodel.iter_next(iter_))
            if (not all(child_dups) and
                    len(path) <= max_depth and
                    not self._rec_no_expand_leaves.search(name)):
                self.tree.expand_row(path, open_all=False)
                stack.append(treemodel.iter_children(iter_))

    def _get_is_latent_sub_tree(self, model, iter_):
        """Return True if the whole model sub tree is latent."""
        if not model.get_value(iter_, self.COLUMN_LATENT_STATUS):
            # This row is not latent.
            return False
        iter_stack = [model.iter_children(iter_)]
        while iter_stack:
            iter_ = iter_stack.pop(0)
            if iter_ is None:
                continue
            if not model.get_value(iter_, self.COLUMN_LATENT_STATUS):
                # This sub-row is not latent.
                return False
            iter_stack.append(model.iter_children(iter_))
            iter_stack.append(model.iter_next(iter_))
        return True

    def _get_should_show(self, model, iter_):
        # Determine whether to show a row.
        latent_status = model.get_value(iter_, self.COLUMN_LATENT_STATUS)
        ignored_status = model.get_value(iter_, self.COLUMN_IGNORED_STATUS)
        has_error = bool(model.get_value(iter_, self.COLUMN_ERROR_INTERNAL))
        child_iter = model.iter_children(iter_)
        is_visible = self._ask_can_show_func(latent_status, ignored_status,
                                             has_error)
        if is_visible:
            return True
        while child_iter is not None:
            if self._get_should_show(model, child_iter):
                return True
            child_iter = model.iter_next(child_iter)
        return False
