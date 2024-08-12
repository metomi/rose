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

from multiprocessing import Process
import os
import queue
import shlex
from subprocess import Popen, PIPE
import sys
import tempfile
import time
import traceback
import webbrowser

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf
from gi.repository import GLib
from gi.repository import Pango

import metomi.rose.gtk.util
import metomi.rose.resource


DIALOG_BUTTON_CLOSE = "Close"
DIALOG_LABEL_README = "README"
DIALOG_PADDING = 10
DIALOG_SUB_PADDING = 5

DIALOG_SIZE_PROCESS = (400, 100)
DIALOG_SIZE_SCROLLED_MAX = (600, 600)
DIALOG_SIZE_SCROLLED_MIN = (300, 100)

DIALOG_TEXT_SHUTDOWN_ASAP = "Shutdown ASAP."
DIALOG_TEXT_SHUTTING_DOWN = "Shutting down."
DIALOG_TEXT_UNCAUGHT_EXCEPTION = ("{0} has crashed. {1}" +
                                  "\n\n<b>{2}</b>: {3}\n{4}")
DIALOG_TITLE_ERROR = "Error"
DIALOG_TITLE_UNCAUGHT_EXCEPTION = "Critical error"
DIALOG_TITLE_EXTRA_INFO = "Further information"
DIALOG_TYPE_ERROR = Gtk.MessageType.ERROR
DIALOG_TYPE_INFO = Gtk.MessageType.INFO
DIALOG_TYPE_WARNING = Gtk.MessageType.WARNING


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
                 stock_id=Gtk.STOCK_EXECUTE,
                 hide_progress=False, modal=True,
                 event_queue=None):
        self.proc = None
        window = get_dialog_parent()
        self.dialog = Gtk.Dialog(buttons=(Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                                 parent=window)
        self.dialog.set_modal(modal)
        self.dialog.set_default_size(*DIALOG_SIZE_PROCESS)
        self._is_destroyed = False
        self.dialog.set_icon(self.dialog.render_icon(Gtk.STOCK_EXECUTE,
                                                     Gtk.IconSize.MENU))
        self.cmd_args = cmd_args
        self.event_queue = event_queue
        str_cmd_args = [metomi.rose.gtk.util.safe_str(a) for a in cmd_args]
        if description is not None:
            str_cmd_args = [description]
        if title is None:
            self.dialog.set_title(" ".join(str_cmd_args[0:2]))
        else:
            self.dialog.set_title(title)
        if callable(cmd_args[0]):
            self.label = Gtk.Label(label=self.DIALOG_FUNCTION_LABEL)
        else:
            self.label = Gtk.Label(label=self.DIALOG_PROCESS_LABEL)
        self.label.set_use_markup(True)
        self.label.show()
        self.image = Gtk.Image.new_from_stock(stock_id,
                                              Gtk.IconSize.DIALOG)
        self.image.show()
        image_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        image_vbox.pack_start(self.image, expand=False, fill=False, padding=0)
        image_vbox.show()
        top_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        top_hbox.pack_start(image_vbox, expand=False, fill=False,
                            padding=DIALOG_PADDING)
        top_hbox.show()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(self.label, expand=False, fill=False,
                        padding=DIALOG_PADDING)
        hbox.show()
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_vbox.show()
        main_vbox.pack_start(hbox, expand=False, fill=False,
                             padding=DIALOG_SUB_PADDING)

        cmd_string = str_cmd_args[0]
        if str_cmd_args[1:]:
            if callable(cmd_args[0]):
                cmd_string += "(" + " ".join(str_cmd_args[1:]) + ")"
            else:
                cmd_string += " " + " ".join(str_cmd_args[1:])
        self.cmd_label = Gtk.Label()
        self.cmd_label.set_markup("<b>" + cmd_string + "</b>")
        self.cmd_label.show()
        cmd_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        cmd_hbox.pack_start(self.cmd_label, expand=False, fill=False,
                            padding=DIALOG_PADDING)
        cmd_hbox.show()
        main_vbox.pack_start(cmd_hbox, expand=False, fill=True,
                             padding=DIALOG_SUB_PADDING)
        # self.dialog.set_modal(True)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.1)
        self.progress_bar.show()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(self.progress_bar, expand=True, fill=True,
                        padding=DIALOG_PADDING)
        hbox.show()
        main_vbox.pack_start(hbox, expand=False, fill=False,
                             padding=DIALOG_SUB_PADDING)
        top_hbox.pack_start(main_vbox, expand=True, fill=True,
                            padding=DIALOG_PADDING)
        if self.event_queue is None:
            self.dialog.vbox.pack_start(top_hbox, expand=True, fill=True, padding=0)
        else:
            text_view_scroll = Gtk.ScrolledWindow()
            text_view_scroll.set_policy(Gtk.PolicyType.NEVER,
                                        Gtk.PolicyType.AUTOMATIC)
            text_view_scroll.show()
            text_view = Gtk.TextView()
            text_view.show()
            self.text_buffer = text_view.get_buffer()
            self.text_tag = self.text_buffer.create_tag()
            self.text_tag.set_property("scale", Pango.SCALE_SMALL)
            text_view.connect('size-allocate', self._handle_scroll_text_view)
            text_view_scroll.add(text_view)
            text_expander = Gtk.Expander(self.DIALOG_LOG_LABEL)
            text_expander.set_spacing(DIALOG_SUB_PADDING)
            text_expander.add(text_view_scroll)
            text_expander.show()
            top_pane = Gtk.VPaned()
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
            if isinstance(child, Gtk.HSeparator):
                child.hide()
        self.dialog.show()

    def run(self):
        """Launch dialog in child process."""
        stdout = tempfile.TemporaryFile()
        stderr = tempfile.TemporaryFile()
        self.proc = Process(
            target=_sep_process, args=[self.cmd_args, stdout, stderr])
        self.proc.start()
        self.dialog.connect("destroy", self._handle_dialog_process_destroy)
        while self.proc.is_alive():
            self.progress_bar.pulse()
            if self.event_queue is not None:
                while True:
                    try:
                        new_text = self.event_queue.get(False)
                    except queue.Empty:
                        break
                    end = self.text_buffer.get_end_iter()
                    self.text_buffer.insert_with_tags(end, new_text,
                                                      self.text_tag)
            while Gtk.events_pending():
                Gtk.main_iteration()
            time.sleep(0.1)
        stdout.seek(0)
        stderr.seek(0)
        if self.proc.exitcode != 0:
            if self._is_destroyed:
                return self.proc.exitcode
            else:
                self.image.set_from_stock(Gtk.STOCK_DIALOG_ERROR,
                                          Gtk.IconSize.DIALOG)
                self.label.hide()
                self.progress_bar.hide()
                self.cmd_label.set_markup(
                    "<b>" + metomi.rose.gtk.util.safe_str(stderr.read()) + "</b>")
                self.ok_button.show()
                for child in self.dialog.vbox.get_children():
                    if isinstance(child, Gtk.HSeparator):
                        child.show()
                self.dialog.run()
        self.dialog.destroy()
        return self.proc.exitcode

    def _handle_dialog_process_destroy(self, dialog):
        if self.proc.is_alive():
            self.proc.terminate()
        self._is_destroyed = True
        return False

    def _handle_scroll_text_view(self, text_view, event=None):
        """Scroll the parent scrolled window to the bottom."""
        vadj = text_view.get_parent().get_vadjustment()
        if vadj.upper > vadj.lower + vadj.page_size:
            vadj.set_value(vadj.upper - 0.95 * vadj.page_size)


def _sep_process(*args):
    sys.exit(_process(*args))


def _process(cmd_args, stdout=sys.stdout, stderr=sys.stderr):
    if callable(cmd_args[0]):
        func = cmd_args.pop(0)
        try:
            func(*cmd_args)
        except Exception as exc:
            stderr.write(type(exc).__name__ + ": " + str(exc) + "\n")
            stderr.read()
            return 1
        return 0
    proc = Popen(cmd_args, stdout=PIPE, stderr=PIPE)
    for line in iter(proc.stdout.readline, ""):
        stdout.write(line)
    for line in iter(proc.stderr.readline, ""):
        stderr.write(line)
    proc.wait()
    stdout.read()  # Magically keep it alive!?
    stderr.read()
    return proc.poll()


def run_about_dialog(name=None, copyright_=None,
                     logo_path=None, website=None):
    parent_window = get_dialog_parent()
    about_dialog = Gtk.AboutDialog()
    about_dialog.set_transient_for(parent_window)
    about_dialog.set_name(name)
    licence_path = os.path.join(os.getenv("ROSE_HOME"),
                                metomi.rose.FILEPATH_README)
    about_dialog.set_license(open(licence_path, "r").read())
    about_dialog.set_copyright(copyright_)
    resource_loc = metomi.rose.resource.ResourceLocator(paths=sys.path)
    logo_path = resource_loc.locate(logo_path)
    about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(logo_path))
    about_dialog.set_website(website)
    Gtk.about_dialog_set_url_hook(
        lambda u, v, w: webbrowser.open(w), about_dialog.get_website())
    about_dialog.run()
    about_dialog.destroy()


