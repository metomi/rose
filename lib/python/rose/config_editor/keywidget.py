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

import re

import pango
import pygtk
pygtk.require('2.0')
import gtk

import rose.config_editor


class KeyWidget(gtk.HBox):

    """This class generates a label or entry box for a variable name."""

    FLAG_ICON_MAP = {
             rose.config_editor.FLAG_TYPE_DEFAULT:
                  gtk.STOCK_INFO,
             rose.config_editor.FLAG_TYPE_ERROR:
                  gtk.STOCK_DIALOG_WARNING,
             rose.config_editor.FLAG_TYPE_OPTIONAL:
                  gtk.STOCK_ABOUT,
             rose.config_editor.FLAG_TYPE_NO_META:
                  gtk.STOCK_DIALOG_QUESTION}

    MODIFIED_COLOUR = gtk.gdk.color_parse(
                              rose.config_editor.COLOUR_VARIABLE_CHANGED)
    LABEL_X_OFFSET = 0.01
    

    def __init__(self, variable, var_ops, launch_help_func, update_func,
                 show_title_on):
        super(KeyWidget, self).__init__(homogeneous=False, spacing=0)
        self.my_variable = variable
        self.var_ops = var_ops
        self.meta = variable.metadata
        self.launch_help = launch_help_func
        self.update_status = update_func
        self.show_title_on = show_title_on
        self.var_flags = []
        self._last_var_comments = None
        if self.my_variable.name != '':
            self.entry = gtk.Label()
            self.entry.set_alignment(
                        self.LABEL_X_OFFSET,
                        self.entry.get_alignment()[1])
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
        self.pack_start(event_box, expand=True, fill=True,
                        padding=0)
        self.comments_box = gtk.HBox()
        self.pack_start(self.comments_box, expand=False, fill=False)
        self.grab_focus = lambda : self.entry.grab_focus()
        self.set_sensitive(True)
        self.set_sensitive = self.entry.set_sensitive 
        event_box.connect('button-press-event',
                          lambda b, w: self.launch_help())
        if 'title' in self.meta and self.show_title_on:
            self.entry.set_text(self.meta['title'])
        else:
            self.entry.set_text(self.my_variable.name)
        self.update_comment_display()
        self.entry.show()
        event_box.show()

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
                edit_button = rose.gtk.util.CustomButton(
                                                     label="#",
                                                     as_tool=True,
                                                     tip_text=tooltip_text)
                edit_button.connect("clicked", self.launch_edit_comments)
                self.comments_box.pack_start(edit_button, expand=False,
                                             fill=False)
            self.comments_box.show()
        else:
            self.comments_box.hide()

    def refresh(self, variable=None):
        """Reload the contents - however, no need for this at present."""
        self.my_variable = variable

    def set_show_title(self, should_show_title):
        """Set the display of a variable title instead of the name."""
        if should_show_title:
            if ('title' in self.meta and 
                self.entry.get_text() != self.meta['title']):
                self.entry.set_text(self.meta['title'])
        else:
            if self.entry.get_text() != self.my_variable.name:
                self.entry.set_text(self.my_variable.name)
        
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

    def add_flag(self, flag_type, tooltip_text=None):
        """Set the display of a flag denoting a property."""
        if flag_type in self.var_flags:
            return
        self.var_flags.append(flag_type)
        stock_id = self.FLAG_ICON_MAP[flag_type]
        image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_MENU)
        image.set_tooltip_text(tooltip_text)
        image.show()
        self.pack_end(image, expand=False, fill=False,
                      padding=rose.config_editor.SPACING_SUB_PAGE)

    def clear_flags(self, just_this_flag_type=None):
        """Remove the flags from the widget, or just one type of flag."""
        if just_this_flag_type is not None:
            flag_stock_id = self.FLAG_ICON_MAP[just_this_flag_type]
            if just_this_flag_type not in self.var_flags:
                return False
        for widget in self.get_children():
            if isinstance(widget, gtk.Image):
                if just_this_flag_type is not None:
                    if widget.get_stock()[0] != flag_stock_id:
                        continue
                    self.var_flags.remove(just_this_flag_type)
                self.remove(widget)
        return True

    def launch_edit_comments(self, *args):
        text = "\n".join(self.my_variable.comments)
        title = rose.config_editor.DIALOG_TITLE_EDIT_COMMENTS.format(
                                   self.my_variable.metadata['id'])
        rose.gtk.util.run_edit_dialog(text,
                                      finish_hook=self._edit_finish_hook,
                                      title=title)

    def _edit_finish_hook(self, text):
        self.var_ops.set_var_comments(self.my_variable, text.splitlines())
        self.update_status()

    def _handle_enter(self, event_box):
        if rose.META_PROP_DESCRIPTION in self.meta:
            tooltip_text = self.meta[rose.META_PROP_DESCRIPTION]
            if rose.META_PROP_TITLE in self.meta:
                if self.entry.get_text() == self.meta[rose.META_PROP_TITLE]:
                    tooltip_text += ("\n (" + self.my_variable.name + ")")
                else:
                    tooltip_text += ("\n (" +  
                                     rose.META_PROP_TITLE.capitalize() + 
                                     ": '" +
                                     self.meta['title'] + "')")
        elif (rose.META_PROP_TITLE in self.meta and
              self.entry.get_text() == self.meta[rose.META_PROP_TITLE]):
            tooltip_text = "(" + self.my_variable.name + ")"
        else:
            tooltip_text = ''
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
            self.meta.update({rose.META_PROP_URL: new_url})
        if (rose.META_PROP_HELP in self.meta or
            rose.META_PROP_URL in self.meta):
            if isinstance(self.entry, gtk.Label):
                att_list = self.entry.get_attributes()
                if att_list is None:
                    att_list = pango.AttrList()
                att_list.insert(pango.AttrUnderline(pango.UNDERLINE_SINGLE,
                                                    start_index=0,
                                                    end_index=-1))
                self.entry.set_attributes(att_list)
        return False

    def _handle_leave(self, event_box):
        event_box.set_tooltip_text(None)
        if isinstance(self.entry, gtk.Label):
            att_list = self.entry.get_attributes()
            if att_list is None:
                att_list = pango.AttrList()
            att_list = att_list.filter(lambda a:
                                        a.type != pango.ATTR_UNDERLINE)
            if att_list is None:
                att_list = pango.AttrList()
            self.entry.set_attributes(att_list)
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
