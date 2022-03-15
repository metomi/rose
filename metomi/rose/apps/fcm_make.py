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
# ----------------------------------------------------------------------------
"""Builtin application: run "fcm make"."""

from contextlib import suppress
import os
from pipes import quote
import shlex
import sys
from tempfile import mkdtemp

from metomi.rose.app_run import BuiltinApp, ConfigValueError
from metomi.rose.env import (
    UnboundEnvironmentVariableError,
    env_export,
    env_var_process,
)
from metomi.rose.fs_util import FileSystemEvent
from metomi.rose.popen import (
    RosePopenError,
    WorkflowFileNotFoundError
)

ORIG = 0
CONT = 1


class FCMMakeApp(BuiltinApp):

    """Run "fcm make"."""

    CFG_FILE_NAME = "fcm-make%(name)s.cfg"
    OPT_JOBS = "4"
    SCHEME = "fcm_make"
    ORIG_CONT_MAP = (SCHEME, SCHEME + "2")

    def get_app_key(self, name):
        """Return the fcm_make* application key if name is fcm_make2*."""
        return name.replace(self.ORIG_CONT_MAP[1], self.ORIG_CONT_MAP[0])

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """Run "fcm make".

        This application will only work under "rose task-run".

        """
        # Determine if this is an original task or a continuation task
        orig_cont_map = _conf_value(
            conf_tree, ["orig-cont-map"], ":".join(self.ORIG_CONT_MAP)
        ).split(":", 1)
        task = app_runner.suite_engine_proc.get_task_props()

        if orig_cont_map[CONT] in task.task_name:
            return self._run_cont(
                app_runner, conf_tree, opts, args, uuid, task, orig_cont_map
            )
        else:
            return self._run_orig(
                app_runner, conf_tree, opts, args, uuid, task, orig_cont_map
            )

    def _get_fcm_make_cmd(self, conf_tree, opts, args, dest, make_name):
        """Return a list containing the "fcm make" command to invoke."""
        cmd = ["fcm", "make"]
        if make_name is None:
            make_name = ""
        cfg_file_name = self.CFG_FILE_NAME % {"name": make_name}
        if os.access(cfg_file_name, os.F_OK | os.R_OK) and dest:
            cmd += ["-f", os.path.abspath(cfg_file_name)]
        if dest:
            cmd += ["-C", dest]
        if make_name:
            # "-n NAME" option requires fcm-2015.05+
            cmd += ["-n", make_name]
        if opts.new_mode:
            cmd.append("-N")
        cmd += [
            "-j",
            _conf_value(
                conf_tree,
                ["opt.jobs"],
                os.getenv("ROSE_TASK_N_JOBS", self.OPT_JOBS),
            ),
        ]
        cmd_args = _conf_value(
            conf_tree, ["args"], os.getenv("ROSE_TASK_OPTIONS")
        )
        if cmd_args:
            cmd += shlex.split(cmd_args)
        if args:
            cmd += args
        return cmd

    def _invoke_fcm_make(
        self,
        app_runner,
        conf_tree,
        opts,
        args,
        uuid,
        task,
        dests,
        fast_root,
        make_name,
    ):
        """Wrap "fcm make" call, may use fast_root working directory."""
        if opts.new_mode:
            # Remove items in destinations in new mode
            # Ensure that it is not the current working directory, which should
            # already be cleaned.
            open(uuid, "w").close()
            try:
                for dest in dests:
                    if dest and ":" in dest:
                        # Remove a remote destination
                        auth, name = dest.split(":", 1)
                        cmd = app_runner.popen.get_cmd(
                            "ssh",
                            auth,
                            (
                                "! test -e %(name)s/%(uuid)s && "
                                + "(ls -d %(name)s || true) && rm -fr %(name)s"
                            )
                            % {"name": quote(name), "uuid": uuid},
                        )
                        out = app_runner.popen.run_ok(*cmd)[0]
                        for line in out.splitlines():
                            if line == name:
                                app_runner.handle_event(
                                    FileSystemEvent(
                                        FileSystemEvent.DELETE, dest
                                    )
                                )
                    elif dest and not os.path.exists(os.path.join(dest, uuid)):
                        # Remove a local destination
                        app_runner.fs_util.delete(dest)
            finally:
                os.unlink(uuid)
        # "rsync" existing dest to fast working directory, if relevant
        # Only work with fcm-2015.05+
        dest = dests[0]
        if fast_root:
            # N.B. Name in "little endian", like cycle task ID
            prefix = ".".join(
                [
                    task.task_name,
                    task.task_cycle_time,
                    # suite_name may be a hierarchical registration which
                    # isn't a safe prefix
                    task.suite_name.replace(os.sep, '_'),
                ]
            )
            os.makedirs(fast_root, exist_ok=True)
            dest = mkdtemp(prefix=prefix, dir=fast_root)
            # N.B. Don't use app_runner.popen.get_cmd("rsync") as we are using
            #      "rsync" for a local copy.
            rsync_prefixes = ["rsync", "-a"]
            if not dests[0]:
                dests[0] = "."
            if os.path.isdir(dests[0]):
                cmd = rsync_prefixes + [dests[0] + os.sep, dest + os.sep]
                try:
                    app_runner.popen.run_simple(*cmd)
                except RosePopenError:
                    app_runner.fs_util.delete(dest)
                    raise

        # Launch "fcm make"
        cmd = self._get_fcm_make_cmd(conf_tree, opts, args, dest, make_name)
        try:
            app_runner.popen(*cmd, stdout=sys.stdout, stderr=sys.stderr)
        finally:
            # "rsync" fast working directory to dests[0], if relevant
            if dest != dests[0] and os.path.isdir(dest):
                app_runner.fs_util.makedirs(dests[0])
                stat = os.stat(dests[0])
                cmd = rsync_prefixes + [dest + os.sep, dests[0] + os.sep]
                app_runner.popen.run_simple(*cmd)
                os.chmod(dests[0], stat.st_mode)
                app_runner.fs_util.delete(dest)

    def _run_orig(
        self, app_runner, conf_tree, opts, args, uuid, task, orig_cont_map
    ):
        """Run "fcm make" in original location."""
        # Determine the destination
        dest_orig_str = _conf_value(conf_tree, ["dest-orig"])
        if dest_orig_str is None and _conf_value(
            conf_tree, ["use-pwd"]
        ) not in ["True", "true"]:
            dest_orig_str = os.path.join("share", task.task_name)
        dest_orig = dest_orig_str
        if dest_orig is not None and not os.path.isabs(dest_orig):
            dest_orig = os.path.join(task.suite_dir, dest_orig)
        dests = [dest_orig]

        # Determine if mirror is necessary or not
        # Determine the name of the continuation task
        task_name_cont = task.task_name.replace(
            orig_cont_map[ORIG], orig_cont_map[CONT]
        )
        auth = None
        with suppress(WorkflowFileNotFoundError):
            auth = app_runner.suite_engine_proc.get_task_auth(
                task.suite_name, task_name_cont
            )
        if auth is not None:
            dest_cont = _conf_value(conf_tree, ["dest-cont"])
            if dest_cont is None:
                if dest_orig_str is not None:
                    dest_cont = dest_orig_str
                elif dest_orig:
                    dest_cont = os.path.join("share", task.task_name)
                else:
                    dest_cont = os.path.join(
                        "work", task.task_cycle_time, task_name_cont
                    )
            if not os.path.isabs(dest_cont):
                dest_cont = os.path.join(task.suite_dir_rel, dest_cont)
            dests.append(auth + ":" + dest_cont)
            # Environment variables for backward compat. "fcm make"
            # supports arguments as extra configurations since version
            # 2014-03.
            for name in ["ROSE_TASK_MIRROR_TARGET", "MIRROR_TARGET"]:
                env_export(name, dests[CONT], app_runner.event_handler)

            # "mirror" for backward compat. Use can specify a null string as
            # value to switch off the mirror target configuration.
            mirror_step = _conf_value(conf_tree, ["mirror-step"], "mirror")
            if mirror_step:
                args.append("%s.target=%s" % (mirror_step, dests[CONT]))
                # "mirror.prop{config-file.name}" requires fcm-2015.05+
                make_name_cont = _conf_value(
                    conf_tree,
                    ["make-name-cont"],
                    orig_cont_map[CONT].replace(orig_cont_map[ORIG], ""),
                )
                if make_name_cont:
                    args.append(
                        "%s.prop{config-file.name}=%s"
                        % (mirror_step, make_name_cont)
                    )

        # Launch "fcm make"
        self._invoke_fcm_make(
            app_runner,
            conf_tree,
            opts,
            args,
            uuid,
            task,
            dests,
            _conf_value(conf_tree, ["fast-dest-root-orig"]),
            _conf_value(conf_tree, ["make-name-orig"]),
        )

    def _run_cont(
        self, app_runner, conf_tree, opts, args, uuid, task, orig_cont_map
    ):
        """Continue "fcm make" in mirror location."""
        # Determine the destination
        dest_cont = _conf_value(conf_tree, ["dest-cont"])
        if dest_cont is None:
            dest_cont = _conf_value(conf_tree, ["dest-orig"])
        if dest_cont is None and _conf_value(conf_tree, ["use-pwd"]) not in [
            "True",
            "true",
        ]:
            task_name_orig = task.task_name.replace(
                orig_cont_map[CONT], orig_cont_map[ORIG]
            )
            dest_cont = os.path.join("share", task_name_orig)
        if dest_cont and not os.path.isabs(dest_cont):
            dest_cont = os.path.join(task.suite_dir, dest_cont)

        # Launch "fcm make"
        self._invoke_fcm_make(
            app_runner,
            conf_tree,
            opts,
            args,
            uuid,
            task,
            [dest_cont],
            _conf_value(conf_tree, ["fast-dest-root-cont"]),
            _conf_value(
                conf_tree,
                ["make-name-cont"],
                orig_cont_map[CONT].replace(orig_cont_map[ORIG], ""),
            ),
        )


def _conf_value(conf_tree, keys, default=None):
    """Return conf setting value, with env var processed."""
    value = conf_tree.node.get_value(keys, default)
    if value is None:
        return
    try:
        return env_var_process(value)
    except UnboundEnvironmentVariableError as exc:
        raise ConfigValueError(keys, value, exc)
