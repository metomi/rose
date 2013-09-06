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

import multiprocessing
import os
import Queue
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import webbrowser

import pygtk
pygtk.require("2.0")
import gtk
import gobject
import glib
import pango

import rose.reporter
import rose.resource


REC_HYPERLINK_ID_OR_URL = re.compile(
                    r"""(?P<start_break>\b)
                        (?P<url>[\w:-]+=\w+|https?://[^\s<]+)
                        (?P<end_break>\b)""", re.X)
MARKUP_URL_HTML = (r"""\g<start_break>""" +
                   r"""<a href='\g<url>'>\g<url></a>""" + 
                   r"""\g<end_break>""")
MARKUP_URL_UNDERLINE = (r"""\g<start_break>""" +
                        r"""<u>\g<url></u>""" + 
                        r"""\g<end_break>""")


class ColourParseError(ValueError):

    """An exception raised when gtk colour parsing fails."""

    def __str__(self):
        return "unable to parse colour specification: %s" % self.args[0]


class CustomButton(gtk.Button):

    """Returns a custom gtk.Button."""

    def __init__(self, label=None, stock_id=None,
                 size=gtk.ICON_SIZE_SMALL_TOOLBAR, tip_text=None,
                 as_tool=False, icon_at_start=False, has_menu=False):
        self.hbox = gtk.HBox()
        self.size = size
        self.as_tool = as_tool
        self.icon_at_start = icon_at_start
        if label is not None:
            self.label = gtk.Label()
            self.label.set_text(label)
            self.label.show()
            
            if self.icon_at_start:
                self.hbox.pack_end(self.label, expand=False, fill=False,
                                   padding=5)
            else:
                self.hbox.pack_start(self.label, expand=False, fill=False,
                                   padding=5)                       
        if stock_id is not None:
            self.stock_id = stock_id
            self.icon = gtk.Image()
            self.icon.set_from_stock(stock_id, size)
            self.icon.show()
            if self.icon_at_start:
                self.hbox.pack_start(self.icon, expand=False, fill=False)
            else:
                self.hbox.pack_end(self.icon, expand=False, fill=False)
        if has_menu:
            arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
            arrow.show()
            self.hbox.pack_end(arrow, expand=False, fill=False)
            self.hbox.reorder_child(arrow, 0)
        self.hbox.show()
        super(CustomButton, self).__init__()
        if self.as_tool:
            self.set_relief(gtk.RELIEF_NONE)
            self.connect("leave", lambda b: b.set_relief(gtk.RELIEF_NONE))
        self.add(self.hbox)
        self.show()
        if tip_text is not None:
            self.set_tooltip_text(tip_text)

    def set_stock_id(self, stock_id):
        """Set an icon based on the stock id."""
        if hasattr(self, "icon"):
            self.hbox.remove(self.icon)
        self.icon.set_from_stock(stock_id, self.size)
        self.stock_id = stock_id
        if self.icon_at_start:
            self.hbox.pack_start(self.icon, expand=False, fill=False)
        else:
            self.hbox.pack_end(self.icon, expand=False, fill=False)
        return False

    def set_tip_text(self, new_text):
        """Set new tooltip text."""
        self.set_tooltip_text(new_text)

    def position_menu(self, menu, widget):
        """Place a drop-down menu carefully below the button."""
        x, y = widget.get_window().get_origin()
        allocated_rectangle = widget.get_allocation()
        x += allocated_rectangle.x
        y += allocated_rectangle.y + allocated_rectangle.height
        return x, y, False


