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

import copy
import difflib
import re

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import rose.config_editor.keywidget
import rose.config_editor.menuwidget
import rose.config_editor.valuewidget
import rose.config_editor.valuewidget.array.row as row
import rose.config_editor.valuewidget.source
import rose.config_editor.util
import rose.gtk.dialog
import rose.gtk.util
import rose.reporter
import rose.resource


class VariableWidget(object):

    """This class generates a set of widgets representing the variable.

    The set of widgets generated depends on the variable metadata, if any.
    Altering values using the widgets will alter the variable object as part
    of the internal data model.

    """

    def __init__(self, variable, var_ops, is_ghost=False, show_modes=None,
                 hide_keywidget_subtext=False):
        self.variable = variable
        self.key = variable.name
        self.value = variable.value
        self.meta = variable.metadata
        self.is_ghost = is_ghost
        self.var_ops = var_ops
        if show_modes is None:
            show_modes = {}
        self.show_modes = show_modes
        self.insensitive_colour = Gtk.Style().bg[0]
        self.bad_colour = rose.gtk.util.color_parse(
            rose.config_editor.COLOUR_VARIABLE_TEXT_ERROR)
        self.hidden_colour = rose.gtk.util.color_parse(
            rose.config_editor.COLOUR_VARIABLE_TEXT_IRRELEVANT)
        self.keywidget = self.get_keywidget(variable, show_modes)
        self.generate_valuewidget(variable)
        self.is_inconsistent = False
        if 'type' in variable.error:
            self._set_inconsistent(self.valuewidget, variable)
        self.errors = list(variable.error.keys())
        self.menuwidget = self.get_menuwidget(variable)
        self.generate_labelwidget()
        self.generate_contentwidget()
        self.yoptions = Gtk.AttachOptions.FILL
        self.force_signal_ids = []
        self.is_modified = False
        for child_widget in self.get_children():
            setattr(child_widget, 'get_parent', lambda: self)
        self.trigger_ignored = lambda v, b: b
        self.get_parent = lambda: None
        self.is_ignored = False
        self.set_ignored()
        self.update_status()

    def get_keywidget(self, variable, show_modes):
        """Creates the keywidget attribute, based on the variable name.

        Loads 'tooltips' or hover-over text based on the variable metadata.

        """
        widget = rose.config_editor.keywidget.KeyWidget(
            variable, self.var_ops, self.launch_help, self.update_status,
            show_modes
        )
        widget.show()
        return widget

    def generate_labelwidget(self):
        """Creates the label widget, a composite of key and menu widgets."""
        self.labelwidget = Gtk.VBox()
        self.labelwidget.show()
        self.labelwidget.set_ignored = self.keywidget.set_ignored
        menu_offset = self.menuwidget.size_request()[1] / 2
        key_offset = self.keywidget.get_centre_height() / 2
        menu_vbox = Gtk.VBox()
        menu_vbox.pack_start(self.menuwidget, expand=False, fill=False,
                             padding=max([(key_offset - menu_offset), 0]))
        menu_vbox.show()
        key_vbox = Gtk.VBox()
        key_vbox.pack_start(self.keywidget, expand=False, fill=False,
                            padding=max([(menu_offset - key_offset) / 2, 0]))
        key_vbox.show()
        label_content_hbox = Gtk.HBox()
        label_content_hbox.pack_start(menu_vbox, expand=False, fill=False)
        label_content_hbox.pack_start(key_vbox, expand=False, fill=False)
        label_content_hbox.show()
        event_box = Gtk.EventBox()
        event_box.show()
        self.labelwidget.pack_start(label_content_hbox, expand=True, fill=True)
        self.labelwidget.pack_start(event_box, expand=True, fill=True)

    def generate_contentwidget(self):
        """Create the content widget, a vbox-packed valuewidget."""
        self.contentwidget = Gtk.VBox()
        self.contentwidget.show()
        content_event_box = Gtk.EventBox()
        content_event_box.show()
        self.contentwidget.pack_start(
            self.valuewidget, expand=False, fill=False)
        self.contentwidget.pack_start(
            content_event_box, expand=True, fill=True)

    def _valuewidget_set_value(self, value):
        # This is called by a valuewidget to change the variable value.
        self.var_ops.set_var_value(self.variable, value)
        self.update_status()

    def generate_valuewidget(self, variable, override_custom=False,
                             use_this_valuewidget=None):
        """Creates the valuewidget attribute, based on value and metadata."""
        custom_arg = None
        if (variable.metadata.get("type") ==
                rose.config_editor.FILE_TYPE_NORMAL):
            use_this_valuewidget = (rose.config_editor.
                                    valuewidget.source.SourceValueWidget)
            custom_arg = self.var_ops
        set_value = self._valuewidget_set_value
        hook_object = rose.config_editor.valuewidget.ValueWidgetHook(
            rose.config_editor.false_function,
            self._get_focus)
        metadata = copy.deepcopy(variable.metadata)
        if use_this_valuewidget is not None:
            self.valuewidget = use_this_valuewidget(variable.value,
                                                    metadata,
                                                    set_value,
                                                    hook_object,
                                                    arg_str=custom_arg)
        elif (rose.config_editor.META_PROP_WIDGET in self.meta and
                not override_custom):
            w_val = self.meta[rose.config_editor.META_PROP_WIDGET]
            info = w_val.split(None, 1)
            if len(info) > 1:
                widget_path, custom_arg = info
            else:
                widget_path, custom_arg = info[0], None
            files = self.var_ops.get_ns_metadata_files(metadata["full_ns"])
            error_handler = lambda e: self.handle_bad_valuewidget(
                str(e), variable, set_value)
            widget = rose.resource.import_object(widget_path,
                                                 files,
                                                 error_handler)
            if widget is None:
                text = rose.config_editor.ERROR_IMPORT_CLASS.format(w_val)
                self.handle_bad_valuewidget(text, variable, set_value)
            try:
                self.valuewidget = widget(variable.value,
                                          metadata,
                                          set_value,
                                          hook_object,
                                          custom_arg)
            except Exception as exc:
                self.handle_bad_valuewidget(str(exc), variable, set_value)
        else:
            widget_maker = rose.config_editor.valuewidget.chooser(
                variable.value, variable.metadata,
                variable.error)
            self.valuewidget = widget_maker(variable.value,
                                            metadata, set_value,
                                            hook_object, custom_arg)
        for child in self.valuewidget.get_children():
            child.connect('focus-in-event', self.handle_focus_in)
            child.connect('focus-out-event', self.handle_focus_out)
            if hasattr(child, 'get_children'):
                for grandchild in child.get_children():
                    grandchild.connect('focus-in-event', self.handle_focus_in)
                    grandchild.connect('focus-out-event',
                                       self.handle_focus_out)
        self.valuewidget.show()

    def handle_bad_valuewidget(self, error_info, variable, set_value):
        """Handle a bad custom valuewidget import."""
        text = rose.config_editor.ERROR_IMPORT_WIDGET.format(error_info)
        rose.reporter.Reporter()(
            rose.config_editor.util.ImportWidgetError(text))
        self.generate_valuewidget(variable, override_custom=True)

    def handle_focus_in(self, widget, event):
        widget._first_colour = widget.style.base[Gtk.StateType.NORMAL]
        new_colour = rose.gtk.util.color_parse(
            rose.config_editor.COLOUR_VALUEWIDGET_BASE_SELECTED)
        widget.modify_base(Gtk.StateType.NORMAL, new_colour)

    def handle_focus_out(self, widget, event):
        if hasattr(widget, "_first_colour"):
            widget.modify_base(Gtk.StateType.NORMAL, widget._first_colour)

    def get_menuwidget(self, variable, menuclass=None):
        """Create the menuwidget attribute, an option menu button."""
        if menuclass is None:
            menuclass = rose.config_editor.menuwidget.MenuWidget
        menuwidget = menuclass(variable,
                               self.var_ops,
                               lambda: self.remove_from(self.get_parent()),
                               self.update_status,
                               self.launch_help)
        menuwidget.show()
        return menuwidget

    def insert_into(self, container, x_info=None, y_info=None,
                    no_menuwidget=False):
        """Inserts the child widgets of an instance into the 'container'.

        As PyGTK is not that introspective, we need arguments specifying where
        the correct area within the widget is - in the case of Gtk.Table
        instances, we need the number of columns and the row index.
        These arguments are generically named x_info and y_info.

        """
        if not hasattr(container, 'num_removes'):
            setattr(container, 'num_removes', 0)
        if isinstance(container, Gtk.Table):
            row_index = y_info
            key_col = 0
            container.attach(self.labelwidget,
                             key_col, key_col + 1,
                             row_index, row_index + 1,
                             xoptions=Gtk.AttachOptions.FILL,
                             yoptions=Gtk.AttachOptions.FILL)
            container.attach(self.contentwidget,
                             key_col + 1, key_col + 2,
                             row_index, row_index + 1,
                             xpadding=5,
                             xoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL,
                             yoptions=self.yoptions)
            self.valuewidget.trigger_scroll = (
                lambda b, e: self.force_scroll(b, container))
            setattr(self, 'get_parent', lambda: container)
        elif isinstance(container, Gtk.VBox):
            container.pack_start(self.labelwidget, expand=False, fill=True,
                                 padding=5)
            container.pack_start(self.contentwidget, expand=True, fill=True,
                                 padding=10)
            self.valuewidget.trigger_scroll = (
                lambda b, e: self.force_scroll(b, container))
            setattr(self, 'get_parent', lambda: container)

        return container

    def force_scroll(self, widget=None, container=None):
        """Adjusts a scrolled window to display the correct widget."""
        y_coordinate = None
        if widget is not None:
            y_coordinate = widget.get_allocation().y
        scroll_container = container.get_parent()
        if scroll_container is None:
            return False
        while not isinstance(scroll_container, Gtk.ScrolledWindow):
            scroll_container = scroll_container.get_parent()
        vadj = scroll_container.get_vadjustment()
        if vadj.upper == 1.0 or y_coordinate == -1:
            if not self.force_signal_ids:
                self.force_signal_ids.append(vadj.connect_after(
                    'changed',
                    lambda a: self.force_scroll(widget, container)))
        else:
            for handler_id in self.force_signal_ids:
                vadj.handler_block(handler_id)
            self.force_signal_ids = []
            vadj.connect('changed', rose.config_editor.false_function)
        if y_coordinate is None:
            vadj.upper = vadj.upper + 0.08 * vadj.page_size
            vadj.set_value(vadj.upper - vadj.page_size)
            return False
        if y_coordinate == -1:  # Bad allocation, don't scroll
            return False
        if not vadj.value < y_coordinate < vadj.value + 0.95 * vadj.page_size:
            vadj.set_value(min(y_coordinate, vadj.upper - vadj.page_size))
        return False

    def remove_from(self, container):
        """Removes the child widgets of an instance from the 'container'."""
        container.num_removes += 1
        self.var_ops.remove_var(self.variable)
        if isinstance(container, Gtk.Table):
            for widget_child in self.get_children():
                for child in container.get_children():
                    if child == widget_child:
                        container.remove(widget_child)
                widget_child.destroy()
        return container

    def get_children(self):
        """Method that returns child widgets - as in some gtk Objects."""
        return [self.labelwidget, self.contentwidget]

    def hide(self):
        for widget in self.get_children():
            widget.hide()

    def show(self):
        for widget in self.get_children():
            widget.show()

    def set_show_mode(self, show_mode, should_show_mode):
        """Sets or unsets special displays for a variable."""
        self.keywidget.set_show_mode(show_mode, should_show_mode)

    def set_ignored(self):
        """Sets or unsets a custom ignored state for the widgets."""
        ign_map = self.variable.ignored_reason
        self.keywidget.set_ignored()
        if ign_map != {}:
            # Technically ignored, but could just be ignored by section.
            self.is_ignored = True
            if "'Ignore'" not in self.menuwidget.option_ui:
                self.menuwidget.old_option_ui = self.menuwidget.option_ui
                self.menuwidget.old_actions = self.menuwidget.actions
            if list(ign_map.keys()) == [rose.variable.IGNORED_BY_SECTION]:
                # Not ignored in itself, so give Ignore option.
                if "'Enable'" in self.menuwidget.option_ui:
                    self.menuwidget.option_ui = re.sub(
                        "<menuitem action='Enable'/>",
                        r"<menuitem action='Ignore'/>",
                        self.menuwidget.option_ui)
            else:
                # Ignored in itself, so needs Enable option.
                self.menuwidget.option_ui = re.sub(
                    "<menuitem action='Ignore'/>",
                    r"<menuitem action='Enable'/>",
                    self.menuwidget.option_ui)
            self.update_status()
            self.set_sensitive(False)
        else:
            # Enabled.
            self.is_ignored = False
            if "'Enable'" in self.menuwidget.option_ui:
                self.menuwidget.option_ui = re.sub(
                    "<menuitem action='Enable'/>",
                    r"<menuitem action='Ignore'/>",
                    self.menuwidget.option_ui)
            self.update_status()
            if not self.is_ghost:
                self.set_sensitive(True)

    def update_status(self):
        """Handles variable modified status."""
        self.set_modified(self.var_ops.is_var_modified(self.variable))
        self.keywidget.update_comment_display()

    def set_modified(self, is_modified=True):
        """Applies or unsets a custom 'modified' state for the widgets."""
        if is_modified == self.is_modified:
            return False
        self.is_modified = is_modified
        self.keywidget.set_modified(is_modified)
        if not is_modified and isinstance(self.keywidget.entry, Gtk.Entry):
            # This variable should now be displayed as a normal variable.
            self.valuewidget.trigger_refresh(self.variable.metadata['id'])

    def set_sensitive(self, is_sensitive=True):
        """Sets whether the widgets are grayed-out or 'insensitive'."""
        for widget in [self.keywidget, self.valuewidget]:
            widget.set_sensitive(is_sensitive)
        return False

    def grab_focus(self, focus_container=None, scroll_bottom=False,
                   index=None):
        """Method similar to Gtk.Widget - get the keyboard focus."""
        if hasattr(self, 'valuewidget'):
            self.valuewidget.grab_focus()
            if (index is not None and
                    hasattr(self.valuewidget, 'set_focus_index')):
                self.valuewidget.set_focus_index(index)
            for child in self.valuewidget.get_children():
                if (Gtk.SENSITIVE & child.flags() and
                        Gtk.PARENT_SENSITIVE & child.flags()):
                    break
            else:
                if hasattr(self, 'menuwidget'):
                    self.menuwidget.get_children()[0].grab_focus()
            if scroll_bottom and focus_container is not None:
                self.force_scroll(None, container=focus_container)
        if hasattr(self, 'keywidget') and self.key == '':
            self.keywidget.grab_focus()
        return False

    def get_focus_index(self):
        """Get the current cursor position in the variable value string."""
        if (hasattr(self, "valuewidget") and
                hasattr(self.valuewidget, "get_focus_index")):
            return self.valuewidget.get_focus_index()
        diff = difflib.SequenceMatcher(None,
                                       self.variable.old_value,
                                       self.variable.value)
        # Return all end-of-block indicies for changed blocks
        indicies = [x[4] for x in diff.get_opcodes() if x[0] != 'equal']
        if not indicies:
            return None
        return indicies[-1]

    def launch_help(self, url_mode=False):
        """Launch a help dialog or a URL in a web browser."""
        if url_mode:
            return self.var_ops.launch_url(self.variable)
        if rose.META_PROP_HELP not in self.meta:
            return
        help_text = None
        if self.show_modes.get(
                rose.config_editor.SHOW_MODE_CUSTOM_HELP):
            format_string = rose.config_editor.CUSTOM_FORMAT_HELP
            help_text = rose.variable.expand_format_string(
                format_string, self.variable)
        if help_text is None:
            help_text = self.meta[rose.META_PROP_HELP]
        self._launch_help_dialog(help_text)

    def _launch_help_dialog(self, help_text):
        """Launch a scrollable dialog for this variable's help text."""
        title = rose.config_editor.DIALOG_HELP_TITLE.format(
            self.variable.metadata["id"])
        ns = self.variable.metadata["full_ns"]
        search_function = lambda i: self.var_ops.search_for_var(ns, i)
        rose.gtk.dialog.run_hyperlink_dialog(
            Gtk.STOCK_DIALOG_INFO, help_text, title, search_function)
        return False

    def _set_inconsistent(self, valuewidget, variable):
        valuewidget.modify_base(Gtk.StateType.NORMAL, self.bad_colour)
        self.is_inconsistent = True
        widget_list = valuewidget.get_children()
        while widget_list:
            widget = widget_list.pop()
            widget.modify_text(Gtk.StateType.NORMAL, self.bad_colour)
            if hasattr(widget, 'set_inconsistent'):
                widget.set_inconsistent(True)
            if isinstance(widget, Gtk.RadioButton):
                widget.set_active(False)
            if (hasattr(widget, 'get_group') and
                    hasattr(widget.get_group(), 'set_inconsistent')):
                widget.get_group().set_inconsistent(True)
            if isinstance(widget, Gtk.Entry):
                widget.modify_fg(Gtk.StateType.NORMAL, self.bad_colour)
            if isinstance(widget, Gtk.SpinButton):
                try:
                    v_value = float(variable.value)
                    w_value = float(widget.get_value())
                except (TypeError, ValueError):
                    widget.modify_text(Gtk.StateType.NORMAL, self.hidden_colour)
                else:
                    if w_value != v_value:
                        widget.modify_text(Gtk.StateType.NORMAL,
                                           self.hidden_colour)
            if hasattr(widget, 'get_children'):
                widget_list.extend(widget.get_children())
            elif hasattr(widget, 'get_child'):
                widget_list.append(widget.get_child())

    def _set_consistent(self, valuewidget, variable):
        normal_style = Gtk.Style()
        normal_base = normal_style.base[Gtk.StateType.NORMAL]
        normal_fg = normal_style.fg[Gtk.StateType.NORMAL]
        normal_text = normal_style.text[Gtk.StateType.NORMAL]
        valuewidget.modify_base(Gtk.StateType.NORMAL, normal_base)
        self.is_inconsistent = True
        for widget in valuewidget.get_children():
            widget.modify_text(Gtk.StateType.NORMAL, normal_text)
            if hasattr(widget, 'set_inconsistent'):
                widget.set_inconsistent(False)
            if isinstance(widget, Gtk.Entry):
                widget.modify_fg(Gtk.StateType.NORMAL, normal_fg)
            if (hasattr(widget, 'get_group') and
                    hasattr(widget.get_group(), 'set_inconsistent')):
                widget.get_group().set_inconsistent(False)

    def _get_focus(self, widget_for_focus):
        widget_for_focus.grab_focus()
        self.valuewidget.trigger_scroll(widget_for_focus, None)
        if isinstance(widget_for_focus, Gtk.Entry):
            text_length = len(widget_for_focus.get_text())
            if text_length > 0:
                widget_for_focus.set_position(text_length)
            widget_for_focus.select_region(text_length,
                                           text_length)
        return False

    def needs_type_error_refresh(self):
        """Check if self needs to be re-created on 'type' error."""
        if hasattr(self.valuewidget, "handle_type_error"):
            return False
        return True

    def type_error_refresh(self, variable):
        """Handle a type error."""
        if rose.META_PROP_TYPE in variable.error:
            self._set_inconsistent(self.valuewidget, variable)
        else:
            self._set_consistent(self.valuewidget, variable)
        self.variable = variable
        self.errors = list(variable.error.keys())
        self.valuewidget.handle_type_error(rose.META_PROP_TYPE in self.errors)
        self.menuwidget.refresh(variable)
        self.keywidget.refresh(variable)


class RowVariableWidget(VariableWidget):

    """This class generates a set of widgets for use as a row in a table."""

    def __init__(self, *args, **kwargs):
        self.length = kwargs.pop("length")
        super(RowVariableWidget, self).__init__(*args, **kwargs)

    def generate_valuewidget(self, variable, override_custom=False):
        """Creates the valuewidget attribute, based on value and metadata."""
        if (rose.META_PROP_LENGTH in variable.metadata or
                isinstance(variable.metadata.get(rose.META_PROP_TYPE), list)):
            use_this_valuewidget = self.make_row_valuewidget
        else:
            use_this_valuewidget = None
        super(RowVariableWidget, self).generate_valuewidget(
            variable, override_custom=override_custom,
            use_this_valuewidget=use_this_valuewidget)

    def make_row_valuewidget(self, *args, **kwargs):
        kwargs.update({"arg_str": str(self.length)})
        return row.RowArrayValueWidget(*args, **kwargs)
