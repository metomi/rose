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

import ast
import os
import re
import sys

import jinja2

import rose.macro
import rose.variable


REC_EXPR_IS_THIS_RULE = re.compile("(?:^.*[^\w]|^)this[^\w].*([<>=]|in\s).*$")


class RuleValueError(Exception):

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        arg_string = " ".join([str(a) for a in self.args])
        return "{0} - could not retrieve value. ".format(arg_string)


class FailureRuleChecker(rose.macro.MacroBase):

    """Check the fail-if and warn-if conditions"""

    ERROR_RULE_FAILED = "failed because"
    REC_RULE_SPLIT = re.compile(r"\s*;\s*")
    RULE_ERROR_NAME = "fail-if"
    RULE_WARNING_NAME = "warn-if"
    RULE_FAIL_FORMAT = "{0}: {1}"
    RULE_MSG_FAIL_FORMAT = "({0}) {1}: {2}"
    WARNING_RULE_FAILED = "warn because"

    def validate(self, config, meta_config):
        """Validate against any rules found in the meta_config."""
        self.reports = []
        rule_data = {self.RULE_ERROR_NAME: {}, self.RULE_WARNING_NAME: {}}
        evaluator = RuleEvaluator()
        for setting_id, sect_node in meta_config.value.items():
            for rule_opt in [self.RULE_ERROR_NAME, self.RULE_WARNING_NAME]:
                if rule_opt in sect_node.value:
                    sect, opt = self._get_section_option_from_id(setting_id)
                    node = config.get([sect, opt], no_ignore=True)
                    if node is not None:
                        rule = sect_node.get([rule_opt]).value
                        id_rules = rule_data[rule_opt]
                        id_rules.setdefault(setting_id, [])
                        rule_lines = rule.splitlines()
                        for rule_line in rule_lines:
                            message = None
                            if "#" in rule_line:
                                rule_line, message = rule_line.split("#", 1)
                                message = message.strip()
                            rule_line = rule_line.strip()
                            for rule_item in self.REC_RULE_SPLIT.split(rule_line):
                                if not rule_item:
                                    continue
                                id_rules[setting_id].append([rule_item, None])
                            if id_rules[setting_id]:
                                id_rules[setting_id][-1][-1] = message
        for rule_type in rule_data:
            is_warning = (rule_type == self.RULE_WARNING_NAME)
            if is_warning:
                f_type = self.WARNING_RULE_FAILED
            else:
                f_type = self.ERROR_RULE_FAILED
            for setting_id, rule_msg_list in rule_data[rule_type].items():
                section, option = self._get_section_option_from_id(setting_id)
                for (rule, message) in rule_msg_list:
                    try:
                        test_failed = evaluator.evaluate_rule(
                                                rule, setting_id, config)
                    except RuleValueError as e:
                        continue
                    if test_failed:
                        value = config.get([section, option]).value
                        if message is None:
                            info = self.RULE_FAIL_FORMAT.format(f_type, rule)
                        else:
                            info = self.RULE_MSG_FAIL_FORMAT.format(message,
                                                                    f_type,
                                                                    rule)
                        self.add_report(section, option, value, info,
                                        is_warning)
        return self.reports