class CustomExpandButton(gtk.Button):

    """Custom button for expanding/hiding something"""
    
    def __init__(self, expander_function=None,
                 label=None,
                 size=gtk.ICON_SIZE_SMALL_TOOLBAR,
                 tip_text=None,
                 as_tool=False, 
                 icon_at_start=False,
                 minimised=True):
    
        self.expander_function = expander_function
        self.minimised = minimised

        self.expand_id = gtk.STOCK_ADD
        self.minimise_id = gtk.STOCK_REMOVE
        
        if minimised:
            self.stock_id = self.expand_id
        else:
            self.stock_id = self.minimise_id
        
        self.hbox = gtk.HBox()
        self.size = size
        self.as_tool = as_tool
        self.icon_at_start = icon_at_start
        
        if label is not None:
            self.label = gtk.Label()
            self.label.set_text(label)
            self.label.show()
            
            if self.icon_at_start:
                self.hbox.pack_end(self.label, expand=False, fill=False,
                                   padding=5)
            else:
                self.hbox.pack_start(self.label, expand=False, fill=False,
                                   padding=5)                       
        self.icon = gtk.Image()
        self.icon.set_from_stock(self.stock_id, size)
        self.icon.show()
        if self.icon_at_start:
            self.hbox.pack_start(self.icon, expand=False, fill=False)
        else:
            self.hbox.pack_end(self.icon, expand=False, fill=False)
        self.hbox.show()
        super(CustomExpandButton, self).__init__()
        
        if self.as_tool:
            self.set_relief(gtk.RELIEF_NONE)
            self.connect("leave", lambda b: b.set_relief(gtk.RELIEF_NONE))
        self.add(self.hbox)
        self.show()
        if tip_text is not None:
            self.set_tooltip_text(tip_text)
        self.connect("clicked", self.toggle)

    def set_stock_id(self, stock_id):
        """Set the icon stock_id""" 
        if hasattr(self, "icon"):
            self.hbox.remove(self.icon)
        self.icon.set_from_stock(stock_id, self.size)
        self.stock_id = stock_id
        if self.icon_at_start:
            self.hbox.pack_start(self.icon, expand=False, fill=False)
        else:
            self.hbox.pack_end(self.icon, expand=False, fill=False)
        return False

    def set_tip_text(self, new_text):
        """Set the tip text"""
        self.set_tooltip_text(new_text)
        
    def toggle(self, minimise=None):    
        """Toggle between show/hide states"""
        if minimise is not None:
            if minimise == self.minimised:
                return
        self.minimised = not self.minimised
        if self.minimised:
            self.stock_id = self.expand_id
        else:
            self.stock_id = self.minimise_id
        if self.expander_function is not None:
            self.expander_function(set_visibility=not self.minimised)                                
        self.set_stock_id(self.stock_id)


class CustomMenuButton(gtk.MenuToolButton):

    """Custom wrapper for the gtk Menu Tool Button."""

    def __init__(self, label=None, stock_id=None,
                 size=gtk.ICON_SIZE_SMALL_TOOLBAR, tip_text=None,
                 menu_items=[], menu_funcs=[]):
        hbox = None
        if stock_id is not None:
            hbox = gtk.HBox()
            self.stock_id = stock_id
            self.icon = gtk.Image()
            self.icon.set_from_stock(stock_id, size)
            self.icon.show()
            hbox.pack_end(self.icon, expand=False, fill=False)
            hbox.show()
        gtk.MenuToolButton.__init__(self, hbox, label)
        self.set_tooltip_text(tip_text)
        self.show()
        button_menu = gtk.Menu()
        for item_tuple, func in zip(menu_items, menu_funcs):
            name = item_tuple[0]
            if len(item_tuple) == 1:
                new_item = gtk.MenuItem(name)
            else:
                new_item = gtk.ImageMenuItem(stock_id=item_tuple[1])
                new_item.set_label(name)
            new_item._func = func
            new_item.connect("activate", lambda m: m._func())
            new_item.show()
            button_menu.append(new_item)
        button_menu.show()
        self.set_menu(button_menu)
        

class ToolBar(gtk.Toolbar):

    """An easier-to-use gtk.Toolbar."""

    def __init__(self, widgets=[], sep_on_name=[]):
        super(ToolBar, self).__init__()
        self.item_dict = {}
        self.show()
        widgets.reverse()
        for name, stock in widgets:
            if name in sep_on_name:
                separator = gtk.SeparatorToolItem()
                separator.show()
                self.insert(separator, 0)
            if isinstance(stock, basestring) and stock.startswith("gtk."):
                stock = getattr(gtk, stock.replace("gtk.", "", 1))
            if callable(stock):
                widget = stock()
                widget.show()
                widget.set_tooltip_text(name)
            else:
                widget = CustomButton(stock_id=stock, tip_text=name,
                                      as_tool=True)
            icon_tool_item = gtk.ToolItem()
            icon_tool_item.add(widget)
            icon_tool_item.show()
            self.item_dict[name] = {"tip": name, "widget": widget,
                                    "func": None}
            self.insert(icon_tool_item, 0)

    def set_widget_function(self, name, function, args=[]):
        self.item_dict[name]["widget"].args = args
        if len(args) > 0:
            self.item_dict[name]["widget"].connect("clicked",
                                                   lambda b: function(*b.args))
        else:
            self.item_dict[name]["widget"].connect("clicked",
                                                   lambda b: function())

    def set_widget_sensitive(self, name, is_sensitive):
        self.item_dict[name]["widget"].set_sensitive(is_sensitive)


