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
"""Task utility: run "fcm make"."""

from rose.env import env_export
from rose.run import TaskUtilBase
import os
import shlex
import sys

class FCMMakeTaskUtil(TaskUtilBase):

    """Run "fcm make"."""

    CONFIG_IS_OPTIONAL = True
    SCHEME = "fcm_make"
    SCHEME2 = SCHEME + "2"

    def can_handle(self, key):
        return key.startswith(self.SCHEME) and not key.startswith(self.SCHEME2)

    def run_impl_main(self, config, opts, args, uuid, work_files):
        t = self.suite_engine_proc.get_task_props()
        task2_name = self.SCHEME2 + t.task_name.replace(self.SCHEME, "")

        use_pwd = config.get_value(["use-pwd"]) in ["True", "true"]
        auth = self.suite_engine_proc.get_task_auth(t.suite_name, task2_name)
        if auth is not None:
            target = "@".join(auth) + ":"
            if use_pwd:
                target += os.path.join(t.suite_dir_rel, "work", t.task_id)
            else:
                target += os.path.join(t.suite_dir_rel, "share", t.task_name)
            env_export("ROSE_TASK_MIRROR_TARGET", target, self.event_handler)
            # N.B. MIRROR_TARGET deprecated
            env_export("MIRROR_TARGET", target, self.event_handler)

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
        self.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)
