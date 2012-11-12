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

import rose.resource


DIALOG_BUTTON_CLOSE = "Close"
DIALOG_LABEL_README = "README"
REC_DIALOG_HYPERLINK_ID_OR_URL = re.compile(r"""(?P<start_break>\b)
                                            (?P<url>[\w:-]+=\w+|https?://\S+)
                                            (?P<end_break>\b)""",
                                            re.X)
DIALOG_MARKUP_URL_HTML = (r"""\g<start_break>""" +
                          r"""<a href='\g<url>'>\g<url></a>""" + 
                          r"""\g<end_break>""")
DIALOG_MARKUP_URL_UNDERLINE = (r"""\g<start_break>""" +
                               r"""<u>\g<url></u>""" + 
                               r"""\g<end_break>""")
DIALOG_PADDING = 10
DIALOG_SUB_PADDING = 5

DIALOG_SIZE_PROCESS = (400, 100)
DIALOG_SIZE_SCROLLED = (600, 600)

DIALOG_TEXT_SHUTDOWN_ASAP = "Shutdown ASAP."
DIALOG_TEXT_SHUTTING_DOWN = "Shutting down."
DIALOG_TEXT_UNCAUGHT_EXCEPTION = ("{0} has crashed. {1}" +
                                  "\n\n<b>{2}</b>: {3}\n{4}")
DIALOG_TITLE_UNCAUGHT_EXCEPTION = "Critical error"
DIALOG_TYPE_ERROR = gtk.MESSAGE_ERROR
DIALOG_TYPE_INFO = gtk.MESSAGE_INFO
DIALOG_TYPE_WARNING = gtk.MESSAGE_WARNING


class CustomButton(gtk.Button):

    """Returns a custom gtk.Button."""

    def __init__(self, label=None, stock_id=None,
                 size=gtk.ICON_SIZE_SMALL_TOOLBAR, tip_text=None,
                 as_tool=False, icon_at_start=False):
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
        self.set_tooltip_text(new_text)

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


class SplashScreen(gtk.Window):

    """Run a splash screen that receives update information."""
    
    BACKGROUND_COLOUR = "white"  # Same as logo background.
    PADDING = 10
    SUB_PADDING = 5
    FONT_DESC = "8"

    def __init__(self, logo_path, title, total_number_of_events):
        super(SplashScreen, self).__init__()
        self.set_title(title)
        self.set_decorated(False)
        self.modify_bg(gtk.STATE_NORMAL,
                       gtk.gdk.color_parse(self.BACKGROUND_COLOUR))
        self.set_gravity(gtk.gdk.GRAVITY_CENTER)
        self.set_position(gtk.WIN_POS_CENTER)
        main_vbox = gtk.VBox()
        main_vbox.show()
        image = gtk.image_new_from_file(logo_path)
        image.show()
        image_hbox = gtk.HBox()
        image_hbox.show()
        image_hbox.pack_start(image, expand=False, fill=True)
        main_vbox.pack_start(image_hbox, expand=False, fill=True)
        self.progress_bar = gtk.ProgressBar()
        self.progress_bar.show()
        self.progress_bar.modify_font(pango.FontDescription(self.FONT_DESC))
        self.progress_bar.set_ellipsize(pango.ELLIPSIZE_END)
        self.event_count = 0.0
        self.total_number_of_events = float(total_number_of_events)
        progress_hbox = gtk.HBox(spacing=self.SUB_PADDING)
        progress_hbox.show()
        progress_hbox.pack_start(self.progress_bar, expand=True, fill=True,
                                 padding=self.SUB_PADDING)
        main_vbox.pack_start(progress_hbox, expand=False, fill=False,
                             padding=self.PADDING)
        self.add(main_vbox)
        if self.total_number_of_events > 0:
            self.show()
        while gtk.events_pending():
            gtk.main_iteration()

    def update(self, event, data_name):
        """Show text corresponding to an event."""
        text = data_name + " - " + event
        if self.total_number_of_events == 0:
            fraction = 1.0
        else:
            fraction = min([1.0, self.event_count /
                                 self.total_number_of_events])
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
        self.event_count += 1.0
        while gtk.events_pending():
            gtk.main_iteration()
        if fraction == 1.0:
            self.finish()

    def finish(self):
        """Delete the splash screen."""
        gobject.idle_add(lambda: self.destroy())


