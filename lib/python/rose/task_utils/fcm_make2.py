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
"""Task utility: run "fcm make" (continue)."""

from rose.run import TaskUtilBase
import os
import shlex
import sys

class FCMMake2TaskUtil(TaskUtilBase):

    """Run "fcm make" (continue)."""

    CONFIG_IS_OPTIONAL = True
    SCHEME = "fcm_make2"
    SCHEME1 = SCHEME[0:-1]

    def get_app_key(self, task_name):
        if task_name.startswith(self.SCHEME):
            return self.SCHEME1 + task_name.replace(self.SCHEME, "")
        return task_name

    def run_impl_main(self, config, opts, args, uuid, work_files):
        t = self.suite_engine_proc.get_task_props()

        cmd = ["fcm", "make"]
        if config.get_value(["use-pwd"]) in ["True", "true"]:
            task1_id = self.SCHEME1 + t.task_id.replace(self.SCHEME, "")
            cmd += ["-C", os.path.join(t.suite_dir, "work", task1_id)]
        else:
            task1_name = self.SCHEME1 + t.task_name.replace(self.SCHEME, "")
            cmd += ["-C", os.path.join(t.suite_dir, "share", task1_name)]
        cmd_opt_jobs = config.get_value(["opt.jobs"],
                                        os.getenv("ROSE_TASK_N_JOBS", "4"))
        cmd += ["-j", cmd_opt_jobs]
        cmd_opts = config.get_value(["opts"], os.getenv("ROSE_TASK_OPTIONS"))
        cmd += shlex.split(cmd_opts)
        cmd += args
        self.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)
