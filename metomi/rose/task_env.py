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
"""Provide a common environment for a task in a cycling suite."""

from glob import glob
import os
from metomi.rose.env import EnvExportEvent
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator
from metomi.rose.suite_engine_proc import SuiteEngineProcessor
import sys
import traceback

PATH_GLOBS = {
    "PATH": ["share/fcm[_-]make*/*/bin", "work/*/fcm[_-]make*/*/bin"],
}


def get_prepend_paths(event_handler=None, path_root=None, path_glob_args=None,
                      full_mode=False):
    """Return map of PATH-like env-var names to path lists to prepend to them.

    event_handler -- An instance of metomi.rose.reporter.Reporter or an object
                     with a similar interface.
    path_root -- If a glob is relative and this is defined, this is the root
                 directory of the relative path.
    path_glob_args -- A list of strings in the form GLOB or NAME=GLOB. NAME is
                      "PATH" by default or should be PATH-like environment
                      variable name. GLOB should be a glob pattern for matching
                      file system paths to prepend to NAME.
    full_mode -- If True, prepend relevant paths in site/user configuration and
                 the setting defined in "rose.task_env.PATH_GLOBS".

    Return something like:
        {"PATH": ["/opt/foo/bin", "/opt/bar/bin"],
         # ... and so on
        }

    """

    prepend_paths_map = {}

    # site/user configuration
    if full_mode:
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
                for value in node.value.split():
                    if os.path.exists(value):
                        values.append(value)
                if values:
                    prepend_paths_map[env_key] = values

    # Default or specified globs
    path_globs_map = {}
    if full_mode:
        for name, path_globs in PATH_GLOBS.items():
            path_globs_map[name] = path_globs
    if path_glob_args:
        for path_glob_arg in path_glob_args:
            if path_glob_arg is None:
                continue
            if "=" in path_glob_arg:
                name, value = path_glob_arg.split("=", 1)
            else:
                name, value = "PATH", path_glob_arg
            if name not in path_globs_map:
                path_globs_map[name] = []
            path_globs_map[name].append(value)
    more_prepend_paths_map = {}
    if not path_root:
        path_root = os.getcwd()
    for name, path_globs in path_globs_map.items():
        if name not in more_prepend_paths_map:
            more_prepend_paths_map[name] = []
        for path_glob in path_globs:
            if path_glob:
                if path_glob.startswith("~"):
                    path_glob = os.path.expanduser(path_glob)
                if not os.path.isabs(path_glob):
                    path_glob = os.path.join(path_root, path_glob)
                for path in sorted(glob(path_glob)):
                    more_prepend_paths_map[name].append(path)
            else:
                more_prepend_paths_map[name] = []  # empty value resets
    for name, more_prepend_paths in more_prepend_paths_map.items():
        if name in prepend_paths_map:
            prepend_paths_map[name].extend(more_prepend_paths)
        elif more_prepend_paths:
            prepend_paths_map[name] = more_prepend_paths
    for key, prepend_paths in prepend_paths_map.items():
        prepend_paths.reverse()

    return prepend_paths_map


def main():
    """rose task-env."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("cycle", "cycle_offsets", "path_globs",
                              "prefix_delim", "suffix_delim")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness - 1)
    suite_engine_proc = SuiteEngineProcessor.get_processor(
        event_handler=report)
    kwargs = dict(vars(opts))
    try:
        task_props = suite_engine_proc.get_task_props(*args, **kwargs)
        for key, value in task_props:
            report(str(EnvExportEvent(key, value)) + "\n", level=0)
        path_globs = opts.path_globs
        if path_globs is None:
            path_globs = []
        prepend_paths_map = get_prepend_paths(report,
                                              task_props.suite_dir,
                                              path_globs,
                                              full_mode=True)
        for key, prepend_paths in prepend_paths_map.items():
            orig_paths = []
            orig_v = os.getenv(key, "")
            if orig_v:
                orig_paths = orig_v.split(os.pathsep)
            path = os.pathsep.join(prepend_paths + orig_paths)
            report(str(EnvExportEvent(key, path)) + "\n", level=0)
    except Exception as exc:
        report(exc)
        if opts.debug_mode:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