class RuleEvaluator(rose.macro.MacroBase):

    """Evaluate logical expressions in the metadata."""

    ARRAY_EXPR = "{0}({1}) {2} {3}"
    ARRAY_FUNC_LOGIC = {"all": " and ",
                        "any": " or "}
    INTERNAL_ID_SETTING = "_id{0}"
    INTERNAL_ID_VALUE = "_value{0}"
    INTERNAL_ID_THIS_SETTING = "_thisid{0}"
    INTERNAL_ID_SCI_NUM = "_scinum{0}"
    REC_ARRAY = {"all": re.compile(r"(\W)all\( *(\S+) *(\S+) *(.*?) *\)(\W)"),
                 "any": re.compile(r"(\W)any\( *(\S+) *(\S+) *(.*?) *\)(\W)")}
    REC_CONFIG_ID = re.compile(r"(?:\W)([\w:]+=\w+(?:\(\d+\))?)(?:\W)")
    REC_SCI_NUM = re.compile(r"""(?:\W|^)
                                 ([-+]?[\d.]+
                                  [edED][-+]?\d+)
                                 (?:\W|$)""",
                             re.I | re.X)
    REC_THIS_ELEMENT_ID = re.compile(r"(?:\W)(this\(\d+\))(?:\W)")
    REC_VALUE = re.compile(r'("[^"]*")')

    def evaluate_rule(self, rule, setting_id, config):
        rule_template_str, rule_id_values = self._process_rule(
                                   rule, setting_id, config)
        template = jinja2.Template(rule_template_str)
        return_string = template.render(rule_id_values)
        return ast.literal_eval(return_string)

    def _process_rule(self, rule, setting_id, config):
        if not (rule.startswith('{%') or rule.startswith('{-%')):
            rule = "{% if " + rule + " %}True{% else %}False{% endif %}"
        local_map = {"this": self._get_value_from_id(setting_id, config)}
        value_id_count = -1
        sci_num_count = -1
        for array_func_key, rec_regex in self.REC_ARRAY.items():
            for search_result in rec_regex.findall(rule):
                start, var_id, operator, value, end = search_result
                if var_id == "this":
                    var_id = setting_id
                setting_value = self._get_value_from_id(var_id, config)
                array_value = rose.variable.array_split(setting_value)
                new_string = start + "("
                for elem_num in range(1, len(array_value) + 1):
                    new_string += self.ARRAY_EXPR.format(var_id, elem_num,
                                                         operator, value)
                    if elem_num < len(array_value):
                        new_string += self.ARRAY_FUNC_LOGIC[array_func_key]
                new_string += ")" + end
                rule = rec_regex.sub(new_string, rule, count=1)
        for search_result in self.REC_SCI_NUM.findall(rule):
            sci_num_count += 1
            key = self.INTERNAL_ID_SCI_NUM.format(sci_num_count)
            local_map[key] = self._evaluate(search_result)
            rule = rule.replace(search_result, key, 1)
        for search_result in self.REC_VALUE.findall(rule):
            value_string = search_result.strip('"')
            for key, value in local_map.items():
                if value == value_string:
                    break
            else:
                value_id_count += 1
                key = self.INTERNAL_ID_VALUE.format(value_id_count)
                local_map[key] = value_string
            rule = rule.replace(search_result, key, 1)
        for search_result in self.REC_THIS_ELEMENT_ID.findall(rule):
            proper_id = search_result.replace("this", setting_id)
            value_string = self._get_value_from_id(proper_id, config)
            for key, value in local_map.items():
                if value == value_string:
                    break
            else:
                x_id_num_str = search_result.replace("this", "").strip('()')
                key = self.INTERNAL_ID_THIS_SETTING.format(x_id_num_str)
                local_map[key] = value_string
            rule = rule.replace(search_result, key, 1)
        config_id_count = -1
        for search_result in self.REC_CONFIG_ID.findall(rule):
            value_string = self._get_value_from_id(search_result, config)
            for key, value in local_map.items():
                if value == value_string:
                    break
            else:
                config_id_count += 1
                key = self.INTERNAL_ID_SETTING.format(config_id_count)
                local_map[key] = value_string
            rule = rule.replace(search_result, key, 1)
        return rule, local_map
                
    def _get_value_from_id(self, variable_id, config):
        section, option = self._get_section_option_from_id(variable_id)
        value = None
        opt_node = config.get([section, option], no_ignore=True)
        if opt_node is not None:
            value = opt_node.value
        if opt_node is None:
            if option is None:
                raise RuleValueError(variable_id)
            if (option.endswith(')') and '(' in option and
                option.count('(') == 1):
                option, element = option.rstrip(')').split('(')
                opt_node = config.get([section, option])
                if opt_node is not None:
                    value = opt_node.value
                if value is not None:
                    try:
                        index = int(element)
                    except (TypeError, ValueError) as e:
                        raise RuleValueError(variable_id)
                    val_array = rose.variable.array_split(value)
                    try:
                        return_value = val_array[index - 1]
                    except IndexError as e:
                        raise RuleValueError(variable_id)
                    else:
                        return self._evaluate(return_value)
            raise RuleValueError(variable_id)
        return self._evaluate(value)

    def _evaluate(self, string):
        try:
            return_value = float(string)
        except (TypeError, ValueError):
            return_value = string
        return return_value
