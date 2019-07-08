# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
"""
Convenient functions for searching resource files.
"""

import os
from metomi.rose.config import ConfigLoader, ConfigNode
import inspect
import string
import sys
from importlib.machinery import SourceFileLoader


ERROR_LOCATE_OBJECT = "Could not locate {0}"


def get_util_home(*args):
    """Return ROSE_LIB or the dirname of the dirname of sys.argv[0].

    If args are specified, they are added to the end of returned path.

    """
    try:
        value = os.environ["ROSE_LIB"]
    except KeyError:
        value = os.path.abspath(__file__)
        for _ in range(3):  # assume __file__ under $ROSE_LIB/metomi/rose/
            value = os.path.dirname(value)
    return os.path.join(value, *args)


class ResourceError(Exception):

    """A named resource not found."""

    def __init__(self, key):
        Exception.__init__(self, "%s: resource not found." % key)


class ResourceLocator(object):

    """A class for searching resource files."""

    SITE_CONF_PATH = get_util_home("etc")
    USER_CONF_PATH = os.path.join(os.path.expanduser("~"), ".metomi")
    ROSE_CONF = "rose.conf"
    _DEFAULT_RESOURCE_LOCATOR = None

    @classmethod
    def default(cls, paths=None, reset=False):
        """Return the default resource locator."""
        if cls._DEFAULT_RESOURCE_LOCATOR is None or reset:
            cls._DEFAULT_RESOURCE_LOCATOR = ResourceLocator(paths)
        return cls._DEFAULT_RESOURCE_LOCATOR

    def __init__(self, namespace=None, util=None, paths=None):
        self.namespace = namespace
        self.util = util
        if paths:
            self.paths = list(paths)
        else:
            home = self.get_util_home()
            name = self.get_util_name("-")
            self.paths = [os.path.join(home, "etc", name),
                          os.path.join(home, "etc")]
        self.conf = None

    def get_conf(self):
        """Return the site/user configuration root node."""
        if self.conf is None:
            paths = [self.SITE_CONF_PATH, self.USER_CONF_PATH]
            if "ROSE_CONF_PATH" in os.environ:
                paths_str = os.getenv("ROSE_CONF_PATH").strip()
                if paths_str:
                    paths = paths_str.split(os.pathsep)
                else:
                    paths = []
            self.conf = ConfigNode()
            config_loader = ConfigLoader()
            for path in paths:
                name = os.path.join(path, self.ROSE_CONF)
                if os.path.isfile(name) and os.access(name, os.R_OK):
                    config_loader.load_with_opts(name, self.conf)
        return self.conf

    def get_doc_url(self):
        """Return the URL of Rose documentation."""
        default = "file://%s/doc/" % self.get_util_home()
        return self.get_conf().get_value(["rose-doc"], default=default)

    def get_synopsis(self):
        """Return line 1 of SYNOPSIS in $ROSE_HOME_BIN/$ROSE_NS-$ROSE_UTIL."""
        try:
            home_bin = os.getenv("ROSE_HOME_BIN")
            path = os.path.join(home_bin, self.get_util_name("-"))
            in_synopsis = False
            for line in open(path):
                if in_synopsis:
                    return line.strip("#" + string.whitespace)
                if line.rstrip() == "# SYNOPSIS":
                    in_synopsis = True
        except IOError:
            return None

    @classmethod
    def get_util_home(cls, *args):
        """Return ROSE_HOME or the dirname of the dirname of sys.argv[0].

        If args are specified, they are added to the end of returned path.

        """
        return get_util_home(*args)

    def get_util_name(self, separator=" "):
        """Return the name of the Rose utility, e.g. "rose app-run".

        This works if ROSE_NS and ROSE_UTIL are defined.
        Use a separator (default=" ") between ROSE_NS and ROSE_UTIL.

        """
        namespace = self.namespace
        util = self.util
        try:
            if namespace is None:
                namespace = os.environ["ROSE_NS"]
            if util is None:
                util = os.environ["ROSE_UTIL"]
            return namespace + separator + util
        except KeyError:
            return os.path.basename(sys.argv[0])

    def get_version(self, ignore_environment=False):
        """return the current metomi.rose_version number.

        By default pass through the value of the ``ROSE_VERSION`` environment
        variable.

        Args:
            ignore_environment (bool): Return the value extracted from the
                ``rose-version`` file.
        """
        version = None
        if not ignore_environment:
            version = os.getenv("ROSE_VERSION")
        if not version:
            for line in open(self.get_util_home("rose-version")):
                if line.startswith("ROSE_VERSION="):
                    value = line.replace("ROSE_VERSION=", "")
                    version = value.strip(string.whitespace + "\";")
                    break
        return version

    def locate(self, key):
        """Return the location of the resource key."""
        key = os.path.expanduser(key)
        for path in self.paths:
            name = os.path.join(path, key)
            if os.path.exists(name):
                return name
        raise ResourceError(key)


def resource_locate(key):
    """Return the location of the resource key."""
    return ResourceLocator.default().locate(key)


def import_object(import_string, from_files, error_handler,
                  module_prefix=None):
    """Import a Python callable.

    import_string is the '.' delimited path to the callable,
    as in normal Python - e.g.
    metomi.rose.config_editor.pagewidget.table.PageTable
    from_files is a list of available Python file paths to search in
    error_handler is a function that accepts an Exception instance
    or string and does something appropriate with it.
    module_prefix is an optional string to prepend to the module
    as an alias - this avoids any clashing between same-name modules.

    """
    is_builtin = False
    module_name = ".".join(import_string.split(".")[:-1])
    if module_name.startswith("rose."):
        is_builtin = True
    if module_prefix is None:
        as_name = module_name
    else:
        as_name = module_prefix + module_name
    class_name = import_string.split(".")[-1]
    module_fpath = "/".join(import_string.rsplit(".")[:-1]) + ".py"
    if module_fpath == ".py":
        # Empty module.
        return None
    module_files = [f for f in from_files if f.endswith(module_fpath)]
    if not module_files and not is_builtin:
        return None
    module = None
    if is_builtin:
        try:
            module = __import__(module_name, globals(), locals(),
                                [], 0)
        except ImportError as exc:
            error_handler(exc)
    else:
        for filename in module_files:
            sys.path.insert(0, os.path.dirname(filename))
            try:
                module = SourceFileLoader(as_name, filename).load_module()
            except ImportError as exc:
                error_handler(exc)
            sys.path.pop(0)
    if module is None:
        error_handler(ERROR_LOCATE_OBJECT.format(module_name))
        return None
    for submodule in module_name.split(".")[1:]:
        module = getattr(module, submodule)
    contents = inspect.getmembers(module)
    return_object = None
    for obj_name, obj in contents:
        if obj_name == class_name and inspect.isclass(obj):
            return_object = obj
    return return_object
