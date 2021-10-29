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
"""Utilities for parsing namelist files."""

import io
import re

# ERROR REPORTING:
ERROR_UPPERCASE = "name should be lowercase"


# REGULAR EXPRESSIONS:
def _rec(exp):
    return re.compile(exp, re.M | re.S | re.X)


# Matches a separator
RE_SEP = r","
# Matches a natural number counter
RE_NATURAL = r"\d+"
# Matches a number with a floating point
RE_FLOAT = r"(?:\.\d+)|(?:" + RE_NATURAL + r")(?:\.\d*)?"
# Matches namelist literals for intrinsic types
RE_INTEGER = r"[\+\-]?(?:" + RE_NATURAL + r")"
REC_INTEGER = _rec(r"\A(?:" + RE_INTEGER + r")\Z")
RE_REAL = r"[\+\-]?(?:" + RE_FLOAT + r")(?:[deDE][\+\-]?\d+)?"
REC_REAL = _rec(r"\A(?:" + RE_REAL + r")\Z")
RE_COMPLEX = r"\(\s*" + RE_REAL + r"\s*" + RE_SEP + r"\s*" + RE_REAL + r"\s*\)"
REC_COMPLEX = _rec(r"\A(?:" + RE_COMPLEX + r")\Z")
RE_LOGICAL = r"\.(?:[Tt][Rr][Uu][Ee]|[Ff][Aa][Ll][Ss][Ee])\."
REC_LOGICAL = _rec(r"\A(?:" + RE_LOGICAL + r")\Z")
RE_CHARACTER = r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\""
REC_CHARACTER = _rec(r"\A(?:" + RE_CHARACTER + r")\Z")
# Matches a complex literal, capture real and imaginary parts
RE_COMPLEX_R_I = (
    r"\(\s*(" + RE_REAL + r")\s*" + RE_SEP + r"\s*(" + RE_REAL + r")\s*\)"
)
REC_COMPLEX_R_I = _rec(RE_COMPLEX_R_I)
# Matches a comment
RE_COMMENT = r"(?:! .*)"
# Matches a name, captures name
RE_NAME = r"(?:[A-Za-z_]\w*)"
# Matches an array index (range)
RE_NAME_INDEX2 = r":(?:" + RE_INTEGER + r")?"
RE_NAME_INDEX1 = RE_INTEGER + r"(?:" + RE_NAME_INDEX2 + r")?|" + RE_NAME_INDEX2
RE_NAME_INDEX0 = (
    r"\((?:(?:" + RE_NAME_INDEX1 + r")(?:," + RE_NAME_INDEX1 + r")*)\)"
)
RE_NAME_INDEX = r"(?:" + RE_NAME_INDEX0 + r"(?!" + RE_NAME_INDEX0 + r"))"
# Matches a derived type component in a name
RE_NAME_COMP = r"(?:\%" + RE_NAME + r")"
# Matches an object name
RE_OBJECT_NAME = (
    r"(?:" + RE_NAME + r"(?:" + RE_NAME_COMP + r"|" + RE_NAME_INDEX + r")*)"
)
# Matches an object initialisation, captures designator
RE_OBJECT_INIT = r"(" + RE_OBJECT_NAME + r")\s*="
# Matches a value, captures value
RE_VALUE = (
    r"(" + r"|".join([RE_REAL, RE_LOGICAL, RE_CHARACTER, RE_COMPLEX]) + r")"
)
REC_VALUE = _rec(r"\A" + RE_VALUE + r"\Z")
# Matches a repeat-value, captures count and value
RE_VALUE_REPEAT = r"(" + RE_NATURAL + r")\*(?:" + RE_VALUE + r")?"
REC_VALUE_REPEAT = _rec(r"\A" + RE_VALUE_REPEAT + r"\Z")
# Matches a group initialisation, captures group name
RE_GROUP_INIT = r"[^&]* &(" + RE_NAME + r")"
# Matches a group termination
RE_GROUP_TERM = r"/"
# Real literal tidy
REC_REAL_TIDY = [
    [_rec(r"[DdE]"), r"e"],  # 1.d0, 1.D0, 1.E0 => 1.e0
    [_rec(r"\A([\+\-]?)\."), r"\g<1>0."],  # .1 => 0.1, -.1 => -0.1
    [_rec(r"\A([\+\-]?\d+)(e)"), r"\1.0\2"],  # 1e1 => 1.0e1
    [_rec(r"e[\+\-]?0+\Z"), r""],  # 1.0e0 => 1.0
    [_rec(r"e0+"), r"e"],  # 1.0e01 => 1.0e1
    [_rec(r"e([\+\-])0+"), r"e\1"],  # 1.0e-01 => 1.0e-1
    [_rec(r"\.(e|\Z)"), r".0\1"],  # 1. => 1.0, 1.e0 => 1.0e0
    [_rec(r"^0+(\d)"), r"\1"],  # 02.0 => 2.0, 000.5 => 0.5
    [_rec(r"^([+-])0+(\d)"), r"\1\2"],
]  # +02.0 => +2.0, -000.5 => -0.5


