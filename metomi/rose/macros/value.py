# Copyright (C) British Crown (Met Office) & Contributors.
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
import re

import metomi.rose.env
import metomi.rose.macro
import metomi.rose.macros.rule
import metomi.rose.meta_type
import metomi.rose.variable

REC_CHARACTER = re.compile(r"'(?:[^']|'')*'$")


class ValueChecker(metomi.rose.macro.MacroBase):

    """Returns sections and options with wrong values according to metadata.

    It can use any metadata widget errors (within the GUI), or some defined
    behaviours (default) to check if a value is outside the
    allowed range, or the wrong type or composition. Call with either
    metomi.rose.config objects or config filenames.

    """

    META_PROPS = [
        metomi.rose.META_PROP_LENGTH,
        metomi.rose.META_PROP_PATTERN,
        metomi.rose.META_PROP_RANGE,
        metomi.rose.META_PROP_TYPE,
        metomi.rose.META_PROP_VALUES,
    ]
    WARNING_BAD_PATTERN = "Value {0} does not contain the pattern: {1}"
    WARNING_BAD_RANGE = "Value {0} is not in the range criteria: {1}"
    WARNING_INVALID_LENGTH = 'Derived type has an invalid length: {0}'
    WARNING_NOT_STRING = 'Value {0} not a string'
    WARNING_WRONG_VALUES = 'Value {0} not in allowed values {1}'
    WARNING_WRONG_VALUE_FIXED = 'Value {0} should be {1}'
    WARNING_WRONG_LENGTH = 'Array longer than max length: {0} instead of {1}'

    def __init__(self, *args, **kwargs):
        self.bad_value_meta_map = {}
        self.good_value_meta_map = {}
        self.pattern_comp_map = {}
        self.range_func_map = {}
        super(ValueChecker, self).__init__(*args, **kwargs)

    def validate(self, config, meta_config=None, _variables=None):
        """Return a list of errors if found, None otherwise."""
        self.reports = []
        for node_keys, node in config.walk(no_ignore=True):
            if isinstance(node.value, dict):
                continue
            sect, key = node_keys
            value = node.value
            # Skip environment variable values
            if metomi.rose.env.contains_env_var(value):
                continue
            var_id = self._get_id_from_section_option(sect, key)
            self._validate_id(var_id, value, meta_config)
        return self.reports

    def validate_variables(self, variables, meta_config):
        """Return a list of errors if found, None otherwise."""
        self.reports = []
        for variable in variables:
            # Don't check ignored variables.
            if variable.ignored_reason:
                continue
            if metomi.rose.env.contains_env_var(variable.value):
                continue
            var_id = variable.metadata["id"]
            value = variable.value
            self._validate_id(var_id, value, meta_config)
        return self.reports

    def _validate_id(self, var_id, value, meta_config):
        """Validate the value of a particular variable id."""
        metadata = metomi.rose.macro.get_metadata_for_config_id(
            var_id, meta_config
        )
        sect, key = self._get_section_option_from_id(var_id)
        saved_metadata = copy.deepcopy(metadata)
        saved_metadata.pop('id')
        for meta_key in list(saved_metadata):
            if meta_key not in self.META_PROPS:
                saved_metadata.pop(meta_key)
        goodness_id = (value, tuple(sorted(saved_metadata.items())))
        if goodness_id in self.good_value_meta_map:
            return
        if goodness_id in self.bad_value_meta_map:
            self.add_report(
                sect, key, value, self.bad_value_meta_map[goodness_id]
            )
            return
        variable = metomi.rose.variable.Variable(key, value, metadata)
        metadata = variable.metadata
        if not isinstance(value, str):
            text = self.WARNING_NOT_STRING.format(repr(value))
            self.bad_value_meta_map[goodness_id] = text
            self.add_report(sect, key, value, text)
            return
        num_elements = variable.metadata.get(metomi.rose.META_PROP_LENGTH, 1)
        if num_elements != 1:
            if num_elements == ':':
                num_elements = -1
            else:
                try:
                    num_elements = int(num_elements)
                except (TypeError, ValueError):
                    num_elements = 1
        val_list = [value]
        type_list = metadata.get(metomi.rose.META_PROP_TYPE, '')
        if isinstance(type_list, str):
            type_list = [type_list]
        if num_elements != 1:
            val_list = metomi.rose.variable.array_split(value)
            if num_elements != -1:
                if len(val_list) > num_elements * len(type_list):
                    text = self.WARNING_WRONG_LENGTH.format(
                        len(val_list), num_elements * len(type_list)
                    )
                    self.bad_value_meta_map[goodness_id] = text
                    self.add_report(sect, key, value, text)
                    return
                elif len(val_list) % len(type_list) != 0:
                    text = self.WARNING_INVALID_LENGTH.format(len(val_list))
                    self.bad_value_meta_map[goodness_id] = text
                    self.add_report(sect, key, value, text)
                    return
            num_elements = len(val_list)
        skip_nulls = (
            metadata.get(metomi.rose.META_PROP_COMPULSORY)
            != metomi.rose.META_PROP_VALUE_TRUE
            and num_elements != 1
        )
        if metomi.rose.META_PROP_VALUES in metadata:
            meta_values = metadata[metomi.rose.META_PROP_VALUES]
            for val in val_list:
                if skip_nulls and not val:
                    continue
                if val not in meta_values:
                    if len(meta_values) > 1:
                        text = self.WARNING_WRONG_VALUES.format(
                            val, repr(meta_values)
                        )
                    else:
                        text = self.WARNING_WRONG_VALUE_FIXED.format(
                            val, meta_values[0]
                        )
                    self.bad_value_meta_map[goodness_id] = text
                    self.add_report(sect, key, value, text)
                    break
        elif metomi.rose.META_PROP_TYPE in metadata:
            meta_type = metadata[metomi.rose.META_PROP_TYPE]
            if num_elements == 1 and isinstance(meta_type, str):
                # A standard, non array variable.
                for val in val_list:
                    try:
                        if not self.meta_check(val, meta_type, sect, key):
                            self.bad_value_meta_map[
                                goodness_id
                            ] = self.reports[-1].info
                    except KeyError:
                        pass

            else:
                # The variable is an array or a derived type array.
                if isinstance(meta_type, str):
                    type_list = [meta_type]
                else:
                    type_list = meta_type
                    val_list = metomi.rose.variable.array_split(value)
                if num_elements == -1:
                    array_length = len(val_list) / len(type_list)
                else:
                    array_length = num_elements
                type_list = type_list * array_length

                for type_name, val in zip(type_list, val_list):
                    if skip_nulls and not val:
                        continue
                    try:
                        if not self.meta_check(val, type_name, sect, key):
                            self.bad_value_meta_map[
                                goodness_id
                            ] = self.reports[-1].info
                            break
                    except KeyError:
                        pass
        if metomi.rose.META_PROP_PATTERN in metadata:
            pattern = metadata[metomi.rose.META_PROP_PATTERN]
            if pattern not in self.pattern_comp_map:
                self.pattern_comp_map[pattern] = re.compile(
                    pattern, re.VERBOSE
                )
            if not self.pattern_comp_map[pattern].search(value):
                text = self.WARNING_BAD_PATTERN.format(value, pattern)
                self.bad_value_meta_map[goodness_id] = text
                self.add_report(sect, key, value, text)
                return
        if metomi.rose.META_PROP_RANGE in metadata:
            range_pat = metadata[metomi.rose.META_PROP_RANGE]
            text = self.check_range(
                range_pat,
                var_id,
                sect,
                key,
                val_list,
                type_list,
                skip_nulls=skip_nulls,
            )
            if text:
                self.bad_value_meta_map[goodness_id] = text
                self.add_report(sect, key, value, text)
                return
        if not self.reports or not (
            sect == self.reports[-1].section and key == self.reports[-1].option
        ):
            # Then this value correctly matches the metadata.
            if goodness_id not in self.good_value_meta_map:
                self.good_value_meta_map[goodness_id] = None

    def meta_check(self, value, meta_type, sect, key):
        """Check function wrapper"""
        res = metomi.rose.meta_type.meta_type_checker(value, meta_type)
        if not res[0]:
            self.add_report(sect, key, value, res[1])
        return res[0]

    def check_character(self, value):
        """Interface to check a 'character' type string."""
        return self.meta_check(value, "character", "", "")

    def check_quoted(self, value):
        """Interface to check a "double quoted" type string."""
        return self.meta_check(value, "quoted", "", "")

    def check_range(
        self,
        range_pat,
        var_id,
        sect,
        key,
        val_list,
        type_list,
        skip_nulls=False,
    ):
        """Check against a range pattern."""
        is_range_complex = "this" in range_pat
        if is_range_complex:
            tiny_config = metomi.rose.config.ConfigNode()
        elif range_pat not in self.range_func_map:
            check_func = metomi.rose.variable.parse_range_expression(range_pat)
            self.range_func_map.update({range_pat: check_func})
        else:
            check_func = self.range_func_map[range_pat]
        check_ok = True
        cur_val = None
        for i, val in enumerate(val_list):
            cur_val = val
            if skip_nulls and not val:
                continue
            if len(type_list) > 1:
                val_type = type_list[i % len(type_list)]
                if val_type not in ["integer", "real"]:
                    continue
            if not self.meta_check(val, "real", sect, key):
                check_ok = False
                break
            if is_range_complex:
                tiny_config.set([sect, key], val)
                tiny_meta_config = metomi.rose.config.ConfigNode()
                evaluator = metomi.rose.macros.rule.RuleEvaluator()
                try:
                    check_ok = evaluator.evaluate_rule(
                        range_pat, var_id, tiny_config, tiny_meta_config
                    )
                except metomi.rose.macros.rule.RuleValueError:
                    pass
            else:
                val_num = float(val)
                if not check_func(val_num):
                    check_ok = False
                    break
        if check_ok:
            return ""
        return self.WARNING_BAD_RANGE.format(cur_val, range_pat)


