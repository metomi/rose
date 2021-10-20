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
import inspect
import re
from typing import Any, Dict, Optional, Type

import metomi.rose.variable

REC_CHARACTER = re.compile(r"'(?:[^']|'')*'$")


class MetaType:

    KEY: Optional[str] = None
    meta_type_classes: Dict[Any, Type] = {}

    @classmethod
    def get_meta_type(cls, key):
        """Return the class for a named meta data type."""
        if key in cls.meta_type_classes:
            return cls.meta_type_classes[key]
        for item in globals().values():
            if inspect.isclass(item):
                if item != cls and issubclass(item, cls):
                    if item.KEY == key:
                        cls.meta_type_classes[key] = item
                        return item
        raise KeyError(key)


class BooleanMetaType(MetaType):

    KEY = "boolean"
    WARNING = "Not true/false: {0}"

    def is_valid(self, value):
        if value in [
            metomi.rose.TYPE_BOOLEAN_VALUE_TRUE,
            metomi.rose.TYPE_BOOLEAN_VALUE_FALSE,
        ]:
            return [True, None]
        else:
            return [False, self.WARNING.format(repr(value))]

    def transform(self, value):
        if value.upper() == metomi.rose.TYPE_BOOLEAN_VALUE_FALSE.upper():
            return metomi.rose.TYPE_BOOLEAN_VALUE_FALSE
        if value.upper() == metomi.rose.TYPE_BOOLEAN_VALUE_TRUE.upper():
            return metomi.rose.TYPE_BOOLEAN_VALUE_TRUE
        return value


class CharacterMetaType(MetaType):

    KEY = "character"
    WARNING = "Not in a valid single quoted format: {0}"

    def is_valid(self, value):
        if not REC_CHARACTER.match(value):
            return [False, self.WARNING.format(repr(value))]
        else:
            return [True, None]

    def transform(self, value):
        if value.startswith('"') and value.endswith('"') and "'" not in value:
            value = "'" + value[1:-1] + "'"
        else:
            if not value.endswith("'"):
                value = value + "'"
            if not value.startswith("'"):
                value = "'" + value
        return value


class IntegerMetaType(MetaType):

    KEY = "integer"
    WARNING = "Not an integer: {0}"

    def is_valid(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return [False, self.WARNING.format(repr(value))]
        return [True, None]


class PythonBooleanMetaType(MetaType):

    KEY = "python_boolean"
    WARNING = "Not a valid Python boolean format (True/False): {0}"

    def is_valid(self, value):
        if value not in [
            metomi.rose.TYPE_PYTHON_BOOLEAN_VALUE_TRUE,
            metomi.rose.TYPE_PYTHON_BOOLEAN_VALUE_FALSE,
        ]:
            return [False, self.WARNING.format(repr(value))]
        return [True, None]


class PythonListMetaType(MetaType):

    KEY = "python_list"
    WARNING = "Not a valid Python list format: {0}"

    def is_valid(self, value):
        try:
            cast_value = ast.literal_eval(value)
            if not isinstance(cast_value, list):
                return [False, self.WARNING.format(repr(value))]
        except (SyntaxError, ValueError):
            return [False, self.WARNING.format(repr(value))]
        return [True, None]


class SpacedListMetaType(MetaType):

    KEY = "spaced_list"
    WARNING = "Not a valid spaced list format: {0}"

    def is_valid(self, value):
        try:
            cast_value = value.split(" ")
            if not isinstance(cast_value, list):
                return [False, self.WARNING.format(repr(value))]
        except (SyntaxError, ValueError):
            return [False, self.WARNING.format(repr(value))]
        return [True, None]


class LogicalMetaType(MetaType):

    KEY = "logical"
    WARNING = "Not Fortran true/false: {0}"

    def is_valid(self, value):
        if value not in [
            metomi.rose.TYPE_LOGICAL_VALUE_TRUE,
            metomi.rose.TYPE_LOGICAL_VALUE_FALSE,
        ]:
            return [False, self.WARNING.format(repr(value))]
        return [True, None]

    def transform(self, value):
        if (
            value.upper() == '.F.'
            or value.upper() == metomi.rose.TYPE_LOGICAL_VALUE_FALSE.upper()
        ):
            return metomi.rose.TYPE_LOGICAL_VALUE_FALSE
        if (
            value.upper() == '.T.'
            or value.upper() == metomi.rose.TYPE_LOGICAL_VALUE_TRUE.upper()
        ):
            return metomi.rose.TYPE_LOGICAL_VALUE_TRUE
        return value


class RealMetaType(MetaType):

    KEY = "real"
    WARNING = "Not a real number: {0}"

    def is_valid(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return [False, self.WARNING.format(repr(value))]
        return [True, None]


class QuotedMetaType(MetaType):

    KEY = "quoted"
    WARNING = "Not in a valid double quoted format: {0}"

    def is_valid(self, value):
        quote_segs = value.split('"')
        if len(quote_segs) < 3 or quote_segs[0] or quote_segs[-1]:
            return [False, self.WARNING.format(repr(value))]
        for i, seg in enumerate(quote_segs):
            num_end_esc = len(seg) - len(seg.rstrip("\\"))
            odd_num_end_esc = num_end_esc % 2 == 1
            if (i == len(quote_segs) - 2 and odd_num_end_esc) or (
                0 < i < len(quote_segs) - 2 and not odd_num_end_esc
            ):
                return [False, self.WARNING.format(repr(value))]
        return [True, None]

    def transform(self, value):
        if (
            value.startswith('"')
            and value.endswith('"')
            and '"' not in value[1:-1]
            and "\\" not in value[1:-1]
        ):
            value = '"' + value[1:-1] + '"'
        else:
            if not value.endswith('"'):
                value = value + '"'
            if not value.startswith('"'):
                value = '"' + value
        return value


def meta_type_checker(value, meta_type):
    item = MetaType.get_meta_type(meta_type)
    item = item()
    return item.is_valid(value)


def meta_type_transform(value, meta_type):
    item = MetaType.get_meta_type(meta_type)
    item = item()
    try:
        return item.transform(value)
    except Exception:
        return False
