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
import sys

class FCMMakeTaskUtil(TaskUtilBase):

    """Run "fcm make"."""

    CONFIG_IS_OPTIONAL = True
    SCHEME = "fcm_make"
    SCHEME2 = "fcm_make2"

    def can_handle(self, key):
        return key.startswith(self.SCHEME) and not key.startswith(self.SCHEME2)

    def run_impl_main(self, config, opts, args, uuid, work_files):
        t = self.suite_engine_proc.get_task_props()
        task2_name = self.SCHEME2 + t.task_name.replace(self.SCHEME, "")
        auth = self.suite_engine_proc.get_remote_auth(t.suite_name, task2_name)
        if auth is not None:
            target = "@".join(auth)
            target += ":" + os.path.join(t.suite_dir_rel, "share", t.task_name)
            # FIXME: name-space for environment variable?
            env_export("MIRROR_TARGET", target, self.event_handler)
        cfg = os.path.join(t.suite_dir, "etc", t.task_name + ".cfg")
        dir = os.path.join(t.suite_dir, "share", t.task_name)
        n_jobs = os.getenv("ROSE_TASK_N_JOBS", "4")
        cmd = "fcm make -f %s -C %s -j %s" % (cfg, dir, n_jobs)
        if os.getenv("ROSE_TASK_OPTIONS"):
            cmd += " " + os.getenv("ROSE_TASK_OPTIONS")
        if args:
            cmd += " " + self.popen.list_to_shell_str(args)
        if os.getenv("ROSE_TASK_PRE_SCRIPT"):
            cmd = ". " + os.getenv("ROSE_TASK_PRE_SCRIPT") + " && " + cmd
        self.popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)
