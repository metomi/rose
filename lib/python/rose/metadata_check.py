# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
"""Module to provide checking facilities for Rose configuration metadata."""

import os
import re
import sys

import rose.config
import rose.config_editor.util
import rose.formats.namelist
import rose.macro
import rose.macros

import rose.opt_parse

ERROR_LOAD_META_CONFIG_DIR = "{0}: not a configuration metadata directory."
INVALID_IMPORT = "Could not import {0}: {1}"
INCOMPATIBLE = "Incompatible with {0}"
INVALID_OBJECT = "Not found: {0}"
INVALID_RANGE_RULE_IDS = "Inter-variable comparison not allowed in range."
INVALID_SYNTAX = "Invalid syntax: {0}"
UNNECESSARY_VALUES_PROP = "Unnecessary property - 'values' overrides"
UNKNOWN_TYPE = "Unknown type: {0}"
UNKNOWN_PROP = "Unknown property: {0}"
VALUE_JOIN = " and "


def get_allowed_metadata_properties():
    """Return a list of allowed properties such as type or values."""
    properties = []
    for key in dir(rose):
        if (key.startswith("META_PROP_") and
            key not in ["META_PROP_VALUE_TRUE", "META_PROP_VALUE_FALSE"]):
            properties.append(getattr(rose, key))
    return properties


def _check_compulsory(value):   
    allowed_values = [rose.META_PROP_VALUE_TRUE,
                      rose.META_PROP_VALUE_FALSE]
    if value not in allowed_values:
        return INVALID_SYNTAX.format(value)


def _check_duplicate(value):
    allowed_values = [rose.META_PROP_VALUE_TRUE,
                      rose.META_PROP_VALUE_FALSE]
    if value not in allowed_values:
        return INVALID_SYNTAX.format(value)


def _check_fail_if(value):
    pass


def _check_length(value):
    if not value.isdigit() and value != ":":
        return INVALID_SYNTAX.format(value)


def _check_macro(value, module_files=None, meta_dir=None):
    if module_files is None:
        module_files = _get_module_files(meta_dir)
    if not module_files:
        return
    try:
        macros = rose.variable.array_split(value, only_this_delim=",")
    except Exception as e:
        return INVALID_SYNTAX.format(e)
    bad_macros = []
    for macro in macros:
        macro_name = macro
        method = None
        if (macro.endswith("." + rose.macro.VALIDATE_METHOD) or
            macro.endswith("." + rose.macro.TRANSFORM_METHOD)):
            macro_name, method = macro.rsplit(".", 1)
        try:
            macro_obj = rose.config_editor.util.import_object(
                                                       macro_name,
                                                       module_files,
                                                       _import_err_handler)
        except Exception as e:
            return INVALID_IMPORT.format(
                                  macro,
                                  type(e).__name__ + ": " + str(e))
        if macro_obj is None:
            return INVALID_OBJECT.format(macro)
        elif method is not None:
            if not hasattr(macro_obj, method):
                return INVALID_OBJECT.format(method)


def _check_pattern(value):
    try:
        re.compile(value, re.VERBOSE)
    except Exception as e:
        err_text = type(e).__name__ + ": " + str(e)
        return INVALID_SYNTAX.format(err_text)


def _check_range(value):
    is_range_complex = "this" in value
    if is_range_complex:
        test_config = rose.config.ConfigNode()
        test_id = "env=A"
        test_config.set(["env", "A"], "0")
        evaluator =  rose.macros.rule.RuleEvaluator()
        try:
            check_ok = evaluator.evaluate_rule(
                                          value, test_id, test_config)
        except rose.macros.rule.RuleValueError as e:
            return INVALID_RANGE_RULE_IDS.format(e)
        except Exception as e:
            return INVALID_SYNTAX.format(e)
    else:
        try:
            check_func = rose.variable.parse_range_expression(value)
        except rose.variable.RangeSyntaxError as e:
            return str(e)
        except Exception as e:
            return INVALID_SYNTAX.format(type(e).__name__ + ": " + str(e))


def _check_value_titles(title_value, values_value):
    try:
        title_list = rose.variable.array_split(title_value,
                                               only_this_delim=",")
    except Exception as e:
        return INVALID_SYNTAX.format(type(e).__name__ + ": " + str(e))
    try:
        value_list = rose.variable.array_split(values_value,
                                               only_this_delim=",")
    except Exception as e:
        return INCOMPATIBLE.format(rose.META_PROP_VALUES)
    if len(title_list) != len(value_list):
        return INCOMPATIBLE.format(rose.META_PROP_VALUES)


def _check_type(value):
    types = rose.variable.parse_type_expression(value)
    if isinstance(types, basestring):
        types = [types]
    if " " in value and not "," in value:
        types = [value]
    bad_types = []
    for type_ in types:
        if type_ not in rose.TYPE_VALUES:
            bad_types.append(type_)
    if bad_types:
        return UNKNOWN_TYPE.format(VALUE_JOIN.join(bad_types))


def _check_values(value):
    try:
        val_list = rose.variable.array_split(value, only_this_delim=",")
    except Exception as e:
        return INVALID_SYNTAX.format(type(e).__name__ + ": " + str(e))
    if not val_list:
        return INVALID_SYNTAX.format(value)


def _check_warn_if(value):
    return _check_fail_if(value)


