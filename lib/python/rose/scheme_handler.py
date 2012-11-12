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
"""Load and select from a group of related functional classes."""


from glob import glob
import inspect
import os


class SchemeHandlersManager(object):
    """Load and select from a group of related functional classes."""

    def __init__(self, paths, attrs=None, *args, **kwargs):
        """Load modules in paths and initialise any classes with a SCHEME.

        If attrs is specified, it should be a list of attributes the class
        has that do not have a None value.

        args and kwargs are passed as *args, **kwargs to the constructor of
        each class. This manager will be passed to the constructor using the
        keyword "manager".

        A handler class should have a h.SCHEME attribute with a str value.
        Optionally, it should have a h.can_handle(scheme, **kwargs) method that
        returns a boolean value to indicate whether it can handle a given
        scheme.

        """
        self.handlers = {}
        cwd = os.getcwd()
        for path in paths:
            os.chdir(path) # assuming that "" is at the front of sys.path
            try:
                for file_name in glob("*.py"):
                    if file_name.startswith("__"):
                        continue
                    mod = __import__(file_name[0:-3])
                    for name, c in inspect.getmembers(mod, inspect.isclass):
                        scheme = getattr(c, "SCHEME", None)
                        if (scheme is None or
                            any([getattr(c, a, None) is None for a in attrs])):
                            continue
                        if self.handlers.has_key(scheme):
                            raise ValueError(c) # Class with the same scheme
                        kwargs["manager"] = self
                        self.handlers[scheme] = c(*args, **kwargs)
            finally:
                os.chdir(cwd)

    def get_handler(self, scheme):
        """Return the handler with a matching scheme.

        Return None if there is no handler with a matching scheme.

        """
        if self.handlers.has_key(scheme):
            return self.handlers[scheme]

    def guess_handler(self, scheme, **kwargs):
        """Return a handler that can handle scheme.

        Return None if there is no handler with a matching scheme.

        """
        handler = self.get_handler(scheme)
        if handler:
            return handler
        for handler in self.handlers.values():
            if (hasattr(handler, "can_handle") and
                callable(handler.can_handle) and
                handler.can_handle(scheme, **kwargs)):
                return handler
