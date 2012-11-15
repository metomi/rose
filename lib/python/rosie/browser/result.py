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

import datetime

import pygtk
pygtk.require("2.0")
import gtk

import rose.external
from rose.opt_parse import RoseOptionParser
import rosie.browser
import rosie.ws_client

STATUS_ICON = {rosie.ws_client.STATUS_DO: gtk.STOCK_MEDIA_FORWARD,
               rosie.ws_client.STATUS_NO: None,
               rosie.ws_client.STATUS_OK: gtk.STOCK_HOME,
               rosie.ws_client.STATUS_MO: gtk.STOCK_EDIT,
               rosie.ws_client.STATUS_SW: gtk.STOCK_CONVERT,
               rosie.ws_client.STATUS_UP: gtk.STOCK_MEDIA_REWIND}

STATUS_TIP = {rosie.ws_client.STATUS_DO: rosie.browser.LOCAL_STATUS_DOWNDATE,
              rosie.ws_client.STATUS_NO: rosie.browser.LOCAL_STATUS_NO,
              rosie.ws_client.STATUS_OK: rosie.browser.LOCAL_STATUS_OK,
              rosie.ws_client.STATUS_MO: rosie.browser.LOCAL_STATUS_MODIFIED,
              rosie.ws_client.STATUS_SW: rosie.browser.LOCAL_STATUS_SWITCH,
              rosie.ws_client.STATUS_UP: rosie.browser.LOCAL_STATUS_UPDATE}