def run_command_arg_dialog(cmd_name, help_text, run_hook):
    """Launch a dialog to get extra arguments for a command."""
    checker_function = lambda t: True
    dialog, container, name_entry = get_naming_dialog(cmd_name,
                                                      checker_function)
    dialog.set_title(cmd_name)
    help_label = Gtk.stock_lookup(Gtk.STOCK_HELP)[1].strip("_")
    help_button = metomi.rose.gtk.util.CustomButton(
        stock_id=Gtk.STOCK_HELP,
        label=help_label,
        size=Gtk.IconSize.LARGE_TOOLBAR)
    help_button.connect(
        "clicked",
        lambda b: run_scrolled_dialog(help_text, title=help_label))
    help_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    help_hbox.pack_start(help_button, expand=False, fill=False, padding=0)
    help_hbox.show()
    container.pack_end(help_hbox, expand=False, fill=False, padding=0)
    name_entry.grab_focus()
    dialog.connect("response", _handle_command_arg_response, run_hook,
                   name_entry)
    dialog.set_modal(False)
    dialog.show()


def _handle_command_arg_response(dialog, response, run_hook, entry):
    text = entry.get_text()
    dialog.destroy()
    if response == Gtk.ResponseType.ACCEPT:
        run_hook(shlex.split(text))


