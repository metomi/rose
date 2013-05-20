# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
#------------------------------------------------------------------------------
"""Provide a common environment for a task in a cycling suite."""

from glob import glob
import os
from rose.env import env_export, EnvExportEvent
from rose.opt_parse import RoseOptionParser
from rose.reporter import Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
import sys
import traceback

PATH_GLOBS = {"PATH": ["share/fcm[_-]make*/*/bin", "work/fcm[_-]make*/*/bin"]}


def get_prepend_paths(event_handler=None, path_root=None, **args):
    """Return map of PATH-like env-var names to path lists to prepend to them.

    event_handler -- an instance of rose.reporter.Reporter or an object with a
                     similar interface.
    path_root -- if a glob is relative and this is defined, this is the root
                 directory of the relative path.
    args -- a list of strings in the form GLOB or NAME=GLOB. NAME is "PATH" by
            default or should be PATH-like environment variable name. GLOB
            should be a glob pattern for matching file system paths to prepend
            to NAME.

    Return something like:
        {"PATH": ["/opt/foo/bin", "/opt/bar/bin"],
         # ... and so on
        }

    """

    prepend_paths_of = {}

    # site/user configuration
    conf = ResourceLocator.default().get_conf()
    my_conf = conf.get(["rose-task-run"], no_ignore=True)
    if my_conf is not None:
        for key, node in sorted(my_conf.value.items()):
            if not key.startswith("path-prepend") or node.is_ignored():
                continue
            env_key = "PATH"
            if key != "path-prepend":
                env_key = key[len("path-prepend."):]
            values = []
            for v in node.value.split():
                if os.path.exists(v):
                    values.append(v)
            if values:
                prepend_paths_of[env_key] = values

    # Default or specified globs
    path_globs_of = {}
    for name, path_globs in PATH_GLOBS.items():
        path_globs_of[name] = path_globs
    for arg in args:
        if not arg:
            continue
        if "=" in arg:
            name, value = arg.split("=", 1)
        else:
            name, value = "PATH", arg
        if name not in path_globs_of:
            path_globs_of[name] = []
        path_globs_of[name].append(value)
    more_prepend_paths_of = {}
    if not path_root:
        path_root = os.getcwd()
    for name, path_globs in path_globs_of.items():
        if name not in more_prepend_paths_of:
            more_prepend_paths_of[name] = []
        for path_glob in path_globs:
            if path_glob:
                if path_glob.startswith("~"):
                    path_glob = os.path.expanduser(path_glob)
                if not os.path.isabs(path_glob):
                    path_glob = os.path.join(path_root, path_glob)
                for path in glob(path_glob):
                    more_prepend_paths_of[name].append(path)
            else:
                more_prepend_paths_of[name] = [] # empty value resets
    for name, more_prepend_paths in more_prepend_paths_of.items():
        if name in prepend_paths_of:
            prepend_paths_of[name].extend(more_prepend_paths)
        elif more_prepend_paths:
            prepend_paths_of[name] = more_prepend_paths

    return prepend_paths_of


def main():
    """rose task-env."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("cycle", "cycle_offsets", "path_globs",
                              "prefix_delim", "suffix_delim")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness - 1)
    suite_engine_proc = SuiteEngineProcessor.get_processor(
            event_handler=report)
    kwargs = {}
    for k, v in vars(opts).items():
        kwargs[k] = v
    try:
        task_props = suite_engine_proc.get_task_props(*args, **kwargs)
        for k, v in task_props:
            report(str(EnvExportEvent(k, v)) + "\n", level=0)
        path_globs = opts.path_globs
        if path_globs is None:
            path_globs = []
        for k, prepend_paths in get_prepend_paths(report,
                                                  task_props.suite_dir,
                                                  *path_globs).items():
            paths = os.getenv(k, "").split(os.pathsep)
            v = os.pathsep.join(prepend_paths + paths)
            report(str(EnvExportEvent(k, v)) + "\n", level=0)
    except Exception as e:
        report(e)
        if opts.debug_mode:
            traceback.print_exc(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
