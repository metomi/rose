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

import datetime
import sys
import time

import pygtk
pygtk.require('2.0')
import gtk

import rose.config
import rose.config_editor
import rose.gtk.console
import rose.reporter


class StatusReporter(rose.reporter.Reporter):

    """Handle event notification."""

    EVENT_KIND_LOAD = "load"

    def __init__(self, loader_update_func, status_bar_update_func):
        self._loader_update_func = loader_update_func
        self._status_bar_update_func = status_bar_update_func

    def event_handler(self, message, kind=None, level=None, prefix=None,
                      clip=None):
        """Handle a message or event."""
        message_kwargs = {}
        if isinstance(message, rose.reporter.Event):
            if kind is None:
                kind = message.kind
            if level is None:
                level = message.level
            message_kwargs = message.kwargs
        if kind == self.EVENT_KIND_LOAD:
            return self._loader_update_func(str(message), **message_kwargs)
        return self._status_bar_update_func(message, kind, level)

    def report_load_event(self, text, no_progress=False):
        """Report a load-related event (to rose.gtk.util.SplashScreen)."""
        event = rose.reporter.Event(text,
                                    kind=self.EVENT_KIND_LOAD,
                                    no_progress=no_progress)
        self.report(event)


class StatusBar(gtk.VBox):

    """Generate the status bar widget."""

    def __init__(self, verbosity=rose.reporter.Reporter.DEFAULT):
        super(StatusBar, self).__init__()
        self.verbosity = verbosity
        self.num_errors = 0
        self.console = None
        hbox = gtk.HBox()
        hbox.show()
        self.pack_start(hbox, expand=False, fill=False)
        self._generate_error_widget()
        hbox.pack_start(self._error_widget, expand=False, fill=False)
        vsep_message = gtk.VSeparator()
        vsep_message.show()
        vsep_eb = gtk.EventBox()
        vsep_eb.show()
        hbox.pack_start(vsep_message, expand=False, fill=False)
        hbox.pack_start(vsep_eb, expand=True, fill=True)
        self._generate_message_widget()
        hbox.pack_end(self._message_widget, expand=False, fill=False,
                      padding=rose.config_editor.SPACING_SUB_PAGE)
        self.messages = []
        self.show()

    def set_message(self, message, kind=None, level=None):
        if isinstance(message, rose.reporter.Event):
            if kind is None:
                kind = message.kind
            if level is None:
                level = message.level
        if level > self.verbosity:
            return
        self.messages.append((kind, str(message), time.time()))
        if len(self.messages) > rose.config_editor.STATUS_BAR_MESSAGE_LIMIT:
            self.messages.pop(0)
        self._update_message_widget(str(message), kind=kind)
        self._update_console()

    def set_num_errors(self, new_num_errors):
        """Update the number of errors."""
        if new_num_errors != self.num_errors:
            self.num_errors = new_num_errors
            self._update_error_widget()

    def _generate_error_widget(self):
        # Generate the error display widget.
        self._error_widget = gtk.HBox()
        self._error_widget.show()
        locator = rose.resource.ResourceLocator(paths=sys.path)
        icon_path = locator.locate(
                            'etc/images/rose-config-edit/error_icon.xpm')
        image = gtk.image_new_from_file(icon_path)
        image.show()
        self._error_widget.pack_start(image, expand=False, fill=False)
        self._error_widget_label = gtk.Label()
        self._error_widget_label.show()
        self._error_widget.pack_start(self._error_widget_label, expand=False,
                                      fill=False,
                                      padding=rose.config_editor.SPACING_SUB_PAGE)
        self._update_error_widget()

    def _generate_message_widget(self):
        # Generate the message display widget.
        self._message_widget = gtk.EventBox()
        self._message_widget.show()
        message_hbox = gtk.HBox()
        message_hbox.show()
        self._message_widget.add(message_hbox)
        self._message_widget.connect("enter-notify-event",
                                           self._handle_enter_message_widget)
        self._message_widget_error_image = gtk.image_new_from_stock(
                                                     gtk.STOCK_DIALOG_ERROR,
                                                     gtk.ICON_SIZE_MENU)
        self._message_widget_info_image = gtk.image_new_from_stock(
                                                    gtk.STOCK_DIALOG_INFO,
                                                    gtk.ICON_SIZE_MENU)
        self._message_widget_label = gtk.Label()
        self._message_widget_label.show()
        vsep = gtk.VSeparator()
        vsep.show()
        self._console_launcher = rose.gtk.util.CustomButton(
                      stock_id=gtk.STOCK_INFO,
                      size=gtk.ICON_SIZE_MENU,
                      tip_text=rose.config_editor.STATUS_BAR_CONSOLE_TIP,
                      as_tool=True)
        self._console_launcher.connect("clicked", self._launch_console)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        setattr(style, "inner-border", [0, 0, 0, 0])
        self._console_launcher.modify_style(style)
        message_hbox.pack_start(
                     self._message_widget_error_image,
                     expand=False, fill=False)
        message_hbox.pack_start(
                     self._message_widget_info_image,
                     expand=False, fill=False)
        message_hbox.pack_start(
                     self._message_widget_label,
                     expand=False, fill=False,
                     padding=rose.config_editor.SPACING_SUB_PAGE)
        message_hbox.pack_start(vsep, expand=False, fill=False,
                     padding=rose.config_editor.SPACING_SUB_PAGE)
        message_hbox.pack_start(
                     self._console_launcher,
                     expand=False, fill=False)

    def _update_error_widget(self):
        # Update the error display widget.
        self._error_widget_label.set_text(str(self.num_errors))
        self._error_widget.set_sensitive((self.num_errors > 0))

    def _update_message_widget(self, message_text, kind):
        # Update the message display widget.
        if kind == rose.reporter.Reporter.KIND_ERR:
            self._message_widget_error_image.show()
            self._message_widget_info_image.hide()
        else:
            self._message_widget_error_image.hide()
            self._message_widget_info_image.show()
        self._message_widget_label.set_text(message_text)

    def _handle_enter_message_widget(self, *args):
        tooltip_text = ""
        for kind, message_text, message_time in self.messages[-5:]:
            if kind == rose.reporter.Reporter.KIND_ERR:
                prefix = rose.reporter.Reporter.PREFIX_FAIL
            else:
                prefix = rose.reporter.Reporter.PREFIX_INFO
            suffix = datetime.datetime.fromtimestamp(message_time).strftime(
                                       rose.config_editor.EVENT_TIME)
            tooltip_text += prefix + " " + message_text + " " + suffix + "\n"
        tooltip_text = tooltip_text.rstrip()
        self._message_widget_label.set_tooltip_text(tooltip_text)

    def _get_console_messages(self):
        err_category = rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_ERROR
        info_category = rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_INFO
        message_tuples = []
        for kind, message, time_info in self.messages:
            if kind == rose.reporter.Reporter.KIND_ERR:
                category = err_category
            else:
                category = info_category
            message_tuples.append((category, message, time_info))
        return message_tuples

    def _handle_destroy_console(self):
        self.console = None

    def _launch_console(self, *args):
        if self.console is not None:
            return self.console.present()
        message_tuples = self._get_console_messages()
        err_category = rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_ERROR
        info_category = rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_INFO
        window = self.get_toplevel()
        self.console = rose.gtk.console.ConsoleWindow(
                            [err_category, info_category], message_tuples,
                            [gtk.STOCK_DIALOG_ERROR, gtk.STOCK_DIALOG_INFO],
                            parent=window,
                            destroy_hook=self._handle_destroy_console)

    def _update_console(self):
        if self.console is not None:
            self.console.update_messages(self._get_console_messages())