class DialogProcess(object):

    """Run a forked process and display a dialog while it runs.
    
    cmd_args can either be a list of shell command components
    e.g. ['sleep', '100'] or a list containing a python function
    followed by any function arguments e.g. [func, '100'].
    description is used for the label, if not None
    title is used for the title, if not None
    stock_id is used for the dialog icon
    hide_progress removes the bouncing progress bar

    Returns the exit code of the process.

    """

    DIALOG_FUNCTION_LABEL = "Executing function"
    DIALOG_LOG_LABEL = "Show log"
    DIALOG_PROCESS_LABEL = "Executing command"

    def __init__(self, cmd_args, description=None, title=None,
                 stock_id=gtk.STOCK_EXECUTE,
                 hide_progress=False, modal=True,
                 event_queue=None):
        window = get_dialog_parent()
        self.dialog = gtk.Dialog(buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                                 parent=window)
        self.dialog.set_modal(modal)
        self.dialog.set_default_size(*DIALOG_SIZE_PROCESS)
        self._is_destroyed = False
        self.dialog.set_icon(self.dialog.render_icon(gtk.STOCK_EXECUTE,
                                                     gtk.ICON_SIZE_MENU))
        self.cmd_args = cmd_args
        self.event_queue = event_queue
        str_cmd_args = [safe_str(a) for a in cmd_args]
        if description is not None:
            str_cmd_args = [description]
        if title is None:
            self.dialog.set_title(" ".join(str_cmd_args[0:2]))
        else:
            self.dialog.set_title(title)
        if callable(cmd_args[0]):
            self.label = gtk.Label(self.DIALOG_FUNCTION_LABEL)
        else:
            self.label = gtk.Label(self.DIALOG_PROCESS_LABEL)
        self.label.set_use_markup(True)
        self.label.show()
        self.image = gtk.image_new_from_stock(stock_id,
                                              gtk.ICON_SIZE_DIALOG)
        self.image.show()
        image_vbox = gtk.VBox()
        image_vbox.pack_start(self.image, expand=False, fill=False)
        image_vbox.show()
        top_hbox = gtk.HBox()
        top_hbox.pack_start(image_vbox, expand=False, fill=False,
                            padding=DIALOG_PADDING)
        top_hbox.show()
        hbox = gtk.HBox()
        hbox.pack_start(self.label, expand=False, fill=False,
                        padding=DIALOG_PADDING)
        hbox.show()
        main_vbox = gtk.VBox()
        main_vbox.show()
        main_vbox.pack_start(hbox, expand=False, fill=False,
                             padding=DIALOG_SUB_PADDING)

        cmd_string = str_cmd_args[0]
        if str_cmd_args[1:]:
            if callable(cmd_args[0]):
                cmd_string += "(" + " ".join(str_cmd_args[1:]) + ")"
            else:
                cmd_string += " " + " ".join(str_cmd_args[1:])
        self.cmd_label = gtk.Label()
        self.cmd_label.set_markup("<b>" + cmd_string + "</b>")
        self.cmd_label.show()
        cmd_hbox = gtk.HBox()
        cmd_hbox.pack_start(self.cmd_label, expand=False, fill=False,
                            padding=DIALOG_PADDING)
        cmd_hbox.show()
        main_vbox.pack_start(cmd_hbox, expand=False, fill=True,
                             padding=DIALOG_SUB_PADDING)
        #self.dialog.set_modal(True)
        self.progress_bar = gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.1)
        self.progress_bar.show()
        hbox = gtk.HBox()
        hbox.pack_start(self.progress_bar, expand=True, fill=True,
                        padding=DIALOG_PADDING)
        hbox.show()
        main_vbox.pack_start(hbox, expand=False, fill=False,
                             padding=DIALOG_SUB_PADDING)
        top_hbox.pack_start(main_vbox, expand=True, fill=True,
                            padding=DIALOG_PADDING)
        if self.event_queue is None:
            self.dialog.vbox.pack_start(top_hbox, expand=True, fill=True)
        else:
            text_view_scroll = gtk.ScrolledWindow()
            text_view_scroll.set_policy(gtk.POLICY_NEVER,
                                        gtk.POLICY_AUTOMATIC)
            text_view_scroll.show()
            text_view = gtk.TextView()
            text_view.show()
            self.text_buffer = text_view.get_buffer()
            self.text_tag = self.text_buffer.create_tag()
            self.text_tag.set_property("scale", pango.SCALE_SMALL)
            text_view.connect('size-allocate', self._handle_scroll_text_view)
            text_view_scroll.add(text_view)
            text_expander = gtk.Expander(self.DIALOG_LOG_LABEL)
            text_expander.set_spacing(DIALOG_SUB_PADDING)
            text_expander.add(text_view_scroll)
            text_expander.show()
            top_pane = gtk.VPaned()
            top_pane.pack1(top_hbox, resize=False, shrink=False)
            top_pane.show()
            self.dialog.vbox.pack_start(top_pane, expand=True, fill=True,
                                        padding=DIALOG_SUB_PADDING)
            top_pane.pack2(text_expander, resize=True, shrink=True)
        if hide_progress:
            progress_bar.hide()
        self.ok_button = self.dialog.get_action_area().get_children()[0]
        self.ok_button.hide()
        for child in self.dialog.vbox.get_children():
            if isinstance(child, gtk.HSeparator):
                child.hide()
        self.dialog.show()

    def run(self):
        stdout = tempfile.TemporaryFile()
        stderr = tempfile.TemporaryFile()
        self.p = multiprocessing.Process(target=_sep_process,
                                         args=[self.cmd_args, stdout, stderr])
        self.p.start()
        self.dialog.connect("destroy", self._handle_dialog_process_destroy)
        while self.p.is_alive():
            self.progress_bar.pulse()
            if self.event_queue is not None:
                try:
                    new_text = self.event_queue.get(False)
                except Queue.Empty:
                    pass
                else:
                    end = self.text_buffer.get_end_iter()
                    tag = gtk
                    self.text_buffer.insert_with_tags(end, new_text,
                                                      self.text_tag)
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.1)
        stdout.seek(0)
        stderr.seek(0)
        if self.p.exitcode != 0:
            if self._is_destroyed:
                return self.p.exitcode
            else:
                self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                                          gtk.ICON_SIZE_DIALOG)
                self.label.hide()
                self.progress_bar.hide()
                self.cmd_label.set_markup("<b>" + safe_str(stderr.read()) +
                                          "</b>")
                self.ok_button.show()
                for child in self.dialog.vbox.get_children():
                    if isinstance(child, gtk.HSeparator):
                        child.show()
                self.dialog.run()
        self.dialog.destroy()
        return self.p.exitcode

    def _handle_dialog_process_destroy(self, dialog):
        if self.p.is_alive():
            self.p.terminate()
        self._is_destroyed = True
        return False

    def _handle_scroll_text_view(self, text_view, event=None):
        """Scroll the parent scrolled window to the bottom."""
        vadj = text_view.get_parent().get_vadjustment()
        if vadj.upper > vadj.lower + vadj.page_size:
            vadj.set_value(vadj.upper - 0.95*vadj.page_size)


