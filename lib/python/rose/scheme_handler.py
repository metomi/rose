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
import os


class SchemeHandlersManager(object):
    """Load and select from a group of related functional classes."""

    def __init__(self, path, attribs=None, **kwargs):
        """Load modules in path and initialise classes with a SCHEME.

        If attribs is specified, it should be a list of attributes the class
        has that do not have a None value.

        kwargs are passed as **kwargs to the constructor of each class.

        """
        self.handlers = {}
        cwd = os.getcwd()
        os.chdir(path)
        try:
            for name in glob("*.py"):
                if name.startswith("__"):
                    continue
                mod = __import__(name)
                for c in vars(mod).values():
                    scheme = getattr(c, "SCHEME", None)
                    if (scheme is None or
                        any([getattr(c, a, None) is None for a in attribs])):
                        continue
                    if self.handlers.has_key(scheme):
                        raise ValueError(c)
                    self.handlers[scheme] = c(**kwargs)
        finally:
            os.chdir(cwd)

    def get_handler(self, scheme):
        """Return the functional object with a matching scheme."""
        if self.handlers.has_key(scheme):
            return self.handlers[scheme]

    def guess_handler(self, scheme):
        """Return a functional object that can handle scheme."""
        handler = self.get_handler(scheme):
        if handler:
            return handler
        for handler in self.handlers.values():
            if (hasattr(handler, "can_handle") and
                callable(handler.can_handle) and
                handler.can_handle(scheme))):
                return handler
