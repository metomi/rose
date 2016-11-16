# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
"""Logic specific to the Cylc suite engine."""

import filecmp
from glob import glob
import os
from pipes import quote
import pwd
import re
from random import shuffle
from rose.fs_util import FileSystemEvent
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import (
    SuiteEngineProcessor, SuiteHostConnectError, SuiteScanResult,
    SuiteEngineGlobalConfCompatError, TaskProps)
import shlex
import signal
import socket
import sqlite3
import tarfile
from tempfile import mkstemp
from time import sleep, time
from uuid import uuid4


_PORT_FILE = "port-file"
_PORT_SCAN = "port-scan"


class CylcProcessor(SuiteEngineProcessor):

    """Logic specific to the cylc suite engine."""

    PGREP_CYLC_RUN = r"python.*/bin/cylc-(run|restart)( | .+ )%s( |$)"
    REC_CYCLE_TIME = re.compile(
        r"\A[\+\-]?\d+(?:W\d+)?(?:T\d+(?:Z|[+-]\d+)?)?\Z")  # Good enough?
    SCHEME = "cylc"
    SUITE_CONF = "suite.rc"
    SUITE_DIR_REL_ROOT = "cylc-run"
    TASK_ID_DELIM = "."

    TIMEOUT = 60  # seconds

    def __init__(self, *args, **kwargs):
        SuiteEngineProcessor.__init__(self, *args, **kwargs)
        self.daos = {}
        self.host = None
        self.user = None

    def check_global_conf_compat(self):
        """Raise exception on incompatible Cylc global configuration."""
        expected = os.path.join("~", self.SUITE_DIR_REL_ROOT)
        expected = os.path.expanduser(expected)
        for key in ["[hosts][localhost]run directory",
                    "[hosts][localhost]work directory"]:
            out = self.popen("cylc", "get-global-config", "-i", key)[0]
            lines = out.splitlines()
            if lines and lines[0] != expected:
                raise SuiteEngineGlobalConfCompatError(
                    self.SCHEME, key, lines[0])

    def clean_hook(self, suite_name=None):
        """Pass."""
        pass

    def cmp_suite_conf(
            self, suite_name, run_mode, strict_mode=False, debug_mode=False):
        """Parse and compare current "suite.rc" with that in the previous run.

        (Re-)register and validate the "suite.rc" file.
        Raise RosePopenError on failure.
        Return True if "suite.rc.processed" is unmodified c.f. previous run.
        Return False otherwise.

        """
        suite_dir = self.get_suite_dir(suite_name)
        if run_mode == "run":
            self.popen.run_simple("cylc", "register", suite_name, suite_dir)
        f_desc, new_suite_rc_processed = mkstemp()
        os.close(f_desc)
        command = ["cylc", "validate", "-v", "-o", new_suite_rc_processed]
        if debug_mode:
            command.append("--debug")
        if strict_mode:
            command.append("--strict")
        command.append(suite_name)
        old_suite_rc_processed = os.path.join(suite_dir, "suite.rc.processed")
        try:
            self.popen.run_simple(*command, stdout_level=Event.V)
            return (
                os.path.exists(old_suite_rc_processed) and
                filecmp.cmp(old_suite_rc_processed, new_suite_rc_processed))
        finally:
            os.unlink(new_suite_rc_processed)

    def gcontrol(self, suite_name, host=None, engine_version=None, args=None):
        """Launch control GUI for a suite_name running at a host."""
        if not self.is_suite_registered(suite_name):
            raise SuiteNotRegisteredError(suite_name)
        if not host:
            host = "localhost"
        environ = dict(os.environ)
        if engine_version:
            environ.update({self.get_version_env_name(): engine_version})
        fmt = r"nohup cylc gui --host=%s %s %s 1>%s 2>&1 &"
        args_str = self.popen.list_to_shell_str(args)
        self.popen(fmt % (host, suite_name, args_str, os.devnull),
                   env=environ, shell=True)

    @classmethod
    def get_suite_dir_rel(cls, suite_name, *paths):
        """Return the relative path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        return os.path.join(cls.SUITE_DIR_REL_ROOT, suite_name, *paths)

    def get_suite_jobs_auths(self, suite_name, cycle_time=None,
                             task_name=None):
        """Return remote ["[user@]host", ...] for submitted jobs."""
        auths = []
        # Check if "task_jobs" table is available or not
        if self._db_has_table(suite_name, "task_jobs"):
            stmt = "SELECT DISTINCT user_at_host FROM task_jobs"
            stmt_where_list = []
            stmt_args = []
        else:
            stmt = "SELECT DISTINCT misc FROM task_events"
            stmt_where_list = ["(event==? OR event==? OR event==?)"]
            stmt_args = ["submission succeeded", "succeeded", "failed"]
        for key, arg in [["cycle", cycle_time], ["name", task_name]]:
            if arg:
                stmt_where_list.append(key + "==?")
                stmt_args.append(arg)
        if stmt_where_list:
            stmt += " WHERE " + " AND ".join(stmt_where_list)
        for row in self._db_exec(suite_name, stmt, stmt_args):
            if row and row[0]:
                auth = self._parse_user_host(auth=row[0])
                if auth:
                    auths.append(auth)
        self._db_close(suite_name)
        return auths

    def get_suite_run_hosts(self, user_name, suite_name, host_names=None):
        """Return a list of host(s) where suite_name has running processes."""
        if user_name is None:
            user_name = pwd.getpwuid(os.getuid()).pw_name
        else:
            try:
                pwd.getpwnam(user_name)
            except KeyError:  # invalid user name
                return []

        # Get suite host name from:
        # * ~USERID/cylc-run/SUITE/.service/contact
        # * ~USERID/cylc-run/SUITE/log/rose-suite-run.host
        for func in [self._host_from_contact_file, self._host_from_rose_log]:
            try:
                file_path, host_name = func(user_name, suite_name)
            except (IOError, IndexError, TypeError):
                # Not running on localhost?
                # Running on usual hosts with no share FS?
                # (port file) Suite started with version before cylc-6.8.0?
                pass
            else:
                if host_name:
                    yes_list, no_list, fail_list = self._suite_hosts_pgrep(
                        user_name, suite_name, [host_name])
                    if yes_list:
                        return [host_name]
                    elif no_list:
                        if file_path:
                            self.fs_util.delete(file_path)
                        return []
                    else:  # fail_list
                        raise SuiteHostConnectError(
                            suite_name, user_name, [host_name])

        # Look for suite on specified or configured suite hosts
        yes_list, _, fail_list = self._suite_hosts_pgrep(
            user_name, suite_name, host_names)
        if yes_list:  # If suite running on any host, report them
            return yes_list
        elif fail_list:  # Suite may still be running on unconnected hosts
            raise SuiteHostConnectError(suite_name, user_name, fail_list)
        else:  # We can be quite sure that suite is not running
            return []

    @classmethod
    def _host_from_contact_file(cls, user_name, suite_name):
        """Get host from port file line 2, require cylc-6.8.0+."""
        file_path = os.path.join(
            os.path.expanduser("~" + user_name),
            cls.get_suite_dir_rel(suite_name, ".service", "contact"))
        try:
            for line in open(file_path):
                key, value = [item.strip() for item in line.split("=", 1)]
                if key == "CYLC_SUITE_HOST":
                    return file_path, value
        except IOError, ValueError:
            return

    def _host_from_rose_log(self, user_name, suite_name):
        """Get host from rose-suite-run.host file."""
        file_path = os.path.join(
            os.path.expanduser("~" + user_name),
            self.get_suite_dir_rel(suite_name, "log", "rose-suite-run.host"))
        return file_path, open(file_path).read().strip()

    def _suite_hosts_pgrep(self, user_name, suite_name, host_names=None):
        """Helper for "self.get_suite_run_hosts".

        Return [yes_list, no_list, fail_list] where yes_list contains a list
        of hosts with processes running suite_name, no_list contains a list of
        hosts with no processes running suite_name and fail_list contains a
        list of hosts that we are unable to connect to.
        """
        if not host_names:
            conf = ResourceLocator.default().get_conf()
            host_names = ["localhost"]
            for key in ["scan-hosts", "hosts"]:
                names = shlex.split(
                    conf.get_value(["rose-suite-run", key], ""))
                if names:
                    host_names += self.host_selector.expand(names)[0]
        pgrep = [
            "pgrep", "-f", "-u", user_name,
            self.PGREP_CYLC_RUN % (suite_name)]
        host_name_ctx_dict = {}
        if self.user is None:
            self.user = pwd.getpwuid(os.getuid()).pw_name
        for host_name in host_names:
            if (self.host_selector.is_local_host(host_name) and
                    (not user_name or user_name == self.user)):
                # localhost
                host_name_ctx_dict[host_name] = (
                    self.popen.run_bg(*pgrep), True)  # is_local=True
            else:
                # alternate host and/or alternate user
                auth = host_name
                if user_name:
                    auth = user_name + "@" + host_name
                command = self.popen.get_cmd("ssh", "-n", auth, (
                    " ".join([quote(item) for item in pgrep]) + " || true"))
                host_name_ctx_dict[host_name] = (
                    self.popen.run_bg(*command), False)  # is_local=False
        yes_list = []
        no_list = []
        fail_list = []
        while host_name_ctx_dict:
            for host_name, ctx in host_name_ctx_dict.items():
                proc, is_local = ctx
                ret_code = proc.poll()
                if ret_code is None:
                    continue
                host_name_ctx_dict.pop(host_name)
                out = proc.communicate()[0]
                ret_code = proc.wait()
                if out and out.splitlines()[0].isdigit():
                    # pgrep has returned some entries
                    # suite running on host
                    yes_list.append(host_name)
                elif is_local or ret_code == 0:
                    # pgrep has no entry, local or ssh did not fail
                    # suite not running on host
                    no_list.append(host_name)
                else:
                    # ssh failed
                    # can't tell if suite running on host or not
                    fail_list.append(host_name)
        return yes_list, no_list, fail_list

    def get_task_auth(self, suite_name, task_name):
        """
        Return [user@]host for a remote task in a suite.

        Or None if task does not run remotely.

        """
        try:
            out = self.popen(
                "cylc", "get-config", "-o",
                "-i", "[runtime][%s][remote]owner" % task_name,
                "-i", "[runtime][%s][remote]host" % task_name,
                suite_name)[0]
        except RosePopenError:
            return
        user, host = (None, None)
        items = out.strip().split(None, 1)
        if items:
            user = items.pop(0).replace("*", " ")
        if items:
            host = items.pop(0).replace("*", " ")
        return self._parse_user_host(user=user, host=host)

    def get_tasks_auths(self, suite_name):
        """Return a list of unique [user@]host for remote tasks in a suite."""
        actual_hosts = {}
        auths = []
        out = self.popen("cylc", "get-config", "-ao",
                         "-i", "[remote]owner",
                         "-i", "[remote]host",
                         suite_name)[0]
        for line in out.splitlines():
            items = line.split(None, 2)
            user, host = (None, None)
            items.pop(0)
            if items:
                user = items.pop(0).replace("*", " ")
            if items:
                host = items.pop(0).replace("*", " ")
            if host in actual_hosts:
                host = str(actual_hosts[host])
                auth = self._parse_user_host(user=user, host=host)
            else:
                auth = self._parse_user_host(user=user, host=host)
                if auth and "@" in auth:
                    actual_hosts[host] = auth.split("@", 1)[1]
                else:
                    actual_hosts[host] = auth
            if auth and auth not in auths:
                auths.append(auth)
        return auths

    def get_task_props_from_env(self):
        """Get attributes of a suite task from environment variables.

        Return a TaskProps object containing the attributes of a suite task.

        """

        suite_name = os.environ["CYLC_SUITE_NAME"]
        suite_dir_rel = self.get_suite_dir_rel(suite_name)
        suite_dir = self.get_suite_dir(suite_name)
        task_id = os.environ["CYLC_TASK_ID"]
        task_name = os.environ["CYLC_TASK_NAME"]
        task_cycle_time = os.environ["CYLC_TASK_CYCLE_POINT"]
        cycling_mode = os.environ.get("CYLC_CYCLING_MODE", "gregorian")
        if task_cycle_time == "1" and not cycling_mode == "integer":
            task_cycle_time = None
        task_log_root = os.environ["CYLC_TASK_LOG_ROOT"]
        task_is_cold_start = "false"
        if os.environ.get("CYLC_TASK_IS_COLDSTART", "True") == "True":
            task_is_cold_start = "true"

        return TaskProps(suite_name=suite_name,
                         suite_dir_rel=suite_dir_rel,
                         suite_dir=suite_dir,
                         task_id=task_id,
                         task_name=task_name,
                         task_cycle_time=task_cycle_time,
                         task_log_dir=os.path.dirname(task_log_root),
                         task_log_root=task_log_root,
                         task_is_cold_start=task_is_cold_start,
                         cycling_mode=cycling_mode)

    def get_version(self):
        """Return Cylc's version."""
        return self.popen("cylc", "--version")[0].strip()

    def is_suite_registered(self, suite_name):
        """See if a suite is registered
            Return True directory for a suite if it is registered
            Return False otherwise
        """
        return self.popen.run("cylc", "get-directory", suite_name)[0] == 0

    def job_logs_archive(self, suite_name, items):
        """Archive cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        cycles = []
        if "*" in items:
            stmt = "SELECT DISTINCT cycle FROM task_events"
            for row in self._db_exec(suite_name, stmt):
                cycles.append(row[0])
            self._db_close(suite_name)
        else:
            for item in items:
                cycle = self._parse_task_cycle_id(item)[0]
                if cycle:
                    cycles.append(cycle)
        self.job_logs_pull_remote(suite_name, cycles, prune_remote_mode=True)
        cwd = os.getcwd()
        self.fs_util.chdir(self.get_suite_dir(suite_name))
        try:
            for cycle in cycles:
                archive_file_name0 = os.path.join("log",
                                                  "job-" + cycle + ".tar")
                archive_file_name = archive_file_name0 + ".gz"
                if os.path.exists(archive_file_name):
                    continue
                glob_ = os.path.join(cycle, "*", "*", "*")
                names = glob(os.path.join("log", "job", glob_))
                if not names:
                    continue
                f_bsize = os.statvfs(".").f_bsize
                tar = tarfile.open(archive_file_name0, "w", bufsize=f_bsize)
                for name in names:
                    cycle, _, s_n, ext = self.parse_job_log_rel_path(name)
                    if s_n == "NN" or ext == "job.status":
                        continue
                    tar.add(name, name.replace("log/", "", 1))
                tar.close()
                # N.B. Python's gzip is slow
                self.popen.run_simple("gzip", "-f", archive_file_name0)
                self.handle_event(FileSystemEvent(FileSystemEvent.CREATE,
                                                  archive_file_name))
                self.fs_util.delete(os.path.join("log", "job", cycle))
        finally:
            try:
                self.fs_util.chdir(cwd)
            except OSError:
                pass

    def job_logs_pull_remote(self, suite_name, items,
                             prune_remote_mode=False, force_mode=False):
        """Pull and housekeep the job logs on remote task hosts.

        suite_name -- The name of a suite.
        items -- A list of relevant items.
        prune_remote_mode -- Remove remote job logs after pulling them.
        force_mode -- Pull even if "job.out" already exists.

        """
        # Pull from remote.
        # Create a file with a uuid name, so system knows to do nothing on
        # shared file systems.
        uuid = str(uuid4())
        log_dir_rel = self.get_suite_dir_rel(suite_name, "log", "job")
        log_dir = os.path.join(os.path.expanduser("~"), log_dir_rel)
        uuid_file_name = os.path.join(log_dir, uuid)
        self.fs_util.touch(uuid_file_name)
        try:
            auths_filters = []  # [(auths, includes, excludes), ...]
            if "*" in items:
                auths = self.get_suite_jobs_auths(suite_name)
                if auths:
                    # A shuffle here should allow the load for doing "rm -rf"
                    # to be shared between job hosts who share a file system.
                    shuffle(auths)
                    auths_filters.append((auths, [], []))
            else:
                for item in items:
                    cycle, name = self._parse_task_cycle_id(item)
                    if cycle is not None:
                        arch_f_name = "job-" + cycle + ".tar.gz"
                        if os.path.exists(arch_f_name):
                            continue
                    # Don't bother if "job.out" already exists
                    # Unless forced to do so
                    if (cycle is not None and name is not None and
                            not prune_remote_mode and not force_mode and
                            os.path.exists(os.path.join(
                                log_dir, str(cycle), name, "NN", "job.out"))):
                        continue
                    auths = self.get_suite_jobs_auths(suite_name, cycle, name)
                    if auths:
                        # A shuffle here should allow the load for doing "rm
                        # -rf" to be shared between job hosts who share a file
                        # system.
                        shuffle(auths)
                        includes = []
                        excludes = []
                        if cycle is None and name is None:
                            includes = []
                            excludes = []
                        elif name is None:
                            includes = ["/" + cycle]
                            excludes = ["/*"]
                        elif cycle is None:
                            includes = ["/*/" + name]
                            excludes = ["/*/*"]
                        else:
                            includes = ["/" + cycle, "/" + cycle + "/" + name]
                            excludes = ["/*", "/*/*"]
                        auths_filters.append((auths, includes, excludes))

            for auths, includes, excludes in auths_filters:
                for auth in auths:
                    data = {"auth": auth,
                            "log_dir_rel": log_dir_rel,
                            "uuid": uuid,
                            "glob_": "*"}
                    if includes:
                        data["glob_"] = includes[-1][1:]  # Remove leading /
                    cmd = self.popen.get_cmd(
                        "ssh", auth,
                        ("cd %(log_dir_rel)s && " +
                         "(! test -f %(uuid)s && ls -d %(glob_)s)") % data)
                    ret_code, ssh_ls_out, _ = self.popen.run(*cmd)
                    if ret_code:
                        continue
                    cmd_list = ["rsync"]
                    for include in includes:
                        cmd_list.append("--include=" + include)
                    for exclude in excludes:
                        cmd_list.append("--exclude=" + exclude)
                    cmd_list.append("%(auth)s:%(log_dir_rel)s/" % data)
                    cmd_list.append(log_dir)
                    try:
                        cmd = self.popen.get_cmd(*cmd_list)
                        self.popen(*cmd)
                    except RosePopenError as exc:
                        self.handle_event(exc, level=Reporter.WARN)
                    if not prune_remote_mode:
                        continue
                    try:
                        cmd = self.popen.get_cmd(
                            "ssh", auth,
                            "cd %(log_dir_rel)s && rm -fr %(glob_)s" % data)
                        self.popen(*cmd)
                    except RosePopenError as exc:
                        self.handle_event(exc, level=Reporter.WARN)
                    else:
                        for line in sorted(ssh_ls_out.splitlines()):
                            event = FileSystemEvent(
                                FileSystemEvent.DELETE,
                                "%s:log/job/%s/" % (auth, line))
                            self.handle_event(event)
        finally:
            self.fs_util.delete(uuid_file_name)

    def job_logs_remove_on_server(self, suite_name, items):
        """Remove cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        cycles = []
        if "*" in items:
            stmt = "SELECT DISTINCT cycle FROM task_events"
            for row in self._db_exec(suite_name, stmt):
                cycles.append(row[0])
            self._db_close(suite_name)
        else:
            for item in items:
                cycle = self._parse_task_cycle_id(item)[0]
                if cycle:
                    cycles.append(cycle)

        cwd = os.getcwd()
        self.fs_util.chdir(self.get_suite_dir(suite_name))
        try:
            for cycle in cycles:
                # tar.gz files
                archive_file_name = os.path.join("log",
                                                 "job-" + cycle + ".tar.gz")
                if os.path.exists(archive_file_name):
                    self.fs_util.delete(archive_file_name)
                # cycle directories
                dir_name_prefix = os.path.join("log", "job")
                dir_name = os.path.join(dir_name_prefix, cycle)
                if os.path.exists(dir_name):
                    self.fs_util.delete(dir_name)
        finally:
            try:
                self.fs_util.chdir(cwd)
            except OSError:
                pass

    @classmethod
    def parse_job_log_rel_path(cls, f_name):
        """Return (cycle, task, submit_num, ext)."""
        return f_name.replace("log/job/", "").split("/", 3)

    @staticmethod
    def process_suite_hook_args(*args, **_):
        """Rearrange args for TaskHook.run."""
        task = None
        if len(args) == 3:
            hook_event, suite, hook_message = args
        else:
            hook_event, suite, task, hook_message = args
        return [suite, task, hook_event, hook_message]

    def run(self, suite_name, host=None, host_environ=None, run_mode=None,
            args=None):
        """Invoke "cylc run" (in a specified host).

        The current working directory is assumed to be the suite log directory.

        suite_name: the name of the suite.
        host: the host to run the suite. "localhost" if None.
        host_environ: a dict of environment variables to export in host.
        run_mode: call "cylc restart|reload" instead of "cylc run".
        args: arguments to pass to "cylc run".

        """

        # Check that "host" is not the localhost
        if host and self.host_selector.is_local_host(host):
            host = None

        # Invoke "cylc run" or "cylc restart"
        if run_mode not in ["reload", "restart", "run"]:
            run_mode = "run"
        opt_force = ""
        if run_mode == "reload":
            opt_force = " --force"
        # N.B. We cannot do "cylc run --host=HOST". STDOUT redirection means
        # that the log will be redirected back via "ssh" to the localhost.
        bash_cmd = r"cylc %s%s %s %s" % (
            run_mode, opt_force, suite_name,
            self.popen.list_to_shell_str(args))
        if host:
            bash_cmd_prefix = "set -eu\ncd\n"
            log_dir = self.get_suite_dir_rel(suite_name, "log")
            bash_cmd_prefix += "mkdir -p %s\n" % log_dir
            bash_cmd_prefix += "cd %s\n" % log_dir
            if host_environ:
                for key, value in host_environ.items():
                    val = self.popen.list_to_shell_str([value])
                    bash_cmd_prefix += "%s=%s\n" % (key, val)
                    bash_cmd_prefix += "export %s\n" % (key)
            ssh_cmd = self.popen.get_cmd("ssh", host, "bash", "--login")
            out, err = self.popen(*ssh_cmd, stdin=(bash_cmd_prefix + bash_cmd))
        else:
            out, err = self.popen(bash_cmd, shell=True)
        if err:
            self.handle_event(err, kind=Event.KIND_ERR)
        if out:
            self.handle_event(out)

    def scan(self, hosts=None, timeout=None):
        """Scan for running suites (in hosts).

        Return (suite_scan_results, exceptions) where
        suite_scan_results is a list of SuiteScanResult instances and
        exceptions is a list of exceptions resulting from any failed scans

        Default timeout for SSH and "cylc scan" command is 5 seconds.

        """
        if not hosts:
            hosts = ["localhost"]
        if timeout is None:
            timeout = self.TIMEOUT
        cmd = ["cylc", "scan", "--pyro-timeout=%s" % timeout] + list(hosts)
        proc = self.popen.run_bg(*cmd)
        results = {}
        exceptions = []
        end_time = time() + timeout
        while time() < end_time:
            sleep(0.1)
            ret_code = proc.poll()
            if ret_code is None:
                continue
            if ret_code == 0:
                for line in proc.communicate()[0].splitlines():
                    name, location = line.split()
                    host = location.split("@")[1].split(":")[0]
                    results[(name, host, _PORT_SCAN)] = SuiteScanResult(
                        name, location)
            else:
                out, err = proc.communicate()
                exceptions.append(RosePopenError(cmd, ret_code, out, err))
            proc = None
            break
        # Timed out, kill remaining processes
        if proc is not None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            else:
                ret_code = proc.wait()
                out, err = proc.communicate()
                exceptions.append(RosePopenError(key[2], ret_code, out, err))
        return (sorted(results.values()), exceptions)

    def shutdown(self, suite_name, host=None, engine_version=None, args=None,
                 stderr=None, stdout=None):
        """Shut down the suite.

        suite_name -- the name of the suite.
        host -- a host where the suite is running.
        engine_version -- if specified, use this version of Cylc.
        stderr -- A file handle for stderr, if relevant for suite engine.
        stdout -- A file handle for stdout, if relevant for suite engine.
        args -- extra arguments for "cylc shutdown".

        """
        command = ["cylc", "shutdown", suite_name, "--force"]
        if host:
            command += ["--host=%s" % host]
        if args:
            command += args
        environ = dict(os.environ)
        if engine_version:
            environ.update({self.get_version_env_name(): engine_version})
        self.popen.run_simple(
            *command, env=environ, stderr=stderr, stdout=stdout)

    def _db_close(self, suite_name):
        """Close a named database connection."""
        if self.daos.get(suite_name) is not None:
            self.daos[suite_name].close()

    def _db_exec(self, suite_name, stmt, stmt_args=None, commit=False):
        """Execute a query on a named database connection."""
        daos = self._db_init(suite_name)
        return daos.execute(stmt, stmt_args, commit)

    def _db_has_table(self, suite_name, table_name):
        """Return True if table_name exists in the suite database."""
        cursor = self._db_exec(
            suite_name,
            "SELECT name FROM sqlite_master WHERE name==?", [table_name])
        return (cursor and cursor.fetchone() is not None)

    def _db_init(self, suite_name):
        """Initialise a named database connection."""
        if suite_name not in self.daos:
            prefix = "~"
            db_f_name = os.path.expanduser(os.path.join(
                prefix, self.get_suite_dir_rel(suite_name, "log", "db")))
            self.daos[suite_name] = CylcSuiteDAO(db_f_name)
        return self.daos[suite_name]

    def _parse_task_cycle_id(self, item):
        """Parse name.cycle. Return (cycle, name)."""
        cycle, name = None, None
        if self.REC_CYCLE_TIME.match(item):
            cycle = item
        elif self.TASK_ID_DELIM in item:
            name, cycle = item.split(self.TASK_ID_DELIM, 1)
        else:
            name = item
        return (cycle, name)

    def _parse_user_host(self, auth=None, user=None, host=None):
        """Parse user@host. Return normalised [user@]host string."""
        if self.user is None:
            self.user = pwd.getpwuid(os.getuid()).pw_name
        if self.host is None:
            self.host = socket.gethostname()
        if auth is not None:
            user = None
            host = auth
            if "@" in auth:
                user, host = auth.split("@", 1)
        if user in ["None", self.user]:
            user = None
        if host and ("`" in host or "$" in host):
            command = ["bash", "-ec", "H=" + host + "; echo $H"]
            host = self.popen(*command)[0].strip()
        if (host in ["None", self.host] or
                self.host_selector.is_local_host(host)):
            host = None
        if user and host:
            auth = user + "@" + host
        elif user:
            auth = user + "@" + self.host
        elif host:
            auth = host
        else:
            auth = None
        return auth