def run_dialog(dialog_type, text, title=None, modal=True,
               cancel=False, extra_text=None):
    """Run a simple dialog with an 'OK' button and some text."""
    parent_window = get_dialog_parent()
    dialog = Gtk.Dialog(parent=parent_window)
    if parent_window is None:
        dialog.set_icon(metomi.rose.gtk.util.get_icon())
    if cancel:
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    if extra_text:
        info_button = Gtk.Button(stock=Gtk.STOCK_INFO)
        info_button.show()
        info_title = DIALOG_TITLE_EXTRA_INFO
        info_button.connect(
            "clicked",
            lambda b: run_scrolled_dialog(extra_text, title=info_title))
        dialog.action_area.pack_start(info_button, expand=False, fill=False)
    ok_button = dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
    if dialog_type == Gtk.MessageType.INFO:
        stock_id = Gtk.STOCK_DIALOG_INFO
    elif dialog_type == Gtk.MessageType.WARNING:
        stock_id = Gtk.STOCK_DIALOG_WARNING
    elif dialog_type == Gtk.MessageType.QUESTION:
        stock_id = Gtk.STOCK_DIALOG_QUESTION
    elif dialog_type == Gtk.MessageType.ERROR:
        stock_id = Gtk.STOCK_DIALOG_ERROR
    else:
        stock_id = None

    if stock_id is not None:
        dialog.image = Gtk.Image.new_from_stock(stock_id, Gtk.IconSize.DIALOG)
        dialog.image.show()

    dialog.label = Gtk.Label(label=text)
    try:
        # could just keep set_text and set_markup?
        Pango.parse_markup(text, len(text), "0")
    except GLib.GError:
        try:
            dialog.label.set_markup(metomi.rose.gtk.util.safe_str(text))
        except Exception:
            dialog.label.set_text(text)
    else:
        dialog.label.set_markup(text)
    dialog.label.show()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

    if stock_id is not None:
        image_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        image_vbox.pack_start(dialog.image, expand=False, fill=False,
                              padding=DIALOG_PADDING)
        image_vbox.show()
        hbox.pack_start(image_vbox, expand=False, fill=False,
                        padding=metomi.rose.config_editor.SPACING_PAGE)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_border_width(0)
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    vbox.pack_start(dialog.label, expand=True, fill=True, padding=0)
    vbox.show()
    scrolled_window.add_with_viewport(vbox)
    scrolled_window.get_child().set_shadow_type(Gtk.ShadowType.NONE)
    scrolled_window.show()
    hbox.pack_start(scrolled_window, expand=True, fill=True,
                    padding=metomi.rose.config_editor.SPACING_PAGE)
    hbox.show()
    dialog.vbox.pack_end(hbox, expand=True, fill=True, padding=0)

    if "\n" in text:
        dialog.label.set_line_wrap(False)
    dialog.set_resizable(True)
    dialog.set_modal(modal)
    if title is not None:
        dialog.set_title(title)

    _configure_scroll(dialog, scrolled_window)
    ok_button.grab_focus()
    if modal or cancel:
        dialog.show()
        response = dialog.run()
        dialog.destroy()
        return (response == Gtk.ResponseType.OK)
    else:
        ok_button.connect("clicked", lambda b: dialog.destroy())
        dialog.show()


