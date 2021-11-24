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
"""Implement "rose task-run"."""

import os
import sys
import traceback

from metomi.rose.app_run import AppRunner
from metomi.rose.env import env_export
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Reporter
from metomi.rose.run import Runner
from metomi.rose.task_env import get_prepend_paths


class TaskAppNotFoundError(Exception):

    """Error: a task has no associated application configuration."""

    def __str__(self):
        return "%s (key=%s): task has no associated application." % self.args


class TaskRunner(Runner):

    """A wrapper to a Rose task."""

    NAME = "task"
    OPTIONS = AppRunner.OPTIONS + [
        "app_key",
        "cycle",
        "cycle_offsets",
        "path_globs",
        "prefix_delim",
        "suffix_delim",
    ]

    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self.app_runner = AppRunner(
            event_handler=self.event_handler,
            popen=self.popen,
            config_pm=self.config_pm,
            fs_util=self.fs_util,
            suite_engine_proc=self.suite_engine_proc,
        )

    def run_impl(self, opts, args, uuid, work_files):
        """Run application configuration as a suite task."""
        # "rose task-env"
        t_prop = self.suite_engine_proc.get_task_props(
            cycle=opts.cycle,
            cycle_offsets=opts.cycle_offsets,
            prefix_delim=opts.prefix_delim,
            suffix_delim=opts.suffix_delim,
        )
        is_changed = False
        for key, value in t_prop:
            if os.getenv(key) != value:
                env_export(key, value, self.event_handler)
                is_changed = True

        path_globs = opts.path_globs
        if path_globs is None:
            path_globs = []
        prepend_paths_map = get_prepend_paths(
            self.event_handler,
            t_prop.suite_dir,
            path_globs,
            full_mode=is_changed,
        )
        for key, prepend_paths in prepend_paths_map.items():
            orig_paths = []
            orig_v = os.getenv(key, "")
            if orig_v:
                orig_paths = orig_v.split(os.pathsep)
            value = os.pathsep.join(prepend_paths + orig_paths)
            env_export(key, value, self.event_handler)

        # Name association with builtin applications
        builtin_app = None
        if opts.app_mode is None:
            builtin_apps_manager = self.app_runner.builtins_manager
            builtin_app = builtin_apps_manager.guess_handler(t_prop.task_name)
            if builtin_app is not None:
                opts.app_mode = builtin_app.SCHEME

        # Determine what app config to use
        if not opts.conf_dir:
            for app_key in [opts.app_key, os.getenv("ROSE_TASK_APP")]:
                if app_key is not None:
                    conf_dir = os.path.join(t_prop.suite_dir, "app", app_key)
                    if not os.path.isdir(conf_dir):
                        raise TaskAppNotFoundError(t_prop.task_name, app_key)
                    break
            else:
                app_key = t_prop.task_name
                conf_dir = os.path.join(
                    t_prop.suite_dir, "app", t_prop.task_name
                )
                if (
                    not os.path.isdir(conf_dir)
                    and builtin_app is not None
                    and builtin_app.get_app_key(t_prop.task_name)
                ):
                    # A builtin application may select a different app_key
                    # based on the task name.
                    app_key = builtin_app.get_app_key(t_prop.task_name)
                    conf_dir = os.path.join(t_prop.suite_dir, "app", app_key)
                if not os.path.isdir(conf_dir):
                    raise TaskAppNotFoundError(t_prop.task_name, app_key)
            opts.conf_dir = conf_dir

        return self.app_runner(opts, args)


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser(
        usage='rose task-run [OPTIONS] [--] [APP-COMMAND ...]',
        description='''
Provide an environment to run a suite task.

Provides environment variables documented in `rose task-env`. It is worth
noting that if the environment variables are already provided by
`rose task-env`, this command will not override them.

Normally, the suite task will select a Rose application configuration
that has the same name as the task. This can be overridden by the
`--app-key=KEY` option or the `ROSE_TASK_APP` environment variable.

SHORT OPTIONS
    All options of `rose app-run` and `rose task-env` are supported.
    Additional options are:

    --app-key=KEY
        Specify a named application configuration.
        ''',
        epilog='''
ENVIRONMENT VARIABLES
    All environment variables of `rose app-run` and `rose task-env` are
    supported. All environment variables documented in `rose task-env` are
    passed to the application `rose task-run` runs.
    The following environment variables are used by `rose task-run`:

    ROSE_TASK_APP
        Specify a named application configuration.

SEE ALSO
    * `rose app-run`
    * `rose task-env`
        ''',
    )
    option_keys = TaskRunner.OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args()
    event_handler = Reporter(opts.verbosity - opts.quietness)
    runner = TaskRunner(event_handler)
    try:
        sys.exit(runner(opts, args))
    except Exception as exc:
        runner.handle_event(exc)
        if opts.debug_mode:
            traceback.print_exc()
        if isinstance(exc, RosePopenError):
            sys.exit(exc.ret_code)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