class CylcSuiteDAO(object):

    """Generic SQLite Data Access Object."""

    CONNECT_RETRY_DELAY = 0.1
    N_CONNECT_TRIES = 10

    def __init__(self, db_f_name):
        self.db_f_name = db_f_name
        self.conn = None
        self.cursor = None

    def close(self):
        """Close the DB connection."""
        if self.conn is not None:
            try:
                self.conn.close()
            except (sqlite3.OperationalError, sqlite3.ProgrammingError):
                pass
        self.cursor = None
        self.conn = None

    def commit(self):
        """Commit any changes to current connection."""
        if self.conn is not None:
            self.conn.commit()

    def connect(self, is_new=False):
        """Connect to the DB. Set the cursor. Return the connection."""
        if self.cursor is not None:
            return self.cursor
        if not is_new and not os.access(self.db_f_name, os.F_OK | os.R_OK):
            return None
        for _ in range(self.N_CONNECT_TRIES):
            try:
                self.conn = sqlite3.connect(
                    self.db_f_name, self.CONNECT_RETRY_DELAY)
                self.cursor = self.conn.cursor()
            except sqlite3.OperationalError:
                sleep(self.CONNECT_RETRY_DELAY)
                self.conn = None
                self.cursor = None
            else:
                break
        return self.conn

    def execute(self, stmt, stmt_args=None, commit=False):
        """Execute a statement. Return the cursor."""
        if stmt_args is None:
            stmt_args = []
        for _ in range(self.N_CONNECT_TRIES):
            if self.connect() is None:
                return []
            try:
                self.cursor.execute(stmt, stmt_args)
            except sqlite3.OperationalError:
                sleep(self.CONNECT_RETRY_DELAY)
                self.conn = None
                self.cursor = None
            except sqlite3.ProgrammingError:
                self.conn = None
                self.cursor = None
            else:
                break
        if self.cursor is None:
            return []
        if commit:
            self.commit()
        return self.cursor


class SuiteNotRegisteredError(Exception):

    """An exception raised when a suite is not registered."""
    def __str__(self):
        return "%s: not a registered suite." % self.args[0]
