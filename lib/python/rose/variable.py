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
"""
This module contains:
 * the class Variable, which acts as a data structure for variable attributes.
 * the helper function get_value_from_metadata, which attempts to generate a
   suitable variable value from its metadata.
 * the metadata parser function parse_trigger_expression, which parses the
   metadata attribute 'trigger'.
"""

import copy
import re

import rose


RE_REAL = "[\+\-]?\d*\.?\d*(?:[de][\+\-]?\d+)?"
RE_CAPT_REAL = '(' + RE_REAL + ')'

REC_RANGE_NUM = re.compile(RE_CAPT_REAL + "$")
REC_RANGE_SPLIT = re.compile('\s*(,)\s*')
REC_RANGE_RANGE = re.compile(
        "(" + RE_REAL + "?)" + "\s*:\s*" +
        "(" + RE_REAL + "?)" + 
        "(?<!^:)$")  # Expression can't just be a colon.


# Ignored types used in rose.variable.ignored_reason,
# used by macros and user switches.
IGNORED_BY_SECTION = 'Section ignored'
IGNORED_BY_SYSTEM = 'Trigger ignored'
IGNORED_BY_USER = 'User ignored'


class Variable(object):

    """This class stores the data and metadata of an input variable.

    The variable is ignored if any ignored_reason keys exist,
    and contains errors if the error attribute is not empty.

    """

    def __init__(self, name, value, metadata=None, ignored_reason=None,
                 error=None, warning=None, flags=None, comments=None):
        self.name = name
        self.value = value
        if metadata is None:
            metadata = {}
        if ignored_reason is None:
            ignored_reason = {}
        if error is None:
            error = {}
        if warning is None:
            warning = {}
        if flags is None:
            flags = {}
        if comments is None:
            comments = []
        self.metadata = self.process_metadata(metadata)
        self.old_value = value
        self.flags = dict(flags.items())
        self.ignored_reason = dict(ignored_reason.items())
        self.error = error
        self.warning = warning
        self.comments = comments

    def process_metadata(self, metadata=None):
        """Process existing or resupplied metadata into the correct form."""
        if metadata is not None:
            self.metadata = metadata
        if ('type' in self.metadata and
            not isinstance(self.metadata['type'], list)):
            self.metadata['type'] = parse_type_expression(
                                               self.metadata['type'])
        if ('values' in self.metadata and
            not isinstance(self.metadata['values'], list)):
            # Replace this kind of thing with a proper metadata handler later.
            val_list = rose.variable.array_split(self.metadata['values'])
            self.metadata['values'] = val_list
        return self.metadata

    def to_hashable(self):
        """Return a hashable summary of the current state."""
        return (self.name, self.value, self.metadata['id'],
                tuple(sorted(self.ignored_reason.keys())),
                tuple(self.comments))

    def copy(self):
        new_variable = Variable(self.name,
                                self.value,
                                copy.deepcopy(self.metadata),
                                copy.deepcopy(self.ignored_reason),
                                copy.deepcopy(self.error),
                                copy.deepcopy(self.warning),
                                copy.deepcopy(self.flags),
                                copy.deepcopy(self.comments))
        new_variable.old_value = self.old_value
        return new_variable

    def __repr__(self):
        text = '<rose.variable :- name: ' + self.name + ', value: '
        text += repr(self.value) + ', old value: ' + repr(self.old_value) + ', '
        text += 'metadata: ' + str(self.metadata)
        text += ', ignored: ' + ['yes', 'no'][self.ignored_reason == {}]
        text += ', error: ' + str(self.error)
        text += ', warning: ' + str(self.warning)
        if self.flags:
            text += ', flags: ' + str(self.flags)
        text += ">"
        return text


def array_split(value, only_this_delim=None):
    """Splits a value into array elements, 1 if no array syntax."""
    delim = ","
    if only_this_delim is not None:
        delim = only_this_delim
    if value.endswith(delim) and not value.endswith("\\" + delim):
        value = value[:-1]
    if delim not in value and only_this_delim is None:
        delim = ' '
    return [i.strip() for i in _scan_string(value, delim)]


