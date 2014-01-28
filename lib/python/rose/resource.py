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
"""
Convenient functions for searching resource files.
"""

import os
from rose.config import ConfigLoader, ConfigNode
import imp
import inspect
import string
import sys


ERROR_LOCATE_OBJECT = "Could not locate {0}"
_DEFAULT_RESOURCE_LOCATOR = None


class ResourceError(Exception):

    def __init__(self, key):
        Exception.__init__(self, "%s: resource not found." % key)


class ResourceLocator(object):

    """A class for searching resource files."""

    @classmethod
    def default(cls, paths=None, reset=False):
        """Return the default resource locator."""
        global _DEFAULT_RESOURCE_LOCATOR
        if _DEFAULT_RESOURCE_LOCATOR is None or reset:
            _DEFAULT_RESOURCE_LOCATOR = ResourceLocator(paths)
        return _DEFAULT_RESOURCE_LOCATOR

    def __init__(self, ns=None, util=None, paths=None):
        self.ns = ns
        self.util = util
        if paths:
            self.paths = list(paths)
        else:
            h = self.get_util_home()
            n = self.get_util_name("-")
            self.paths = [os.path.join(h, "etc", n), os.path.join(h, "etc")]
        self.conf = None

    def get_conf(self):
        """Return the site/user configuration root node."""
        if self.conf is None:
            paths = [os.path.join(self.get_util_home(), "etc"),
                     os.path.join(os.path.expanduser("~"), ".metomi")]
            if "ROSE_CONF_PATH" in os.environ:
                paths_str = os.getenv("ROSE_CONF_PATH").strip()
                if paths_str:
                    paths = paths_str.split(os.pathsep)
                else:
                    paths = []
            self.conf = ConfigNode()
            config_loader = ConfigLoader()
            for path in paths:
                file = os.path.join(path, "rose.conf")
                if os.path.isfile(file) and os.access(file, os.R_OK):
                    config_loader.load_with_opts(file, self.conf)
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
        except:
            return None

    def get_util_home(self, *args):
        """Return ROSE_HOME or the dirname of the dirname of sys.argv[0].

        If args are specified, they are added to the end of returned path.

        """
        try:
            d = os.getenv("ROSE_HOME")
        except KeyError:
            d = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
        return os.path.join(d, *args)

    def get_util_name(self, separator=" "):
        """Return the name of the Rose utility, e.g. "rose app-run".

        This works if ROSE_NS and ROSE_UTIL are defined.
        Use a separator (default=" ") between ROSE_NS and ROSE_UTIL.

        """
        ns = self.ns
        util = self.util
        try:
            if ns is None:
                ns = os.getenv("ROSE_NS")
            if util is None:
                util = os.getenv("ROSE_UTIL")
            return ns + separator + util
        except KeyError:
            return os.path.basename(sys.argv[0])

    def get_version(self):
        """Return ROSE_VERSION."""
        version = os.getenv("ROSE_VERSION")
        if version is None:
            for line in open(self.get_util_home("doc", "rose-version.js")):
                if line.startswith("ROSE_VERSION="):
                    value = line.replace("ROSE_VERSION=", "")
                    version = value.strip(string.whitespace + "\";")
                    break
        return version

    def locate(self, key):
        """Return the location of the resource key."""
        key = os.path.expanduser(key)
        for path in self.paths:
            file = os.path.join(path, key)
            if os.path.exists(file):
                return file
        raise ResourceError(key)


def resource_locate(key):
    """Return the location of the resource key."""
    return ResourceLocator.default().locate(key)


def import_object(import_string, from_files, error_handler,
                  module_prefix=None):
    """Import a Python callable.

    import_string is the '.' delimited path to the callable,
    as in normal Python - e.g.
    rose.config_editor.pagewidget.table.PageTable
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
    module_dirs = set([os.path.dirname(f) for f in module_files])
    module = None
    if is_builtin:
        try:
            module = __import__(module_name, globals(), locals(),
                                [], 0)
        except Exception as e:
            error_handler(e)
    else:
        for filename in module_files:
            sys.path.insert(0, os.path.dirname(filename))
            try:
                module = imp.load_source(as_name, filename)
            except Exception as e:
                error_handler(e)
            sys.path.pop(0)
    if module is None:
        error_handler(
              ERROR_LOCATE_OBJECT.format(module_name))
        return None
    for submodule in module_name.split(".")[1:]:
        module = getattr(module, submodule)
    contents = inspect.getmembers(module)
    return_object = None
    for obj_name, obj in contents:
        if obj_name == class_name and inspect.isclass(obj):
            return_object = obj
    return return_object
