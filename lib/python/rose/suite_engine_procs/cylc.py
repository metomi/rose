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
from glob import glob
import os
import pwd
import re
import rose.config
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter
from rose.suite_engine_proc \
        import SuiteEngineProcessor, SuiteScanResult, TaskProps
import socket
import sqlite3
from time import mktime, sleep, strptime


class CylcProcessor(SuiteEngineProcessor):

    """Logic specific to the Cylc suite engine."""

    PYRO_TIMEOUT = 5
    RUN_DIR_REL_ROOT = "cylc-run"
    SCHEME = "cylc"
    SUITE_CONF = "suite.rc"
    TASK_ID_DELIM = "."
    TASK_LOG_DELIM = "."

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

    def get_suite_db_file(self, suite_name):
        """Return the path to the suite runtime database file."""
        return self.get_suite_dir(suite_name, "cylc-suite.db")

    def get_suite_dir_rel(self, suite_name, *args):
        """Return the relative path to the suite running directory.

        Extra args, if specified, are added to the end of the path.

        """
        return os.path.join(self.RUN_DIR_REL_ROOT, suite_name, *args)

    def get_suite_events(self, suite_name):
        """Parse the cylc suite running database for task events.

        Return a data structure that looks like:
        {   <task_id>: {
                "name": <name>,
                "cycle_time": <cycle time string>,
                "submits": [
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
                ]
            }
            # ... more task IDs
        }
        """
        for i in range(3): # 3 retries
            try:
                return self._get_suite_events(suite_name)
            except sqlite3.OperationalError:
                sleep(1.0)
        return {}

    def _get_suite_events(self, suite_name):
        data = {}

        # Read task events from suite runtime database
        conn = sqlite3.connect(self.get_suite_db_file(suite_name))
        c = conn.cursor()
        EVENTS = {"submitted": "submit",
                  "started": "init",
                  "succeeded": "pass",
                  "failed": "fail",
                  "signaled": "fail"}
        for row in c.execute(
                "SELECT time,name,cycle,submit_num,event,message"
                " FROM task_events"
                " ORDER BY time"):
            time, name, cycle_time, submit_num, key, message = row
            event = EVENTS.get(key, None)
            if event is None:
                continue
            event_time = mktime(strptime(time, "%Y-%m-%dT%H:%M:%S"))
            task_id = name + self.TASK_ID_DELIM + cycle_time
            if task_id not in data:
                data[task_id] = {"name": name,
                                 "cycle_time": cycle_time,
                                 "submits": []}
            submits = data[task_id]["submits"]
            submit_num = int(submit_num)
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
            if event in ["pass", "fail"]:
                status = event
                submit["events"]["exit"] = event_time
                submit["status"] = status
                if key == "signaled":
                    submit["signal"] = message.rsplit(None, 1)[-1]

        # Locate task log files
        for task_id, task_datum in data.items():
            name = task_datum["name"]
            cycle_time = task_datum["cycle_time"]
            for i, submit in enumerate(task_datum["submits"]):
                root = "job/" + self.TASK_LOG_DELIM.join([name, cycle_time,
                                                          str(i + 1)])
                for path in glob(root + "*"):
                    key = path[len(root) + 1:]
                    if not key:
                        key = "script"
                    elif key == "status":
                        continue
                    submit["files"][key] = {"n_bytes": os.stat(path).st_size}
        return data

    def get_suite_jobs_auths(self, suite_name, task_id=None):
        """Return remote [(user, host), ...] for submitted jobs (of a task)."""
        my_user = pwd.getpwuid(os.getuid())[0]
        my_host = socket.gethostname()
        conn = sqlite3.connect(self.get_suite_db_file(suite_name))
        c = conn.cursor()
        auths = []
        stmt = "SELECT DISTINCT host FROM task_events"
        stmt_args = tuple()
        if task_id:
            stmt += " WHERE name==? AND cycle==? AND event=='submitted'"
            stmt_args = tuple(task_id.split(self.TASK_ID_DELIM))
        for row in c.execute(stmt, stmt_args):
            u, h = row[0].split("@")
            user, host, my_user, my_host = self._parse_user_host(u, h)
            if (my_user, my_host) != (user, host):
                auths.append((user, host))
        return auths

    def get_task_auth(self, suite_name, task_name):
        """
        Return (user, host) for a remote task in a suite.

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
        u, h = None
        items = out.strip().split(None, 1)
        if items:
            u = items.pop(0).replace("*", " ")
        if items:
            h = items.pop(0).replace("*", " ")
        user, host, my_user, my_host = self._parse_user_host(u, h)
        if (my_user, my_host) == (user, host):
            return
        return (user, host)

    def get_tasks_auths(self, suite_name):
        """Return a list of unique user@host for remote tasks in a suite."""
        my_user = pwd.getpwuid(os.getuid())[0]
        my_host = socket.gethostname()
        actual_hosts = {}
        auths = []
        out, err = self.popen("cylc", "get-config", "-ao",
                              "-i", "[remote]owner",
                              "-i", "[remote]host",
                              suite_name)
        for line in out.splitlines():
            items = line.split(None, 2)
            task = items.pop(0).replace("*", " ")
            user, host = (my_user, my_host)
            if items:
                user = items.pop(0).replace("*", " ")
            if items:
                host = items.pop(0).replace("*", " ")
            if not actual_hosts.has_key(host):
                result = self._parse_user_host(user, host, my_user, my_host)
                user, actual_hosts[host] = result[0:2]
            if user in [None, "None"]:
                user = my_user
            host = actual_hosts[host]
            if (user, host) != (my_user, my_host) and (user, host) not in auths:
                auths.append((user, host))
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

    def ping(self, suite_name, hosts=None):
        """Return a list of host names where suite_name is running."""
        if not hosts:
            hosts = ["localhost"]
        host_proc_dict = {}
        for host in sorted(hosts):
            proc = self.popen.run_bg(
                    "cylc", "ping", "--host=" + host, suite_name)
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
            self.handle_event(err, type=Event.TYPE_ERR)
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

    def shutdown(self, suite_name, host=None, engine_version=None, args=None):
        """Shut down the suite."""
        command = ["cylc", "shutdown", "--force"]
        if host:
            command += ["--host=%s" % host]
        if args:
            command += args
        command += [suite_name]
        environ = dict(os.environ)
        if engine_version:
            environ.update({self.get_version_env_name(): engine_version})
        self.popen.run_simple(*command, env=environ)

    def update_job_log(self, suite_name, task_ids=None):
        """Update the log(s) of task jobs in suite_name.

        If "task_ids" is None, update the logs for all task jobs.

        """
        id_user_host_set = set()
        if task_ids:
            for task_id in task_ids:
                auths = self.get_suite_jobs_auths(suite_name, task_id)
                for user, host in auths:
                    id_user_host_set.add((task_id, user, host))
        else:
            users_and_hosts = self.get_suite_jobs_auths(suite_name)
            for user, host in users_and_hosts:
                id_user_host_set.add(("", user, host))

        log_dir_rel = self.get_task_log_dir_rel(suite_name)
        log_dir = os.path.join(os.path.expanduser("~"), log_dir_rel)
        for task_id, user, host in id_user_host_set:
            r_log_dir = "%s@%s:%s/%s*" % (user, host, log_dir_rel, task_id)
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

    def _parse_user_host(self, user, host, my_user=None, my_host=None):
        if my_user is None:
            my_user = pwd.getpwuid(os.getuid())[0]
        if my_host is None:
            my_host = socket.gethostname()
        if user in [None, "None"]:
            user = my_user
        if host in [None, "None", "localhost"]:
            host = my_host
        elif "`" in host or "$" in host:
            command = ["bash", "-ec", "H=" + host + "; echo $H"]
            host = self.popen(*command)[0].strip()
        return (user, host, my_user, my_host)