def _check_widget(value, module_files=None, meta_dir=None):
    if module_files is None:
        module_files = _get_module_files(meta_dir)
    if not module_files:
        return
    widget_name = value.split()[0]
    try:
        widget = rose.config_editor.util.import_object(widget_name,
                                                       module_files,
                                                       _import_err_handler)
    except Exception as e:
        return INVALID_IMPORT.format(widget_name,
                                            type(e).__name__ + ": " + str(e))
    if widget is None:
        return INVALID_OBJECT.format(value)


def _get_module_files(meta_dir=None):
    module_files = []
    if meta_dir is not None:
        lib_dir = os.path.join(meta_dir, "lib", "python")
        if os.path.isdir(lib_dir):
            for dirpath, dirnames, filenames in os.walk(lib_dir):
                if '/.' in dirpath:
                    continue
                for filename in filenames:
                    if filename.endswith(".py"):
                        abs_filename = os.path.abspath(
                                          os.path.join(dirpath, filename))
                        module_files.append(abs_filename)
    return module_files
    

def metadata_check(meta_config, meta_dir=None,
                   only_these_sections=None,
                   only_these_properties=None):
    """Check metadata validity."""
    allowed_properties = get_allowed_metadata_properties()
    reports = []
    module_files = _get_module_files(meta_dir)
    sections = meta_config.value.keys()
    sections.sort(rose.config.sort_settings)
    for section in sections:
        node = meta_config.value[section]
        if node.is_ignored() or not isinstance(node.value, dict):
            continue
        if (only_these_sections is not None and
            section not in only_these_sections):
            continue
        if node.get([rose.META_PROP_VALUES], no_ignore=True) is not None:
            # 'values' supercedes other type-like props, so don't use them.
            unnecessary_props = []
            for type_like_prop in [rose.META_PROP_PATTERN,
                                   rose.META_PROP_RANGE,
                                   rose.META_PROP_TYPE]:
                if node.get([type_like_prop], no_ignore=True) is not None:
                    info = UNNECESSARY_VALUES_PROP
                    value = node.get([type_like_prop]).value
                    reports.append(rose.macro.MacroReport(
                                              section, type_like_prop,
                                              value, info))
        options = node.value.keys()
        options.sort(rose.config.sort_settings)
        for option in options:
            opt_node = node.value[option]
            if ((only_these_properties is not None and
                 option not in only_these_properties) or
                opt_node.is_ignored()):
                continue
            value = opt_node.value
            if (option not in allowed_properties and
                not option.startswith(rose.META_PROP_WIDGET)):
                info = UNKNOWN_PROP.format(option)
                reports.append(rose.macro.MacroReport(section, option,
                                                      value, info))
            if option.startswith(rose.META_PROP_WIDGET):
                check_func = lambda v: _check_widget(
                                 v, module_files)
            elif option == rose.META_PROP_MACRO:
                check_func = lambda v: _check_macro(
                                 v, module_files)
            elif option == rose.META_PROP_VALUE_TITLES:
                check_func = lambda v: _check_value_titles(
                                 v, node.get_value([rose.META_PROP_VALUES]))
            else:
                func_name = "_check_" + option.replace("-", "_")
                check_func = globals().get(func_name, lambda v: None)
            info = check_func(value)
            if info:
                reports.append(rose.macro.MacroReport(section, option,
                                                      value, info))
    # Check triggering.
    trigger_macro = rose.macros.trigger.TriggerMacro()
    # The .validate method will be replaced in a forthcoming enhancement.
    trig_reports = trigger_macro.validate(rose.config.ConfigNode(),
                                          meta_config=meta_config)
    for report in trig_reports:
        if report.option is None:
            new_rep_section = report.section
        else:
            new_rep_section = (report.section + rose.CONFIG_DELIMITER +
                               report.option)
        rep_id_node = meta_config.get([new_rep_section], no_ignore=True)
        if rep_id_node is None:
            new_rep_option = None
            new_rep_value = None
        else:
            new_rep_option = rose.META_PROP_TRIGGER
            rep_trig_node = meta_config.get([new_rep_section, new_rep_option],
                                            no_ignore=True)
            if rep_trig_node is None:
                new_rep_value = None
            else:
                new_rep_value = rep_trig_node.value
        reports.append(rose.macro.MacroReport(new_rep_section, new_rep_option,
                                              new_rep_value, report.info))
    sorter = rose.config.sort_settings
    reports.sort(rose.macro.report_sort)
    return reports


def _import_err_handler(exception):
    if isinstance(exception, Exception):
        raise exception
    raise Exception(exception)


def main():
    opt_parser = rose.opt_parse.RoseOptionParser()
    opt_parser.add_my_options("conf_dir", "property")
    opts, args = opt_parser.parse_args()

    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    opts.conf_dir = os.path.abspath(opts.conf_dir)
    meta_conf_file_path = os.path.join(opts.conf_dir, rose.META_CONFIG_NAME)
    if not os.path.isfile(meta_conf_file_path):
        sys.exit(ERROR_LOAD_META_CONFIG_DIR.format(opts.conf_dir))
    meta_config = rose.config.load(meta_conf_file_path)
    sections = None
    if args:
        sections = args
    properties = None
    if opts.property:
        properties = opts.property
    reports = metadata_check(meta_config,
                             meta_dir=opts.conf_dir,
                             only_these_sections=sections,
                             only_these_properties=properties)
    macro_id = rose.macro.MACRO_OUTPUT_ID.format(
                                rose.macro.VALIDATE_METHOD.upper()[0],
                                "rose.metadata_check.MetadataChecker")
    text = rose.macro.get_reports_as_text(
                                    reports,
                                    macro_id)
    if reports:
        sys.stderr.write(text)
        sys.exit(1)


if __name__ == "__main__":
    main()