def array_join(array):
    """Joins an array of strings into a variable value."""
    delim = ','
    return delim.join(array)


def _scan_string(string, delim=','):
    item = ''
    skip_inds = []
    for quote_pair_match in re.finditer(r"""(''|"")$""", string):
        skip_inds.extend([quote_pair_match.start(0),
                          quote_pair_match.end(0)])
    is_in_quotes = {'"': False, "'": False}
    other_quote = {'"': "'", "'": '"'}
    esc_char = "\\"
    was_escaped = False
    is_escaped = False
    for i, letter in enumerate(string):
        if (letter in is_in_quotes and
            i not in skip_inds and
            not is_in_quotes[other_quote[letter]] and
            not is_escaped):
            is_in_quotes[letter] = not is_in_quotes[letter]
        was_escaped = is_escaped
        is_escaped = (letter == esc_char and not is_escaped)
        if (letter == delim and
            not any(is_in_quotes.values()) and
            not was_escaped):
            yield item
            item = ''
        elif item + letter == string:
            item += letter
            yield item
            item = ''
        else:
            item += letter
    if item != '':
        yield item


def get_ignored_markup(variable):
    """Return pango markup for a variable's ignored reason."""
    markup = ""
    if IGNORED_BY_SECTION in variable.ignored_reason:
        markup += '^'
    if IGNORED_BY_SYSTEM in variable.ignored_reason:
        markup += rose.config.ConfigNode.STATE_SYST_IGNORED
    elif IGNORED_BY_USER in variable.ignored_reason:
        markup += rose.config.ConfigNode.STATE_USER_IGNORED
    if markup:
        markup = "<b>" + markup + "</b> "
    return markup


def _is_quote_state_change(string, index, quote_lookup, quote_state):
    letter = string[index]
    next_letter_is_same = False
    i = 0
    while (i > 0):
        if string[i - 1] != letter:
            break
        i += 1
    prev_letters_escaped = (i % 2 == 0)
    if index < len(string) - 1:
        next_letter_is_same = (string[index + 1] == letter)
    if (letter in quote_state and
        not quote_state[quote_lookup[letter]]):
        if prev_letters_escaped and not next_letter_is_same:
            return True
    return False


def get_value_from_metadata(meta_data):
    """Use raw metadata to get a 'correct' value for a variable."""
    var_value = ''
    if rose.META_PROP_VALUES in meta_data:
        var_value = meta_data[rose.META_PROP_VALUES].replace(' ', '')
        var_value = var_value.replace(',', ' ').split()[0]
    elif rose.META_PROP_TYPE in meta_data:
        if meta_data[rose.META_PROP_TYPE] == 'logical':
            var_value = rose.TYPE_LOGICAL_VALUE_FALSE
        elif meta_data[rose.META_PROP_TYPE] == 'boolean':
            var_value = rose.TYPE_BOOLEAN_VALUE_FALSE
        elif meta_data[rose.META_PROP_TYPE] in ['integer', 'real']:
            var_value = '0'
    return var_value


class RangeSubFunction(object):

    """Holds a checking function."""

    def __init__(self, operator, values):
        self.operator = operator
        self.values = copy.copy(values)
        if isinstance(self.values, tuple):
            self.values = list(self.values)
            for i, val in enumerate(self.values):
                self.values[i] = float(val) if val else None
        else:
            self.values = float(self.values)

    def check(self, number):
        """Check the number against operator and value(s)."""
        if self.operator == '==':
            return number == self.values
        if isinstance(self.values, list):
            return ((self.values[1] is None or self.values[1] >= number) and
                    (self.values[0] is None or number >= self.values[0]))
        return None

    def __repr__(self):
        return "<RangeSubFunction operator:{0} values:{1}>".format(
                                                            self.operator,
                                                            self.values)