class AsyncStatusbar(gtk.Statusbar):

    """Wrapper class to add polling a file to statusbar API."""

    def __init__(self, *args):
        super(AsyncStatusbar, self).__init__(*args)
        self.show()
        self.queue = multiprocessing.Queue()
        self.ctx_id = self.get_context_id("_all")
        self.should_stop = False
        self.connect("destroy", self._handle_destroy)
        gobject.timeout_add(1000, self._poll)

    def _handle_destroy(self, *args):
        self.should_stop = True

    def _poll(self):
        self.update()
        return not self.should_stop

    def update(self):
        try:
            message = self.queue.get(block=False)
        except Queue.Empty:
            pass
        else:
            self.push(self.ctx_id, message)

    def put(self, message, instant=False):
        if instant:
            self.push(self.ctx_id, message)
        else:
            self.queue.put_nowait(message)
            self.update()


class AsyncLabel(gtk.Label):

    """Wrapper class to add polling a file to label API."""

    def __init__(self, *args):
        super(AsyncLabel, self).__init__(*args)
        self.show()
        self.queue = multiprocessing.Queue()
        self.should_stop = False
        self.connect("destroy", self._handle_destroy)
        gobject.timeout_add(1000, self._poll)

    def _handle_destroy(self, *args):
        self.should_stop = True

    def _poll(self):
        self.update()
        return not self.should_stop

    def update(self):
        try:
            message = self.queue.get(block=False)
        except Queue.Empty:
            pass
        else:
            self.set_text(message)

    def put(self, message, instant=False):
        if instant:
            self.set_text(message)
        else:
            self.queue.put_nowait(message)
            self.update()


class ThreadedProgressBar(gtk.ProgressBar):

    """Wrapper class to allow threaded progress bar pulsing."""

    def __init__(self, *args, **kwargs):
        super(ThreadedProgressBar, self).__init__(*args, **kwargs)
        self.set_fraction(0.0)
        self.set_pulse_step(0.1)

    def start_pulsing(self):
        self.stop = False
        self.show()
        self.thread = threading.Thread()
        self.thread.run = lambda: gobject.timeout_add(50, self._run)
        self.thread.start()
        
    def _run(self):
        gtk.gdk.threads_enter()
        self.pulse()
        if self.stop:
            self.set_fraction(1.0)
        while gtk.events_pending():
            gtk.main_iteration()
        gtk.gdk.threads_leave()
        return not self.stop

    def stop_pulsing(self):
        self.stop = True
        self.thread.join()
        gobject.idle_add(self.hide)


class Notebook(gtk.Notebook):

    """Wrapper class to improve the gtk.Notebook API."""

    def __init__(self, *args):
        super(Notebook, self).__init__(*args)
        self.set_scrollable(True)
        self.show()

    def get_pages(self):
        """Return all 'page' container widgets."""
        pages = []
        for n in range(self.get_n_pages()):
            pages.append(self.get_nth_page(n))
        return pages

    def get_page_labels(self):
        """Return all first pieces of text found in page labelwidgets."""
        labels = []
        for n in range(self.get_n_pages()):
            nth_page = self.get_nth_page(n)
            widgets = [self.get_tab_label(nth_page)]
            while not hasattr(widgets[0], "get_text"):
                if hasattr(widgets[0], "get_children"):
                    widgets.extend(widgets[0].get_children())
                elif hasattr(widgets[0], "get_child"):
                    widgets.append(widgets[0].get_child())
                widgets.pop(0)
            labels.append(widgets[0].get_text())
        return labels

    def get_page_ids(self):
        """Return the namespace id attributes for all notebook pages."""
        ids = []
        for n in range(self.get_n_pages()):
            nth_page = self.get_nth_page(n)
            if hasattr(nth_page, "namespace"):
                ids.append(nth_page.namespace)
        return ids

    def delete_by_label(self, label):
        """Remove the (unique) page with this label as title."""
        self.remove_page(self.get_page_labels().index(label))
        
    def delete_by_id(self, page_id):
        """Use this only with pages with the attribute 'namespace'."""
        self.remove_page(self.get_page_ids().index(page_id))

    def set_tab_label_packing(self, page, expand=False, fill=True,
                              pack_type=gtk.PACK_START):
        super(Notebook, self).set_tab_label_packing(page, expand, fill,
                                                    pack_type)


