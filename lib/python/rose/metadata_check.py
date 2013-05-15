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
import sys

import rose.config
import rose.formats.namelist
import rose.macro
import rose.macros.value
from rose.opt_parse import RoseOptionParser


INVALID_ALLOWED_VALUE = "Invalid value - should be {0}"
INVALID_RANGE = "Could not process range: {0}"
INVALID_RANGE_RULE_IDS = "Other ids not allowed - error: {0}"
INVALID_RANGE_RULE = "Invalid rule syntax: {0}"
INVALID_LENGTH = "Invalid length - should be : or positive integer"
INVALID_PATTERN = "Invalid regex: {0}"
INVALID_VALUES = "Could not process values: {0}"
INVALID_VALUES_LENGTH = "Invalid values length"
INVALID_WIDGET_MODULE = "Invalid widget module"
UNNECESSARY_VALUES_PROP = "Property not needed - 'values' property overrides"
UNKNOWN_TYPE = "Unknown type: {0}"
UNKNOWN_PROP = "Unknown property."
VALUE_JOIN = " and "


def get_allowed_metadata_properties():
    """Return a list of allowed properties such as type or values."""
    properties = []
    for key in dir(rose):
        if (key.startswith("META_PROP_") and
            not key.startswith("META_PROP_VALUE_")):
            properties.append(key)
    return properties


def _check_compulsory(value):   
    allowed_values = [rose.META_PROP_VALUE_TRUE,
                      rose.META_PROP_VALUE_FALSE]
    if value not in allowed_values:
        return INVALID_ALLOWED_VALUE.format("/".join(allowed_values))


def _check_duplicate(value):
    allowed_values = [rose.META_PROP_VALUE_TRUE,
                      rose.META_PROP_VALUE_FALSE]
    if value not in allowed_values:
        return INVALID_ALLOWED_VALUE.format("/".join(allowed_values))


def _check_length(value):
    if not value.isdigit() and value != ":":
        return INVALID_LENGTH.format(value)


def _check_macro(value, module_files=None, meta_dir=None):
    if module_files is None:
        module_files = _get_module_files(meta_dir)
    if not module_files:
        return
    try:
        macros = rose.variable.array_split(value)
    except Exception as e:
        return INVALID_MACRO_SYNTAX.format(e)
    bad_macros = []
    for macro in macros:
        try:
            macro = rose.config_editor.util.import_object(value, module_files,
                                                          _import_err_handler)
        except Exception as e:
            return INVALID_MACRO_IMPORT.format(
                                 macro,
                                 type(e).__name__ + ": " + str(e))


def _check_pattern(value):
    try:
        re.compile(value, re.VERBOSE)
    except Exception as e:
        err_text = type(e).__name__ + ": " + str(e)
        return INVALID_PATTERN.format(err_text)


def _check_range(value):
    is_range_complex = "this" in value
    if is_range_complex:
        test_config = rose.config.ConfigNode()
        test_id = "env=A"
        test_config.set(["env", "A"], "0")
        evaluator =  rose.macros.rule.RuleEvaluator()
        try:
            check_ok = evaluator.evaluate_rule(
                                          range_pat, var_id, tiny_config)
        except RuleValueError as e:
            return INVALID_RANGE_RULE_IDS.format(e)
        except Exception as e:
            return INVALID_RANGE_RULE.format(e)
    else:
        try:
            check_func = rose.variable.parse_range_expression(range_pat)
        except Exception as e:
            return INVALID_RANGE.format(type(e).__name__ + ": " + str(e))


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
        val_list = rose.variable.array_split(value)
    except Exception as e:
        return INVALID_VALUES.format(type(e).__name__ + ": " + str(e))
    if not val_list:
        return INVALID_VALUES_LENGTH.format(value)


def _check_widget(value, module_files=None, meta_dir=None):
    if module_files is None:
        module_files = _get_module_files(meta_dir)
    if not module_files:
        return
    try:
        widget = rose.config_editor.util.import_object(value, module_files,
                                                       _import_err_handler)
    except Exception as e:
        return INVALID_WIDGET_IMPORT.format(type(e).__name__ + ": " + str(e))


def _get_module_files(meta_dir=None):
    module_files = []
    if meta_dir is not None:
        lib_dir = os.path.join(meta_dir, "lib", "python")
        if os.path.isdir(lib_dir):
            for dirpath, dirnames, filenames in os.walk(lib_dir):
                for filename in filenames:
                    if filename.endswith(".py"):
                        module_files.append(filename)
    return module_files


def metadata_check(meta_config, meta_dir=None,
                   only_these_sections=None,
                   only_these_properties=None):
    """Check metadata validity."""
    allowed_properties = get_allowed_metadata_properties()
    reports = []
    module_files = _get_module_files(meta_dir)
    for section, node in meta_config.value.items():
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
        for option, opt_node in node.value.items():
            if ((only_these_properties is not None and
                 option not in only_these_properties) or
                opt_node.is_ignored()):
                continue
            value = opt_node.value
            if option not in allowed_properties:
                info = UNKNOWN_PROP
                reports.append(rose.macro.MacroReport(section, option,
                                                      value, info))
            if option.startswith(rose.META_PROP_WIDGET):
                check_func = lambda v: _check_widget(
                                 v, module_files)
            elif option == rose.META_PROP_MACRO:
                check_func = lambda v: _check_macro(
                                 v, module_files)
            else:
                check_func = locals().get("_check_" + option, lambda v: None)
            info = check_func(value)
            if info:
                reports.append(rose.macro.MacroReport(section, option,
                                                      value, info))
    # Check triggering.
    trigger_macro = rose.macros.trigger.TriggerMacro()
    # The .validate method will be replaced in a forthcoming enhancement.
    reports.extend(trigger_macro.validate(rose.config.ConfigNode(),
                                          meta_config=meta_config))
    sorter = rose.config.sort_settings
    reports.sort(lambda x, y: sorter(x.option, y.option))
    reports.sort(lambda x, y: sorter(x.section, y.section))
    return reports


def _import_err_handler(exception):
    raise exception


def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("conf_dir", "property")
    opts, args = opt_parser.parse_args()

    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    opts.conf_dir = os.path.abspath(opts.conf_dir)
    meta_conf_file_path = os.path.join(opts.conf_dir, rose.META_CONFIG_NAME)
    if not os.path.isfile(meta_conf_file_path):
        sys.exit(opt_parser.get_usage())
    meta_config = rose.config.load(meta_conf_file_path)
    reports = metadata_check(meta_config,
                             meta_dir=opts.conf_dir,
                             only_these_sections=args,
                             only_these_properties=opts.property)
    text = rose.macro.get_reports_as_text(
                                    reports,
                                    "Metadata Checker")
    if reports:
        sys.exit(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
