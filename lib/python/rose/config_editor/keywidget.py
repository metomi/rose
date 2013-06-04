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

import re

import pango
import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor
import rose.variable


class KeyWidget(gtk.VBox):

    """This class generates a label or entry box for a variable name."""

    FLAG_ICON_MAP = {
             rose.config_editor.FLAG_TYPE_DEFAULT:
                  gtk.STOCK_INFO,
             rose.config_editor.FLAG_TYPE_ERROR:
                  gtk.STOCK_DIALOG_WARNING,
             rose.config_editor.FLAG_TYPE_FIXED:
                  gtk.STOCK_DIALOG_AUTHENTICATION,
             rose.config_editor.FLAG_TYPE_OPT_CONF:
                  gtk.STOCK_INDEX,
             rose.config_editor.FLAG_TYPE_OPTIONAL:
                  gtk.STOCK_ABOUT,
             rose.config_editor.FLAG_TYPE_NO_META:
                  gtk.STOCK_DIALOG_QUESTION}

    MODIFIED_COLOUR = gtk.gdk.color_parse(
                              rose.config_editor.COLOUR_VARIABLE_CHANGED)
    LABEL_X_OFFSET = 0.01
    

    def __init__(self, variable, var_ops, launch_help_func, update_func,
                 show_modes):
        super(KeyWidget, self).__init__(homogeneous=False, spacing=0)
        self.my_variable = variable
        self.hbox = gtk.HBox()
        self.hbox.show()
        self.pack_start(self.hbox, expand=False, fill=False)
        self.var_ops = var_ops
        self.meta = variable.metadata
        self.launch_help = launch_help_func
        self.update_status = update_func
        self.show_modes = show_modes
        self.var_flags = []
        self._last_var_comments = None
        self.ignored_label = gtk.Label()
        self.ignored_label.show()
        self.hbox.pack_start(self.ignored_label, expand=False, fill=False)
        self.set_ignored()
        if self.my_variable.name != '':
            self.entry = gtk.Label()
            self.entry.set_alignment(
                        self.LABEL_X_OFFSET,
                        self.entry.get_alignment()[1])
            self.entry.set_text(self.my_variable.name)
        else:
            self.entry = gtk.Entry()
            self.entry.modify_text(gtk.STATE_NORMAL,
                                   self.MODIFIED_COLOUR)
            self.entry.connect("focus-out-event",
                               lambda w, e: self._setter(w, variable))
        event_box = gtk.EventBox()
        event_box.add(self.entry)
        event_box.connect('enter-notify-event',
                          lambda b, w: self._handle_enter(b))
        event_box.connect('leave-notify-event',
                          lambda b, w: self._handle_leave(b))
        self.hbox.pack_start(event_box, expand=True, fill=True,
                             padding=0)
        self.comments_box = gtk.HBox()
        self.hbox.pack_start(self.comments_box, expand=False, fill=False)
        self.grab_focus = lambda : self.entry.grab_focus()
        self.set_sensitive(True)
        self.set_sensitive = self.entry.set_sensitive 
        event_box.connect('button-press-event', self.handle_launch_help)
        self.update_comment_display()
        self.entry.show()
        for key, value in self.show_modes.items():
            if key not in [rose.config_editor.SHOW_MODE_CUSTOM_DESCRIPTION,
                           rose.config_editor.SHOW_MODE_CUSTOM_HELP,
                           rose.config_editor.SHOW_MODE_CUSTOM_TITLE]:
                self.set_show_mode(key, value)
        if (rose.META_PROP_VALUES in self.meta and
            len(self.meta[rose.META_PROP_VALUES]) == 1):
            self.add_flag(rose.config_editor.FLAG_TYPE_FIXED,
                          rose.config_editor.VAR_FLAG_TIP_FIXED)
        event_box.show()
        self.show()

    def add_flag(self, flag_type, tooltip_text=None):
        """Set the display of a flag denoting a property."""
        if flag_type in self.var_flags:
            return
        self.var_flags.append(flag_type)
        stock_id = self.FLAG_ICON_MAP[flag_type]
        event_box = gtk.EventBox()
        event_box._flag_type = flag_type
        image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_MENU)
        image.set_tooltip_text(tooltip_text)
        image.show()
        event_box.add(image)
        event_box.show()
        event_box.connect("button-press-event", self._toggle_flag_label)
        self.hbox.pack_end(event_box, expand=False, fill=False,
                           padding=rose.config_editor.SPACING_SUB_PAGE)

    def get_centre_height(self):
        """Return the vertical displacement of the centre of this widget."""
        return (self.entry.size_request()[1] / 2)

    def handle_launch_help(self, widget, event):
        """Handle launching help."""
        if event.type == gtk.gdk.BUTTON_PRESS and event.button != 3:
            self.launch_help()

    def launch_edit_comments(self, *args):
        """Launch an edit comments dialog."""
        text = "\n".join(self.my_variable.comments)
        title = rose.config_editor.DIALOG_TITLE_EDIT_COMMENTS.format(
                                   self.my_variable.metadata['id'])
        rose.gtk.util.run_edit_dialog(text,
                                      finish_hook=self._edit_finish_hook,
                                      title=title)

    def refresh(self, variable=None):
        """Reload the contents - however, no need for this at present."""
        self.my_variable = variable

    def remove_flag(self, flag_type):
        """Remove the flag from the widget."""
        for widget in self.get_children():
            if (isinstance(widget, gtk.EventBox) and
                getattr(widget, "_flag_type", None) == flag_type):
                self.remove(widget)
        if flag_type in self.var_flags:
            self.var_flags.remove(flag_type)
        return True

    def set_ignored(self):
        """Update the ignored display."""
        self.ignored_label.set_markup(
                     rose.variable.get_ignored_markup(self.my_variable))
        hover_string = ""
        if not self.my_variable.ignored_reason:
            self.ignored_label.set_tooltip_text(None)
        for key, value in sorted(self.my_variable.ignored_reason.items()):
            hover_string += key + " " + value + "\n"
        self.ignored_label.set_tooltip_text(hover_string.strip())

    def set_modified(self, is_modified):
        """Set the display of modified status in the text."""
        if is_modified:
            if isinstance(self.entry, gtk.Label):
                att_list = self.entry.get_attributes()
                if att_list is None:
                    att_list = pango.AttrList()
                att_list.insert(pango.AttrForeground(
                                      self.MODIFIED_COLOUR.red,
                                      self.MODIFIED_COLOUR.green,
                                      self.MODIFIED_COLOUR.blue,
                                      start_index=0,
                                      end_index=-1))
                self.entry.set_attributes(att_list)
        else:
            if isinstance(self.entry, gtk.Label):
                att_list = self.entry.get_attributes()
                if att_list is not None:
                    att_list = att_list.filter(
                        lambda a: a.type != pango.ATTR_FOREGROUND)

                if att_list is None:
                    att_list = pango.AttrList()
                self.entry.set_attributes(att_list)

    def set_show_mode(self, show_mode, should_show_mode):
        """Set the display of a mode on or off."""
        if show_mode in [rose.config_editor.SHOW_MODE_CUSTOM_DESCRIPTION,
                         rose.config_editor.SHOW_MODE_CUSTOM_HELP,
                         rose.config_editor.SHOW_MODE_CUSTOM_TITLE]:
            return self._set_show_custom_meta_text(show_mode, should_show_mode)
        if show_mode == rose.config_editor.SHOW_MODE_NO_TITLE:
            return self._set_show_title(not should_show_mode)
        if show_mode == rose.config_editor.SHOW_MODE_NO_DESCRIPTION:
            return self._set_show_meta_text_mode(rose.META_PROP_DESCRIPTION,
                                                 not should_show_mode)
        if show_mode == rose.config_editor.SHOW_MODE_NO_HELP:
            return self._set_show_meta_text_mode(rose.META_PROP_HELP,
                                                 not should_show_mode)
        if show_mode == rose.config_editor.SHOW_MODE_FLAG_OPTIONAL:
            if (should_show_mode and
                self.meta.get(rose.META_PROP_COMPULSORY) !=
                rose.META_PROP_VALUE_TRUE):
                    return self.add_flag(
                                rose.config_editor.FLAG_TYPE_OPTIONAL,
                                rose.config_editor.VAR_FLAG_TIP_OPTIONAL)
            return self.remove_flag(rose.config_editor.FLAG_TYPE_OPTIONAL)
        if show_mode == rose.config_editor.SHOW_MODE_FLAG_NO_META:
            if should_show_mode and len(self.meta) <= 2:
                return self.add_flag(rose.config_editor.FLAG_TYPE_NO_META,
                                     rose.config_editor.VAR_FLAG_TIP_NO_META)
            return self.remove_flag(rose.config_editor.FLAG_TYPE_NO_META)
        if show_mode == rose.config_editor.SHOW_MODE_FLAG_OPT_CONF:
            if (should_show_mode and rose.config_editor.FLAG_TYPE_OPT_CONF in
                self.my_variable.flags):
                opts_info = self.my_variable.flags[
                               rose.config_editor.FLAG_TYPE_OPT_CONF]
                info_text = ""
                info_format = rose.config_editor.VAR_FLAG_TIP_OPT_CONF_INFO
                for opt, diff in sorted(opts_info.items()):
                    info_text += info_format.format(opt, diff)
                info_text = info_text.rstrip()
                if info_text:
                    text = rose.config_editor.VAR_FLAG_TIP_OPT_CONF.format(
                                info_text)
                    return self.add_flag(
                                    rose.config_editor.FLAG_TYPE_OPT_CONF,
                                    text)
            return self.remove_flag(rose.config_editor.FLAG_TYPE_OPT_CONF)

    def update_comment_display(self):
        """Update the display of variable comments."""
        if self.my_variable.comments == self._last_var_comments:
            return
        self._last_var_comments = self.my_variable.comments
        if (self.my_variable.comments or
            rose.config_editor.SHOULD_SHOW_ALL_COMMENTS):
            format = rose.config_editor.VAR_COMMENT_TIP
            comments = [format.format(c) for c in self.my_variable.comments]
            tooltip_text = "\n".join(comments)
            comment_widgets = self.comments_box.get_children()
            if comment_widgets:
                comment_widgets[0].set_tooltip_text(tooltip_text)
            else:
                edit_eb = gtk.EventBox()
                edit_eb.show()
                edit_label = gtk.Label("#")
                edit_label.show()
                edit_eb.add(edit_label)
                edit_eb.set_tooltip_text(tooltip_text)
                edit_eb.connect("button-press-event",
                                self._handle_comment_click)
                edit_eb.connect("enter-notify-event",
                                self._handle_comment_enter_leave, True)
                edit_eb.connect("leave-notify-event",
                                self._handle_comment_enter_leave, False)
                self.comments_box.pack_start(
                              edit_eb, expand=False, fill=False,
                              padding=rose.config_editor.SPACING_SUB_PAGE)
            self.comments_box.show()
        else:
            self.comments_box.hide()

    def _get_metadata_formatting(self, mode):
        """Apply the correct formatting for a metadata property."""
        mode_format = "{" + mode + "}"
        if (mode == rose.META_PROP_DESCRIPTION and
            self.show_modes[
                      rose.config_editor.SHOW_MODE_CUSTOM_DESCRIPTION]):
            mode_format = rose.config_editor.CUSTOM_FORMAT_DESCRIPTION
        if (mode == rose.META_PROP_HELP and
            self.show_modes[rose.config_editor.SHOW_MODE_CUSTOM_HELP]):
            mode_format = rose.config_editor.CUSTOM_FORMAT_HELP
        if (mode == rose.META_PROP_TITLE and
            self.show_modes[rose.config_editor.SHOW_MODE_CUSTOM_TITLE]):
            mode_format = rose.config_editor.CUSTOM_FORMAT_TITLE
        mode_string = rose.variable.expand_format_string(mode_format,
                                                         self.my_variable)
        if mode_string is None:
            return self.my_variable.metadata[mode]
        return mode_string

    def _set_show_custom_meta_text(self, mode, should_show_mode):
        """Set the display of a custom format for a metadata property."""
        if mode == rose.config_editor.SHOW_MODE_CUSTOM_TITLE:
            return self._set_show_title(
                         not self.show_modes[
                                  rose.config_editor.SHOW_MODE_NO_TITLE])
        if mode == rose.config_editor.SHOW_MODE_CUSTOM_DESCRIPTION:
            is_shown = not self.show_modes[
                            rose.config_editor.SHOW_MODE_NO_DESCRIPTION]
            if is_shown:
                self._set_show_meta_text_mode(rose.META_PROP_DESCRIPTION,
                                              False)
                self._set_show_meta_text_mode(rose.META_PROP_DESCRIPTION,
                                              True)
        if mode == rose.config_editor.SHOW_MODE_CUSTOM_HELP:
            is_shown = not self.show_modes[
                                rose.config_editor.SHOW_MODE_NO_HELP]
            if is_shown:
                self._set_show_meta_text_mode(rose.META_PROP_HELP, False)
                self._set_show_meta_text_mode(rose.META_PROP_HELP, True)
                                          

    def _set_show_meta_text_mode(self, mode, should_show_mode):
        """Set the display of description or help below the title/name."""
        if should_show_mode:
            search_func = lambda i: self.var_ops.search_for_var(
                                                 self.meta["full_ns"], i)
            if mode not in self.meta:
                return
            mode_text = self._get_metadata_formatting(mode)
            mode_text = rose.gtk.util.safe_str(mode_text)
            mode_text = rose.config_editor.VAR_FLAG_MARKUP.format(mode_text)
            label = rose.gtk.util.get_hyperlink_label(mode_text, search_func)
            label.show()
            hbox = gtk.HBox()
            hbox.show()
            hbox.pack_start(label, expand=False, fill=False)
            hbox._show_mode = mode
            self.pack_start(hbox, expand=False, fill=False,
                            padding=rose.config_editor.SPACING_SUB_PAGE)
            show_mode_widget_indices = []
            for i, widget in enumerate(self.get_children()):
                if hasattr(widget, "_show_mode"):
                   show_mode_widget_indices.append((widget._show_mode, i))
            show_mode_widget_indices.sort()
            for j, (show_mode, i) in enumerate(show_mode_widget_indices):
                if show_mode == mode and j < len(show_mode_widget_indices) - 1:
                    # The new widget goes before the next one alphabetically.
                    new_index = show_mode_widget_indices[j + 1][1]
                    self.reorder_child(hbox, new_index)
                    break
        else:
            for widget in self.get_children():
                if (isinstance(widget, gtk.HBox) and
                    hasattr(widget, "_show_mode") and
                    widget._show_mode == mode):
                    self.remove(widget)

    def _set_show_title(self, should_show_title):
        """Set the display of a variable title instead of the name."""
        if not self.my_variable.name:
            return False
        if should_show_title:
            if rose.META_PROP_TITLE in self.meta:
                title_string = self._get_metadata_formatting(
                                         rose.META_PROP_TITLE)
                if title_string != self.entry.get_text():
                    return self.entry.set_text(title_string)
        if self.entry.get_text() != self.my_variable.name:
            self.entry.set_text(self.my_variable.name)

    def _toggle_flag_label(self, event_box, event, text=None):
        """Toggle a label describing the flag."""
        flag_type = event_box._flag_type
        if text is None:
            text = event_box.get_child().get_tooltip_text()
        for widget in self.get_children():
            if (hasattr(widget, "_flag_type") and
                widget._flag_type == flag_type):
                return self.remove(widget)
        label = gtk.Label()
        markup = rose.gtk.util.safe_str(text)
        markup = rose.config_editor.VAR_FLAG_MARKUP.format(markup)
        label.set_markup(markup)
        label.show()
        hbox = gtk.HBox()
        hbox._flag_type = flag_type
        hbox.pack_start(label, expand=False, fill=False)
        hbox.show()
        self.pack_start(hbox, expand=False, fill=False)

    def _edit_finish_hook(self, text):
        self.var_ops.set_var_comments(self.my_variable, text.splitlines())
        self.update_status()

    def _handle_comment_enter_leave(self, widget, event, is_entering=False):
        label = widget.get_child()
        self._set_underline(label, underline=is_entering)

    def _handle_comment_click(self, widget, event):
        if event.button == 1:
            self.launch_edit_comments()

    def _handle_enter(self, event_box):
        label_text = self.entry.get_text()
        tooltip_text = ""
        if rose.META_PROP_DESCRIPTION in self.meta:
            tooltip_text = self._get_metadata_formatting(
                                         rose.META_PROP_DESCRIPTION)
        if rose.META_PROP_TITLE in self.meta:
            if self.show_modes[rose.config_editor.SHOW_MODE_NO_TITLE]:
                # Titles are hidden, so show them in the hover-over.
                tooltip_text += ("\n (" +  
                                    rose.META_PROP_TITLE.capitalize() + 
                                    ": '" +
                                    self.meta[rose.META_PROP_TITLE] + "')")
            elif (self.my_variable.name not in label_text or
                  not self.show_modes[
                                rose.config_editor.SHOW_MODE_CUSTOM_TITLE]):
                # No custom title, or a custom title without the name.
                tooltip_text += ("\n (" + self.my_variable.name + ")")
        if self.my_variable.comments:
            format = rose.config_editor.VAR_COMMENT_TIP
            if tooltip_text:
                tooltip_text += "\n"
            comments = [format.format(c) for c in self.my_variable.comments]
            tooltip_text += "\n".join(comments)
        changes = self.var_ops.get_var_changes(self.my_variable)
        if changes != '' and tooltip_text != '':
            tooltip_text += '\n' + changes
        else:
            tooltip_text += changes
        tooltip_text.strip()
        if tooltip_text == '':
            tooltip_text = None
        event_box.set_tooltip_text(tooltip_text)
        if (rose.META_PROP_URL not in self.meta and
            'http://' in self.my_variable.value):
            new_url = re.search('(http://[^ ]+)',
                                self.my_variable.value).group()
            # This is not very nice.
            self.meta.update({rose.META_PROP_URL: new_url})
        if (rose.META_PROP_HELP in self.meta or
            rose.META_PROP_URL in self.meta):
            if isinstance(self.entry, gtk.Label):
                self._set_underline(self.entry, underline=True)
        return False

    def _set_underline(self, label, underline=False):
        # Set an underline in a label widget.
        att_list = label.get_attributes()
        if att_list is None:
            att_list = pango.AttrList()
        if underline:
            att_list.insert(pango.AttrUnderline(pango.UNDERLINE_SINGLE,
                                                start_index=0,
                                                end_index=-1))
        else:
            att_list = att_list.filter(lambda a:
                                       a.type != pango.ATTR_UNDERLINE)
            if att_list is None:
                att_list = pango.AttrList()
        label.set_attributes(att_list)

    def _handle_leave(self, event_box):
        event_box.set_tooltip_text(None)
        if isinstance(self.entry, gtk.Label):
            self._set_underline(self.entry, underline=False)       
        return False

    def _setter(self, widget, variable):
        """Re-set the name of the variable in the dictionary object."""
        new_name = widget.get_text()
        if variable.name != new_name:
            section = variable.metadata['id'].split(rose.CONFIG_DELIMITER)[0]
            if section.startswith("namelist:"):
                if new_name.lower() != new_name:
                    text = rose.config_editor.DIALOG_BODY_NL_CASE_CHANGE
                    text = text.format(new_name.lower())
                    title = rose.config_editor.DIALOG_TITLE_NL_CASE_WARNING
                    new_name = rose.gtk.util.run_choices_dialog(
                                        text, [new_name.lower(), new_name],
                                        title)
                    if new_name is None:
                        return None
            self.var_ops.remove_var(variable)
            variable.name = new_name
            id_prefix = ':'
            variable.metadata['id'] = (section + rose.CONFIG_DELIMITER +
                                       variable.name)
            self.var_ops.add_var(variable)