def _sep_process(*args):
    sys.exit(_process(*args))


def _process(cmd_args, stdout=sys.stdout, stderr=sys.stderr):
    if callable(cmd_args[0]):
        func = cmd_args.pop(0)
        try:
            func(*cmd_args)
        except Exception as e:
            stderr.write(type(e).__name__ + ": " + str(e) + "\n")
            text1 = stderr.read()
            return 1
        return 0
    p = subprocess.Popen(cmd_args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    for line in iter(p.stdout.readline, ""):
        stdout.write(line)
    for line in iter(p.stderr.readline, ""):
        stderr.write(line)
    p.wait()
    text0 = stdout.read()  # Magically keep it alive.
    text1 = stderr.read()
    return p.poll()


run_gtk_main = gtk.main
quit_gtk_main = gtk.main_quit


def run_about_dialog(name=None, copyright=None,
                     logo_path=None, website=None):
    parent_window = get_dialog_parent()
    about_dialog = gtk.AboutDialog()
    about_dialog.set_transient_for(parent_window)
    about_dialog.set_name(name)
    licence_path = os.path.join(os.getenv("ROSE_HOME"), "README")
    about_dialog.set_license(open(licence_path, "r").read())
    about_dialog.set_copyright(copyright)
    resource_loc = rose.resource.ResourceLocator(paths=sys.path)
    logo_path = resource_loc.locate(logo_path)
    about_dialog.set_logo(gtk.gdk.pixbuf_new_from_file(logo_path))
    about_dialog.set_website(website)
    gtk.about_dialog_set_url_hook(
                        lambda u, v, w: webbrowser.open(w),
                        about_dialog.get_website())
    about_dialog.run()
    about_dialog.destroy()


def run_command_arg_dialog(cmd_name, help_text, run_hook):
    """Launch a dialog to get extra arguments for a command."""
    checker_function = lambda t: True
    dialog, container, name_entry = get_naming_dialog(cmd_name,
                                                      checker_function)
    dialog.set_title(cmd_name)
    help_label = gtk.stock_lookup(gtk.STOCK_HELP)[1].strip("_")
    help_button = rose.gtk.util.CustomButton(
            stock_id=gtk.STOCK_HELP,
            label=help_label,
            size=gtk.ICON_SIZE_LARGE_TOOLBAR)
    help_button.connect(
                "clicked",
                lambda b: rose.gtk.util.run_scrolled_dialog(
                                help_text,
                                title=help_label))
    help_hbox = gtk.HBox()
    help_hbox.pack_start(help_button, expand=False, fill=False)
    help_hbox.show()
    container.pack_end(help_hbox, expand=False, fill=False)
    name_entry.grab_focus()
    dialog.connect("response", _handle_command_arg_response, run_hook,
                   name_entry)
    dialog.set_modal(False)
    dialog.show()


def _handle_command_arg_response(dialog, response, run_hook, entry):
    text = entry.get_text()
    dialog.destroy()
    if response == gtk.RESPONSE_ACCEPT:
        run_hook(shlex.split(text))


def run_dialog(dialog_type, text, title=None, modal=True):
    """Run a simple dialog with an 'OK' button and some text."""
    parent_window = get_dialog_parent()
    dialog = gtk.MessageDialog(type=dialog_type,
                               buttons=gtk.BUTTONS_OK,
                               parent=parent_window)
    try:
        pango.parse_markup(text)
    except glib.GError:
        try:
            dialog.set_markup(safe_str(text))
        except:
            dialog.format_secondary_text(text)
    else:
        dialog.set_markup(text)
    if "\n" in text:
        dialog.label.set_line_wrap(False)
    dialog.set_resizable(True)
    dialog.set_modal(modal)
    if title is not None:
        dialog.set_title(title)
    dialog.run()
    dialog.destroy()


def run_hyperlink_dialog(stock_id=None, text="", title=None,
                         search_func=lambda i: False):
    """Run a dialog with inserted hyperlinks."""
    parent_window = get_dialog_parent()
    dialog = gtk.Window()
    dialog.set_transient_for(parent_window)
    dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
    dialog.set_title(title)
    dialog.set_modal(False)
    top_vbox = gtk.VBox()
    top_vbox.show()
    main_hbox = gtk.HBox(spacing=DIALOG_PADDING)
    main_hbox.show()
    # Insert the image
    image_vbox = gtk.VBox()
    image_vbox.show()
    image = gtk.image_new_from_stock(stock_id,
                                     size=gtk.ICON_SIZE_DIALOG)
    image.show()
    image_vbox.pack_start(image, expand=False, fill=False,
                          padding=DIALOG_PADDING)
    main_hbox.pack_start(image_vbox, expand=False, fill=False)
    # Apply the text
    message_vbox = gtk.VBox()
    message_vbox.show()
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
            text = REC_DIALOG_HYPERLINK_ID_OR_URL.sub(
                                        DIALOG_MARKUP_URL_UNDERLINE, text)
            label.set_markup(text)
        else:
            text = REC_DIALOG_HYPERLINK_ID_OR_URL.sub(
                                        DIALOG_MARKUP_URL_HTML, text)
            label.set_markup(text)
    message_vbox.pack_start(label, expand=True, fill=True,
                            padding=DIALOG_PADDING)
    main_hbox.pack_start(message_vbox, expand=False, fill=True, 
                         padding=DIALOG_PADDING)
    top_vbox.pack_start(main_hbox, expand=False, fill=True)
    # Insert the button
    button_box = gtk.HBox(spacing=DIALOG_PADDING)
    button_box.show()
    button = CustomButton(label=DIALOG_BUTTON_CLOSE,
                          size=gtk.ICON_SIZE_LARGE_TOOLBAR,
                          stock_id=gtk.STOCK_CLOSE)
    button.connect("clicked", lambda b: dialog.destroy())
    button_box.pack_end(button, expand=False, fill=False,
                        padding=DIALOG_PADDING)
    top_vbox.pack_end(button_box, expand=False, fill=False,
                      padding=DIALOG_PADDING)
    dialog.add(top_vbox)
    if "\n" in text:
        label.set_line_wrap(False)
    dialog.set_resizable(True)
    dialog.show()
    label.set_selectable(True)
    button.grab_focus()


def run_scrolled_dialog(text, title=None):
    """Run a dialog intended for the display of a large amount of text."""
    parent_window = get_dialog_parent()
    window = gtk.Window()
    window.set_transient_for(parent_window)
    window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
    window.set_border_width(DIALOG_SUB_PADDING)
    if title is not None:
        window.set_title(title)
    window.set_default_size(*DIALOG_SIZE_SCROLLED)
    scrolled = gtk.ScrolledWindow()
    scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolled.show()
    label = gtk.Label()
    try:
        pango.parse_markup(text)
    except glib.GError:
        label.set_text(text)
    else:
        label.set_markup(text)
    label.show()
    label_box = gtk.VBox()
    label_box.pack_start(label, expand=True, fill=True)
    label_box.show()
    scrolled.add_with_viewport(label_box)
    scrolled.get_child().set_shadow_type(gtk.SHADOW_NONE)
    button = gtk.Button(stock=gtk.STOCK_OK)
    button.connect("clicked", lambda b: window.destroy())
    button.show()
    button.grab_focus()
    button_box = gtk.HBox()
    button_box.pack_end(button, expand=False, fill=False)
    button_box.show()
    main_vbox = gtk.VBox(spacing=DIALOG_SUB_PADDING)
    main_vbox.pack_start(scrolled, expand=True, fill=True)
    main_vbox.pack_end(button_box, expand=False, fill=False)
    main_vbox.show()
    window.add(main_vbox)
    window.show()
    return False


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


def get_naming_dialog(label, checker, ok_tip=None,
                      err_tip=None):
    """Return a dialog, container, and entry for entering a name."""
    button_list = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
    parent_window = get_dialog_parent()
    dialog = gtk.Dialog(buttons=button_list)
    dialog.set_transient_for(parent_window)
    dialog.set_modal(True)
    ok_button = dialog.action_area.get_children()[0]
    main_vbox = gtk.VBox()
    name_hbox = gtk.HBox()
    name_label = gtk.Label()
    name_label.set_text(label)
    name_label.show()
    name_entry = gtk.Entry()
    name_entry.set_tooltip_text(ok_tip)
    name_entry.connect("changed", _name_checker, checker, ok_button,
                       ok_tip, err_tip)
    name_entry.connect("activate", lambda b: dialog.response(
                                                    gtk.RESPONSE_ACCEPT))
    name_entry.show()
    name_hbox.pack_start(name_label, expand=False, fill=False,
                         padding=DIALOG_SUB_PADDING)
    name_hbox.pack_start(name_entry, expand=False, fill=True,
                         padding=DIALOG_SUB_PADDING)
    name_hbox.show()
    main_vbox.pack_start(name_hbox, expand=False, fill=True,
                         padding=DIALOG_PADDING)
    main_vbox.show()
    hbox = gtk.HBox()
    hbox.pack_start(main_vbox, expand=False, fill=True,
                    padding=DIALOG_PADDING)
    hbox.show()
    dialog.vbox.pack_start(hbox, expand=False, fill=True,
                           padding=DIALOG_PADDING)
    return dialog, main_vbox, name_entry

def _name_checker(entry, checker, ok_button, ok_tip, err_tip):
    good_colour = ok_button.style.text[gtk.STATE_NORMAL]
    bad_colour = gtk.gdk.color_parse(
                         rose.config_editor.COLOUR_VARIABLE_TEXT_ERROR)
    name = entry.get_text()
    if checker(name):
        entry.modify_text(gtk.STATE_NORMAL, good_colour)
        entry.set_tooltip_text(ok_tip)
        ok_button.set_sensitive(True)
    else:
        entry.modify_text(gtk.STATE_NORMAL, bad_colour)
        entry.set_tooltip_text(err_tip)
        ok_button.set_sensitive(False)
    return False


def run_choices_dialog(text, choices, title=None):
    """Run a dialog for choosing between a set of options."""
    parent_window = get_dialog_parent()
    dialog = gtk.Dialog(title,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                 gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                        parent=parent_window)
    dialog.set_border_width(DIALOG_SUB_PADDING)
    label = gtk.Label()
    try:
        pango.parse_markup(text)
    except glib.GError:
        label.set_text(text)
    else:
        label.set_markup(text)
    dialog.vbox.set_spacing(DIALOG_SUB_PADDING)
    dialog.vbox.pack_start(label, expand=False, fill=False)
    if len(choices) < 5:
        for i, choice in enumerate(choices):
            group = None
            if i > 0:
                group = radio_button
            if i == 1:
                radio_button.set_active(True)
            radio_button = gtk.RadioButton(group,
                                           label=choice,
                                           use_underline=False)
            dialog.vbox.pack_start(radio_button, expand=False, fill=False)
        getter = (lambda: 
                  [b.get_label() for b in radio_button.get_group()
                   if b.get_active()].pop())
    else:
        combo_box = gtk.combo_box_new_text()
        for choice in choices:
            combo_box.append_text(choice)
        combo_box.set_active(0)
        dialog.vbox.pack_start(combo_box, expand=False, fill=False)
        getter = lambda: choices[combo_box.get_active()]
    dialog.show_all()
    response = dialog.run()
    if response == gtk.RESPONSE_ACCEPT:
        choice = getter()
        dialog.destroy()
        return choice
    dialog.destroy()
    return None


def run_edit_dialog(text, finish_hook=None, title=None):
    """Run a dialog for editing some text."""
    parent_window = get_dialog_parent()
    dialog = gtk.Dialog(title,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                 gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                        parent=parent_window)
    dialog.set_default_size(*DIALOG_SIZE_PROCESS)
    dialog.set_border_width(DIALOG_SUB_PADDING)
    text_buffer = gtk.TextBuffer()
    text_buffer.set_text(text)
    text_view = gtk.TextView()
    text_view.set_editable(True)
    text_view.show()
    text_view.set_buffer(text_buffer)
    dialog.vbox.pack_start(text_view, expand=True, fill=True,
                           padding=DIALOG_SUB_PADDING)
    get_text = lambda: text_buffer.get_text(text_buffer.get_start_iter(),
                                            text_buffer.get_end_iter())
    if finish_hook is None:
        response = dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            text = get_text().strip()
            dialog.destroy()
            return text
        dialog.destroy()
    else:
        finish_func = lambda: finish_hook(get_text().strip())
        dialog.connect("response", _handle_edit_dialog_response, finish_func)
        dialog.show()


def _handle_edit_dialog_response(dialog, response, finish_hook):
    if response == gtk.RESPONSE_ACCEPT:
        finish_hook()
    dialog.destroy()


def get_dialog_parent():
    """Find the currently active window, if any, and reparent dialog."""
    ok_windows = []
    max_size = -1
    for window in gtk.window_list_toplevels():
        if (window.get_title() is not None and
            window.get_toplevel() == window):
            ok_windows.append(window)
            size_proxy = window.get_size()[0] * window.get_size()[1]
            if size_proxy > max_size:
                max_size = size_proxy
    for window in ok_windows:
        if window.is_active():
            return window
    for window in ok_windows:
        if window.get_size()[0] * window.get_size()[1] == max_size:
            return window


def rc_setup(rc_resource):
    """Run gtk.rc_parse on the resource, to setup the gtk settings."""
    gtk.rc_parse(rc_resource)


def set_exception_hook(keep_alive=False):
    """Set a dialog to run once an uncaught exception occurs."""
    prev_hook = sys.excepthook
    sys.excepthook = (lambda c, i, t:
                      _handle_exception(c, i, t, prev_hook,
                                        keep_alive))

def _handle_exception(exc_class, exc_inst, tback, hook, keep_alive):
    # Handle an uncaught exception.
    if exc_class == KeyboardInterrupt:
        return False
    hook(exc_class, exc_inst, tback)
    program_name = rose.resource.ResourceLocator().get_util_name()
    tback_text = safe_str("".join(traceback.format_tb(tback)))
    shutdown_text = DIALOG_TEXT_SHUTTING_DOWN
    if keep_alive:
        shutdown_text = DIALOG_TEXT_SHUTDOWN_ASAP
    text = DIALOG_TEXT_UNCAUGHT_EXCEPTION.format(program_name,
                                                 shutdown_text,
                                                 exc_class.__name__,
                                                 exc_inst,
                                                 tback_text)
    run_dialog(DIALOG_TYPE_ERROR, text,
               title=DIALOG_TITLE_UNCAUGHT_EXCEPTION)
    if not keep_alive:
        try:
            gtk.main_quit()
        except RuntimeError:
            pass


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
    exp_icon_path = locator.locate("etc/images/rose-icon-trim.png")
    exp_icon_pixbuf = gtk.gdk.pixbuf_new_from_file(exp_icon_path)

    new_icon_factory.add("rose-exp-logo", gtk.IconSet(exp_icon_pixbuf))
    new_icon_factory.add_default()


def safe_str(value):
    """Formats a value safely for use in pango markup."""
    string = str(value).replace("&", "&amp;")
    return  string.replace(">", "&gt;").replace("<", "&lt;")
