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

import ast
import re

import jinja2
import jinja2.exceptions

import metomi.rose.macro
import metomi.rose.variable

REC_EXPR_IS_THIS_RULE = re.compile(
    r"""(?:^.*[^\w:=]|^)   (?# Break or beginning)
         this              (?# 'this')
         (?:               (?# Followed by:)
           $               (?# the end)
          |                (?# or)
           \W              (?# break plus)
           .*              (?# anything)
           (               (?# Start operator)
             [+*%<>=-]    (?# Arithmetic)
            |              (?# or)
             in\s          (?# String)
            |              (?# or)
             not\s         (?# Logical not)
            |              (?# or)
             and\s         (?# Logical and)
            |              (?# or)
             or\s          (?# Logical or)
           )               (?# End operator)
           .*              (?# anything)
           $               (?# the end)
         )""",
    re.X,
)


class Int(int):
    """Override integer to maintain Python2 style interface
    """
    def __lt__(self, other):
        """
        Examples:
            >>> Int(4) < Int(6)
            True
            >>> Int(4) < Float(6.1)
            True
            >>> Int(4) < Str('Zaphod Beeblebrox')
            True
            >>> Int(99999) < Str('Zaphod Beeblebrox')
            True
            >>> Int(4) < Float(-5.5)
            False
            >>> Int(42) < 42
            False
            >>> Int(77) < ''
            False
        """
        try:
            return int(self) < other
        except TypeError:
            return False

    def __gt__(self, other):
        """
        Examples:
            >>> Int(2) > Float(2.0)
            False
            >>> Int(3) > Float(2.0)
            True
        """
        try:
            return int(self) > other
        except TypeError:
            return True

    def __le__(self, other):
        return not self.__gt__(other)

    def __ge__(self, other):
        return not self.__lt__(other)


class Float(float):
    def __lt__(self, other):
        """
        Examples:
            >>> Int(4) < Int(6)
            True
            >>> Int(4) < Float(6.1)
            True
            >>> Int(4) < Str('Zaphod Beeblebrox')
            True
            >>> Int(99999) < Str('Zaphod Beeblebrox')
            True
            >>> Int(4) < Float(-5.5)
            False
            >>> Int(1199) < 1199
            False
        """
        try:
            return float(self) < float(other)
        except (TypeError, ValueError):
            return True

    def __gt__(self, other):
        """
        Examples:
            >>> Int(2) > Float(2.0)
            False
            >>> Int(3) > Float(2.0)
            True
        """
        try:
            return float(self) > float(other)
        except (TypeError, ValueError):
            return False

    def __le__(self, other):
        return not self.__gt__(other)

    def __ge__(self, other):
        return not self.__lt__(other)


class Str(str):
    def __lt__(self, other):
        """
        Examples:
            >>> Str('aardvaark') < Str('zebra')
            True
            >>> Str('alligator') < Int(400)
            False
            >>> Str('pink fairy armadillo') < 'syrian hamster'
            True
        """
        if isinstance(other, (int, float, Float, Int)):
            return False
        elif isinstance(other, Str):
            return str(self) < str(other)
        else:
            return str(self) < other

    def __gt__(self, other):
        """
        Examples:
            >>> Str('aardvaark') > Str('zebra')
            False
            >>> Str('alligator') > Int(400)
            True
            >>> Str('pink fairy armadillo') > 'syrian hamster'
            False
        """
        if isinstance(other, (int, float, Float, Int)):
            return True
        elif isinstance(other, Str):
            return str(self) > str(other)
        else:
            return str(self) > other

    def __le__(self, other):
        return not self.__gt__(other)

    def __ge__(self, other):
        return not self.__lt__(other)


MYTYPES = {str: Str, int: Int, bool: Int, float: Float}


class RuleValueError(Exception):
    def __init__(self, *args):
        self.args = args

    def __str__(self):
        arg_string = " ".join([str(a) for a in self.args])
        return "{0} - could not retrieve value. ".format(arg_string)


