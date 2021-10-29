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

import metomi.rose

RE_REAL = r"[\+\-]?\d*\.?\d*(?:[de][\+\-]?\d+)?"
RE_CAPT_REAL = '(' + RE_REAL + ')'

REC_RANGE_NUM = re.compile(RE_CAPT_REAL + r"$")
REC_RANGE_SPLIT = re.compile(r'\s*(,)\s*')
REC_RANGE_RANGE = re.compile(
    r"(" + RE_REAL + r"?)" + r"\s*:\s*" + r"(" + RE_REAL + r"?)" + r"(?<!^:)$"
)  # Expression can't just be a colon.
REC_FULL_URL = re.compile(r"^(\w+://|www\.)")

# Ignored types used in metomi.rose.variable.ignored_reason,
# used by macros and user switches.
IGNORED_BY_SECTION = 'Section ignored'
IGNORED_BY_SYSTEM = 'Trigger ignored'
IGNORED_BY_USER = 'User ignored'


class Variable:

    """This class stores the data and metadata of an input variable.

    The variable is ignored if any ignored_reason keys exist,
    and contains errors if the error attribute is not empty.

    """

    __slots__ = [
        "name",
        "value",
        "metadata",
        "old_value",
        "flags",
        "ignored_reason",
        "error",
        "warning",
        "comments",
    ]

    def __init__(
        self,
        name,
        value,
        metadata=None,
        ignored_reason=None,
        error=None,
        warning=None,
        flags=None,
        comments=None,
    ):
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
        if 'type' in self.metadata and not isinstance(
            self.metadata['type'], list
        ):
            self.metadata['type'] = parse_type_expression(
                self.metadata['type']
            )
        if 'element-titles' in self.metadata and not isinstance(
            self.metadata['element-titles'], list
        ):
            self.metadata['element-titles'] = parse_type_expression(
                self.metadata['element-titles']
            )
        # Replace this kind of thing with a proper metadata handler later.
        for key, delim in [
            ("values", ","),
            ("value-titles", None),
            ("value-hints", ","),
        ]:
            if key in self.metadata and not isinstance(
                self.metadata[key], list
            ):
                self.metadata[key] = array_split(
                    self.metadata[key],
                    only_this_delim=delim,
                    remove_esc_char=True,
                )

        return self.metadata

    def to_hashable(self):
        """Return a hashable summary of the current state."""
        return (
            self.name,
            self.value,
            self.metadata['id'],
            tuple(sorted(self.ignored_reason.keys())),
            tuple(self.comments),
        )

    def copy(self):
        new_variable = Variable(
            self.name,
            self.value,
            copy.deepcopy(self.metadata),
            copy.deepcopy(self.ignored_reason),
            copy.deepcopy(self.error),
            copy.deepcopy(self.warning),
            copy.deepcopy(self.flags),
            copy.deepcopy(self.comments),
        )
        new_variable.old_value = self.old_value
        return new_variable

    def getattrs(self):
        """Return a list of attributes and values."""
        attrs = []
        for name in self.__slots__:
            attrs.append((name, getattr(self, name)))
        return attrs

    def __repr__(self):
        text = '<rose.variable :- name: ' + self.name + ', value: '
        text += (
            repr(self.value) + ', old value: ' + repr(self.old_value) + ', '
        )
        text += 'metadata: ' + str(self.metadata)
        text += ', ignored: ' + ['yes', 'no'][self.ignored_reason == {}]
        text += ', error: ' + str(self.error)
        text += ', warning: ' + str(self.warning)
        if self.flags:
            text += ', flags: ' + str(self.flags)
        text += ">"
        return text


def array_split(value, only_this_delim=None, remove_esc_char=False):
    """Splits a value into array elements, 1 if no array syntax."""
    delim = ","
    if only_this_delim is not None:
        delim = only_this_delim
    if delim not in value and only_this_delim is None:
        delim = ' '
    lex = _scan_string(value.strip(), delim, remove_esc_char)
    return [item.strip() for item in lex]


def array_join(array):
    """Joins an array of strings into a variable value."""
    delim = ','
    return delim.join(array)


def _scan_string(value, delim=',', remove_esc_char=False):
    """Split "value" by "delim", handling quotes."""
    item = ''
    skip_inds = []
    for quote_pair_match in re.finditer(r"""(''|"")$""", value):
        skip_inds.extend([quote_pair_match.start(0), quote_pair_match.end(0)])
    is_in_quotes = {'"': False, "'": False}
    other_quote = {'"': "'", "'": '"'}
    esc_char = "\\"
    was_escaped = False
    is_escaped = False
    letter = None
    for i, letter in enumerate(value):
        if (
            letter in is_in_quotes
            and i not in skip_inds
            and not is_in_quotes[other_quote[letter]]
            and not is_escaped
        ):
            is_in_quotes[letter] = not is_in_quotes[letter]
        was_escaped = is_escaped
        is_escaped = letter == esc_char and not is_escaped
        if remove_esc_char and was_escaped and letter in (delim + esc_char):
            item = item[:-1] + letter
        elif (
            letter == delim
            and not any(is_in_quotes.values())
            and not was_escaped
        ):
            yield item
            item = ''
        elif item + letter == value:
            item += letter
            yield item
            item = ''
        else:
            item += letter
    if item or (
        letter == delim and not any(is_in_quotes.values()) and not was_escaped
    ):
        yield item


