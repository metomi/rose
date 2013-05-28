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
"""Logic specific to the Cylc suite engine."""

import ast
from fnmatch import fnmatchcase
from glob import glob
import os
import pwd
import re
import rose.config
from rose.env import env_var_process
from rose.fs_util import FileSystemEvent
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import \
        StillRunningError, SuiteEngineProcessor, SuiteScanResult, TaskProps
import shlex
import socket
import sqlite3
import tarfile
from time import mktime, sleep, strptime


class CylcProcessor(SuiteEngineProcessor):

    """Logic specific to the Cylc suite engine."""

    EVENTS = {"submission succeeded": "submit",
              "submission failed": "submit-fail",
              "started": "init",
              "succeeded": "pass",
              "failed": "fail",
              "execution started": "init",
              "execution succeeded": "pass",
              "execution failed": "fail",
              "signaled": "fail"}
    N_DB_CONNECT_RETRIES = 3
    PYRO_TIMEOUT = 5
    RUN_DIR_REL_ROOT = "cylc-run"
    SCHEME = "cylc"
    SUITE_CONF = "suite.rc"
    TASK_ID_DELIM = "."
    TASK_LOG_DELIM = "."

    def archive_job_logs(self, suite_name, log_archive_threshold):
        """Archive cycle job logs older than a threshold.

        Assume current working directory is suite's log directory.
        
        """
        rows = []
        for i in range(self.N_DB_CONNECT_RETRIES):
            try:
                conn = sqlite3.connect(self.get_suite_db_file(suite_name))
                c = conn.cursor()
                rows = c.execute("SELECT DISTINCT cycle FROM task_events")
            except sqlite3.OperationalError:
                sleep(1.0)
            else:
                break
        for row in rows:
            cycle_time = row[0]
            archive_file_name = self.get_cycle_log_archive_name(cycle_time)
            if (os.path.exists(archive_file_name) or
                cycle_time > log_archive_threshold): # str cmp
                continue
            # Pull from each remote host all job log files of this
            # cycle time.
            auths = self.get_suite_jobs_auths(suite_name, cycle_time)
            log_dir_rel = self.get_task_log_dir_rel(suite_name)
            log_dir = os.path.join(os.path.expanduser("~"), log_dir_rel)
            glob_pat = self.TASK_LOG_DELIM.join(["*", cycle_time, "*"])
            for auth in auths:
                r_glob = "%s:%s/%s" % (auth, log_dir_rel, glob_pat)
                cmd = self.popen.get_cmd("rsync", r_glob, log_dir)
                try:
                    out, err = self.popen(*cmd)
                except RosePopenError as e:
                    self.handle_event(e, level=Reporter.WARN)
            # Create the job log archive for this cycle time.
            tar = tarfile.open(archive_file_name, "w:gz")
            names = glob("job/" + glob_pat)
            for name in names:
                tar.add(name)
            tar.close()
            self.handle_event(FileSystemEvent(FileSystemEvent.CREATE,
                                              archive_file_name))
            # Remove local job log files of this cycle time.
            for name in names:
                self.fs_util.delete(name)
            # Remove remote job log files of this cycle time.
            for auth in auths:
                r_glob = "%s/%s" % (log_dir_rel, glob_pat)
                cmd = self.popen.get_cmd("ssh", auth, "rm", "-f", r_glob)
                try:
                    out, err = self.popen(*cmd)
                except RosePopenError as e:
                    self.handle_event(e, level=Reporter.WARN)

    def clean(self, suite_name):
        """Remove items created by the previous run of a suite.

        Change to user's $HOME for safety.

        """
        os.chdir(os.path.expanduser('~'))
        if not os.path.isdir(self.get_suite_dir_rel(suite_name)):
            return
        hostnames = ["localhost"]
        host_file_path = self.get_suite_dir_rel(
                suite_name, "log", "rose-suite-run.host")
        if os.access(host_file_path, os.F_OK | os.R_OK):
            for line in open(host_file_path):
                hostnames.append(line.strip())
        conf = ResourceLocator.default().get_conf()
        
        hostnames = self.host_selector.expand(
              conf.get_value(["rose-suite-run", "hosts"], "").split() +
              conf.get_value(["rose-suite-run", "scan-hosts"], "").split() +
              ["localhost"])[0]
        hostnames = list(set(hostnames))
        hosts_str = conf.get_value(["rose-suite-run", "scan-hosts"])
        
        hosts = []
        for h in hostnames:
            if h not in hosts:
                hosts.append(h)
            
        running_hosts = self.ping(suite_name, hosts)
        if running_hosts:
            raise StillRunningError(suite_name, running_hosts[0])
        job_auths = []
        if os.access(self.get_suite_db_file(suite_name), os.F_OK | os.R_OK):
            try:
                job_auths = self.get_suite_jobs_auths(suite_name)
            except sqlite3.OperationalError as e:
                pass
        for job_auth in job_auths + ["localhost"]:
            if "@" in job_auth:
                job_host = job_auth.split("@", 1)[1]
            else:
                job_host = job_auth
            dirs = [] 
            for key in ["share", "work"]:
                item_root = None
                node_value = conf.get_value(
                        ["rose-suite-run", "root-dir-" + key])
                for line in node_value.strip().splitlines():
                    pattern, value = line.strip().split("=", 1)
                    if fnmatchcase(job_host, pattern):
                        item_root = value.strip()
                        break
                if item_root is not None:
                    dir_rel = self.get_suite_dir_rel(suite_name, key)
                    item_path_source = os.path.join(item_root, dir_rel)
                    dirs.append(item_path_source)
            dirs.append(self.get_suite_dir_rel(suite_name))
            if job_auth == "localhost":
                for d in dirs:
                    d = os.path.realpath(env_var_process(d))
                    if os.path.exists(d):
                        self.fs_util.delete(d)
            else:
                command = self.popen.get_cmd("ssh", job_auth, "rm", "-rf")
                command += dirs
                self.popen(*command)

    def gcontrol(self, suite_name, host=None, engine_version=None, args=None):
        """Launch control GUI for a suite_name running at a host."""
        if not host:
            host = "localhost"
        environ = dict(os.environ)
        if engine_version:
            environ.update({self.get_version_env_name(): engine_version})
        fmt = r"nohup cylc gui --host=%s %s %s 1>%s 2>&1 &"
        args_str = self.popen.list_to_shell_str(args)
        self.popen(fmt % (host, suite_name, args_str, os.devnull),
                   env=environ, shell=True)

    def get_cycle_log_archive_name(self, cycle_time):
        """Return the jobs log archive file name of a given cycle time."""
        return "job-" + cycle_time + ".tar.gz"

    def get_suite_db_file(self, suite_name):
        """Return the path to the suite runtime database file."""
        return self.get_suite_dir(suite_name, "cylc-suite.db")

    def get_suite_dir_rel(self, suite_name, *args):
        """Return the relative path to the suite running directory.

        Extra args, if specified, are added to the end of the path.

        """
        return os.path.join(self.RUN_DIR_REL_ROOT, suite_name, *args)

    def get_suite_events(self, suite_name, task_ids):
        """Parse the cylc suite running database for task events.

        suite_name -- The name of the suite.
        task_ids -- A list of relevant task IDs. If empty or None, all tasks
                    are relevant.

        Assume current working directory is suite's log directory.

        Return a  data structure that looks like:
        {   <cycle time string>: {
                "cycle_time": <cycle time>,
                "tasks": {
                    <task name>: [
                        {   "events": {
                                "submit": <seconds-since-epoch>,
                                "init": <seconds-since-epoch>,
                                "exit": <seconds-since-epoch>,
                            },
                            "files": {
                                "script": {"n_bytes": <n_bytes>},
                                "out": {"n_bytes": <n_bytes>},
                                "err": {"n_bytes": <n_bytes>},
                                # ... more files
                            },
                            "signal": <signal-name-if-job-killed-by-signal>,
                            "status": <"pass"|"fail">,
                        },
                        # ... more re-submits of the task
                    ],
                    # ... more relevant task names
                }
            }
            # ... more relevant cycle times
        }
        """

        # Read task events from suite runtime database
        where = ""
        where_args = []
        for task_id in task_ids:
            cycle = None
            if self.TASK_ID_DELIM in task_id:
                name, cycle = task_id.split(self.TASK_ID_DELIM, 1)
                where_args += [name, cycle]
            else:
                where_args.append(task_id)
            if where:
                where += " OR"
            where += " (name=?"
            if cycle is not None:
                where += " AND cycle=?"
            where += ")"
        if where:
            where = " WHERE" + where
        rows = []
        for i in range(self.N_DB_CONNECT_RETRIES):
            try:
                conn = sqlite3.connect(self.get_suite_db_file(suite_name))
                c = conn.cursor()
                rows = c.execute(
                        "SELECT time,name,cycle,submit_num,event,message" +
                        " FROM task_events" +
                        where +
                        " ORDER BY time", where_args)
            except sqlite3.OperationalError as e:
                sleep(1.0)
            else:
                break

        data = {}
        for row in rows:
            ev_time, name, cycle_time, submit_num, key, message = row
            event = self.EVENTS.get(key, None)
            if event is None:
                continue
            event_time = mktime(strptime(ev_time, "%Y-%m-%dT%H:%M:%S"))
            task_id = name + self.TASK_ID_DELIM + cycle_time
            if cycle_time not in data:
                data[cycle_time] = {"cycle_time": cycle_time, "tasks": {}}
            if name not in data[cycle_time]["tasks"]:
                data[cycle_time]["tasks"][name] = []
            submits = data[cycle_time]["tasks"][name]
            submit_num = int(submit_num)
            if not submit_num:
                continue
            while submit_num > len(submits):
                submits.append({"events": {},
                                "status": None,
                                "signal": None,
                                "files": {}})
                for name in ["submit", "init", "exit"]:
                    submits[-1]["events"][name] = None
            submit = submits[submit_num - 1]
            submit["events"][event] = event_time
            status = None
            if event in ["init"]:
                if submit["events"]["submit"] is None:
                    submit["events"]["submit"] = event_time
            elif event in ["pass", "fail"]:
                status = event
                submit["events"]["exit"] = event_time
                submit["status"] = status
                if key == "signaled":
                    submit["signal"] = message.rsplit(None, 1)[-1]
                if submit["events"]["submit"] is None:
                    submit["events"]["submit"] = event_time
                if submit["events"]["init"] is None:
                    submit["events"]["init"] = event_time
            elif event in ["submit-fail"]:
                submit["events"]["submit"] = event_time
                submit["status"] = event

        # Job log files
        for cycle_time, datum in data.items():
            archive_file_name = self.get_cycle_log_archive_name(cycle_time)
            # Job logs of this cycle already archived
            if os.access(archive_file_name, os.F_OK | os.R_OK):
                datum["is_archived"] = True
                tar = tarfile.open(archive_file_name, "r:gz")
                for tarinfo in tar:
                    size = tarinfo.size
                    name = tarinfo.name[len("job/"):]
                    names = name.split(self.TASK_LOG_DELIM, 3)
                    if len(names) == 3:
                        key = "script"
                        task_name, c, submit_num = names
                    elif len(names) == 4:
                        task_name, c, submit_num, key = names
                        if key == "status":
                            continue
                    if task_name in datum["tasks"]:
                        submit = datum["tasks"][task_name][int(submit_num) - 1]
                        submit["files"][key] = {"n_bytes": size}
                tar.close()
                continue
            # Check stats of job logs of this cycle
            for name, submits in datum["tasks"].items():
                for i, submit in enumerate(submits):
                    delim = self.TASK_LOG_DELIM
                    root = "job/" + delim.join([name, cycle_time, str(i + 1)])
                    for path in glob(root + "*"):
                        key = path[len(root) + 1:]
                        if not key:
                            key = "script"
                        elif key == "status":
                            continue
                        n_bytes = os.stat(path).st_size
                        submit["files"][key] = {"n_bytes": n_bytes}
        return data

    def get_suite_jobs_auths(self, suite_name, cycle_time=None,
                             task_name=None):
        """Return remote [(user, host), ...] for submitted jobs (of a task)."""
        conn = sqlite3.connect(self.get_suite_db_file(suite_name))
        c = conn.cursor()
        auths = []
        stmt = "SELECT DISTINCT misc FROM task_events WHERE "
        stmt_args = tuple()
        if cycle_time:
            stmt += "cycle==? AND "
            stmt_args = stmt_args + (cycle_time,)
        if task_name:
            stmt += "name==? AND "
            stmt_args = stmt_args + (task_name,)
        stmt += "event=='submission succeeded'"
        for row in c.execute(stmt, stmt_args):
            if row and "@" in row[0]:
                auth = self._parse_user_host(auth=row[0])
                if auth:
                    auths.append(auth)
        return auths

    def get_task_auth(self, suite_name, task_name):
        """
        Return [user@]host for a remote task in a suite.

        Or None if task does not run remotely.

        """
        try:
            out, err = self.popen(
                    "cylc", "get-config", "-o",
                    "-i", "[runtime][%s][remote]owner" % task_name,
                    "-i", "[runtime][%s][remote]host" % task_name,
                    suite_name)
        except RosePopenError:
            return
        u, h = (None, None)
        items = out.strip().split(None, 1)
        if items:
            u = items.pop(0).replace("*", " ")
        if items:
            h = items.pop(0).replace("*", " ")
        return self._parse_user_host(user=u, host=h)

    def get_tasks_auths(self, suite_name):
        """Return a list of unique [user@]host for remote tasks in a suite."""
        actual_hosts = {}
        auths = []
        out, err = self.popen("cylc", "get-config", "-ao",
                              "-i", "[remote]owner",
                              "-i", "[remote]host",
                              suite_name)
        for line in out.splitlines():
            items = line.split(None, 2)
            task = items.pop(0).replace("*", " ")
            u, h = (None, None)
            if items:
                u = items.pop(0).replace("*", " ")
            if items:
                h = items.pop(0).replace("*", " ")
            if actual_hosts.has_key(h):
                h = str(actual_hosts[h])
                auth = self._parse_user_host(user=u, host=h)
            else:
                auth = self._parse_user_host(user=u, host=h)
                if auth and "@" in auth:
                    actual_hosts[h] = auth.split("@", 1)[1]
                else:
                    actual_hosts[h] = auth
            if auth and auth not in auths:
                auths.append(auth)
        return auths

    def get_task_log_dir_rel(self, suite):
        """Return the relative path to the log directory for suite tasks."""
        return self.get_suite_dir_rel(suite, "log", "job")

    def get_task_props_from_env(self):
        """Get attributes of a suite task from environment variables.

        Return a TaskProps object containing the attributes of a suite task.

        """

        suite_name = os.environ["CYLC_SUITE_REG_NAME"]
        suite_dir_rel = self.get_suite_dir_rel(suite_name)
        suite_dir = os.path.join(os.path.expanduser("~"), suite_dir_rel)
        task_id = os.environ["CYLC_TASK_ID"]
        task_name = os.environ["CYLC_TASK_NAME"]
        task_cycle_time = os.environ["CYLC_TASK_CYCLE_TIME"]
        if task_cycle_time == "1":
            task_cycle_time = None
        task_log_root = os.environ["CYLC_TASK_LOG_ROOT"]
        task_is_cold_start = "false"
        if os.environ["CYLC_TASK_IS_COLDSTART"] == "True":
            task_is_cold_start = "true"

        return TaskProps(suite_name=suite_name,
                         suite_dir_rel=suite_dir_rel,
                         suite_dir=suite_dir,
                         task_id=task_id,
                         task_name=task_name,
                         task_cycle_time=task_cycle_time,
                         task_log_root=task_log_root,
                         task_is_cold_start=task_is_cold_start)

    def get_version(self):
        """Return Cylc's version."""
        out, err = self.popen("cylc", "--version")
        return out.strip()

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler if it is callable."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def ping(self, suite_name, hosts=None, timeout=10):
        """Return a list of host names where suite_name is running."""
        if not hosts:
            hosts = ["localhost"]
        host_proc_dict = {}
        for host in sorted(hosts):
            proc = self.popen.run_bg(
                    "cylc", "ping", "--host=" + host, suite_name, 
                    "--pyro-timeout=" + str(timeout))
            host_proc_dict[host] = proc
        ping_ok_hosts = []
        while host_proc_dict:
            for host, proc in host_proc_dict.items():
                rc = proc.poll()
                if rc is not None:
                    host_proc_dict.pop(host)
                    if rc == 0:
                        ping_ok_hosts.append(host)
            if host_proc_dict:
                sleep(0.1)
        return ping_ok_hosts

    def process_suite_hook_args(self, *args, **kwargs):
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
        if host:
            localhosts = ["localhost"]
            try:
                localhosts.append(socket.gethostname())
            except IOError:
                pass
            if host in localhosts:
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
                    v = self.popen.list_to_shell_str([value])
                    bash_cmd_prefix += "%s=%s\n" % (key, v)
                    bash_cmd_prefix += "export %s\n" % (key)
            ssh_cmd = self.popen.get_cmd("ssh", host, "bash", "--login")
            out, err = self.popen(*ssh_cmd, stdin=(bash_cmd_prefix + bash_cmd))
        else:
            out, err = self.popen(bash_cmd, shell=True)
        if err:
            self.handle_event(err, type_=Event.TYPE_ERR)
        if out:
            self.handle_event(out)

    def scan(self, hosts=None):
        """Return a list of SuiteScanResult for suites running in hosts.
        """
        if not hosts:
            hosts = ["localhost"]
        host_proc_dict = {}
        for host in sorted(hosts):
            timeout = "--pyro-timeout=%s" % self.PYRO_TIMEOUT
            proc = self.popen.run_bg("cylc", "scan", "--host=" + host, timeout)
            host_proc_dict[host] = proc
        ret = []
        while host_proc_dict:
            for host, proc in host_proc_dict.items():
                rc = proc.poll()
                if rc is not None:
                    host_proc_dict.pop(host)
                    if rc == 0:
                        for line in proc.communicate()[0].splitlines():
                            ret.append(SuiteScanResult(*line.split()))
            if host_proc_dict:
                sleep(0.1)
        return ret

    def shutdown(self, suite_name, host=None, engine_version=None, args=None,
                 stderr=None, stdout=None):
        """Shut down the suite."""
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

    def update_job_log(self, suite_name, task_ids=None):
        """Update the log(s) of task jobs in suite_name.

        If "task_ids" is None, update the logs for all task jobs.

        """
        id_auth_set = set()
        if task_ids:
            for task_id in task_ids:
                task_name, cycle_time = task_id.split(self.TASK_ID_DELIM)
                archive_file_name = self.get_cycle_log_archive_name(cycle_time)
                if os.path.exists(archive_file_name):
                    continue
                auths = self.get_suite_jobs_auths(suite_name, cycle_time,
                                                  task_name)
                for auth in auths:
                    id_auth_set.add((task_id, auth))
        else:
            auths = self.get_suite_jobs_auths(suite_name)
            for auth in auths:
                id_auth_set.add(("", auth))

        log_dir_rel = self.get_task_log_dir_rel(suite_name)
        log_dir = os.path.join(os.path.expanduser("~"), log_dir_rel)
        for task_id, auth in id_auth_set:
            r_log_dir = ""
            r_log_dir += "%s:%s/%s*" % (auth, log_dir_rel, task_id)
            cmd = self.popen.get_cmd("rsync", r_log_dir, log_dir)
            try:
                out, err = self.popen(*cmd)
            except RosePopenError as e:
                self.handle_event(e, level=Reporter.WARN)

    def validate(self, suite_name, strict_mode=False):
        """(Re-)register and validate a suite."""
        suite_dir_rel = self.get_suite_dir_rel(suite_name)
        home = os.path.expanduser("~")
        suite_dir = os.path.join(home, suite_dir_rel)
        rc, out, err = self.popen.run("cylc", "get-directory", suite_name)
        suite_dir_old = None
        if out:
            suite_dir_old = out.strip()
        suite_passphrase = os.path.join(suite_dir, "passphrase")
        self.popen.run_simple("cylc", "refresh", "--unregister",
                              stdout_level=Event.VV)
        if suite_dir_old != suite_dir or not os.path.exists(suite_passphrase):
            self.popen.run_simple("cylc", "unregister", suite_name)
            suite_dir_old = None
        if suite_dir_old is None:
            self.popen.run_simple("cylc", "register", suite_name, suite_dir)
        passphrase_dir_root = os.path.join(home, ".cylc")
        for name in os.listdir(passphrase_dir_root):
            p = os.path.join(passphrase_dir_root, name)
            if os.path.islink(p) and not os.path.exists(p):
                self.fs_util.delete(p)
        passphrase_dir = os.path.join(passphrase_dir_root, suite_name)
        self.fs_util.symlink(suite_dir, passphrase_dir)
        command = ["cylc", "validate", "-v"]
        if strict_mode:
            command.append("--strict")
        command.append(suite_name)
        self.popen.run_simple(*command, stdout_level=Event.V)

    def _parse_user_host(self, auth=None, user=None, host=None):
        if getattr(self, "user", None) is None:
            self.user = pwd.getpwuid(os.getuid()).pw_name
        if getattr(self, "host", None) is None:
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
        if host in ["None", "localhost", self.host]:
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
