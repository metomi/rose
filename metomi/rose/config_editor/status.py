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

import datetime
import sys
import time

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import threading

import metomi.rose.config
import metomi.rose.config_editor
import metomi.rose.gtk.console
import metomi.rose.reporter


class StatusReporter(metomi.rose.reporter.Reporter):

    """Handle event notification.

    load_updater must be a metomi.rose.gtk.splash.SplashScreenProcess
    instance (or have the same interface to update and stop methods).

    status_bar_update_func must be a function that accepts a
    metomi.rose.reporter.Event, a metomi.rose.reporter kind-of-event string, and a
    level of importance/verbosity. See metomi.rose.reporter for more details.

    """

    EVENT_KIND_LOAD = "load"

    def __init__(self, load_updater, status_bar_update_func):
        self._load_updater = load_updater
        self._status_bar_update_func = status_bar_update_func
        self._no_load = False

    def event_handler(self, message, kind=None, level=None, prefix=None,
                      clip=None):
        """Handle a message or event."""
        print(1000)
        message_kwargs = {}
        if isinstance(message, metomi.rose.reporter.Event):
            if kind is None:
                kind = message.kind
            if level is None:
                level = message.level
            message_kwargs = message.kwargs
        if kind == self.EVENT_KIND_LOAD and not self._no_load:
            print(str(threading.get_ident())+" 1001")
            ret = self._load_updater.update(str(message), **message_kwargs)
            print(str(threading.get_ident())+" 1001---")
            return ret
        print(1002)
        return self._status_bar_update_func(message, kind, level)

    def report_load_event(
            self, text, no_progress=False, new_total_events=None):
        """Report a load-related event (to metomi.rose.gtk.util.SplashScreen)."""
        event = metomi.rose.reporter.Event(text,
                                    kind=self.EVENT_KIND_LOAD,
                                    no_progress=no_progress,
                                    new_total_events=new_total_events)
        print("Status 1")
        self.report(event)
        print("Status 1-1")

    def set_no_load(self):
        self._no_load = True

    def stop(self):
        """Stop the updater."""
        self._load_updater.stop()


