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

import sys

import pygtk
pygtk.require('2.0')
import gtk

import rose.config
import rose.config_editor
import rose.reporter


class Reporter(rose.reporter.Reporter):

    """Handle event notification."""

    EVENT_TYPE_LOAD = "load"

    def __init__(self, loader_update_func, status_bar_update_func):
        self._loader_update_func = loader_update_func
        self._status_bar_update_func = status_bar_update_func

    def event_handler(self, message, type_=None, level=None, prefix=None,
                      clip=None):
        """Handle a message or event."""
        message_kwargs = {}
        if isinstance(message, rose.reporter.Event):
            if type_ is None:
                type_ = message.type_
            if level is None:
                level = message.level
            message_kwargs = message.kwargs
        if type_ == self.EVENT_TYPE_LOAD:
            return self._loader_update_func(message, **message_kwargs)
        return self._status_bar_update_func(message, type_, level)

    def report_load_event(self, text, no_progress=False):
        """Report a load-related event (to rose.gtk.util.SplashScreen)."""
        event = rose.reporter.Event(text,
                                    type_=self.EVENT_TYPE_LOAD,
                                    no_progress=no_progress)
        self.report(event)


class StatusBar(gtk.VBox):

    """Generate the status bar widget."""

    def __init__(self, verbosity=rose.reporter.Reporter.DEFAULT):
        super(StatusBar, self).__init__()
        self.verbosity = verbosity
        self.num_errors = 0
        hsep = gtk.HSeparator()
        hsep.show()
        self.pack_start(hsep, expand=False, fill=False)
        hbox = gtk.HBox()
        hbox.show()
        self.pack_start(hbox, expand=False, fill=False)
        self._generate_error_widget()
        hbox.pack_start(self._error_widget, expand=False, fill=False)
        self._generate_message_widget()
        vsep_message = gtk.VSeparator()
        vsep_message.show()
        hbox.pack_start(vsep_message, expand=False, fill=False)
        hbox.pack_start(self._message_widget, expand=True, fill=True)
        self.messages = []
        self.show()

    def set_message(self, message, type_=None, level=None):
        if isinstance(message, rose.reporter.Event):
            if type_ is None:
                type_ = message.type_
            if level is None:
                level = message.level
        if level > self.verbosity:
            return
        self.messages.append((str(message), type_))
        if len(self.messages) > rose.config_editor.STATUS_BAR_MESSAGE_LIMIT:
            self.messages.pop(0)
        self._update_message_widget(str(message), type_=type_)

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
        image = gtk.gdk.image_new_from_file(icon_path)
        image.show()
        self._error_widget.pack_start(image, expand=False, fill=False)
        self._error_widget_label = gtk.Label()
        self._error_widget_label.show()
        self._error_widget.pack_start(self.error_widget_label, expand=False,
                                      fill=False)
        self._update_error_widget()

    def _generate_message_widget(self):
        # Generate the message display widget.
        self._message_widget = gtk.HBox()
        self._message_widget.show()
        self._message_widget_error_image = gtk.image_new_from_stock(
                                                     gtk.STOCK_ERROR,
                                                     gtk.ICON_SIZE_MENU)
        self._message_widget.pack_start(self._message_widget_error_image,
                                        expand=False, fill=False)
        self._message_widget_label = gtk.Label()
        self._message_widget_label.show()
        self._message_widget.pack_start(self.message_widget_label,
                                        expand=False,
                                        fill=False)

    def _update_error_widget(self):
        # Update the error display widget.
        self._error_widget_label.set_text(str(self.num_errors))
        self._error_widget.set_sensitive((self.num_errors > 0))

    def _update_message_widget(self, message_text, type_):
        # Update the message display widget.
        if type_ == rose.reporter.Reporter.TYPE_ERR:
            self._message_widget_error_image.show()
        else:
            self._message_widget_error_image.hide()
        self._message_widget_label.set_text(message_text)