class FailureRuleChecker(metomi.rose.macro.MacroBase):

    """Check the fail-if and warn-if conditions"""

    ERROR_RULE_FAILED = "failed because"
    REC_RULE_SPLIT = re.compile(r"\s*;\s*")
    RULE_ERROR_NAME = "fail-if"
    RULE_WARNING_NAME = "warn-if"
    RULE_FAIL_FORMAT = "{0}: {1}"
    RULE_MSG_FAIL_FORMAT = "({0}) {1}: {2}"
    RULE_SYNTAX_FAIL_FORMAT = "Syntax error ({0}) {1}: {2}"
    WARNING_RULE_FAILED = "warn because"

    def validate(self, config, meta_config):
        """Validate against any rules found in the meta_config."""
        self.reports = []
        rule_data = {self.RULE_ERROR_NAME: {}, self.RULE_WARNING_NAME: {}}
        evaluator = RuleEvaluator()
        for node_keys, node in config.walk(no_ignore=True):
            if isinstance(node.value, dict):
                continue
            sect, opt = node_keys
            value = node.value
            setting_id = self._get_id_from_section_option(sect, opt)
            metadata = metomi.rose.macro.get_metadata_for_config_id(
                setting_id, meta_config
            )
            for rule_opt in [self.RULE_ERROR_NAME, self.RULE_WARNING_NAME]:
                if rule_opt in metadata:
                    rule = metadata.get(rule_opt)
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
            is_warning = rule_type == self.RULE_WARNING_NAME
            if is_warning:
                f_type = self.WARNING_RULE_FAILED
            else:
                f_type = self.ERROR_RULE_FAILED
            for setting_id, rule_msg_list in rule_data[rule_type].items():
                section, option = self._get_section_option_from_id(setting_id)
                for (rule, message) in rule_msg_list:
                    info = None
                    try:
                        test_failed = evaluator.evaluate_rule(
                            rule, setting_id, config, meta_config
                        )
                    except (
                        ZeroDivisionError,
                        TypeError,
                        ValueError,
                        IndexError,
                    ) as exc:
                        test_failed = True
                        info = self.RULE_MSG_FAIL_FORMAT.format(
                            exc, f_type, rule
                        )
                    except jinja2.exceptions.TemplateError as exc:
                        test_failed = True
                        info = self.RULE_SYNTAX_FAIL_FORMAT.format(
                            rule_type, rule, exc
                        )
                    except RuleValueError:
                        continue

                    if test_failed:
                        value = config.get([section, option]).value
                        if info is None:
                            if message is None:
                                info = self.RULE_FAIL_FORMAT.format(
                                    f_type, rule
                                )
                            else:
                                info = self.RULE_MSG_FAIL_FORMAT.format(
                                    message, f_type, rule
                                )
                        self.add_report(
                            section, option, value, info, is_warning
                        )
        return self.reports


