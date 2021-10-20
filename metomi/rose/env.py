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
# ----------------------------------------------------------------------------
"""Environment variable substitution in strings.

Note: os.path.expandvars(path) does not work correctly because unbound
environment variables are left unchanged.

"""

import os
import re

from metomi.rose.reporter import Event

# _RE_DEFAULT = re.compile(r"""
#     \A                                 # start
#     (?P<head>.*?)                      # shortest of anything
#     (?P<escape>\\*)                    # escapes
#     (?P<symbol>                        # start symbol
#         \$                                 # variable sigil, dollar
#         (?P<brace_open>\{)?                # brace open, optional
#         (?P<name>[A-z_]\w*)                # variable name
#         (?(brace_open)\})                  # brace close, if brace_open
#     )                                  # end symbol
#     (?P<tail>.*)                       # rest of string
#     \Z                                 # end
# """, re.M | re.S | re.X)
_RE_DEFAULT = re.compile(
    r"\A"
    r"(?P<head>.*?)"
    r"(?P<escape>\\*)"
    r"(?P<symbol>"
    r"\$"
    r"(?P<brace_open>\{)?"
    r"(?P<name>[A-z_]\w*)"
    r"(?(brace_open)\})"
    r")"
    r"(?P<tail>.*)"
    r"\Z",
    re.M | re.S,
)


# _RE_BRACE = re.compile(r"""
#     \A                                 # start
#     (?P<head>.*?)                      # shortest of anything
#     (?P<escape>\\*)                    # escapes
#     (?P<symbol>\$\{                    # start symbol ${
#         (?P<name>[A-z_]\w*)                # variable name
#     \})                                # } end symbol
#     (?P<tail>.*)                       # rest of string
#     \Z                                 # end
# """, re.M | re.S | re.X)
_RE_BRACE = re.compile(
    r"\A"
    r"(?P<head>.*?)"
    r"(?P<escape>\\*)"
    r"(?P<symbol>\$\{"
    r"(?P<name>[A-z_]\w*)"
    r"\})"
    r"(?P<tail>.*)"
    r"\Z",
    re.M | re.S,
)


_MATCH_MODES = {"brace": _RE_BRACE, "default": _RE_DEFAULT, None: _RE_DEFAULT}


_EXPORTED_ENVS = {}


class EnvExportEvent(Event):

    """Event raised when an environment variable is exported."""

    RE_SHELL_ESCAPE = re.compile(r"([\"'\s])")

    def __str__(self):
        key, value = self.args
        return "export %s=%s" % (key, self.RE_SHELL_ESCAPE.sub(r"\\\1", value))


class UnboundEnvironmentVariableError(Exception):

    """An error raised on attempt to substitute an unbound variable."""

    def __repr__(self):
        return "[UNDEFINED ENVIRONMENT VARIABLE] %s" % (self.args)

    __str__ = __repr__


def env_export(key, value, event_handler=None):
    """Export an environment variable."""
    if key not in _EXPORTED_ENVS or os.environ.get(key) != value:
        # N.B. Should be safe, because the list of environment variables is
        #      normally quite small.
        _EXPORTED_ENVS[key] = value
        os.environb[key.encode('UTF-8')] = value.encode('UTF-8')
        if callable(event_handler):
            event_handler(EnvExportEvent(key, value))


def env_var_escape(text, match_mode=None):
    """Escape $NAME and ${NAME} syntax in "text"."""
    ret = ""
    tail = text
    while tail:
        match = _MATCH_MODES[match_mode].match(tail)
        if match:
            groups = match.groupdict()
            ret += (
                groups["head"] + groups["escape"] * 2 + "\\" + groups["symbol"]
            )
            tail = groups["tail"]
        else:
            ret += tail
            tail = ""
    return ret


def env_var_process(text, unbound=None, match_mode=None, environ=os.environ):
    """Substitute environment variables into a string.

    For each $NAME and ${NAME} in "text", substitute with the value
    of the environment variable NAME. If NAME is not defined in the
    environment and "unbound" is None, raise an
    UnboundEnvironmentVariableError. If NAME is not defined in the
    environment and "unbound" is not None, substitute NAME with the
    value of "unbound".

    """
    ret = ""
    try:
        tail = text.decode()
    except AttributeError:
        tail = text
    while tail:
        match = _MATCH_MODES[match_mode].match(tail)
        if match:
            groups = match.groupdict()
            substitute = groups["symbol"]
            if len(groups["escape"]) % 2 == 0:
                if groups["name"] in environ:
                    substitute = environ[groups["name"]]
                elif unbound is not None:
                    substitute = str(unbound)
                else:
                    raise UnboundEnvironmentVariableError(groups["name"])
            ret += (
                groups["head"]
                + groups["escape"][0 : len(groups["escape"]) // 2]
                + substitute
            )
            tail = groups["tail"]
        else:
            ret += tail
            tail = ""
    return ret


def contains_env_var(text, match_mode=None):
    """Check if a string contains unescaped $NAME and/or ${NAME} syntax."""
    match = _MATCH_MODES[match_mode].match(text)
    return match and len(match.groupdict()["escape"]) % 2 == 0