class NamelistGroup:
    """Represent a namelist group.

    It has the following attributes:
    name: the name of the namelist group.
    objects: a list containing the objects (i.e. key=value pairs) of the
             namelist groups. Each object is a NamelistObject object.
    file_: (optional) the name of the source file containing this namelist
          group.

    """

    def __init__(self, name, objects=None, file_=None):
        self.name = name
        if objects is None:
            objects = []
        self.objects = objects
        self.file_ = file_

    def __repr__(self):
        object_strings = [str(obj) for obj in self.objects]
        object_strings.sort()
        return "&%s\n%s\n/\n" % (self.name, "\n".join(object_strings))


class NamelistObject:
    """Represent an object in a namelist group.

    An object can be an assignment or a key=value pair in a
    namelist group.

    It has the following attributes:
    lhs: left hand side (i.e. the key) of the assignment in the namelist
         object.
    rhs: right hand side (i.e. the value) of the assignment in the namelist
         object.  It is a list of strings representing the values.

    """

    IDX_R = 0  # index: repeat
    IDX_V = 1  # index: value

    def __init__(self, lhs, rhs=None):
        self.lhs = lhs
        if rhs is None:
            rhs = []
        self.rhs = rhs

    def __repr__(self):
        return "%s=%s," % (self.lhs, self.get_rhs_as_string())

    def append_rhs(self, value, repeat=1):
        """Correctly append values to the right hand side of the assignment."""
        self.rhs.extend([value] * repeat)

    def _collect_rhs_repeats(self, min_repeat_length=5):
        """Gather together repeated items."""
        if len(self.rhs) < min_repeat_length:
            return [str(v) for v in self.rhs]
        items = []  # ([value, repeat], ...)
        for value in self.rhs:
            if items and str(value) == str(items[-1][self.IDX_V]):
                items[-1][self.IDX_R] += 1
            else:
                items.append([1, value])
        values = []
        for item in items:
            if item[self.IDX_R] > 1:
                if item[self.IDX_R] >= min_repeat_length and REC_VALUE.search(
                    str(item[self.IDX_V])
                ):
                    values.append(
                        str(item[self.IDX_R]) + "*" + str(item[self.IDX_V])
                    )
                else:
                    values.extend([str(item[self.IDX_V])] * item[self.IDX_R])
            else:
                values.append(item[self.IDX_V])
        return [str(v) for v in values]

    def get_rhs_as_string(self, min_repeats=5, wrapped=False, max_len=60):
        """Return the RHS of this object as a nicely formatted string."""
        rhs_items = self._collect_rhs_repeats(min_repeats)
        if not wrapped:
            return ",".join(rhs_items)
        lines = [""]
        for item in rhs_items:
            if lines[-1] and len(lines[-1] + item + ",") > max_len:
                lines.append("")
            lines[-1] += item + ","
        lines[-1] = lines[-1].rpartition(",")[0]
        return "\n".join(lines)


class NamelistValue:
    """Represent a value in a namelist object."""

    def __init__(self, value_init, quote=False):
        self.quote = quote
        self.value_init = value_init
        self.value = None

    def __repr__(self):
        if self.value is None:
            self.tidy()
        return str(self.value)

    __str__ = __repr__

    def tidy(self):
        self.value = self.value_init
        if self.value is not None:
            if self.quote:
                self.value = self._tidy_character(self.value)
            elif REC_REAL.match(self.value):
                self.value = self._tidy_real(self.value)
            elif REC_COMPLEX.match(self.value):
                self.value = self._tidy_complex(self.value)
            elif REC_LOGICAL.match(self.value):
                self.value = self.value.lower()
            else:
                self.value = self._tidy_character(self.value)
        else:
            self.value = ""
        return self

    def _tidy_character(self, value):
        return "'" + value.replace("'", "''") + "'"

    def _tidy_complex(self, value):
        match = REC_COMPLEX_R_I.match(value)
        real, img = match.group(1, 2)
        return "(%s,%s)" % (self._tidy_real(real), self._tidy_real(img))

    def _tidy_real(self, value):
        for rec, sub in REC_REAL_TIDY:
            value = rec.sub(sub, value)
        return value


class _ParseContext:
    """Convenient object for storing the parser's state."""

    def __init__(self):
        self.files = []
        self.handle = None
        self.line = None
        self.line_length = None
        self.line_number = None
        self.state = None
        self.tail = None


def parse(in_files):
    """Parse namelist groups in a list of input files "in_files".
    Return a list of NamelistGroup objects.
    """
    handler_of = {
        "group-init": _handle_group,
        "name": _handle_name,
        "value": _handle_value,
        "value-repeat": _handle_value,
    }
    groups = []
    ctx = _ParseContext()
    ctx.files += in_files
    for tag, filename, data in iter(lambda: _parse_func(ctx), None):
        if tag in handler_of:
            handler_of[tag](groups, filename, data)
    return groups