class RuleEvaluator(metomi.rose.macro.MacroBase):

    """Evaluate logical expressions in the metadata."""

    ARRAY_EXPR = "{0}({1}) {2} {3}"
    ARRAY_FUNC_LOGIC = {"all": " and ", "any": " or "}
    INTERNAL_ID_SETTING = "_id{0}"
    INTERNAL_ID_VALUE = "_value{0}"
    INTERNAL_ID_THIS_SETTING = "_thisid{0}"
    INTERNAL_ID_SCI_NUM = "_scinum{0}"
    REC_ARRAY = {
        "all": re.compile(r"(\W)all\( *(\S+) *(\S+) *(.*?) *\)(\W)"),
        "any": re.compile(r"(\W)any\( *(\S+) *(\S+) *(.*?) *\)(\W)"),
    }
    REC_CONFIG_ID = re.compile(
        r"""
                      (?:\W|^)        (?# Break or beginning)
                      (               (?# Begin ID capture)
                       [\w:.]*         (?# 1st part of section, including :)
                       (?:\{.*?\})?   (?# Optional modifier for the section)
                       (?:\([^)]*\))? (?# Optional element for the section)
                       =              (?# Section-option delimiter)
                       [a-zA-Z][\w-]+ (?# Option name )
                       (?:\(\d+\))?   (?# Optional element for the option )
                      )               (?# End ID capture )
                      (?:\W|$)        (?# Break or end)""",
        re.X,
    )
    REC_LEN_FUNC = re.compile(r"(\W)len\( *(\S+) *\)(\W)")
    REC_SCI_NUM = re.compile(
        r"""
                     (?:\W|^)    (?# Break or beginning)
                     (           (?# Begin number capture)
                      [-+]?      (?# Optional sign)
                      [\d.]+     (?# Optional sign. Digit and dot)
                      [ed][-+]?  (?# Exponent, [edED] with ignored case)
                      \d+        (?# Exponent number)
                     )           (?# End number capture)
                     (?:\W|$)    (?# Break or end)
                                 """,
        re.I | re.X,
    )
    REC_THIS_ELEMENT_ID = re.compile(
        r"""
                             (?:\W|^)        (?# Break or beginning)
                             (this\(\d+\))   (?# 'this' element)
                             (?:\W|$)        (?# Break or end)""",
        re.X,
    )
    REC_VALUE = re.compile(r'("[^"]*")')

    def evaluate_rule(self, rule, setting_id, config, meta_config):
        """Evaluate the logic in the provided rule based on config values."""
        rule_template_str, rule_id_values = self._process_rule(
            rule, setting_id, config, meta_config
        )
        template = jinja2.Template(rule_template_str)

        # Recast to our own implementations of base types to maintain
        # Python 2 behaviour
        for key, value in rule_id_values.items():
            for basetype, mytype in MYTYPES.items():
                if isinstance(value, basetype):
                    rule_id_values[key] = mytype(rule_id_values[key])

        return_string = template.render(rule_id_values)
        return ast.literal_eval(return_string)

    def evaluate_rule_id_usage(self, rule, setting_id, meta_config):
        """Return a set of setting ids referenced in the provided rule."""
        log_ids = set()
        self._process_rule(
            rule, setting_id, None, meta_config, log_ids=log_ids
        )
        return log_ids

    def _process_rule(
        self, rule, setting_id, config, meta_config, log_ids=None
    ):
        """Pre-process the provided rule into valid jinja2."""
        if log_ids is None:
            get_value_from_id = self._get_value_from_id
        else:
            get_value_from_id = (
                lambda id_, conf, m_conf, p_id: self._log_id_usage(
                    id_, conf, m_conf, p_id, log_ids
                )
            )
        if not (rule.startswith('{%') or rule.startswith('{-%')):
            rule = "{% if " + rule + " %}True{% else %}False{% endif %}"

        # Start processing out our additional syntax.
        local_map = {
            "this": get_value_from_id(
                setting_id, config, meta_config, setting_id
            )
        }
        value_id_count = -1
        sci_num_count = -1

        # any/all processing.
        for array_func_key, rec_regex in self.REC_ARRAY.items():
            for search_result in rec_regex.findall(rule):
                start, var_id, operator, value, end = search_result
                if var_id == "this":
                    var_id = setting_id
                setting_value = get_value_from_id(
                    var_id, config, meta_config, setting_id
                )
                array_value = metomi.rose.variable.array_split(
                    str(setting_value)
                )
                new_string = start + "("
                for elem_num in range(1, len(array_value) + 1):
                    new_string += self.ARRAY_EXPR.format(
                        var_id, elem_num, operator, value
                    )
                    if elem_num < len(array_value):
                        new_string += self.ARRAY_FUNC_LOGIC[array_func_key]
                new_string += ")" + end
                rule = rec_regex.sub(new_string, rule, count=1)

        # len(...) processing.
        for search_result in self.REC_LEN_FUNC.findall(rule):
            start, var_id, end = search_result
            if var_id == "this":
                var_id = setting_id
            elif self.REC_THIS_ELEMENT_ID.search(rule):
                var_id = var_id.replace("this", setting_id)
            setting_value = get_value_from_id(
                var_id, config, meta_config, setting_id
            )
            array_value = metomi.rose.variable.array_split(str(setting_value))
            new_string = start + str(len(array_value)) + end
            rule = self.REC_LEN_FUNC.sub(new_string, rule, count=1)

        # Number-like-strings into numbers.
        for search_result in self.REC_SCI_NUM.findall(rule):
            sci_num_count += 1
            key = self.INTERNAL_ID_SCI_NUM.format(sci_num_count)
            local_map[key] = self._evaluate(search_result)
            rule = rule.replace(search_result, key, 1)

        # Strings into proper string variables.
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

        # Replace 'this' id with the cast value.
        for search_result in self.REC_THIS_ELEMENT_ID.findall(rule):
            proper_id = search_result.replace("this", setting_id)
            value_string = get_value_from_id(
                proper_id, config, meta_config, setting_id
            )
            for key, value in local_map.items():
                if value == value_string:
                    break
            else:
                x_id_num_str = search_result.replace("this", "").strip('()')
                key = self.INTERNAL_ID_THIS_SETTING.format(x_id_num_str)
                local_map[key] = value_string
            rule = rule.replace(search_result, key, 1)

        # Replace ids (namelist:foo=bar) with their cast values.
        config_id_count = -1
        for search_result in self.REC_CONFIG_ID.findall(rule):
            value_string = get_value_from_id(
                search_result, config, meta_config, setting_id
            )
            for key, value in local_map.items():
                if value == value_string:
                    break
            else:
                config_id_count += 1
                key = self.INTERNAL_ID_SETTING.format(config_id_count)
                local_map[key] = value_string
            rule = rule.replace(search_result, key, 1)

        # Return the now valid Jinja2 template with a map of variables.
        return rule, local_map

    def _log_id_usage(
        self, variable_id, config, meta_config, parent_id, id_set
    ):
        """Wrap _get_value_from_id, storing variable_id in id_set."""
        id_set.add(variable_id)
        if config is None:
            return "None"
        return self._get_value_from_id(
            variable_id, config, meta_config, parent_id
        )

    def _get_value_from_id(self, variable_id, config, meta_config, parent_id):
        """Extract a value for variable_id from config, or fail."""
        section, option = self._get_section_option_from_id(variable_id)
        if variable_id != parent_id:
            # We may need to de-duplicate the section in the variable_id.
            dupl_section = metomi.rose.macro.REC_ID_STRIP.sub("", section)
            dupl_node = meta_config.get(
                [dupl_section, metomi.rose.META_PROP_DUPLICATE], no_ignore=True
            )
            if (
                dupl_node is not None
                and dupl_node.value == metomi.rose.META_PROP_VALUE_TRUE
            ):
                # This is an id in a duplicate namelist.
                parent_section = self._get_section_option_from_id(parent_id)[0]
                parent_dupl_section = metomi.rose.macro.REC_ID_STRIP.sub(
                    "", parent_section
                )
                if parent_dupl_section != dupl_section:
                    raise RuleValueError(variable_id)
                # Set section to be the same as the parent id's section.
                section = parent_section
        value = None
        opt_node = config.get([section, option], no_ignore=True)
        if opt_node is not None:
            value = opt_node.value
        if opt_node is None:
            if option is None:
                raise RuleValueError(variable_id)
            if (
                option.endswith(')')
                and '(' in option
                and option.count('(') == 1
            ):
                option, element = option.rstrip(')').split('(')
                opt_node = config.get([section, option])
                if opt_node is not None:
                    value = opt_node.value
                if value is not None:
                    try:
                        index = int(element)
                    except (TypeError, ValueError):
                        raise RuleValueError(variable_id)
                    val_array = metomi.rose.variable.array_split(value)
                    try:
                        return_value = val_array[index - 1]
                    except IndexError:
                        raise RuleValueError(variable_id)
                    else:
                        return self._evaluate(return_value)
            raise RuleValueError(variable_id)
        return self._evaluate(value)

    def _evaluate(self, string):
        """Try to return string as a number, if possible."""
        try:
            return_value = float(string)
        except (TypeError, ValueError):
            return_value = string
        return return_value
