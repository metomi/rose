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
"""Reporter for diagnostic messages."""

import multiprocessing
import os
import re
import sys

_DEFAULT_REPORTER = None

class Reporter(object):

    """Report diagnostic messages.

    Note: How about the "logging" module in the standard library?
    It needs a lot of fiddling to get it working in our reporting model. We want:
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
    TYPE_ERR = "TYPE_ERR"
    TYPE_OUT = "TYPE_OUT"

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
        if contexts is not None:
            self.contexts.update(contexts)
        self.contexts.setdefault("stderr",
                                 ReporterContext(self.TYPE_ERR, verbosity))
        self.contexts.setdefault("stdout",
                                 ReporterContext(self.TYPE_OUT, verbosity))
        self.event_handler = None
        self.raise_on_exc = raise_on_exc

    def report(self, message, type=None, level=None, prefix=None, clip=None):
        """Report a message, if relevant for the reporter contexts.

        message:
            The message to report. An Event, an Exception, an object
            with a __str__ method, or a callable that returns an object
            with a __str__ method.
        type:
            The message type. The default is determined by message.
            If it is an Event, the default is message.type. If it is an
            Exception, the default is TYPE_ERR. Otherwise, the default
            is TYPE_OUT.
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
            return self.event_handler(message, type, level, prefix, clip)

        if isinstance(message, Event):
            if type is None:
                type = message.type
            if level is None:
                level = message.level
        elif isinstance(message, Exception):
            if type is None:
                type = self.TYPE_ERR
            if level is None:
                level = self.FAIL
        if type is None:
            type = self.TYPE_OUT
        if level is None:
            level = self.DEFAULT
        msg = None
        for key, context in self.contexts.items():
            if context.is_closed():
                self.contexts.pop(key) # remove contexts with closed file handles
                continue
            if context.type is not None and context.type != type:
                continue
            if level > context.verbosity:
                continue
            if prefix is None:
                prefix = context.get_prefix(type, level)
            elif callable(prefix):
                prefix = prefix(type, level)
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
                    msg = msg[:clip]
                context.write(msg)
        if isinstance(message, Exception) and self.raise_on_exc:
            raise message

    __call__ = report


class ReporterContext(object):

    """A context for the reporter object.

    It has the following attributes:
    type:
        The message type to report to this context.
        (Reporter.TYPE_ERR, Reporter.TYPE_ERR or None.)
    verbosity:
        The verbosity of this context.
    handle:
        The file handle to write to.
    prefix:
        The default message prefix (str or callable).

    """

    def __init__(self,
                 type=None,
                 verbosity=Reporter.DEFAULT,
                 handle=None,
                 prefix=None):
        if type == Reporter.TYPE_ERR:
            if handle is None:
                handle = sys.stderr
        elif type == Reporter.TYPE_OUT:
            if handle is None:
                handle = sys.stdout
        self.type = type
        self.handle = handle
        self.verbosity = verbosity
        self.prefix = prefix

    def get_prefix(self, type, level):
        if self.prefix is None:
            if type == Reporter.TYPE_OUT:
                if level:
                    return Reporter.PREFIX_INFO
                else:
                    return ""
            elif level > Reporter.FAIL:
                return Reporter.PREFIX_WARN
            else:
                return Reporter.PREFIX_FAIL
        elif callable(self.prefix):
            return self.prefix(type, level)
        else:
            return self.prefix

    def is_closed(self):
        return self.handle.closed

    def write(self, message):
        return self.handle.write(message)


class ReporterContextQueue(ReporterContext):

    """A context for the reporter object.

    It has the following attributes:
    type:
        The message type to report to this context.
        (Reporter.TYPE_ERR, Reporter.TYPE_ERR or None.)
    verbosity:
        The verbosity of this context.
    queue:
        The multiprocessing.Queue.
    prefix:
        The default message prefix (str or callable).

    """

    def __init__(self,
                 type=None,
                 verbosity=Reporter.DEFAULT,
                 queue=None,
                 prefix=None):
        ReporterContext.__init__(self, type, verbosity, None, prefix)
        if queue is None:
            queue = multiprocessing.Queue()
        self.queue = queue
        self.closed = False

    def close(self):
        self.closed = True

    def is_closed(self):
        return self.closed

    def write(self, message):
        self.queue.put(message, block=True, timeout=0.1)


class Event(object):

    """A base class for events suitable for feeding into a Reporter."""

    VV = Reporter.VV
    V = Reporter.V
    DEFAULT = Reporter.DEFAULT
    WARN = Reporter.WARN
    FAIL = Reporter.FAIL
    TYPE_ERR = Reporter.TYPE_ERR
    TYPE_OUT = Reporter.TYPE_OUT

    LEVEL = None
    TYPE = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.level = kwargs.get("level", self.LEVEL)
        self.type = kwargs.get("type", self.TYPE)

    def __str__(self):
        if len(self.args) == 1:
            return str(self.args[0])
        return str(self.args)
