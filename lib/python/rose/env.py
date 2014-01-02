# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
#
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
#-----------------------------------------------------------------------------
"""Environment variable substitution in strings.

Note: os.path.expandvars(path) does not work correctly because unbound
environment variables are left unchanged.

"""

import os
import re
from rose.reporter import Event
import sys

#_RE = re.compile(r"""
#    \A                                 # start
#    (?P<head>.*?)                      # shortest of anything
#    (?P<escape>\\*)                    # escapes
#    (?P<sigil>\$)                      # variable sigil, dollar
#    (?P<brace_open>\{)?                # brace open, optional
#    (?P<name>[A-z_]\w*)                # variable name
#    (?P<brace_close>(?(brace_open)\})) # brace close, if brace_open matches
#    (?P<tail>.*)                       # rest of string
#    \Z                                 # end
#""", re.M | re.S | re.X)
_RE = re.compile(r"\A"
                 r"(?P<head>.*?)"
                 r"(?P<escape>\\*)"
                 r"(?P<sigil>\$)"
                 r"(?P<brace_open>\{)?"
                 r"(?P<name>[A-z_]\w*)"
                 r"(?P<brace_close>(?(brace_open)\}))"
                 r"(?P<tail>.*)"
                 r"\Z",
                 re.M | re.S)


class EnvExportEvent(Event):

    RE_SHELL_ESCAPE = re.compile(r"([\"'\s])")

    def __str__(self):
        key, value = self.args
        return "export %s=%s" % (key, self.RE_SHELL_ESCAPE.sub(r"\\\1", value))


class UnboundEnvironmentVariableError(Exception):

    def __repr__(self):
        return "[UNDEFINED ENVIRONMENT VARIABLE] %s" % (self.args)

    __str__ = __repr__


def env_export(key, value, event_handler=None):
    os.environ[key] = value
    if callable(event_handler):
        event_handler(EnvExportEvent(key, value))


def env_var_escape(s):
    """Escape $NAME and ${NAME} syntax in "s".
    """
    ret = ""
    tail = s
    while tail:
        match = _RE.match(tail)
        if match:
            m = match.groupdict()
            if not m["brace_open"]:
                m["brace_open"] = ""
            symbol = m["sigil"] + m["brace_open"] + m["name"] + m["brace_close"]
            ret += m["head"] + m["escape"] * 2 + "\\" + symbol
            tail = m["tail"]
        else:
            ret += tail
            tail = ""
    return ret


def env_var_process(s, unbound=None):
    """Substitute environment variables into a string.

    For each $NAME and ${NAME} in "s", substitute with the value
    of the environment variable NAME. If NAME is not defined in the
    environment and "unbound" is None, raise an
    UnboundEnvironmentVariableError. If NAME is not defined in the
    environment and "unbound" is not None, substitute NAME with the
    value of "unbound".

    """
    ret = ""
    tail = s
    while tail:
        match = _RE.match(tail)
        if match:
            m = match.groupdict()
            if not m["brace_open"]:
                m["brace_open"] = ""
            symbol = m["sigil"] + m["brace_open"] + m["name"] + m["brace_close"]
            substitute = symbol
            if len(m["escape"]) % 2 == 0:
                if os.environ.has_key(m["name"]):
                    substitute = os.environ[m["name"]]
                elif unbound is not None:
                    substitute = str(unbound)
                else:
                    raise UnboundEnvironmentVariableError(m["name"])
            ret += m["head"] + m["escape"][0 : len(m["escape"]) / 2] + substitute
            tail = m["tail"]
        else:
            ret += tail
            tail = ""
    return ret


environment_variable_process = env_var_process


def contains_env_var(s):
    """Check if a string contains an environment variable."""
    match = _RE.match(s)
    return (match and len(match.groupdict()["escape"]) % 2 == 0)
