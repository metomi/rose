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
"""
Convenient functions for searching resource files.
"""

import os
import rose.config
import string
import sys

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
            site_file = os.path.join(self.get_util_home(), "etc", "rose.conf")
            user_file = os.path.join(
                    os.path.expanduser("~"), ".metomi", "rose.conf")
            self.conf = rose.config.ConfigNode()
            for file in [site_file, user_file]:
                if os.path.isfile(file) and os.access(file, os.R_OK):
                    rose.config.load(file, self.conf)
        return self.conf

    def get_doc_url(self):
        """Return the URL of Rose documentation."""
        default = "file://%s/doc/" % self.get_util_home()
        return self.get_conf().get_value(["rose-doc"], default=default)

    def get_synopsis(self):
        """Return the 1st line of SYNOPSIS in ROSE_HOME_BIN/ROSE_UTIL."""
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

    def get_util_home(self):
        """Return ROSE_HOME or the dirname of the dirname of sys.argv[0]."""
        try:
            return os.getenv("ROSE_HOME")
        except KeyError:
            return os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))

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
