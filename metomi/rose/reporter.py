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
"""Reporter for diagnostic messages."""


import doctest
import sys
import time
from typing import Optional


class Reporter:

    """Report diagnostic messages.

    Note: How about the "logging" module in the standard library? It needs a
    lot of fiddling to get it working in our reporting model. We want:
    * [FAIL] in any verbosity to stderr.
    * [WARN] in default verbosity to stderr.
    * Raw output to stdout in any verbosity.
    * [INFO] in default verbosity to stdout.
    * [INFO] in -v verbosity to stdout.
    * [INFO] in -vv verbosity to stdout.
    * and everything goes to the log file with -vv verbosity by default.
    """

    _INST = None
    VV = 3
    V = 2
    DEFAULT = 1
    WARN = 1
    FAIL = 0
    PREFIX_FAIL = "[FAIL] "
    PREFIX_INFO = "[INFO] "
    PREFIX_WARN = "[WARN] "
    KIND_ERR = "KIND_ERR"
    KIND_OUT = "KIND_OUT"

    @classmethod
    def default(cls, verbosity=None, reset=False):
        """Return the default reporter."""
        if cls._INST is None or reset:
            cls._INST = Reporter(verbosity)
        return cls._INST

    def __init__(self, verbosity=DEFAULT, contexts=None, raise_on_exc=False):
        """Create a reporter with contexts at a given verbosity."""
        self.contexts = {}
        if verbosity < 0:
            verbosity = 0
        if contexts is not None:
            self.contexts.update(contexts)
        self.contexts.setdefault(
            "stderr", ReporterContext(self.KIND_ERR, verbosity)
        )
        self.contexts.setdefault(
            "stdout", ReporterContext(self.KIND_OUT, verbosity)
        )
        self.event_handler = None
        self.raise_on_exc = raise_on_exc

    def format_msg(self, msg, verbosity, prefix=None, clip=None):
        """Format a message for reporting."""

        msg_lines = []

        if verbosity >= self.VV:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z ")
        else:
            stamp = ""

        if prefix:
            for line in msg.splitlines():
                msg_line = prefix + stamp + line
                if clip is not None:
                    msg_line = msg_line[:clip]
                msg_line = msg_line + "\n"
                msg_lines.append(msg_line)
        else:
            msg_line = stamp
            should_insert_newline = False
            if clip is not None:
                if msg.endswith("\n") and len(msg) > clip:
                    should_insert_newline = True
                    msg = msg[:-1]
                msg_line = msg_line + msg[:clip]
            if should_insert_newline:
                msg_line = msg_line + "\n"
            else:
                msg_line = msg
            msg_lines.append(msg_line)

        return msg_lines

    def report(self, message, kind=None, level=None, prefix=None, clip=None):
        """Report a message, if relevant for the reporter contexts.

        message:
            The message to report. An Event, an Exception, an object
            with a __str__ method, or a callable that returns an object
            with a __str__ method.
        kind:
            The message kind. The default is determined by message.
            If it is an Event, the default is message.kind. If it is an
            Exception, the default is KIND_ERR. Otherwise, the default
            is KIND_OUT.
        level:
            The level of the message. The default is determined by
            message. If it is an Event, the default is message.level.
            If it is an Exception, the default is FAIL. Otherwise, the
            default is DEFAULT.
        prefix:
            Prefix each line of the message with this prefix.
            Default is context dependent.
        clip:
            The maximum length of the message to print.

        If self.event_handler is defined, self.event_handler with all the
        arguments and return its result instead.

        """
        if isinstance(message, bytes):
            message = message.decode()
        if callable(self.event_handler):
            return self.event_handler(message, kind, level, prefix, clip)

        if isinstance(message, Event):
            if kind is None:
                kind = message.kind
            if level is None:
                level = message.level
        elif isinstance(message, Exception):
            if kind is None:
                kind = self.KIND_ERR
            if level is None:
                level = self.FAIL
        if kind is None:
            kind = self.KIND_OUT
        if level is None:
            level = self.DEFAULT
        msg = None
        for key, context in list(self.contexts.items()):
            if context.is_closed():
                self.contexts.pop(key)  # remove contexts with closed handles
                continue
            if context.kind is not None and context.kind != kind:
                continue
            if level > context.verbosity:
                continue
            if prefix is None:
                prefix = context.get_prefix(kind, level)
            elif callable(prefix):
                prefix = prefix(kind, level)
            if msg is None:
                if callable(message):
                    msg = message()
                else:
                    msg = message
                msg = str(msg)

            msg_lines = self.format_msg(msg, context.verbosity, prefix, clip)
            for line in msg_lines:
                context.write(line)

        if isinstance(message, Exception) and self.raise_on_exc:
            raise message

    __call__ = report