class TooltipTreeView(gtk.TreeView):

    """Wrapper class for gtk.TreeView with a better tooltip API.

    It takes two keyword arguments, model as in gtk.TreeView and
    get_tooltip_func which is analogous to the 'query-tooltip'
    connector in gtk.TreeView.

    This should be overridden either at or after initialisation.
    It takes four arguments - the gtk.TreeView, a gtk.TreeIter and
    a column index for the gtk.TreeView, and a gtk.ToolTip.

    Return True to display the ToolTip, or False to hide it.

    """

    def __init__(self, model=None, get_tooltip_func=None):
        super(TooltipTreeView, self).__init__(model)
        self.get_tooltip = get_tooltip_func
        self.set_has_tooltip(True)
        self._last_tooltip_path = None
        self._last_tooltip_column = None
        self.connect('query-tooltip', self._handle_tooltip)

    def _handle_tooltip(self, view, x, y, kbd_ctx, tip):
        """Handle creating a tooltip for the treeview."""
        x, y = view.convert_widget_to_bin_window_coords(x, y)
        pathinfo = view.get_path_at_pos(x, y)
        if pathinfo is None:
            return False
        path, column = pathinfo[:2]
        if path is None:
            return False
        if (path != self._last_tooltip_path or
            column != self._last_tooltip_column):
            self._last_tooltip_path = path
            self._last_tooltip_column = column
            return False
        col_index = view.get_columns().index(column)
        row_iter = view.get_model().get_iter(path)
        if self.get_tooltip is None:
            return False
        return self.get_tooltip(view, row_iter, col_index, tip)


class TreeModelSortUtil(object):

    """This class contains useful sorting methods for TreeModelSort.
    
    Arguments:
    sort_model_getter_func - a function accepting no arguments that
    returns the TreeModelSort. This is necessary if a combination
    of TreeModelFilter and TreeModelSort is used.
    
    Keyword Arguments:
    multi_sort_num - the maximum number of columns to sort by. For
    example, setting this to 2 means that a single secondary sort
    may be applied based on the previous sort column.

    You must connect to both handle_sort_column_change and sort_column
    for multi-column sorting. Example code:
    
    sort_model = gtk.TreeModelSort(filter_model)
    sort_util = TreeModelSortUtil(
                         lambda: sort_model,
                         multi_sort_num=2)
    for i in range(len(columns)):
        sort_model.set_sort_func(i, sort_util.sort_column, i)
    sort_model.connect("sort-column-changed",
                       sort_util.handle_sort_column_change)

    """

    def __init__(self, sort_model_getter_func, multi_sort_num=1):
        self._get_sort_model = sort_model_getter_func
        self.multi_sort_num = multi_sort_num
        self._sort_columns_stored = []

    def clear_sort_columns(self):
        """Clear any multi-sort information."""
        self._sort_columns_stored = []

    def cmp_(self, value1, value2):
        """Perform a useful form of 'cmp'"""
        if (isinstance(value1, basestring) and
            isinstance(value2, basestring)):
            if value1.isdigit() and value2.isdigit():
                return cmp(float(value1), float(value2))
            return rose.config.sort_settings(value1, value2)
        return cmp(value1, value2)

    def handle_sort_column_change(self, model):
        """Store previous sorting information for multi-column sorts."""
        id_, order = model.get_sort_column_id()
        if id_ is None and order is None:
            return False
        if (self._sort_columns_stored and
            self._sort_columns_stored[0][0] == id_):
            self._sort_columns_stored.pop(0)
        self._sort_columns_stored.insert(0, (id_, order))
        if len(self._sort_columns_stored) > 2:
            self._sort_columns_stored.pop()

    def sort_column(self, model, iter1, iter2, col_index):
        """Multi-column sort."""
        val1 = model.get_value(iter1, col_index)
        val2 = model.get_value(iter2, col_index)
        rval = self.cmp_(val1, val2)
        # If rval is 1 or -1, no need for a multi-column sort.
        if rval == 0:
            if isinstance(model, gtk.TreeModelSort):
                this_order = model.get_sort_column_id()[1]
            else:
                this_order = self._get_sort_model().get_sort_column_id()[1]
            cmp_factor = 1
            if this_order == gtk.SORT_DESCENDING:
                # We need to de-invert the sort order for multi sorting.
                cmp_factor = -1
        i = 0
        while rval == 0 and i < len(self._sort_columns_stored):
            next_id, next_order = self._sort_columns_stored[i]
            if next_id == col_index:
                i += 1
                continue
            next_cmp_factor = cmp_factor * 1
            if next_order == gtk.SORT_DESCENDING:
                # Set the correct order for multi sorting.
                next_cmp_factor = cmp_factor * -1
            val1 = model.get_value(iter1, next_id)
            val2 = model.get_value(iter2, next_id)
            rval = next_cmp_factor * self.cmp_(val1, val2)
            i += 1
        return rval 