class CombinedRangeSubFunction(object):

    def __init__(self, *range_insts):
        self.range_insts = range_insts
    
    def check(self, number):
        return all([r.check(number) for r in self.range_insts])

    def __repr__(self):
        return ("<CombinedRangeSubFunction members:" + 
                 ", ".join([repr(r) for r in self.range_insts]) + ">")


def parse_range_expression(expr):
    """Parse numeric limits on a variable value into a checker function.

    The string may contain ordinary values and ranges e.g.
    range = :-200, -10:-1, 1.2, 2, 3, 5:8, 9:
    The returned function will return True only if the value passed in
    matches at least one of the comma-delimited expressions. The value
    must be passed in as a numeric type (an integer or a float).

    """
    truth_funcs = []
    for items, token in _scan_range_string(expr):
        truth_funcs.append(RangeSubFunction(token, items))
    return lambda n: any([t.check(n) for t in truth_funcs])


def parse_trigger_expression(expr):
    """Parse a string containing a Python-syntax dictionary or list."""
    expr = expr.replace('\n', '')
    trigger_data = {}
    current_key = None
    is_in_group = False
    for item, token in _scan_trigger_string(expr):
        if token == 'KEY':
            current_key = item
            trigger_data.update({item: []})
            is_in_group = True
        elif token == 'GROUP_END':
            if is_in_group:
                # The KEY has been declared, so this is a value.
                trigger_data[current_key].append(item)
            else:
                # Must be a KEY.
                current_key = item
                trigger_data.update({item: []})
            is_in_group = False
        elif token == 'VALUE' and is_in_group:
            trigger_data[current_key].append(item)
    return trigger_data


def parse_type_expression(expr):
    """Parse a string containing a variable type.
    
    If the expression is a simple word such as integer or real, that
    is returned as is. Otherwise it is mapped to a list
    of types. For example:
    
    'integer'       => 'integer'
    'integer, real' => ['integer', 'real']
    
    """
    types = array_split(expr.strip())
    if len(types) == 1:
        types = types[0]
    return types


def _scan_range_string(string):
    for item in REC_RANGE_SPLIT.split(string):
        if REC_RANGE_NUM.match(item):
            yield item, '=='
        elif REC_RANGE_RANGE.match(item):
            yield REC_RANGE_RANGE.match(item).groups(), '<='


def _scan_trigger_string(string):
    item = ''
    is_in_quotes = {'"': False, "'": False}
    other_quote = {'"': "'", "'": '"'}
    delim_tokens = {': ': 'KEY', ',': 'VALUE', ';': 'GROUP_END'}
    esc_char = "\\"
    is_escaped = False
    i = -1
    while i < len(string) - 1:
        i += 1
        letter = string[i]
        is_letter_junk = False
        if (letter in is_in_quotes and
            not is_in_quotes[other_quote[letter]] and
            not is_escaped):
            # Quote state change.
            is_in_quotes[letter] = not is_in_quotes[letter]
        if not any(is_in_quotes.values()) and not is_escaped:
            for delim, token in delim_tokens.items():
                if string[i:i + len(delim)] == delim:
                    # String next contains a valid delimiter
                    # Yield the built-up item and a token
                    yield item.strip(), token
                    item = ''
                    i += len(delim) - 1
                    is_letter_junk = True
                    break
        is_escaped = (letter == esc_char and not is_escaped)      
        if (letter == esc_char and is_escaped and
            not any(is_in_quotes.values()) and i + 1 < len(string)):
            for delim, token in delim_tokens.items():
                if string[i + 1:i + 1 + len(delim)] == delim:
                    # A valid escape character before a delimiter.
                    # Discard the escape character for the parsed text.
                    is_letter_junk = True
                    break
        if not is_letter_junk:
            item += letter
    if item:
        yield item.strip(), delim_tokens[';']