class ReporterContext:

    """A context for the reporter object.

    It has the following attributes:
    kind:
        The message type to report to this context.
        (Reporter.KIND_ERR, Reporter.KIND_ERR or None.)
    verbosity:
        The verbosity of this context.
    handle:
        The file handle to write to.
    prefix:
        The default message prefix (str or callable).

    """

    TTY_COLOUR_ERR = "\033[1;31m"
    TTY_COLOUR_NORM = "\033[0m"

    def __init__(
        self, kind=None, verbosity=Reporter.DEFAULT, handle=None, prefix=None
    ):
        if kind == Reporter.KIND_ERR:
            if handle is None:
                handle = sys.stderr
        elif kind == Reporter.KIND_OUT:
            if handle is None:
                handle = sys.stdout
        self.kind = kind
        self.handle = handle
        self.verbosity = verbosity
        self.prefix = prefix

    def get_prefix(self, kind, level):
        """Return the prefix suitable for the message kind and level."""
        if self.prefix is None:
            if kind == Reporter.KIND_OUT:
                if level:
                    return Reporter.PREFIX_INFO
                else:
                    return ""
            elif level > Reporter.FAIL:
                return self._tty_colour_err(Reporter.PREFIX_WARN)
            else:
                return self._tty_colour_err(Reporter.PREFIX_FAIL)
        if callable(self.prefix):
            return self.prefix(kind, level)
        else:
            return self.prefix

    def is_closed(self):
        """Return True if the context's handle is closed."""
        return self.handle.closed

    def write(self, message):
        """Write the message to the context's handle."""
        if isinstance(self.handle, doctest._SpoofOut):
            # If context is a doctest:
            ret_code = self.handle.write(message)
        else:
            try:
                ret_code = self.handle.buffer.write(message.encode("utf-8"))
            except TypeError:
                ret_code = self.handle.write(message)
            except AttributeError:
                ret_code = self.handle.write(message.encode('UTF-8'))
            self.handle.flush()
        return ret_code

    def _tty_colour_err(self, str_):
        """Colour error string for terminal."""
        try:
            if self.handle.isatty():
                return "%s%s%s" % (
                    self.TTY_COLOUR_ERR,
                    str_,
                    self.TTY_COLOUR_NORM,
                )
        except AttributeError:
            pass
        return str_


class Event:

    """A base class for events suitable for feeding into a Reporter."""

    VV = Reporter.VV
    V = Reporter.V
    DEFAULT = Reporter.DEFAULT
    WARN = Reporter.WARN
    FAIL = Reporter.FAIL
    KIND_ERR = Reporter.KIND_ERR
    KIND_OUT = Reporter.KIND_OUT

    LEVEL: Optional[int] = None
    KIND: Optional[str] = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.level = kwargs.pop("level", self.LEVEL)
        self.kind = kwargs.pop("kind", self.KIND)
        self.kwargs = kwargs

    def __str__(self):
        if len(self.args) == 1:
            return str(self.args[0])
        return str(self.args)
