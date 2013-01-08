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

import inspect
import re
import rose.variable

REC_CHARACTER = re.compile(r"'(?:[^']|'')*'$")


class MetaType():

    KEY = None
    meta_type_classes = {}

    @classmethod
    def get_meta_type(cls, key):
        """Return the class for a named meta data type."""
        if cls.meta_type_classes.has_key(key):
            return cls.meta_type_classes[key]
        for c in globals().values():
            if inspect.isclass(c):
                if c != cls and issubclass(c, cls):
                    if c.KEY == key:
                        cls.meta_type_classes[key] = c
                        return c
        raise KeyError(key)

    
class BooleanMetaType(MetaType):

    KEY = "boolean"
    WARNING = "Not true/false: {0}"
    
    def is_valid(self, value):
        if value in [rose.TYPE_BOOLEAN_VALUE_TRUE,
                     rose.TYPE_BOOLEAN_VALUE_FALSE]:
            return [True, None]
        else:
            return [False, self.WARNING.format(repr(value))]

    def transform(self, value):
        if value.upper() == rose.TYPE_BOOLEAN_VALUE_FALSE.upper():
            return rose.TYPE_BOOLEAN_VALUE_FALSE
        if value.upper() == rose.TYPE_BOOLEAN_VALUE_TRUE.upper():
            return rose.TYPE_BOOLEAN_VALUE_TRUE
        return value


class CharacterMetaType(MetaType):

    KEY = "character"
    WARNING = "Value {0} isn't in a valid single quoted format"
    
    def is_valid(self, value):
        if not REC_CHARACTER.match(value):
            return [False, self.WARNING.format(repr(value))]
        else:
            return [True, None]    

    def transform(self, value):
        if (value.startswith('"') and value.endswith('"') and
            "'" not in value):
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


class LogicalMetaType(MetaType):

    KEY = "logical"
    WARNING = "Not Fortran true/false: {0}"
    
    def is_valid(self, value):    
        if value not in [rose.TYPE_LOGICAL_VALUE_TRUE,
                         rose.TYPE_LOGICAL_VALUE_FALSE]:
            return [False, self.WARNING.format(repr(value))]
        return [True, None]

    def transform(self, value):
        if (value.upper() == '.F.' or
            value.upper() == rose.TYPE_LOGICAL_VALUE_FALSE.upper()):
            return rose.TYPE_LOGICAL_VALUE_FALSE
        if (value.upper() == '.T.' or
            value.upper() == rose.TYPE_LOGICAL_VALUE_TRUE.upper()):
            return rose.TYPE_LOGICAL_VALUE_TRUE
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
    WARNING = "Value {0} isn't in a valid double quoted format"
    
    def is_valid(self, value):
        quote_segs = value.split('"')
        if len(quote_segs) < 3 or quote_segs[0] or quote_segs[-1]:
            return [False, self.WARNING.format(repr(value))]
        for i, s in enumerate(quote_segs):
            num_end_esc = len(s) - len(s.rstrip("\\"))
            odd_num_end_esc = num_end_esc % 2 == 1
            if ((i == len(quote_segs) - 2 and odd_num_end_esc) or
                (0 < i < len(quote_segs) - 2 and not odd_num_end_esc)):
                return [False, self.WARNING.format(repr(value))]
        return [True, None]

    def transform(self, value):
        if (value.startswith('"') and value.endswith('"') and
            '"' not in value[1:-1] and "\\" not in value[1:-1]):
            value = '"' + value[1:-1] + '"'
        else:
            if not value.endswith('"'):
                value = value + '"'
            if not value.startswith('"'):
                value = '"' + value
        return value    


def meta_type_checker(value, meta_type):
    c = MetaType.get_meta_type(meta_type)
    c = c()
    return c.is_valid(value)

def meta_type_transform(value, meta_type):
    c = MetaType.get_meta_type(meta_type)
    c = c()
    try:
        return c.transform(value)
    except:
        return False