run_gtk_main = gtk.main
quit_gtk_main = gtk.main_quit


def color_parse(color_specification):
    """Wrap gtk.gdk.color_parse and report errors with the specification."""
    try:
        return gtk.gdk.color_parse(color_specification)
    except ValueError:
        rose.reporter.Reporter().report(
                ColourParseError(color_specification))
        # Return a noticeable colour.
        return gtk.gdk.color_parse("#0000FF")  # Blue


def get_hyperlink_label(text, search_func=lambda i: False):
    """Return a label with clickable hyperlinks."""
    label = gtk.Label()
    label.show()
    try:
        pango.parse_markup(text)
    except glib.GError:
        label.set_text(text)
    else:
        try:
            label.connect("activate-link",
                          lambda l, u: handle_link(u, search_func))
        except TypeError:  # No such signal before PyGTK 2.18
            label.connect("button-release-event",
                          lambda l, e: extract_link(l, search_func))
            text = REC_HYPERLINK_ID_OR_URL.sub(
                                        MARKUP_URL_UNDERLINE, text)
            label.set_markup(text)
        else:
            text = REC_HYPERLINK_ID_OR_URL.sub(
                                        MARKUP_URL_HTML, text)
            label.set_markup(text)
    return label


def get_icon(system="rose"):
    """Return a gtk.gdk.Pixbuf for the system icon."""
    locator = rose.resource.ResourceLocator(paths=sys.path)
    icon_path = locator.locate("etc/images/{0}-icon-trim.svg".format(system))
    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file(icon_path)
    except Exception:
        icon_path = locator.locate(
                            "etc/images/{0}-icon-trim.png".format(system))
        pixbuf = gtk.gdk.pixbuf_new_from_file(icon_path)
    return pixbuf


def handle_link(url, search_function, handle_web=False):
    if url.startswith("http"):
        if handle_web:
            webbrowser.open(url)
    else:
        search_function(url)
    return False

    
def extract_link(label, search_function):
    text = label.get_text()
    bounds = label.get_selection_bounds()
    if not bounds:
        return None
    lower_bound, upper_bound = bounds
    while lower_bound > 0:
        if text[lower_bound - 1].isspace():
            break
        lower_bound -= 1
    while upper_bound < len(text):
        if text[upper_bound].isspace():
            break
        upper_bound += 1
    link = text[lower_bound: upper_bound]
    if any([c.isspace() for c in link]):
        return None
    handle_link(link, search_function, handle_web=True)


def rc_setup(rc_resource):
    """Run gtk.rc_parse on the resource, to setup the gtk settings."""
    gtk.rc_parse(rc_resource)


def setup_scheduler_icon(ipath=None):
    """Setup a 'stock' icon for the scheduler"""
    new_icon_factory = gtk.IconFactory()
    locator = rose.resource.ResourceLocator(paths=sys.path)
    iname = "rose-gtk-scheduler"
    if ipath is None:
        new_icon_factory.add(iname, gtk.icon_factory_lookup_default(
                                        gtk.STOCK_MISSING_IMAGE))
    else:
        path = locator.locate(ipath)
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        new_icon_factory.add(iname, gtk.IconSet(pixbuf))
    new_icon_factory.add_default()


def setup_stock_icons():
    """Setup any additional 'stock' icons."""
    new_icon_factory = gtk.IconFactory()
    locator = rose.resource.ResourceLocator(paths=sys.path)
    for png_icon_name in ["gnome_add",
                          "gnome_add_errors",
                          "gnome_add_warnings",
                          "gnome_package_system",
                          "gnome_package_system_errors",
                          "gnome_package_system_warnings"]:
        ifile = png_icon_name + ".png"
        istring = png_icon_name.replace("_", "-")
        path = locator.locate("etc/images/rose-config-edit/" + ifile)
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        new_icon_factory.add("rose-gtk-" + istring,
                             gtk.IconSet(pixbuf))
    exp_icon_pixbuf = get_icon()
    new_icon_factory.add("rose-exp-logo", gtk.IconSet(exp_icon_pixbuf))
    new_icon_factory.add_default()


def safe_str(value):
    """Formats a value safely for use in pango markup."""
    string = str(value).replace("&", "&amp;")
    return string.replace(">", "&gt;").replace("<", "&lt;")