class StatusBar(Gtk.VBox):

    """Generate the status bar widget."""

    def __init__(self, verbosity=metomi.rose.reporter.Reporter.DEFAULT):
        super(StatusBar, self).__init__()
        self.verbosity = verbosity
        self.num_errors = 0
        self.console = None
        hbox = Gtk.HBox()
        hbox.show()
        self.pack_start(hbox, expand=False, fill=False, padding=0)
        self._generate_error_widget()
        hbox.pack_start(self._error_widget, expand=False, fill=False, padding=0)
        vsep_message = Gtk.VSeparator()
        vsep_message.show()
        vsep_eb = Gtk.EventBox()
        vsep_eb.show()
        hbox.pack_start(vsep_message, expand=False, fill=False, padding=0)
        hbox.pack_start(vsep_eb, expand=True, fill=True, padding=0)
        self._generate_message_widget()
        hbox.pack_end(self._message_widget, expand=False, fill=False,
                      padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        self.messages = []
        self.show()

    def set_message(self, message, kind=None, level=None):
        if isinstance(message, metomi.rose.reporter.Event):
            if kind is None:
                kind = message.kind
            if level is None:
                level = message.level
        if level > self.verbosity:
            return
        if isinstance(message, Exception):
            kind = metomi.rose.reporter.Reporter.KIND_ERR
            level = metomi.rose.reporter.Reporter.FAIL
        self.messages.append((kind, str(message), time.time()))
        if len(self.messages) > metomi.rose.config_editor.STATUS_BAR_MESSAGE_LIMIT:
            self.messages.pop(0)
        self._update_message_widget(str(message), kind=kind)
        self._update_console()
        while Gdk.events_pending():
            Gtk.main_iteration()

    def set_num_errors(self, new_num_errors):
        """Update the number of errors."""
        if new_num_errors != self.num_errors:
            self.num_errors = new_num_errors
            self._update_error_widget()
            while Gdk.events_pending():
                Gtk.main_iteration()

    def _generate_error_widget(self):
        # Generate the error display widget.
        self._error_widget = Gtk.HBox()
        self._error_widget.show()
        locator = metomi.rose.resource.ResourceLocator(paths=sys.path)
        icon_path = locator.locate(
            'etc/images/rose-config-edit/error_icon.png')
        image = Gtk.Image.new_from_file(str(icon_path))
        image.show()
        self._error_widget.pack_start(image, expand=False, fill=False, padding=0)
        self._error_widget_label = Gtk.Label()
        self._error_widget_label.show()
        self._error_widget.pack_start(
            self._error_widget_label, expand=False, fill=False,
            padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        self._update_error_widget()

    def _generate_message_widget(self):
        # Generate the message display widget.
        self._message_widget = Gtk.EventBox()
        self._message_widget.show()
        message_hbox = Gtk.HBox()
        message_hbox.show()
        self._message_widget.add(message_hbox)
        self._message_widget.connect("enter-notify-event",
                                     self._handle_enter_message_widget)
        self._message_widget_error_image = Gtk.Image.new_from_stock(
            Gtk.STOCK_DIALOG_ERROR,
            Gtk.IconSize.MENU)
        self._message_widget_info_image = Gtk.Image.new_from_stock(
            Gtk.STOCK_DIALOG_INFO,
            Gtk.IconSize.MENU)
        self._message_widget_label = Gtk.Label()
        self._message_widget_label.show()
        vsep = Gtk.VSeparator()
        vsep.show()
        self._console_launcher = metomi.rose.gtk.util.CustomButton(
            stock_id=Gtk.STOCK_INFO,
            size=Gtk.IconSize.MENU,
            tip_text=metomi.rose.config_editor.STATUS_BAR_CONSOLE_TIP,
            as_tool=True)
        self._console_launcher.connect("clicked", self._launch_console)
        # None of this works anymore and needs to be set by CSS
        # which does not look simple
        # style = Gtk.RcStyle()
        # style.xthickness = 0
        # style.ythickness = 0
        # setattr(style, "inner-border", [0, 0, 0, 0])
        # self._console_launcher.modify_style(style)
        message_hbox.pack_start(
            self._message_widget_error_image,
            expand=False, fill=False, padding=0)
        message_hbox.pack_start(
            self._message_widget_info_image,
            expand=False, fill=False, padding=0)
        message_hbox.pack_start(
            self._message_widget_label,
            expand=False, fill=False,
            padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        message_hbox.pack_start(
            vsep, expand=False, fill=False,
            padding=metomi.rose.config_editor.SPACING_SUB_PAGE)
        message_hbox.pack_start(
            self._console_launcher, expand=False, fill=False, padding=0)

    def _update_error_widget(self):
        # Update the error display widget.
        self._error_widget_label.set_text(str(self.num_errors))
        self._error_widget.set_sensitive((self.num_errors > 0))

    def _update_message_widget(self, message_text, kind):
        # Update the message display widget.
        if kind == metomi.rose.reporter.Reporter.KIND_ERR:
            self._message_widget_error_image.show()
            self._message_widget_info_image.hide()
        else:
            self._message_widget_error_image.hide()
            self._message_widget_info_image.show()
        last_line = message_text.splitlines()[-1]
        self._message_widget_label.set_text(last_line)

    def _handle_enter_message_widget(self, *args):
        tooltip_text = ""
        for kind, message_text, message_time in self.messages[-5:]:
            if kind == metomi.rose.reporter.Reporter.KIND_ERR:
                prefix = metomi.rose.reporter.Reporter.PREFIX_FAIL
            else:
                prefix = metomi.rose.reporter.Reporter.PREFIX_INFO
            suffix = datetime.datetime.fromtimestamp(message_time).strftime(
                metomi.rose.config_editor.EVENT_TIME)
            tooltip_text += prefix + " " + message_text + " " + suffix + "\n"
        tooltip_text = tooltip_text.rstrip()
        self._message_widget_label.set_tooltip_text(tooltip_text)

    def _get_console_messages(self):
        err_category = metomi.rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_ERROR
        info_category = metomi.rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_INFO
        message_tuples = []
        for kind, message, time_info in self.messages:
            if kind == metomi.rose.reporter.Reporter.KIND_ERR:
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
        err_category = metomi.rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_ERROR
        info_category = metomi.rose.config_editor.STATUS_BAR_CONSOLE_CATEGORY_INFO
        window = self.get_toplevel()
        self.console = metomi.rose.gtk.console.ConsoleWindow(
            [err_category, info_category], message_tuples,
            [Gtk.STOCK_DIALOG_ERROR, Gtk.STOCK_DIALOG_INFO],
            parent=window,
            destroy_hook=self._handle_destroy_console)

    def _update_console(self):
        if self.console is not None:
            self.console.update_messages(self._get_console_messages())