def run_exception_dialog(exception):
    """Run a dialog displaying an exception."""
    text = type(exception).__name__ + ": " + str(exception)
    return run_dialog(DIALOG_TYPE_ERROR, text, DIALOG_TITLE_ERROR)


def run_hyperlink_dialog(stock_id=None, text="", title=None,
                         search_func=lambda i: False):
    """Run a dialog with inserted hyperlinks."""
    parent_window = get_dialog_parent()
    dialog = Gtk.Window()
    dialog.set_transient_for(parent_window)
    dialog.set_type_hint(Gdk.WindowTypeHint.DIALOG)
    dialog.set_title(title)
    dialog.set_modal(False)
    top_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    top_vbox.show()
    main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=DIALOG_PADDING)
    main_hbox.show()
    # Insert the image
    image_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    image_vbox.show()
    image = Gtk.Image.new_from_stock(stock_id,
                                     size=Gtk.IconSize.DIALOG)
    image.show()
    image_vbox.pack_start(image, expand=False, fill=False,
                          padding=DIALOG_PADDING)
    main_hbox.pack_start(image_vbox, expand=False, fill=False,
                         padding=DIALOG_PADDING)
    # Apply the text
    message_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    message_vbox.show()
    label = metomi.rose.gtk.util.get_hyperlink_label(text, search_func)
    message_vbox.pack_start(label, expand=True, fill=True,
                            padding=DIALOG_PADDING)
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_border_width(DIALOG_PADDING)
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
    scrolled_window.add_with_viewport(message_vbox)
    scrolled_window.get_child().set_shadow_type(Gtk.ShadowType.NONE)
    scrolled_window.show()
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    vbox.pack_start(scrolled_window, expand=True, fill=True, padding=0)
    vbox.show()
    main_hbox.pack_start(vbox, expand=True, fill=True, padding=0)
    top_vbox.pack_start(main_hbox, expand=True, fill=True, padding=0)
    # Insert the button
    button_box = Gtk.Box(spacing=DIALOG_PADDING)
    button_box.show()
    button = metomi.rose.gtk.util.CustomButton(label=DIALOG_BUTTON_CLOSE,
                                        size=Gtk.IconSize.LARGE_TOOLBAR,
                                        stock_id=Gtk.STOCK_CLOSE)
    button.connect("clicked", lambda b: dialog.destroy())
    button_box.pack_end(button, expand=False, fill=False,
                        padding=DIALOG_PADDING)
    top_vbox.pack_end(button_box, expand=False, fill=False,
                      padding=DIALOG_PADDING)
    dialog.add(top_vbox)
    if "\n" in text:
        label.set_line_wrap(False)
    dialog.set_resizable(True)
    _configure_scroll(dialog, scrolled_window)
    dialog.show()
    label.set_selectable(True)
    button.grab_focus()


def run_scrolled_dialog(text, title=None):
    """Run a dialog intended for the display of a large amount of text."""
    parent_window = get_dialog_parent()
    window = Gtk.Window()
    window.set_transient_for(parent_window)
    window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
    window.set_border_width(DIALOG_SUB_PADDING)
    window.set_default_size(*DIALOG_SIZE_SCROLLED_MIN)
    if title is not None:
        window.set_title(title)
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.show()
    label = Gtk.Label()
    try:
        Pango.parse_markup(text, len(text), "0")
    except GLib.GError:
        label.set_text(text)
    else:
        label.set_markup(text)
    label.show()
    filler_eb = Gtk.EventBox()
    filler_eb.show()
    label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    label_box.pack_start(label, expand=False, fill=False)
    label_box.pack_start(filler_eb, expand=True, fill=True)
    label_box.show()
    width, height = label.size_request()
    max_width, max_height = DIALOG_SIZE_SCROLLED_MAX
    width = min([max_width, width]) + 2 * DIALOG_PADDING
    height = min([max_height, height]) + 2 * DIALOG_PADDING
    scrolled.add_with_viewport(label_box)
    scrolled.get_child().set_shadow_type(Gtk.ShadowType.NONE)
    scrolled.set_size_request(width, height)
    button = Gtk.Button(stock=Gtk.STOCK_OK)
    button.connect("clicked", lambda b: window.destroy())
    button.show()
    button.grab_focus()
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    button_box.pack_end(button, expand=False, fill=False, padding=0)
    button_box.show()
    main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=DIALOG_SUB_PADDING)
    main_vbox.pack_start(scrolled, expand=True, fill=True, padding=0)
    main_vbox.pack_end(button_box, expand=False, fill=False, padding=0)
    main_vbox.show()
    window.add(main_vbox)
    window.show()
    label.set_selectable(True)
    return False


