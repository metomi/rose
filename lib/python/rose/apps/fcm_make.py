# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# ----------------------------------------------------------------------------
"""Builtin application: run "fcm make"."""

from rose.env import env_export
from rose.app_run import BuiltinApp
import os
import shlex
import sys

ORIG = 0
CONT = 1


class FCMMakeApp(BuiltinApp):

    """Run "fcm make"."""

    OPT_JOBS = "4"
    SCHEME = "fcm_make"
    ORIG2CONT = (SCHEME, SCHEME + "2")

    def get_app_key(self, name):
        """Return the fcm_make* application key if name is fcm_make2*."""
        return name.replace(self.ORIG2CONT[1], self.ORIG2CONT[0])

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """Run "fcm make".

        This application will only work under "rose task-run".

        """
        task_name_orig2cont = conf_tree.node.get_value(
            ["task-name-orig2cont"], ":".join(self.ORIG2CONT)).split(":", 1)
        task = app_runner.suite_engine_proc.get_task_props()

        if task_name_orig2cont[CONT] in task.task_name:
            return self._run_cont(
                app_runner, conf_tree, args, task, task_name_orig2cont)

        cmd = ["fcm", "make"]
        use_pwd = conf_tree.node.get_value(["use-pwd"]) in ["True", "true"]
        for cfg in [
                "fcm-make.cfg",
                os.path.join(task.suite_dir, "etc", task.task_name + ".cfg")]:
            if os.access(cfg, os.F_OK | os.R_OK):
                if cfg != "fcm-make.cfg" or not use_pwd:
                    cmd += ["-f", os.path.abspath(cfg)]
                break
        if not use_pwd:
            cmd += [
                "-C",
                os.path.join(task.suite_dir, "share", task.task_name)]
        cmd += ["-j", conf_tree.node.get_value(
            ["opt.jobs"], os.getenv("ROSE_TASK_N_JOBS", self.OPT_JOBS))]
        cmd_args = conf_tree.node.get_value(
            ["args"], os.getenv("ROSE_TASK_OPTIONS"))
        if cmd_args:
            cmd += shlex.split(cmd_args)
        if args:
            cmd += args

        # "mirror" for backward compat. Use can specify a null string as value
        # to switch off the mirror target configuration.
        task_name_cont = task.task_name.replace(
            task_name_orig2cont[ORIG], task_name_orig2cont[CONT])
        auth = app_runner.suite_engine_proc.get_task_auth(
            task.suite_name, task_name_cont)
        if auth is not None:
            target = auth + ":"
            if use_pwd:
                target += os.path.join(
                    task.suite_dir_rel, "work", task.task_cycle_time,
                    task_name_cont)
            else:
                target += os.path.join(
                    task.suite_dir_rel, "share", task.task_name)
            # Environment variables for backward compat. "fcm make"
            # supports arguments as extra configurations since version
            # 2014-03.
            for name in ["ROSE_TASK_MIRROR_TARGET", "MIRROR_TARGET"]:
                env_export(name, target, app_runner.event_handler)

            mirror_step = conf_tree.node.get_value(["mirror-step"], "mirror")
            if mirror_step:
                cmd.append("%s.target=%s" % (mirror_step, target))
                make_name_cont = conf_tree.node.get_value(
                    ["make-name-cont"],
                    task_name_orig2cont[CONT].replace(
                        task_name_orig2cont[ORIG], ""))
                if make_name_cont:
                    cmd.append("%s.prop{config-file.name}=%s" % (
                        mirror_step, make_name_cont))

        app_runner.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)

    def _run_cont(self, app_runner, conf_tree, args, task,
                  task_name_orig2cont):
        """Continue "fcm make" in mirror location."""
        cmd = ["fcm", "make"]

        if not conf_tree.node.get_value(["use-pwd"]) in ["True", "true"]:
            task_name_orig = task.task_name.replace(
                task_name_orig2cont[CONT], task_name_orig2cont[ORIG])
            dest = os.path.join(task.suite_dir, "share", task_name_orig)
            cmd += ["-C", dest]
        make_name_cont = conf_tree.node.get_value(
            ["make-name-cont"],
            task_name_orig2cont[CONT].replace(task_name_orig2cont[ORIG], ""))
        if make_name_cont:
            cmd += ["-n", make_name_cont]

        cmd += ["-j", conf_tree.node.get_value(
            ["opt.jobs"], os.getenv("ROSE_TASK_N_JOBS", self.OPT_JOBS))]
        cmd_args = conf_tree.node.get_value(
            ["args"], os.getenv("ROSE_TASK_OPTIONS"))
        if cmd_args:
            cmd += shlex.split(cmd_args)
        if args:
            cmd += args
        app_runner.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)