class TypeFixer(metomi.rose.macro.MacroBase):

    """Fix incorrect types."""

    WARNING_CHANGED_VALUE = '{0} -> {1}'

    def transform(self, config, meta_config=None):
        """Transform configuration and return it with a list of changes."""
        self.reports = []
        if meta_config is None:
            meta_config = self._load_meta_config(config, meta_config)
        checker = ValueChecker()
        type_err_list = checker.validate(config, meta_config)
        if type_err_list is None:
            return config, None
        for item in type_err_list:
            sect = item.section
            opt = item.option
            var_id = self._get_id_from_section_option(sect, opt)
            metadata = metomi.rose.macro.get_metadata_for_config_id(
                var_id, meta_config
            )
            saved_metadata = copy.deepcopy(metadata)
            saved_metadata.pop('id')
            node = config.get([sect, opt])
            value = node.value
            ignored_state = node.state
            old_value = value
            m_type = metadata.get(metomi.rose.META_PROP_TYPE)
            if m_type in ["boolean", "character", "logical", "quoted"]:
                if (
                    metadata.get(metomi.rose.META_PROP_LENGTH, '').isdigit()
                    or metadata.get(metomi.rose.META_PROP_LENGTH) == ':'
                ):
                    val_list = metomi.rose.variable.array_split(value)
                    for i, val in enumerate(val_list):
                        val_list[i] = self.meta_transform(val, m_type)
                    value = metomi.rose.variable.array_join(val_list)
                else:
                    value = self.meta_transform(value, m_type)
            if value != old_value:
                config.set([sect, opt], value, ignored_state)
                text = self.WARNING_CHANGED_VALUE.format(old_value, value)
                self.add_report(sect, opt, value, text)
        return config, self.reports

    def meta_transform(self, value, meta_type):
        return metomi.rose.meta_type.meta_type_transform(value, meta_type)