def get_naming_dialog(label, checker, ok_tip=None,
                      err_tip=None):
    """Return a dialog, container, and entry for entering a name."""
    button_list = (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                   Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT)
    parent_window = get_dialog_parent()
    dialog = Gtk.Dialog(buttons=button_list)
    dialog.set_transient_for(parent_window)
    dialog.set_modal(True)
    ok_button = dialog.action_area.get_children()[0]
    main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    name_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    name_label = Gtk.Label()
    name_label.set_text(label)
    name_label.show()
    name_entry = Gtk.Entry()
    name_entry.set_tooltip_text(ok_tip)
    name_entry.connect("changed", _name_checker, checker, ok_button,
                       ok_tip, err_tip)
    name_entry.connect(
        "activate", lambda b: dialog.response(Gtk.ResponseType.ACCEPT))
    name_entry.show()
    name_hbox.pack_start(name_label, expand=False, fill=False,
                         padding=DIALOG_SUB_PADDING)
    name_hbox.pack_start(name_entry, expand=False, fill=True,
                         padding=DIALOG_SUB_PADDING)
    name_hbox.show()
    main_vbox.pack_start(name_hbox, expand=False, fill=True,
                         padding=DIALOG_PADDING)
    main_vbox.show()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    hbox.pack_start(main_vbox, expand=False, fill=True,
                    padding=DIALOG_PADDING)
    hbox.show()
    dialog.vbox.pack_start(hbox, expand=False, fill=True,
                           padding=DIALOG_PADDING)
    return dialog, main_vbox, name_entry


def _name_checker(entry, checker, ok_button, ok_tip, err_tip):
    good_colour = ok_button.style.text[Gtk.StateType.NORMAL]
    bad_colour = metomi.rose.gtk.util.color_parse(
        metomi.rose.config_editor.COLOUR_VARIABLE_TEXT_ERROR)
    name = entry.get_text()
    if checker(name):
        entry.modify_text(Gtk.StateType.NORMAL, good_colour)
        entry.set_tooltip_text(ok_tip)
        ok_button.set_sensitive(True)
    else:
        entry.modify_text(Gtk.StateType.NORMAL, bad_colour)
        entry.set_tooltip_text(err_tip)
        ok_button.set_sensitive(False)
    return False


def run_choices_dialog(text, choices, title=None):
    """Run a dialog for choosing between a set of options."""
    parent_window = get_dialog_parent()
    dialog = Gtk.Dialog(title,
                        buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                 Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                        parent=parent_window)
    dialog.set_border_width(DIALOG_SUB_PADDING)
    label = Gtk.Label()
    try:
        Pango.parse_markup(text, len(text), "0")
    except GLib.GError:
        label.set_text(text)
    else:
        label.set_markup(text)
    dialog.vbox.set_spacing(DIALOG_SUB_PADDING)
    dialog.vbox.pack_start(label, expand=False, fill=False, padding=0)
    if len(choices) < 5:
        for i, choice in enumerate(choices):
            group = None
            if i > 0:
                group = radio_button
            if i == 1:
                radio_button.set_active(True)
            radio_button = Gtk.RadioButton(group,
                                           label=choice,
                                           use_underline=False)
            dialog.vbox.pack_start(radio_button, expand=False, fill=False, padding=0)
        getter = (lambda:
                  [b.get_label() for b in radio_button.get_group()
                   if b.get_active()].pop())
    else:
        combo_box = Gtk.ComboBoxText()
        for choice in choices:
            combo_box.append_text(choice)
        combo_box.set_active(0)
        dialog.vbox.pack_start(combo_box, expand=False, fill=False, padding=0)
        getter = lambda: choices[combo_box.get_active()]
    dialog.show_all()
    response = dialog.run()
    if response == Gtk.ResponseType.ACCEPT:
        choice = getter()
        dialog.destroy()
        return choice
    dialog.destroy()
    return None


