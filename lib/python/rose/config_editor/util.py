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
"""
This module contains a utility class to transform between data types.

It also contains a function to launch an introspective dialog, and
one to import custom plugins.

"""

import inspect
import re

import pygtk
pygtk.require("2.0")
import gtk

import rose
import rose.gtk.util


class Lookup(object):

    """Collection of data lookup functions used by multiple modules."""

    def __init__(self):
        self.section_option_id_lookup = {}
        self.full_ns_split_lookup = {}

    def get_id_from_section_option(self, section, option):
        """Return a variable id from a section and option."""
        if option is None:
            id_ = section
        else:
            id_ = section + rose.CONFIG_DELIMITER + option
        self.section_option_id_lookup[id_] = (section, option)
        return id_

    def get_section_option_from_id(self, var_id):
        """Return a section and option from a variable id.

        This uses a dictionary to improve speed, as this method
        is called repeatedly with no variation in results.

        """
        if var_id in self.section_option_id_lookup:
            return self.section_option_id_lookup[var_id]
        split_char = rose.CONFIG_DELIMITER
        option_name = var_id.split(split_char)[-1]
        section = var_id.replace(split_char + option_name, '', 1)
        if option_name == section:
            option_name = None
        self.section_option_id_lookup[var_id] = (section, option_name)
        return section, option_name

    def split_full_ns(self, data, full_namespace):
        """Return the config name and the internal namespace from full ns."""
        if full_namespace not in self.full_ns_split_lookup:
            for config_name in data.config.keys():
                if config_name == '/' + data.top_level_name:
                    continue
                if full_namespace.startswith(config_name + '/'):
                    sub_space = full_namespace.replace(config_name + '/',
                                                       '', 1)
                    self.full_ns_split_lookup[full_namespace] = (config_name,
                                                                 sub_space)
                    break
                elif full_namespace == config_name:
                    sub_space = ''
                    self.full_ns_split_lookup[full_namespace] = (config_name,
                                                                 sub_space)
                    break
            else:
                # A top level based namespace
                config_name = "/" + data.top_level_name
                sub_space = full_namespace.replace(config_name + '/', '', 1)
                self.full_ns_split_lookup[full_namespace] = (config_name,
                                                             sub_space)
        return self.full_ns_split_lookup.get(full_namespace, (None, None))


def import_object(import_string, from_files, error_handler):
    """Import a Python callable.

    import_string is the '.' delimited path to the callable,
    as in normal Python - e.g. rose.config_editor.page.PageWidget
    from_files is a list of available Python file paths to search in
    error_handler is a function that accepts an Exception instance
    and does something appropriate with it.

    """
    is_builtin = False
    module_name = ".".join(import_string.split(".")[:-1])
    if module_name.startswith("rose."):
        is_builtin = True
    class_name = import_string.split(".")[-1]
    module_fpath = "/".join(import_string.rsplit(".")[:-1]) + ".py"
    module_files = [f for f in from_files if f.endswith(module_fpath)]
    if not module_files and not is_builtin:
        return None
    if not is_builtin:
        module_dir = os.path.dirname(module_files.pop())
        sys.path.insert(0, module_dir)
    try:
        module = __import__(module_name, globals(), locals(),
                            [], 0)
    except Exception as e:
        if not is_builtin:
            sys.path.pop(0)
        error_handler(e)
        return None
    for submodule in module_name.split(".")[1:]:
        module = getattr(module, submodule)
    contents = inspect.getmembers(module)
    return_object = None
    for obj_name, obj in contents:
        if obj_name == class_name and inspect.isclass(obj):
            return_object = obj
    if not is_builtin:
        sys.path.pop(0)
    return return_object


def launch_node_info_dialog(node, changes, search_function):
    """Launch a dialog displaying attributes of a variable or section."""
    title = node.__class__.__name__ + " " + node.metadata['id']
    safe_str = rose.gtk.util.safe_str
    text = ''
    if changes:
        text += rose.config_editor.DIALOG_NODE_INFO_CHANGES.format(
                                                        changes) + "\n"
    text += rose.config_editor.DIALOG_NODE_INFO_DATA
    att_list = vars(node).items()
    att_list.sort()
    att_list.sort(lambda x, y: (y[0] in ['name', 'value']) - 
                               (x[0] in ['name', 'value']))
    metadata_start_index = len(att_list)
    for key, value in sorted(node.metadata.items()):
        att_list.append([key, value])
    delim = rose.config_editor.DIALOG_NODE_INFO_DELIMITER
    name = rose.config_editor.DIALOG_NODE_INFO_ATTRIBUTE
    sub_name = rose.config_editor.DIALOG_NODE_INFO_SUB_ATTRIBUTE
    maxlen = rose.config_editor.DIALOG_NODE_INFO_MAX_LEN
    for i, (att_name, att_val) in enumerate(att_list):
        if (att_name == 'metadata' or att_name.startswith("_") or
            callable(att_val)):
            continue
        if i == metadata_start_index:
            text += "\n" + rose.config_editor.DIALOG_NODE_INFO_METADATA
        prefix = name.format(att_name) + delim
        indent0 = len(prefix)
        text += prefix
        lenval = maxlen - indent0
        if isinstance(att_val, dict) and att_val:
            for key, val in att_val.items():
                text += "\n" + " " * indent0
                sub_prefix = sub_name.format(safe_str(key)) + delim
                sub_ind0 = indent0 + len(sub_prefix)
                sub_lenval = lenval - len(sub_prefix)
                text += sub_prefix + wrap_string(val, sub_lenval, sub_ind0)
        elif isinstance(att_val, list) and att_val:
            val = ",".join(att_val)
            text += wrap_string(val, lenval, indent0)
        elif att_val != {} and att_val != []:
            text += wrap_string(att_val, lenval, indent0)
        text += "\n"
    rose.gtk.util.run_hyperlink_dialog(gtk.STOCK_DIALOG_INFO, text, title,
                                       search_function)


def launch_error_dialog(exception=None, text=""):
    """This will be replaced by rose.reporter utilities."""
    if text:
        text += "\n"
    if exception is not None:
        text += type(exception).__name__ + ": " + str(exception)
    rose.gtk.util.run_dialog(rose.gtk.util.DIALOG_TYPE_ERROR,
                             text, rose.config_editor.DIALOG_TITLE_ERROR)


def wrap_string(text, maxlen=72, indent0=0, maxlines=4, sep=","):
    """Return a wrapped string - 'textwrap' is not flexible enough for this."""
    lines = [""]
    linelen = maxlen - indent0
    for item in text.split(sep):
        dtext = rose.gtk.util.safe_str(item) + sep
        if lines[-1] and len(lines[-1] + dtext) > linelen:
            lines.append("")
            linelen = maxlen
        lines[-1] += dtext
    lines[-1] = lines[-1][:-len(sep)]
    if len(lines) > maxlines:
        lines = lines[:4] + ["..."]
    return "\n".join(lines)
    
