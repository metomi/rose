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

import pygtk
pygtk.require("2.0")
import gtk

import rose.gtk.util
import rosie.browser
import rosie.vc


class SuiteDirector():

    """Class for managing version control operations on suites"""

    def __init__(self, event_handler):
        self.last_vc_event = ""
        self.event_logged = False
        self.vc_client = rosie.vc.Client(event_handler=event_handler)
        
    def checkout(self, *args, **kwargs):
        """Check out a suite."""
        id_ = kwargs.get("id_")
        if id_ is None:
            return False
        else:
            id_text = id_.to_string_with_version()
        rc = rose.gtk.util.DialogProcess([self.vc_client.checkout, id_],
                      description=rosie.browser.DIALOG_MESSAGE_CHECKOUT.format(
                                                id_text), 
                      title=rosie.browser.DIALOG_TITLE_CHECKOUT).run()
        if rc != 0:
            return False    

    def delete(self, to_delete, *args):
        """"Handles deletion of a suite."""
        warning = rosie.browser.DIALOG_MESSAGE_DELETE_CONFIRMATION.format(
                                                                   to_delete)
        label = gtk.Label(warning)
        label.set_line_wrap(True)
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK_CANCEL,
                                   warning)
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            try:
                self.vc_client.delete(to_delete)
            except rose.popen.RosePopenError as e:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR, 
                                         rosie.browser.ERROR_PERMISSIONS 
                                         + "\n\n" + str(e))
            except rosie.vc.LocalCopyStatusError as e:
                 rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR, 
                               rosie.browser.ERROR_MODIFIED_LOCAL_COPY_DELETE +
                               "\n\n" + str(e))               
            return True
        
        return False

    def delete_local(self, sid, *args):
        """"Handles deletion of working copies of suites."""
        warning = rosie.browser.DIALOG_MESSAGE_DELETE_LOCAL_CONFIRM.format(sid)
        label = gtk.Label(warning)
        label.set_line_wrap(True)
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK_CANCEL,
                                   warning)
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            try:
                self.vc_client.delete(sid, True)
            except rose.popen.RosePopenError as e:
                rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR, 
                                         rosie.browser.ERROR_PERMISSIONS 
                                         + "\n\n" + str(e))
            except rosie.vc.LocalCopyStatusError as e:
                 rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR, 
                               rosie.browser.ERROR_MODIFIED_LOCAL_COPY_DELETE +
                               "\n\n" + str(e))               
            return True
        
        return False

    def _edit_config(self, config, window, back_function, finish_function):
        window.set_modal(False)
        project = config.get(["project"]).value
        config.set(["project"], project)
        meta_config = rose.macro.load_meta_config(config)
        fixer_macro = rose.macros.DefaultTransforms()
        config, change_list = fixer_macro.transform(config, meta_config)
        for child in window.action_area:
            window.action_area.remove(child)
        for child in window.vbox:
            if window.vbox.query_child_packing(child)[3] == gtk.PACK_END:
                break
            window.vbox.remove(child)
        editor = rose.config_editor.main.MainController(
                             config_objs={"discovery": config},
                             pluggable=True)
        page_box = editor.get_orphan_page("/discovery")
        page = page_box.get_children()[0]
        vbox = gtk.VBox()
        vbox.pack_start(page_box)
        vbox.show()
        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        ok_button.connect(
                  "clicked",
                  lambda b: self._finish_config(page_box, window,
                                                editor, finish_function))
        ok_button.show()
        back_button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        back_button.connect("clicked", back_function)
        back_button.show()
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect("clicked",
                              lambda b: window.destroy())
        cancel_button.show()
        window.action_area.pack_start(cancel_button, expand=False, fill=False)
        window.action_area.pack_start(back_button, expand=False, fill=False)
        window.action_area.pack_start(ok_button, expand=False, fill=False)
        hbox = gtk.HBox()
        add_button = rose.gtk.util.CustomButton(stock_id=gtk.STOCK_ADD,
                                                label="Add property",
                                                tip_text="Add a new property")
        add_button.connect(
                   "button-press-event",
                   lambda b, e: page_box.get_children()[0].launch_add_menu(
                                             e.button, e.time))
        hbox.pack_start(add_button, expand=False, fill=False)
        hbox.show()
        window.vbox.pack_start(hbox, expand=False, fill=False)
        window.vbox.pack_start(vbox, expand=True, fill=True)
        vbox.grab_focus()

    def _finish_config(self, page_container, window, editor, finish_function):
        page = page_container.get_children()[0]
        if page.validate_errors():
            ok_dialog = gtk.MessageDialog(
                           parent=dialog,
                           message_format=rosie.browser.LABEL_ERROR_DISCOVERY,
                           type=gtk.MESSAGE_ERROR,
                           buttons=gtk.BUTTONS_NONE)
            ok_dialog.set_title(rosie.browser.TITLE_ERROR_DISCOVERY)
            ok_dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
            ok_dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            response = ok_dialog.run()
            ok_dialog.destroy()
            if response != gtk.RESPONSE_ACCEPT:
                return False
        window.destroy()
        config = editor.output_config_objects()['/discovery']
        finish_function(config)

    def run_new_suite_wizard(self, config, create_suite, parent_window,
                             window=None):
        """Run the suite wizard."""
        if window is None:
            window = gtk.Dialog(title=rosie.browser.TITLE_NEW_SUITE_WIZARD,
                                parent=parent_window)
            window.set_default_size(*rosie.browser.SIZE_WINDOW_NEW_SUITE)
            window.set_modal(False)
        project = self._select_project(config.get(["project"]).value, window)
        if project is None:
            window.destroy()
            return None
        config.set(["project"], project)
        back_hook = lambda *a: self.run_new_suite_wizard(config,
                                                         create_suite,
                                                         parent_window,
                                                         window)
        finish_hook = create_suite
        self._edit_config(config, window, back_hook, finish_hook)

    def _select_project(self, project, window):
        for child in window.action_area:
            window.action_area.remove(child)
        for child in window.vbox:
            if window.vbox.query_child_packing(child)[3] == gtk.PACK_END:
                break
            window.vbox.remove(child)
        forward_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        forward_button.connect("clicked",
                               lambda b: window.response(gtk.RESPONSE_ACCEPT))
        forward_button.show()
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect("clicked",
                              lambda b: window.response(gtk.RESPONSE_REJECT))
        cancel_button.show()
        window.action_area.pack_start(cancel_button, expand=False, fill=False)
        window.action_area.pack_start(forward_button, expand=False,
                                      fill=False)
        label = gtk.Label(rosie.browser.LABEL_EDIT_PROJECT)
        label.show()
        entry = gtk.Entry()
        entry.set_text(project)
        entry.connect("activate",
                      lambda w: window.response(gtk.RESPONSE_ACCEPT))
        entry.show()
        label_hbox = gtk.HBox()
        label_hbox.pack_start(label, expand=False, fill=False)
        label_hbox.pack_start(entry, expand=False, fill=True, padding=5)
        label_hbox.show()
        vbox = gtk.VBox()
        vbox.pack_start(label_hbox, expand=False, fill=False)
        vbox.show()
        align = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.1, yscale=0.1)
        align.add(vbox)
        align.show()
        window.set_border_width(5)
        window.vbox.pack_start(align, expand=True, fill=True)
        entry.grab_focus()
        entry.select_region(-1, -1)
        response = window.run()
        project_text = entry.get_text()
        if response == gtk.RESPONSE_ACCEPT:
            return project_text
        return None

