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
"""
Convenient functions for searching resource files.
"""

from importlib.machinery import SourceFileLoader
import inspect
import os
from pathlib import Path
import string
import sys

import metomi.rose
from metomi.rose.config import ConfigLoader, ConfigNode
import metomi.rose.opt_parse
from metomi.rose.reporter import Reporter

ERROR_LOCATE_OBJECT = "Could not locate {0}"


class ResourceError(Exception):

    """A named resource not found."""

    def __init__(self, key):
        Exception.__init__(self, "%s: resource not found." % key)


ROSE_CONF_PATH = 'ROSE_CONF_PATH'
ROSE_SITE_CONF_PATH = 'ROSE_SITE_CONF_PATH'
ROSE_INSTALL_ROOT = Path(metomi.rose.__file__).parent


class ResourceLocator:
    """A class for searching resource files.

    Loads files in the following order:

    System:
        /etc
    Site:
        $ROSE_SITE_CONF_PATH
    User:
        ~/.metomi

    If $ROSE_CONF_PATH is defined these files are skipped and configuration
    found in $ROSE_CONF_PATH is loaded instead.

    """

    SYST_CONF_PATH = Path('/etc')
    USER_CONF_PATH = Path('~/.metomi').expanduser()
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
            self.paths = list(map(Path, paths))
        else:
            self.paths = [
                (ROSE_INSTALL_ROOT / 'etc') / self.get_util_name("-"),
                ROSE_INSTALL_ROOT / 'etc',
            ]
        self.conf = None

    def get_conf(self):
        """Return the site/user configuration root node."""
        if self.conf is None:
            # base system conf path
            paths = [self.SYST_CONF_PATH]

            # add $ROSE_SITE_CONF_PATH if defined
            if "ROSE_SITE_CONF_PATH" in os.environ:
                path_str = os.environ["ROSE_SITE_CONF_PATH"].strip()
                if path_str:
                    paths.append(Path(path_str))

            # add user conf path
            paths.append(self.USER_CONF_PATH)

            # use $ROSE_CONF_PATH (and ignore all others) if defined
            if "ROSE_CONF_PATH" in os.environ:
                paths_str = os.getenv("ROSE_CONF_PATH").strip()
                if paths_str:
                    paths = [
                        Path(path) for path in paths_str.split(os.pathsep)
                    ]
                else:
                    paths = []

            # load and cache config
            self.conf = ConfigNode()
            config_loader = ConfigLoader()
            for path in paths:
                conffile = path / self.ROSE_CONF
                if conffile.is_file() and os.access(conffile, os.R_OK):
                    config_loader.load_with_opts(str(conffile), self.conf)

        return self.conf

    def get_synopsis(self):
        """Return line 1 of SYNOPSIS in $ROSE_HOME_BIN/$ROSE_NS-$ROSE_UTIL.

        Note:
            This is used for bash sub commands only.

        """
        try:
            home_bin = os.getenv("ROSE_HOME_BIN")
            if not home_bin:
                return None
            path = os.path.join(home_bin, self.get_util_name("-"))
            in_synopsis = False
            for line in open(path):
                if in_synopsis:
                    return line.strip("#" + string.whitespace)
                if line.rstrip() == "# SYNOPSIS":
                    in_synopsis = True
        except IOError:
            return None

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

    def locate(self, key):
        """Return the location of the resource key."""
        key = os.path.expanduser(key)
        for path in self.paths:
            name = path / key
            if name.exists():
                return name
        raise ResourceError(key)


def import_object(
    import_string, from_files, error_handler, module_prefix=None
):
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
            module = __import__(module_name, globals(), locals(), [], 0)
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


def main():
    """Launcher for the CLI."""
    opt_parser = metomi.rose.opt_parse.RoseOptionParser(
        usage='rose resource RESOURCE_PATH',
        description='''
Display the path of resources in the Rose Python installation.

* If the requested resource exists and is a file its path is printed.
* If the requested resource exists and is a directory it is listed.

Provide no arguments to see a list of top-level resources.

EXAMPLES
    # List top-level resources:
    $ rose resource

    # List the contents of the "syntax" directory:
    $ rose resource syntax

    # Locate the Rose syntax file for the Vim text editor:
    $ rose resource syntax/rose-conf.vim
        ''',
        epilog='''
ARGUMENTS
    RESOURCE_PATH
        Path of the resource to extract.

        Run `rose resource` to see the list of resources.
        ''',
    )
    opt_parser.add_my_options()
    opts, args = opt_parser.parse_args()
    reporter = Reporter(opts.verbosity - opts.quietness)
    is_top_level = False
    if len(args) > 1:
        reporter.report('Only one argument accepted\n', level=Reporter.FAIL)
        sys.exit(1)
    if len(args) == 0:
        key = ROSE_INSTALL_ROOT / 'etc'
        path = ResourceLocator(paths=[ROSE_INSTALL_ROOT]).locate('etc')
        is_top_level = True
    else:
        key = args[0]
        try:
            path = ResourceLocator().locate(key)
        except ResourceError:
            reporter.report('Resource not found\n', level=Reporter.FAIL)
            sys.exit(1)
    if path.is_file():
        print(path)
    elif path.is_dir():
        print(f'{key}/')
        for item in path.iterdir():
            if is_top_level:
                item = item.relative_to(path)
            else:
                item = item.relative_to(path.parent)
            print(f'  {item}')


if __name__ == "__main__":
    main()