def expand_format_string(format_string, variable):
    """Expand a string that references variable properties or metadata."""
    data_metadata = {}
    for attr in dir(variable):
        if attr.startswith("_"):
            continue
        data_metadata[attr] = str(getattr(variable, attr))
    data_metadata.update(variable.metadata)
    try:
        format_string = format_string.format(**data_metadata)
    except (IndexError, KeyError):
        return None
    return format_string


def get_ignored_markup(variable):
    """Return pango markup for a variable's ignored reason."""
    markup = ""
    if IGNORED_BY_SECTION in variable.ignored_reason:
        markup += metomi.rose.config.STATE_SECT_IGNORED
    if IGNORED_BY_SYSTEM in variable.ignored_reason:
        markup += metomi.rose.config.ConfigNode.STATE_SYST_IGNORED
    elif IGNORED_BY_USER in variable.ignored_reason:
        markup += metomi.rose.config.ConfigNode.STATE_USER_IGNORED
    if markup:
        markup = "<b>" + markup + "</b> "
    return markup


def _is_quote_state_change(string, index, quote_lookup, quote_state):
    letter = string[index]
    next_letter_is_same = False
    i = 0
    while i > 0:
        if string[i - 1] != letter:
            break
        i += 1
    prev_letters_escaped = i % 2 == 0
    if index < len(string) - 1:
        next_letter_is_same = string[index + 1] == letter
    if letter in quote_state and not quote_state[quote_lookup[letter]]:
        if prev_letters_escaped and not next_letter_is_same:
            return True
    return False


def get_value_from_metadata(meta_data):
    """Use raw metadata to get a 'correct' value for a variable."""
    var_value = ''
    if metomi.rose.META_PROP_VALUES in meta_data:
        var_value = array_split(meta_data[metomi.rose.META_PROP_VALUES])[0]
    elif metomi.rose.META_PROP_TYPE in meta_data:
        var_type = meta_data[metomi.rose.META_PROP_TYPE]
        if var_type == 'logical':
            var_value = metomi.rose.TYPE_LOGICAL_VALUE_FALSE
        elif var_type == 'boolean':
            var_value = metomi.rose.TYPE_BOOLEAN_VALUE_FALSE
        elif var_type in ['integer', 'real']:
            var_value = '0'
        elif var_type == 'character':
            var_value = "''"
        elif var_type == 'quoted':
            var_value = '""'
    elif metomi.rose.META_PROP_VALUE_HINTS in meta_data:
        var_value = array_split(meta_data[metomi.rose.META_PROP_VALUE_HINTS])[
            0
        ]
    return var_value


class RangeSubFunction:

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
            return (self.values[1] is None or self.values[1] >= number) and (
                self.values[0] is None or number >= self.values[0]
            )
        return None

    def __repr__(self):
        return "<RangeSubFunction operator:{0} values:{1}>".format(
            self.operator, self.values
        )


class CombinedRangeSubFunction:
    def __init__(self, *range_insts):
        self.range_insts = range_insts

    def check(self, number):
        return all([r.check(number) for r in self.range_insts])

    def __repr__(self):
        return (
            "<CombinedRangeSubFunction members:"
            + ", ".join([repr(r) for r in self.range_insts])
            + ">"
        )


class RangeSyntaxError(Exception):

    """Raised when the metadata range option is passed invalid syntax."""

    def __str__(self):
        return "Invalid syntax: {0}".format(self.args[0])


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
    return lambda n: any(t.check(n) for t in truth_funcs)


def parse_trigger_expression(expr):
    """Parse a trigger expression."""
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
    types = array_split(expr.strip(), only_this_delim=",")
    if len(types) == 1:
        types = types[0]
    return types


def _scan_range_string(string):
    for item in REC_RANGE_SPLIT.split(string):
        if REC_RANGE_NUM.match(item):
            yield item, '=='
        elif REC_RANGE_RANGE.match(item):
            yield REC_RANGE_RANGE.match(item).groups(), '<='
        elif item != ",":
            raise RangeSyntaxError(item)


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
        if (
            letter in is_in_quotes
            and not is_in_quotes[other_quote[letter]]
            and not is_escaped
        ):
            # Quote state change.
            is_in_quotes[letter] = not is_in_quotes[letter]
        if not any(is_in_quotes.values()) and not is_escaped:
            for delim, token in delim_tokens.items():
                if string[i : i + len(delim)] == delim:
                    # String next contains a valid delimiter
                    # Yield the built-up item and a token
                    yield item.strip(), token
                    item = ''
                    i += len(delim) - 1
                    is_letter_junk = True
                    break
        is_escaped = letter == esc_char and not is_escaped
        if (
            letter == esc_char
            and is_escaped
            and not any(is_in_quotes.values())
            and i + 1 < len(string)
        ):
            for delim, token in delim_tokens.items():
                if string[i + 1 : i + 1 + len(delim)] == delim:
                    # A valid escape character before a delimiter.
                    # Discard the escape character for the parsed text.
                    is_letter_junk = True
                    break
        if not is_letter_junk:
            item += letter
    if item:
        yield item.strip(), delim_tokens[';']
