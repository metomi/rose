# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
"""Builtin application: run "fcm make"."""

from rose.env import env_export
from rose.run import BuiltinApp
import os
import shlex
import sys

class FCMMakeApp(BuiltinApp):

    """Run "fcm make"."""

    SCHEME = "fcm_make"
    SCHEME2 = SCHEME + "2"

    def get_app_key(self, name):
        """Return the fcm_make* application key if name is fcm_make2*."""
        if name.startswith(self.SCHEME2):
            return self.SCHEME + name.replace(self.SCHEME2, "")
        return name

    def run(self, app_runner, config, opts, args, uuid, work_files):
        """
        Run "fcm make".

        This application will only work under "rose task-run".

        """
        t = app_runner.suite_engine_proc.get_task_props()

        if t.task_name.startswith(self.SCHEME2):
            self._run2(app_runner, config, opts, args, uuid, work_files, t)
            return

        task2_name = self.SCHEME2 + t.task_name.replace(self.SCHEME, "")

        use_pwd = config.get_value(["use-pwd"]) in ["True", "true"]
        auth = app_runner.suite_engine_proc.get_task_auth(
                t.suite_name, task2_name)
        if auth is not None:
            target = "@".join(auth) + ":"
            if use_pwd:
                target += os.path.join(t.suite_dir_rel, "work", t.task_id)
            else:
                target += os.path.join(t.suite_dir_rel, "share", t.task_name)
            env_export("ROSE_TASK_MIRROR_TARGET", target,
                       app_runner.event_handler)
            # N.B. MIRROR_TARGET deprecated
            env_export("MIRROR_TARGET", target, app_runner.event_handler)

        cmd = ["fcm", "make"]
        for c in [os.path.abspath("fcm-make.cfg"),
                  os.path.join(t.suite_dir, "etc", t.task_name + ".cfg")]:
            if os.access(c, os.F_OK | os.R_OK):
                cmd += ["-f", c]
                break
        if not use_pwd:
            cmd += ["-C", os.path.join(t.suite_dir, "share", t.task_name)]
        cmd_opt_jobs = config.get_value(["opt.jobs"],
                                        os.getenv("ROSE_TASK_N_JOBS", "4"))
        cmd += ["-j", cmd_opt_jobs]
        cmd_opts = config.get_value(["opts"], os.getenv("ROSE_TASK_OPTIONS"))
        cmd += shlex.split(cmd_opts)
        cmd += args
        app_runner.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)

    def _run2(self, app_runner, config, opts, args, uuid, work_files, t):
        cmd = ["fcm", "make"]
        if config.get_value(["use-pwd"]) in ["True", "true"]:
            task1_id = self.SCHEME + t.task_id.replace(self.SCHEME2, "")
            cmd += ["-C", os.path.join(t.suite_dir, "work", task1_id)]
        else:
            task1_name = self.SCHEME + t.task_name.replace(self.SCHEME2, "")
            cmd += ["-C", os.path.join(t.suite_dir, "share", task1_name)]
        cmd_opt_jobs = config.get_value(["opt.jobs"],
                                        os.getenv("ROSE_TASK_N_JOBS", "4"))
        cmd += ["-j", cmd_opt_jobs]
        cmd_opts = config.get_value(["opts"], os.getenv("ROSE_TASK_OPTIONS"))
        cmd += shlex.split(cmd_opts)
        cmd += args
        app_runner.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)
