# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# -----------------------------------------------------------------------------
"""Reporter for diagnostic messages."""

import Queue

import multiprocessing
import os
import re
import sys

_DEFAULT_REPORTER = None


class Reporter(object):

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
        """Return the default reporter.
        """
        global _DEFAULT_REPORTER
        if _DEFAULT_REPORTER is None or reset:
            _DEFAULT_REPORTER = Reporter(verbosity)
        return _DEFAULT_REPORTER

    def __init__(self, verbosity=DEFAULT, contexts=None, raise_on_exc=False):
        """Create a reporter with contexts at a given verbosity."""
        self.contexts = {}
        if verbosity < 0:
            verbosity = 0
        if contexts is not None:
            self.contexts.update(contexts)
        self.contexts.setdefault("stderr",
                                 ReporterContext(self.KIND_ERR, verbosity))
        self.contexts.setdefault("stdout",
                                 ReporterContext(self.KIND_OUT, verbosity))
        self.event_handler = None
        self.raise_on_exc = raise_on_exc

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
        if self.event_handler is not None:
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
        for key, context in self.contexts.items():
            insert_newline = False
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
                    msg = str(message())
                else:
                    msg = str(message)
            if prefix:
                for line in msg.splitlines():
                    msg_line = prefix + line
                    if clip is not None:
                        msg_line = msg_line[:clip]
                    context.write(msg_line + "\n")
            else:
                if clip is not None:
                    if msg.endswith("\n") and len(msg) > clip:
                        insert_newline = True
                        msg = msg[:-1]
                    msg_line = msg[:clip]
                if insert_newline:
                    context.write(msg_line + "\n")
                else:
                    context.write(msg)
        if isinstance(message, Exception) and self.raise_on_exc:
            raise message

    __call__ = report


class ReporterContext(object):

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

    def __init__(self,
                 kind=None,
                 verbosity=Reporter.DEFAULT,
                 handle=None,
                 prefix=None):
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
        return self.handle.write(message)

    def _tty_colour_err(self, s):
        try:
            if self.handle.isatty():
                return self.TTY_COLOUR_ERR + s + "\033[0m"
        except:
            pass
        return s


class ReporterContextQueue(ReporterContext):

    """A context for the reporter object.

    It has the following attributes:
    kind:
        The message kind to report to this context.
        (Reporter.KIND_ERR, Reporter.KIND_ERR or None.)
    verbosity:
        The verbosity of this context.
    queue:
        The multiprocessing.Queue.
    prefix:
        The default message prefix (str or callable).

    """

    def __init__(self,
                 kind=None,
                 verbosity=Reporter.DEFAULT,
                 queue=None,
                 prefix=None):
        ReporterContext.__init__(self, kind, verbosity, None, prefix)
        if queue is None:
            queue = multiprocessing.Manager().Queue()
        self.queue = queue
        self.closed = False
        self._messages_pending = []

    def close(self):
        self._send_pending_messages()
        self.closed = True

    def is_closed(self):
        return self.closed

    def write(self, message):
        self._messages_pending.append(message)
        self._send_pending_messages()

    def _send_pending_messages(self):
        for message in list(self._messages_pending):
            try:
                self.queue.put(self._messages_pending[0], block=False)
            except Queue.Full:
                break
            self._messages_pending.pop(0)


class Event(object):

    """A base class for events suitable for feeding into a Reporter."""

    VV = Reporter.VV
    V = Reporter.V
    DEFAULT = Reporter.DEFAULT
    WARN = Reporter.WARN
    FAIL = Reporter.FAIL
    KIND_ERR = Reporter.KIND_ERR
    KIND_OUT = Reporter.KIND_OUT

    LEVEL = None
    KIND = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.level = kwargs.pop("level", self.LEVEL)
        self.kind = kwargs.pop("kind", self.KIND)
        self.kwargs = kwargs

    def __str__(self):
        if len(self.args) == 1:
            return str(self.args[0])
        return str(self.args)