class DisplayBox(gtk.VBox):

    """Custom widget for displaying search results"""
    
    descending = None
    sort_title = None
    query_rows = None
    group_index = None
    TREE_COLUMNS = 20 * [str] + [bool]
    TREE_COLUMN_GROUP = len(TREE_COLUMNS) - 1
    display_columns = []

    def __init__(self, tree_column_getter, display_cols_getter):
        super(DisplayBox, self).__init__()
        self.get_tree_columns = tree_column_getter
        self.display_cols_getter = display_cols_getter
        self.treestore = gtk.TreeStore(*self.TREE_COLUMNS)
        self.treeview = rose.gtk.util.TooltipTreeView(
                             model=self.treestore,
                             get_tooltip_func=self._get_treeview_tooltip)
        self.treeview.show()
        self.treeview.set_rules_hint(True)
        self.treeview_scroll = gtk.ScrolledWindow()
        self.treeview_scroll.set_policy(gtk.POLICY_AUTOMATIC, 
                                        gtk.POLICY_AUTOMATIC)
        self.treeview_scroll.show()
        self.treeview_scroll.add(self.treeview)
        self.treeview_scroll.set_shadow_type(gtk.SHADOW_IN)
        self.treeview.enable_model_drag_source(
                  gtk.gdk.BUTTON1_MASK,
                  [('text/plain', 0, 0)],
                  gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)
        self.pack_start(self.treeview_scroll, expand=True, fill=True)
        self.show()

    def get_column_index_by_name(self, column_title):
        """Return the index of a main treeview column with this title."""
        for i, column in enumerate(self.treeview.get_columns()):
            if column.get_widget().get_text() == column_title:
                return i
        return None

    def get_info_text(self, path=None):
        """Select a suite to display properties for."""
        idx, branch, revision = self.get_suite_keys_treeview(path)
        return self._result_info[(idx, branch, revision)] 
        
    def get_selected_suite_field(self, field=None):
        """Return the currently selected suite title."""
        if field is None:
            return None
        else:
            index = -1
            path, col = self.treeview.get_cursor()
            columns = self.treeview.get_columns()
            for i, col in enumerate(columns):
                if col.get_widget().get_text() == field:
                    index = i
                    break
            if index > -1:
                this_iter = self.treestore.get_iter(path)
                details = self.treestore.get_value(this_iter, index)
                return details
            else:
                return None   
        
    def get_suite_keys_treeview(self, path=None):
        """Return the suite keys for a selected suite"""
        if path is None:
            path, col = self.treeview.get_cursor()
            if path is None:
                return None, None, None
        columns = self.treeview.get_columns()
        for i, col in enumerate(columns):
            if col.get_widget().get_text() == "idx":
                suite_col_index = i
                break
        else:
            return None, None, None
        for i, col in enumerate(columns):
            if col.get_widget().get_text() == "branch":
                branch_col_index = i
                break
        else:
            return None, None, None
        for i, col in enumerate(columns):
            if col.get_widget().get_text() == "revision":
                rev_col_index = i
                break
        else:
            return None, None, None
        this_iter = self.treestore.get_iter(path)
        idx = self.treestore.get_value(this_iter, suite_col_index)
        branch = self.treestore.get_value(this_iter, branch_col_index)
        revision = int(self.treestore.get_value(this_iter, rev_col_index))
        return idx, branch, revision

    def _get_treeview_path_status(self, path):
        """Get the status of a suite"""
        model = self.treeview.get_model()
        i = self.get_column_index_by_name("local")
        if i is None:
            return False
        return model.get_value(model.get_iter(path), i)    

    def _get_treeview_tooltip(self, view, row_iter, col_index, tip):
        """Handle creating a tooltip for the treeview."""
        local_index = self.get_column_index_by_name("local")
        if col_index == local_index:
            value = view.get_model().get_value(row_iter, col_index)
            tip.set_text(STATUS_TIP[value])
            return True
        path = view.get_model().get_path(row_iter)
        tip.set_text(self.get_info_text(path))
        return True

    def handle_column_sort(self, column):
        """Handle a sort on a main tree view column header."""
        if self.group_index is None:
            # No problem, gtk will take care of it
            return False
        cols = self.get_tree_columns()
        k = self.group_index
        cols = cols[k: k + 1] + cols[0: k] + cols[k + 1:]
        sort_index = cols.index(column.get_widget().get_text())
        descending = (column.get_sort_order() == gtk.SORT_DESCENDING)
        self.descending = descending
        self.update_treemodel(sort_index, descending) 

    def _handle_grouping(self, menuitem):
        """Handle grouping of treeview items"""
        if menuitem.col_name is None:
            self.group_index = None
        else:
            self.group_index = self.get_tree_columns().index(menuitem.col_name)

    def _set_date_cell(self, column, cell, model, r_iter):
        """Set the date to human readable format"""
        index = self.treeview.get_columns().index(column)
        epoch = model.get_value(r_iter, index)
        path = model.get_path(r_iter)
        if epoch is not None:
            date = datetime.datetime.fromtimestamp(float(epoch))
        else:
            date = None
        cell.set_property('text', date)

    def _set_local_cell(self, column, cell, model, r_iter):
        """Set the icon for local status."""
        index = self.treeview.get_columns().index(column)
        status = model.get_value(r_iter, index)
        path = model.get_path(r_iter)
        cell.set_property("stock-id", STATUS_ICON[status])

    def _update_local_status_row(self, model, path, r_iter, data):
        """Update the status for a row of the treeview"""
        (index_map, local_suites, search_manager) = data
        idx = model.get_value(r_iter, index_map["idx"])
        branch = model.get_value(r_iter, index_map["branch"])
        revision = int(model.get_value(r_iter, index_map["revision"]))
        local_status = rosie.ws_client.get_local_status(
                             local_suites, search_manager.get_datasource(),
                             idx, branch, revision)
        model.set_value(r_iter, index_map["local"], local_status)
        return False

    def update_result_info(self, id_tuple, result_map, local_status, 
                           search_manager, id_formatter): 
        """Update the cached info for a suite."""
        prefix = search_manager.get_datasource()
        idx, branch, revision = id_tuple
        id_text = id_formatter(prefix, idx, branch, revision)
        loc = STATUS_TIP[local_status]
        self._result_info[id_tuple] = id_text + "\n" + loc + "\n\n"
        for key in sorted(result_map):
            if key in ["idx", "branch", "revision"]:
                continue
            value = result_map[key]
            if value is None:
                continue
            if isinstance(value, list):
                value = " ".join(value)
            if key == "date":
                value = datetime.datetime.fromtimestamp(float(value))
            line = key + rosie.browser.DELIM_KEYVAL + str(value)
            self._result_info[id_tuple] += line + "\n"
        self._result_info[id_tuple] = self._result_info[id_tuple].rstrip()
    
    def update_treemodel(self, sort_index=0, descending=False):
        """Update or rearrange the main tree model."""
        display_columns = self.display_cols_getter()
        expanded_rows = []
        self.treeview.map_expanded_rows(lambda r, d: expanded_rows.append(d))
        expanded_groups = []
        for path in expanded_rows:
            p_iter = self.treestore.get_iter(path)
            expanded_groups.append(self.treestore.get_value(p_iter, 0))
        self.treestore.clear()
        results = [[q for q in r] for r in self.query_rows]
        if self.group_index is not None:
            k = self.group_index
            results = [r[k: k + 1] + r[0: k] + r[k + 1:] for r in results]
        if self.group_index is not None:
            fac = (-1 if descending else 1)
            results.sort(lambda x, y:
                         fac * cmp(x[sort_index], y[sort_index]))
        row_group_headers = {}
        prev_row = None
        prev_val = None
        cs = [c.get_widget().get_text() for c in self.treeview.get_columns()]
        for i, values in enumerate(results):
            row_vals = [v for v in values]
            this_row = (row_vals + [""] * 
                        (len(self.TREE_COLUMNS) - 1 - len(values)))
            if (this_row[0] in row_group_headers and
                self.group_index is not None):
                prev_row = row_group_headers[this_row[0]]
                self.treestore.insert(prev_row, i, this_row + [False])
            else:
                prev_row = self.treestore.insert(None, i, this_row + [True])
                prev_val = this_row[0]
                row_group_headers.setdefault(prev_val, prev_row)
        for group_val, row_iter in row_group_headers.items():
            if group_val in expanded_groups:
                path = self.treestore.get_path(row_iter)
                self.treeview.expand_to_path(path)        

    def update_treemodel_local_status(self, local_suites, search_manager):
        """Update the local status column in the main tree model."""
        keys = ["local", "idx", "branch", "revision"]
        index_map = {}
        for key in keys:
            index_map.update({key: self.get_column_index_by_name(key)})
        self.treestore.foreach(self._update_local_status_row,
                               (index_map, local_suites, search_manager))
                
    def update_treeview(self, activation_handler, visibility_getter, 
                        query_rows=None, sort_title=None, descending=False):
        """Insert query rows into treeview."""
        if query_rows is not None:
            self.query_rows = [list(q) for q in query_rows]
        elif self.query_rows is None:
            return
        query_rows = self.query_rows
        results = [q for q in query_rows]

        old_sort_id, old_descending = self.treestore.get_sort_column_id()

        if old_sort_id is not None:
            cols = self.treeview.get_columns()
            self.sort_title = cols[old_sort_id].get_widget().get_text()

        if old_descending is not None:
            self.descending = old_descending
        
        for col in self.treeview.get_columns():
            self.treeview.remove_column(col)
        cols = self.get_tree_columns()
        group_index = self.group_index

        if sort_title is not None:
            self.sort_title = sort_title
        
        if group_index is None:
            if sort_title is None:
                if self.sort_title is None:
                    sort_title = "revision"
                else:
                    sort_title = self.sort_title
            if self.descending is None:        
                descending = True
            else:
                descending = self.descending
        else:
            k = group_index
            cols = cols[k: k + 1] + cols[0: k] + cols[k + 1:]
            results = [r[k: k + 1] + r[0: k] + r[k + 1:] for r in results]
        if results:
            col_types = []
            for i in range(len(results[0])):
                if all([isinstance(r[i], int) for r in results]):
                    col_types.append(int)
                elif all([isinstance(r[i], bool) for r in results]):
                    col_types.append(bool)
                else:
                    col_types.append(str)
            for i in range(len(results[0]), len(self.TREE_COLUMNS)):
                col_types.append(self.TREE_COLUMNS[i])
            self.treestore = gtk.TreeStore(*col_types)
            self.treestore.connect("row-deleted", activation_handler) 
            self.treeview.set_model(self.treestore)
        else:
            self.treestore.clear()
        result_columns = [c for c in cols if c != "local"]
        for i, title in enumerate(cols):
            col = gtk.TreeViewColumn()
            label = gtk.Label(title)
            label.set_use_underline(False)
            label.show()
            col.set_widget(label)
            if title == "local":
                cell = gtk.CellRendererPixbuf()
            else:
                cell = gtk.CellRendererText()
            col.pack_start(cell)
            col.set_sort_column_id(i)
            if title == "local":
                col.set_cell_data_func(cell, self._set_local_cell)
            elif title == "date":
                col.set_cell_data_func(cell, self._set_date_cell)
            else:
                col.add_attribute(cell, attribute='text', column=i)
                if i == 0 and group_index is not None:
                    col.add_attribute(cell, attribute='visible',
                                      column=self.TREE_COLUMN_GROUP)
            if group_index is None and title == sort_title:
                self.treestore.set_sort_column_id(
                    i, [gtk.SORT_ASCENDING, gtk.SORT_DESCENDING][descending])
            elif group_index is not None and i == 0:
                self.treestore.set_sort_column_id(i, gtk.SORT_ASCENDING)
            col.set_resizable(True)
            self.treeview.append_column(col)
            col.connect("clicked", self.handle_column_sort)
            if not visibility_getter(title, True):
                col.set_visible(False)
        
        self.treeview.set_enable_search(False)
        self.update_treemodel() 