def run_edit_dialog(text, finish_hook=None, title=None):
    """Run a dialog for editing some text."""
    parent_window = get_dialog_parent()
    dialog = Gtk.Dialog(title,
                        buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                 Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                        parent=parent_window)

    dialog.set_border_width(DIALOG_SUB_PADDING)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_border_width(DIALOG_SUB_PADDING)
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

    text_buffer = Gtk.TextBuffer()
    text_buffer.set_text(text)
    text_view = Gtk.TextView()
    text_view.set_editable(True)
    text_view.set_wrap_mode(Gtk.WrapMode.NONE)
    text_view.set_buffer(text_buffer)
    text_view.show()

    scrolled_window.add_with_viewport(text_view)
    scrolled_window.show()

    dialog.vbox.pack_start(scrolled_window, expand=True, fill=True,
                           padding=0)
    get_text = lambda: text_buffer.get_text(text_buffer.get_start_iter(),
                                            text_buffer.get_end_iter())

    max_size = metomi.rose.config_editor.SIZE_MACRO_DIALOG_MAX
    # defines the minimum acceptable size for the edit dialog
    min_size = DIALOG_SIZE_PROCESS

    # hacky solution to get "true" size for dialog
    dialog.show()
    start_size = dialog.size_request()
    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    end_size = dialog.size_request()
    my_size = (max([start_size[0], end_size[0], min_size[0]]) + 20,
               max([start_size[1], end_size[1], min_size[1]]) + 20)
    new_size = [-1, -1]
    for i in [0, 1]:
        new_size[i] = min([my_size[i], max_size[i]])
    dialog.set_size_request(*new_size)

    if finish_hook is None:
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            text = get_text().strip()
            dialog.destroy()
            return text
        dialog.destroy()
    else:
        finish_func = lambda: finish_hook(get_text().strip())
        dialog.connect("response", _handle_edit_dialog_response, finish_func)
        dialog.show()


def _handle_edit_dialog_response(dialog, response, finish_hook):
    if response == Gtk.ResponseType.ACCEPT:
        finish_hook()
    dialog.destroy()


def get_dialog_parent():
    """Find the currently active window, if any, and reparent dialog."""
    ok_windows = []
    max_size = -1
    # not sure if this window change is correct
    for window in Gtk.Window.list_toplevels():
        if window.get_title() is not None and window.get_toplevel() == window:
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


def set_exception_hook_dialog(keep_alive=False):
    """Set a dialog to run once an uncaught exception occurs."""
    prev_hook = sys.excepthook
    sys.excepthook = (lambda c, i, t:
                      _run_exception_dialog(c, i, t, prev_hook,
                                            keep_alive))


def _configure_scroll(dialog, scrolled_window):
    """Set scroll window size and scroll policy."""
    # make sure the dialog size doesn't exceed the maximum - if so change it
    max_size = metomi.rose.config_editor.SIZE_MACRO_DIALOG_MAX
    my_size = dialog.get_size()
    new_size = [-1, -1]
    for i, scrollbar_cls in [(0, Gtk.Scrollbar.new(orientation=Gtk.Orientation.VERTICAL)), (1, Gtk.Scrollbar.new(orientation=Gtk.Orientation.HORIZONTAL))]:
        new_size[i] = min(my_size[i], max_size[i])
        if new_size[i] < max_size[i]:
            # Factor in existence of a scrollbar in the other dimension.
            # For horizontal dimension, add width of vertical scroll bar + 2
            # For vertical dimension, add height of horizontal scroll bar + 2
            # What is the value in rose 2019? - here it is zero on load.
            new_size[i] += getattr(
                scrollbar_cls.get_preferred_size().natural_size,
                ["width", "height"][i]
            ) + 2
    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    dialog.set_default_size(*new_size)


def _run_exception_dialog(exc_class, exc_inst, tback, hook, keep_alive):
    # Handle an uncaught exception.
    if exc_class == KeyboardInterrupt:
        return False
    hook(exc_class, exc_inst, tback)
    program_name = metomi.rose.resource.ResourceLocator().get_util_name()
    tback_text = metomi.rose.gtk.util.safe_str("".join(traceback.format_tb(tback)))
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
            Gtk.main_quit()
        except RuntimeError:
            pass
