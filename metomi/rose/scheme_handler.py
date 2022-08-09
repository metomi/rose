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
"""Load and select from a group of related functional classes."""


from glob import glob
import inspect
import os
from pathlib import Path
import sys


class SchemeHandlersManager:
    """Load and select from a group of related functional classes."""

    CAN_HANDLE = "can_handle"

    def __init__(
        self, paths, ns=None, attrs=None, can_handle=None, *args, **kwargs
    ):
        """Load modules in paths and initialise any classes with a SCHEME.

        If "ns" is not None, only modules under the specified name-space in
        paths are searched and imported. ("ns" should be a str in the form
        "a.b", which will be converted as "a/b" for path search.)

        Initialise each handler, and save it in self.handlers, which is a dict
        of {scheme: handler, ...}.

        If attrs is specified, it should be a list of attributes the class
        has that do not have None values.

        args and kwargs are passed as *args, **kwargs to the constructor of
        each class. This manager will be passed to the constructor using the
        kwargs["manager"].

        Each handler class may have a SCHEMES attribute (a list of str) or a
        SCHEME attribute with a str value, which will be used as the keys to
        self.handlers of this manager.

        Optionally, a handler may have a h.can_handle(scheme, **kwargs) method
        that returns a boolean value to indicate whether it can handle a given
        value.

        """
        self.handlers = {}
        if can_handle is None:
            can_handle = self.CAN_HANDLE
        self.can_handle = can_handle
        cwd = os.getcwd()
        ns_path = ""
        if ns:
            ns_path = os.path.join(*(ns.split("."))) + os.sep
        for path in paths:
            os.chdir(path)  # assuming that "" is at the front of sys.path
            sys.path.insert(0, path)
            try:
                kwargs["manager"] = self
                for file_name in glob(ns_path + "*.py"):
                    if file_name.startswith("__"):
                        continue
                    mod_path = file_name[0:-3]
                    mod_name = mod_path.replace(os.sep, ".")
                    mod = __import__(mod_name, fromlist=[""])
                    members = inspect.getmembers(mod, inspect.isclass)
                    scheme0_default = None
                    if len(members) == 1:
                        scheme0_default = os.path.basename(mod_path)
                    for _, class_ in members:
                        if any(
                            getattr(class_, a, None) is None for a in attrs
                        ):
                            continue
                        handler = None
                        scheme0 = getattr(class_, "SCHEME", scheme0_default)
                        schemes = []
                        if scheme0 is not None:
                            schemes = [scheme0]
                        for scheme in getattr(class_, "SCHEMES", schemes):
                            if scheme in self.handlers:
                                raise ValueError(class_)  # scheme already used
                            kwargs["manager"] = self
                            if handler is None:
                                handler = class_(*args, **kwargs)
                            self.handlers[scheme] = handler
            finally:
                os.chdir(cwd)
                sys.path.pop(0)

    def get_handler(self, scheme):
        """Return the handler with a matching scheme.

        Return None if there is no handler with a matching scheme.

        """
        try:
            return self.handlers[scheme]
        except (KeyError, TypeError):
            pass

    def guess_handler(self, item):
        """Return a handler that can handle item.

        Return None if there is no handler with a matching scheme.

        """
        handler = self.get_handler(item)
        if handler:
            return handler
        for handler in self.handlers.values():
            can_handle = getattr(handler, self.can_handle, None)
            if callable(can_handle) and can_handle(item):
                return handler

    @staticmethod
    def get_rose_path():
        """Get path where rose handlers can be found.

        n.b. At Python 3 there is no requirement to have a __init__ file
        in a module, and therefore we need to get metomi.rose's path (where
        there is an __init__.py) and not just metomi.
        """
        path = str(
            Path(sys.modules["metomi.rose"].__file__).parent.parent.parent)
        return path