_PARSERS_FOR = {
    "": [[RE_GROUP_INIT, "group-init", "group"], [r".*", "comment", None]],
    "group": [
        [RE_OBJECT_INIT, "name", "value0"],
        [RE_GROUP_TERM, "group-term", ""],
        [RE_COMMENT, "comment", None],
    ],
    "value0": [
        [RE_OBJECT_INIT, "name", "value0"],
        [RE_VALUE_REPEAT, "value-repeat", "value1"],
        [RE_VALUE, "value", "value1"],
        [RE_SEP, "value", None],
        [RE_GROUP_TERM, "group-term", ""],
        [RE_COMMENT, "comment", None],
    ],
    "value1": [
        [RE_OBJECT_INIT, "name", "value0"],
        [RE_VALUE_REPEAT, "value-repeat", None],
        [RE_VALUE, "value", None],
        [RE_SEP, "value-sep", "value0"],
        [RE_GROUP_TERM, "group-term", ""],
        [RE_COMMENT, "comment", None],
    ],
}


def _parse_func(ctx):
    """The parsers at each "state" - each "state" has a set of parsers.

    Each parser contains a regular expression, the item type to return
    on a match, and the name of the next state (if the match triggers
    a state change).

    If the current string does not match, it will move on to the next
    parser. A syntax error is raised if no more parsers are available
    for the current state.

    """
    while ctx.files:
        if ctx.handle is None:
            ctx.handle = ctx.files[0]
            if not isinstance(ctx.handle, io.IOBase):
                ctx.handle = open(ctx.handle, "r")
            # FIXME: may be incorrect for already opened file
            ctx.line_number = 0
            ctx.state = ""
        while ctx.handle is not None:
            if ctx.tail:
                for pattern, tag, next_state in _PARSERS_FOR[ctx.state]:
                    rec = _rec(r"\A\s*(?:" + pattern + r")\s*(.*)\Z")
                    match = rec.match(ctx.tail)
                    if match:
                        data = list(match.groups())
                        ctx.tail = data.pop()
                        if next_state is not None:
                            ctx.state = next_state
                        return [tag, ctx.handle.name, data]
                exc = SyntaxError()
                exc.filename = ctx.handle.name
                exc.lineno = ctx.line_number
                exc.offset = ctx.line_length - len(ctx.tail) + 1
                exc.text = ctx.line
                raise exc
            else:
                ctx.line = ctx.handle.readline()
                ctx.line_number += 1
                if ctx.line:
                    ctx.line = ctx.line.rstrip()
                    ctx.line_length = len(ctx.line)
                    ctx.tail = ctx.line
                    ctx.tail = ctx.tail.lstrip()
                else:
                    if ctx.files[0] != ctx.handle:
                        ctx.handle.close()
                    ctx.files.pop(0)
                    ctx.handle = None
    return None


def _handle_group(groups, file_, data):
    groups.append(NamelistGroup(data[0], file_=file_))


def _handle_name(groups, _, data):
    groups[-1].objects.append(NamelistObject(data[0]))


def _handle_value(groups, _, data):
    value = None
    quote = False
    repeat = 1
    if len(data) >= 2:
        repeat = int(data.pop(0))
    if data:
        value = data[0]
    if value and REC_CHARACTER.match(value):
        quote_mark = value[0]
        value = value[1 : len(value) - 1]
        value = value.replace(quote_mark + quote_mark, quote_mark)
        quote = True
    groups[-1].objects[-1].append_rhs(NamelistValue(value, quote), repeat)


def standard_format(values):
    """Standardise a namelist value list (e.g. removing all repeats)."""
    for i, value in enumerate(values):
        values[i] = _expand_repeats(value)
    return ",".join(values)


def _expand_repeats(val_item):
    """Expand repeated items e.g. "3*.true." to ".true.,.true.,.true."."""
    search = REC_VALUE_REPEAT.search(val_item)
    if search:
        repeat, data = search.groups()
        if data is None:
            # null string, e.g. '7*'
            data = ""
        return ",".join([data] * int(repeat))
    else:
        return val_item


def pretty_format_value(values):
    """Pretty-format a namelist value list."""
    nm_item = NamelistObject("", values)
    return nm_item.get_rhs_as_string(wrapped=True)


def pretty_format_keys(keys):
    """Pretty-format namelist keys."""
    return [item.lower() for item in keys]


def validate_config(config, meta_config, add_report_func):
    """Validate a configuration."""
    for keys, node in config.walk():
        section = keys[0]
        if not section.startswith("namelist:"):
            continue
        if len(keys) == 1:
            option = None
            value = None
            is_error = section.lower() != section
        else:
            option = keys[1]
            value = node.value
            is_error = option.lower() != option
        if is_error:
            add_report_func(section, option, value, ERROR_UPPERCASE)
