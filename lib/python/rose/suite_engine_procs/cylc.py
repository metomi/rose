# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
#-----------------------------------------------------------------------------
"""Logic specific to the Cylc suite engine."""

from fnmatch import fnmatch, fnmatchcase
from glob import glob
import os
import pwd
import re
from rose.env import env_var_process
from rose.fs_util import FileSystemEvent
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter
from rose.resource import ResourceLocator
from rose.suite_engine_proc import \
        SuiteEngineProcessor, SuiteScanResult, TaskProps
import socket
import sqlite3
import tarfile
from time import sleep
from uuid import uuid4


class CylcProcessor(SuiteEngineProcessor):

    """Logic specific to the Cylc suite engine."""

    EVENTS = {"submission succeeded": "submit",
              "submission failed": "fail(submit)",
              "submitting now": "submit-init",
              "started": "init",
              "succeeded": "success",
              "failed": "fail",
              "execution started": "init",
              "execution succeeded": "success",
              "execution failed": "fail",
              "signaled": "fail(%s)"}
    EVENT_TIME_INDICES = {"submit-init": 0, "init": 1, "success": 2, "fail": 2}
    EVENT_RANKS = {"submit-init": 0, "submit": 1, "fail(submit)": 1, "init": 2,
                   "success": 3, "fail": 3, "fail(%s)": 4}
    JOB_LOGS_DB = "log/rose-job-logs.db"
    JOB_LOG_TAIL_KEYS = {"": "00-script", "out": "01-out", "err": "02-err"}
    ORDERS = {
            "time_desc":
            "time DESC, task_events.submit_num DESC, name DESC, cycle DESC",
            "time_asc":
            "time ASC, task_events.submit_num ASC, name ASC, cycle ASC",
            "cycle_desc_name_asc":
            "cycle DESC, name ASC, task_events.submit_num DESC",
            "cycle_desc_name_desc":
            "cycle DESC, name DESC, task_events.submit_num DESC",
            "cycle_asc_name_asc":
            "cycle ASC, name ASC, task_events.submit_num DESC",
            "cycle_asc_name_desc":
            "cycle ASC, name DESC, task_events.submit_num DESC",
            "name_asc_cycle_asc":
            "name ASC, cycle ASC, task_events.submit_num DESC",
            "name_desc_cycle_asc":
            "name DESC, cycle ASC, task_events.submit_num DESC",
            "name_asc_cycle_desc":
            "name ASC, cycle DESC, task_events.submit_num DESC",
            "name_desc_cycle_desc":
            "name DESC, cycle DESC, task_events.submit_num DESC"}
    PYRO_TIMEOUT = 5
    REC_CYCLE_TIME = re.compile(r"\A[\+\-]?\d+(?:T\d+)?\Z") # Good enough?
    REC_SEQ_LOG = re.compile(r"\A(.*\.)(\d+)(\.html)?\Z")
    SCHEME = "cylc"
    STATUSES = {"active": ["submitting", "submitted", "running"],
                "fail": ["submission failed", "failed"],
                "success": ["succeeded"]}
    SUITE_CONF = "suite.rc"
    SUITE_DB = "cylc-suite.db"
    SUITE_DIR_REL_ROOT = "cylc-run"
    TASK_ID_DELIM = "."

    def __init__(self, *args, **kwargs):
        SuiteEngineProcessor.__init__(self, *args, **kwargs)
        self.daos = {self.SUITE_DB: {}, self.JOB_LOGS_DB: {}}

    def clean_hook(self, suite_name=None):
        """Run "cylc refresh --unregister" (at end of "rose suite-clean")."""
        self.popen.run("cylc", "refresh", "--unregister")
        passphrase_dir_root = os.path.expanduser(os.path.join("~", ".cylc"))
        for name in os.listdir(passphrase_dir_root):
            p = os.path.join(passphrase_dir_root, name)
            if os.path.islink(p) and not os.path.exists(p):
                self.fs_util.delete(p)

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

    def get_cycle_items_globs(self, name, cycle):
        """Return a glob to match named items created for a given cycle.

        E.g.:
        suite_engine_proc.get_cycle_items_globs("datac", "2013010100")
        # return "share/data/2013010100"

        Return None if named item not supported.

        """
        d = {"datac": "share/data/" + cycle, "work": "work/*." + cycle}
        return d.get(name)

    def get_suite_dir_rel(self, suite_name, *paths):
        """Return the relative path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        return os.path.join(self.SUITE_DIR_REL_ROOT, suite_name, *paths)

    def get_suite_job_events(self, user_name, suite_name, cycles, tasks,
                             no_statuses, order, limit, offset):
        """Return suite job events.

        user -- A string containing a valid user ID
        suite -- A string containing a valid suite ID
        cycles -- Display only task jobs matching these cycles. A value in the
                  list can be a cycle, the string "before|after CYCLE", or a
                  glob to match cycles.
        tasks -- Display only jobs for task names matching these names. Values
                 can be a valid task name or a glob like pattern for matching
                 valid task names.
        no_statuses -- Do not display jobs with these statuses. Valid values
                       are the keys of CylcProcessor.STATUSES.
        order -- Order search in a predetermined way. A valid value is one of
                 the keys in CylcProcessor.ORDERS.
        limit -- Limit number of returned entries
        offset -- Offset entry number

        Return (entries, of_n_entries) where:
        entries -- A list of matching entries
        of_n_entries -- Total number of entries matching query

        Each entry is a dict:
            {"cycle": cycle, "name": name, "submit_num": submit_num,
             "events": [time_submit, time_init, time_exit],
             "status": None|"submit|fail(submit)|init|success|fail|fail(%s)",
             "logs": {"script": {"path": path, "path_in_tar", path_in_tar,
                                 "size": size, "mtime": mtime},
                      "out": {...},
                      "err": {...},
                      ...}}

        """
        # Build WHERE expression to select by cycles and/or task names
        where = ""
        stmt_args = []
        if cycles:
            where_fragments = []
            for cycle in cycles:
                if cycle.startswith("before "):
                    value = cycle.split(None, 1)[-1]
                    where_fragments.append("cycle <= ?")
                elif cycle.startswith("after "):
                    value = cycle.split(None, 1)[-1]
                    where_fragments.append("cycle >= ?")
                else:
                    value = cycle
                    where_fragments.append("cycle GLOB ?")
                stmt_args.append(value)
            where += " AND (" + " OR ".join(where_fragments) + ")"
        if tasks:
            where_fragments = []
            for task in tasks:
                where_fragments.append("name GLOB ?")
                stmt_args.append(task)
            where += " AND (" + " OR ".join(where_fragments) + ")"
        if no_statuses:
            where_fragments = []
            for no_status in no_statuses:
                for status in self.STATUSES.get(no_status, []):
                    where_fragments.append("status != ?")
                    stmt_args.append(status)
            where += " AND (" + " AND ".join(where_fragments) + ")"
        # Execute query to get number of entries
        of_n_entries = 0
        stmt = ("SELECT COUNT(*) FROM"
                " task_events JOIN task_states USING (name,cycle)"
                " WHERE event==?")
        if where:
            stmt += " " + where
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt,
                                 ["submitting now"] + stmt_args):
            of_n_entries = row[0]
            break
        if not of_n_entries:
            return ([], 0)
        # Execute query to get entries
        entries = []
        stmt = ("SELECT" +
                " cycle, name, task_events.submit_num," +
                " group_concat(time), group_concat(event)," +
                " group_concat(message) " +
                " FROM" +
                " task_events JOIN task_states USING (cycle,name)" +
                " WHERE" +
                " (event==? OR event==? OR event==? OR" +
                "  event==? OR event==? OR event==?)" +
                where +
                " GROUP BY cycle, name, task_events.submit_num" +
                " ORDER BY " +
                self.ORDERS.get(order, self.ORDERS["time_desc"]))
        stmt_args_head = ["submitting now", "submission failed", "started",
                          "succeeded", "failed", "signaled"]
        stmt_args_tail = []
        if limit:
            stmt += " LIMIT ? OFFSET ?"
            stmt_args_tail = [limit, offset]
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name, stmt,
                stmt_args_head + stmt_args + stmt_args_tail):
            cycle, name, submit_num, times_str, events_str, messages_str = row
            entry = {"cycle": cycle, "name": name, "submit_num": submit_num,
                     "submit_num_max": 1, "events": [None, None, None],
                     "status": None, "logs": {}, "seq_logs_indexes": {}}
            entries.append(entry)
            events = events_str.split(",")
            times = times_str.split(",")
            if messages_str:
                messages = messages_str.split(",")
            else:
                messages = events
            event_rank = -1
            for event, t, message in zip(events, times, messages):
                my_event = self.EVENTS.get(event)
                if self.EVENT_TIME_INDICES.get(my_event) is not None:
                    entry["events"][self.EVENT_TIME_INDICES[my_event]] = t
                if (self.EVENT_RANKS.get(my_event) is not None and
                    self.EVENT_RANKS[my_event] > event_rank):
                    entry["status"] = my_event
                    event_rank = self.EVENT_RANKS[my_event]
                    if my_event == "fail(%s)":
                        signal = message.rsplit(None, 1)[-1]
                        entry["status"] = "fail(%s)" % signal

        submit_num_max_of = {}
        for entry in entries:
            cycle = entry["cycle"]
            name = entry["name"]
            if (cycle, name) not in submit_num_max_of:
                stmt = ("SELECT submit_num FROM task_states" +
                        " WHERE cycle==? AND name==?")
                for row in self._db_exec(self.SUITE_DB, user_name, suite_name,
                                         stmt, [cycle, name]):
                    submit_num_max_of[(cycle, name)] = row[0]
                    break
            entry["submit_num_max"] = submit_num_max_of[(cycle, name)]

        self._db_close(self.SUITE_DB, user_name, suite_name)

        # Job logs DB
        stmt = ("SELECT key,path,path_in_tar,mtime,size FROM log_files " +
                "WHERE cycle==? AND task==? AND submit_num==?")
        prefix = "~"
        if user_name:
            prefix += user_name
        user_suite_dir = os.path.join(os.path.expanduser(prefix),
                                      self.get_suite_dir_rel(suite_name))
        for entry in entries:
            stmt_args = [entry["cycle"], entry["name"], entry["submit_num"]]
            cursor = self._db_exec(self.JOB_LOGS_DB, user_name, suite_name,
                                   stmt, stmt_args)
            if cursor is None:
                continue
            for row in cursor:
                key, path, path_in_tar, mtime, size = row
                abs_path = os.path.join(user_suite_dir, path)
                entry["logs"][key] = {"path": path,
                                      "path_in_tar": path_in_tar,
                                      "mtime": mtime,
                                      "size": size,
                                      "exists": os.path.exists(abs_path),
                                      "seq_key": None}
                seq_log_match = self.REC_SEQ_LOG.match(key)
                if seq_log_match:
                    head, index_str, tail = seq_log_match.groups()
                    if not tail:
                        tail = ""
                    seq_key = head + "*" + tail
                    entry["logs"][key]["seq_key"] = seq_key
                    if seq_key not in entry["seq_logs_indexes"]:
                        entry["seq_logs_indexes"][seq_key] = {}
                    entry["seq_logs_indexes"][seq_key][int(index_str)] = key

            for seq_key, indexes in entry["seq_logs_indexes"].items():
                if len(indexes) <= 1:
                    entry["seq_logs_indexes"].pop(seq_key)
            for key, log_dict in entry["logs"].items():
                if log_dict["seq_key"] not in entry["seq_logs_indexes"]:
                    log_dict["seq_key"] = None
        self._db_close(self.JOB_LOGS_DB, user_name, suite_name)
        return (entries, of_n_entries)

    def get_suite_jobs_auths(self, suite_name, cycle_time=None,
                             task_name=None):
        """Return remote ["[user@]host", ...] for submitted jobs."""
        auths = []
        stmt = "SELECT DISTINCT misc FROM task_events WHERE "
        stmt_args = []
        if cycle_time:
            stmt += "cycle==? AND "
            stmt_args.append(cycle_time)
        if task_name:
            stmt += "name==? AND "
            stmt_args.append(task_name)
        stmt += "(event==? OR event==? OR event==?)"
        stmt_args += ["submission succeeded", "succeeded", "failed"]
        for row in self._db_exec(self.SUITE_DB, None, suite_name, stmt,
                                 stmt_args):
            if row and row[0]:
                auth = self._parse_user_host(auth=row[0])
                if auth:
                    auths.append(auth)
        self._db_close(self.SUITE_DB, None, suite_name)
        return auths

    def get_suite_logs_info(self, user_name, suite_name):
        """Return the information of the suite logs.

        Return a tuple that looks like:
            ("cylc-run",
             {"err": {"path": "log/suite/err", "mtime": mtime, "size": size},
              "log": {"path": "log/suite/log", "mtime": mtime, "size": size},
              "out": {"path": "log/suite/out", "mtime": mtime, "size": size}})

        """
        logs_info = {}
        prefix = "~"
        if user_name:
            prefix += user_name
        d_rel = self.get_suite_dir_rel(suite_name)
        d = os.path.expanduser(os.path.join(prefix, d_rel))
        for key in ["cylc-suite-env",
                    "log/suite/err", "log/suite/log", "log/suite/out",
                    "suite.rc", "suite.rc.processed"]:
            f_name = os.path.join(d, key)
            if os.path.isfile(f_name):
                s = os.stat(f_name)
                logs_info[key] = {"path": key,
                                  "mtime": s.st_mtime,
                                  "size": s.st_size}
        return ("cylc", logs_info)

    def get_suite_state_summary(self, user_name, suite_name):
        """Return a the state summary of a user's suite.

        Return {"last_activity_time": s, "is_running": b, "is_failed": b}
        where:
        * last_activity_time is a string in %Y-%m-%dT%H:%M:%S format,
          the time of the latest activity in the suite
        * is_running is a boolean to indicate if the suite is running
        * is_failed: a boolean to indicate if any tasks (submit) failed

        """
        last_activity_time = None
        stmt = "SELECT time FROM task_events ORDER BY time DESC LIMIT 1"
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt):
            last_activity_time = row[0]
            break

        is_running = self.is_suite_running(user_name, suite_name)
        is_running = bool(is_running)

        is_failed = False
        stmt = "SELECT status FROM task_states WHERE status GLOB ? LIMIT 1"
        stmt_args = ["*failed"]
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt,
                                 stmt_args):
            is_failed = True
            break
        self._db_close(self.SUITE_DB, user_name, suite_name)

        return {"last_activity_time": last_activity_time,
                "is_running": is_running,
                "is_failed": is_failed}

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
            if h in actual_hosts:
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

    def get_task_props_from_env(self):
        """Get attributes of a suite task from environment variables.

        Return a TaskProps object containing the attributes of a suite task.

        """

        suite_name = os.environ["CYLC_SUITE_REG_NAME"]
        suite_dir_rel = self.get_suite_dir_rel(suite_name)
        suite_dir = self.get_suite_dir(suite_name)
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

    def is_conf(self, path):
        """Return "cylc-suite-rc" if path is a Cylc suite.rc file."""
        if fnmatch(os.path.basename(path), "suite*.rc*"):
            return "cylc-suite-rc"

    def is_suite_registered(self, suite_name):
        """See if a suite is registered
            Return True directory for a suite if it is registered
            Return False otherwise
        """
        rc, out, err = self.popen.run("cylc", "get-directory", suite_name)
        return rc == 0

    def is_suite_running(self, user_name, suite_name, hosts=None):
        """Return the port file path if it looks like suite is running.

        If port file exists, return "PORT-FILE-PATH".
        If port file exists on a host, return "HOSTNAME:PORT-FILE-PATH".
        If no port file but process exists on a host return:
            "process running for this suite on HOSTNAME"
        Or None otherwise.

        """
        if not hosts:
            hosts = ["localhost"]
        prefix = "~"
        if user_name:
            prefix += user_name
        port_file = os.path.join(prefix, ".cylc", "ports", suite_name)
        if ("localhost" in hosts and
            os.path.exists(os.path.expanduser(port_file))):
            return port_file
        if user_name is None:
            user_name = pwd.getpwuid(os.getuid()).pw_name
        pgrep = ["pgrep", "-f", "-l", "-u", user_name,
                 "python.*cylc-(run|restart).*\\<" + suite_name + "\\>"]
        rc, out, err = self.popen.run(*pgrep)
        if rc == 0:
            for line in out.splitlines():
                if suite_name in line.split():
                    return "localhost:process=" + line
        host_proc_dict = {}
        opt_user = "-u `whoami`"
        if user_name:
            opt_user = "-u " + user_name
        for host in sorted(hosts):
            if host == "localhost":
                continue
            cmd = self.popen.get_cmd("ssh", host,
                                     "ls " + port_file +
                                     " || pgrep -f -l " + opt_user +
                                     " 'python.*cylc-(run|restart).*\\<" +
                                     suite_name + "\\>'")
            host_proc_dict[host] = self.popen.run_bg(*cmd)
        reason = None
        while host_proc_dict:
            for host, proc in host_proc_dict.items():
                rc = proc.poll()
                if rc is not None:
                    host_proc_dict.pop(host)
                    if rc == 0:
                        out, err = proc.communicate()
                        for line in out.splitlines():
                            if suite_name in line.split():
                                reason = host + ":" + line
            if host_proc_dict:
                sleep(0.1)
        return reason

    def job_logs_archive(self, suite_name, items):
        """Archive cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        cycles = []
        if "*" in items:
            stmt = "SELECT DISTINCT cycle FROM task_events"
            for row in self._db_exec(self.SUITE_DB, None, suite_name, stmt):
                cycles.append(row[0])
            self._db_close(self.SUITE_DB, None, suite_name)
        else:
            for item in items:
                cycle = self._parse_task_cycle_id(item)[0]
                if cycle:
                    cycles.append(cycle)
        self.job_logs_pull_remote(suite_name, cycles, prune_remote_mode=True)
        log_dir_rel = self.get_suite_dir_rel(suite_name, "log")
        log_dir = self.get_suite_dir(suite_name, "log")
        cwd = os.getcwd()
        self.fs_util.chdir(log_dir)
        try:
            stmt = ("UPDATE log_files SET path=?, path_in_tar=? " +
                    "WHERE cycle==? AND task==? AND submit_num==? AND key==?")
            for cycle in cycles:
                archive_file_name0 = "job-" + cycle + ".tar"
                archive_file_name = archive_file_name0 + ".gz"
                if os.path.exists(archive_file_name):
                    continue
                glob_ = self.TASK_ID_DELIM.join(["*", cycle, "*"])
                names = glob(os.path.join("job", glob_))
                if not names:
                    continue
                f_bsize = os.statvfs(".").f_bsize
                tar = tarfile.open(archive_file_name0, "w", bufsize=f_bsize)
                for name in names:
                    tar.add(name)
                tar.close()
                # N.B. Python's gzip is slow
                self.popen.run_simple("gzip", archive_file_name0)
                self.handle_event(FileSystemEvent(FileSystemEvent.CREATE,
                                                  archive_file_name))
                for name in sorted(names):
                    self.fs_util.delete(name)
                for name in names:
                    # cycle, task, submit_num, extension
                    c, t, s, e = self._parse_job_log_base_name(name)
                    key = e
                    if e in self.JOB_LOG_TAIL_KEYS:
                        key = self.JOB_LOG_TAIL_KEYS[e]
                    stmt_args = [os.path.join("log", archive_file_name),
                                 name, c, t, s, key]
                    self._db_exec(self.JOB_LOGS_DB, None, suite_name,
                                  stmt, stmt_args, commit=True)
        finally:
            try:
                self.fs_util.chdir(cwd)
            except OSError:
                pass
        self._db_close(self.JOB_LOGS_DB, None, suite_name)

    def job_logs_db_create(self, suite_name, close=False):
        """Create the job logs database."""
        if (None, suite_name) in self.daos[self.JOB_LOGS_DB]:
            return self.daos[self.JOB_LOGS_DB][(None, suite_name)]
        db_f_name = self.get_suite_dir(suite_name, self.JOB_LOGS_DB)
        dao = DAO(db_f_name)
        if os.access(db_f_name, os.R_OK | os.F_OK):
            return dao
        self.daos[self.JOB_LOGS_DB][(None, suite_name)] = dao
        dao.connect(is_new=True)
        stmt = ("CREATE TABLE log_files(" +
                "cycle TEXT, task TEXT, submit_num TEXT, key TEXT, " +
                "path TEXT, path_in_tar TEXT, mtime TEXT, size INTEGER, " +
                "PRIMARY KEY(cycle, task, submit_num, key))")
        dao.execute(stmt, commit=True)
        if close:
            dao.close()
        return dao

    def job_logs_pull_remote(self, suite_name, items, prune_remote_mode=False):
        """Pull and housekeep the job logs on remote task hosts.

        suite_name -- The name of a suite.
        items -- A list of relevant items.
        prune_remote_mode -- Remove remote job logs after pulling them.

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
            glob_auths_map = {}
            if "*" in items:
                auths = self.get_suite_jobs_auths(suite_name)
                if auths:
                    glob_auths_map["*"] = self.get_suite_jobs_auths(suite_name)
            else:
                for item in items:
                    cycle, name = self._parse_task_cycle_id(item)
                    if cycle is not None:
                        arch_f_name = "job-" + cycle + ".tar.gz"
                        if os.path.exists(arch_f_name):
                            continue
                    auths = self.get_suite_jobs_auths(suite_name, cycle, name)
                    if auths:
                        glob_names = []
                        for v in [name, cycle, None]:
                            if v is None:
                                glob_names.append("*")
                            else:
                                glob_names.append(v)
                        glob_ = self.TASK_ID_DELIM.join(glob_names)
                        glob_auths_map[glob_] = auths
            # FIXME: more efficient if auth is key?
            for glob_, auths in glob_auths_map.items():
                for auth in auths:
                    data = {"auth": auth,
                            "log_dir_rel": log_dir_rel,
                            "uuid": uuid,
                            "glob_": glob_}
                    cmd = self.popen.get_cmd(
                            "ssh", auth,
                            ("cd %(log_dir_rel)s && " +
                             "(! test -f %(uuid)s && ls %(glob_)s)") % data)
                    if self.popen.run(*cmd)[0]:
                        continue
                    try:
                        cmd = self.popen.get_cmd(
                                "rsync",
                                "%(auth)s:%(log_dir_rel)s/%(glob_)s" % data,
                                log_dir)
                        self.popen(*cmd)
                    except RosePopenError as e:
                        self.handle_event(e, level=Reporter.WARN)
                    if not prune_remote_mode:
                        continue
                    try:
                        cmd = self.popen.get_cmd(
                                "ssh", auth,
                                "cd %(log_dir_rel)s && rm -f %(glob_)s" % data)
                        self.popen(*cmd)
                    except RosePopenError as e:
                        self.handle_event(e, level=Reporter.WARN)
        finally:
            self.fs_util.delete(uuid_file_name)

        # Update job log DB
        dao = self.job_logs_db_create(suite_name)
        d = self.get_suite_dir(suite_name)
        stmt = ("REPLACE INTO log_files VALUES(?, ?, ?, ?, ?, ?, ?, ?)")
        for item in items:
            cycle, name = self._parse_task_cycle_id(item)
            if not cycle:
                cycle = "*"
            if not name:
                name = "*"
            logs_prefix = self.get_suite_dir(
                            suite_name,
                            "log/job/%s.%s." % (name, cycle))
            for f_name in glob(logs_prefix + "*"):
                if f_name.endswith(".status"):
                    continue
                stat = os.stat(f_name)
                rel_f_name = f_name[len(d) + 1:]
                # cycle, task, submit_num, extension
                c, t, s, e = self._parse_job_log_base_name(f_name)
                key = e
                if e in self.JOB_LOG_TAIL_KEYS:
                    key = self.JOB_LOG_TAIL_KEYS[e]
                stmt_args = [c, t, s, key, rel_f_name, "",
                             stat.st_mtime, stat.st_size]
                dao.execute(stmt, stmt_args)
        dao.commit()
        dao.close()

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
            self.handle_event(err, kind=Event.KIND_ERR)
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

    def validate(self, suite_name, strict_mode=False, debug_mode=False):
        """(Re-)register and validate a suite."""
        suite_dir = self.get_suite_dir(suite_name)
        rc, out, err = self.popen.run("cylc", "get-directory", suite_name)
        suite_dir_old = None
        if out:
            suite_dir_old = out.strip()
        suite_passphrase = os.path.join(suite_dir, "passphrase")
        self.clean_hook(suite_name)
        if suite_dir_old != suite_dir or not os.path.exists(suite_passphrase):
            self.popen.run_simple("cylc", "unregister", suite_name)
            suite_dir_old = None
        if suite_dir_old is None:
            self.popen.run_simple("cylc", "register", suite_name, suite_dir)
        passphrase_dir = os.path.join("~", ".cylc", suite_name)
        passphrase_dir = os.path.expanduser(passphrase_dir)
        self.fs_util.symlink(suite_dir, passphrase_dir)
        command = ["cylc", "validate", "-v"]
        if debug_mode:
            command.append("--debug")
        if strict_mode:
            command.append("--strict")
        command.append(suite_name)
        self.popen.run_simple(*command, stdout_level=Event.V)

    def _db_close(self, db_name, user_name, suite_name):
        key = (user_name, suite_name)
        if self.daos[db_name].get(key) is not None:
            self.daos[db_name][key].close()

    def _db_exec(self, db_name, user_name, suite_name, stmt, stmt_args=None,
                 commit=False):
        key = (user_name, suite_name)
        if key not in self.daos[db_name]:
            prefix = "~"
            if user_name:
                prefix += user_name
            db_f_name = os.path.expanduser(os.path.join(
                    prefix, self.get_suite_dir_rel(suite_name, db_name)))
            self.daos[db_name][key] = DAO(db_f_name)
        return self.daos[db_name][key].execute(stmt, stmt_args, commit)

    def _parse_job_log_base_name(self, f_name):
        """Return (cycle, task, submit_num, ext)."""
        b_names = os.path.basename(f_name).split(self.TASK_ID_DELIM, 3)
        task, cycle, submit_num = b_names[0:3]
        ext = ""
        if len(b_names) > 3:
            ext = b_names[3]
        return (cycle, task, submit_num, ext)

    def _parse_task_cycle_id(self, item):
        cycle, name = None, None
        if self.REC_CYCLE_TIME.match(item):
            cycle = item
        elif self.TASK_ID_DELIM in item:
            name, cycle = item.split(self.TASK_ID_DELIM, 1)
        else:
            name = item
        return (cycle, name)

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


class DAO(object):

    """Generic SQLite Data Access Object."""

    CONNECT_RETRY_DELAY = 0.1
    N_CONNECT_TRIES = 5

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
        for i in range(self.N_CONNECT_TRIES):
            try:
                self.conn = sqlite3.connect(self.db_f_name)
                self.cursor = self.conn.cursor()
            except sqlite3.OperationalError as e:
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
        for i in range(self.N_CONNECT_TRIES):
            if self.connect() is None:
                return []
            try:
                self.cursor.execute(stmt, stmt_args)
            except sqlite3.OperationalError as e:
                sleep(self.CONNECT_RETRY_DELAY)
                self.conn = None
                self.cursor = None
            except sqlite3.ProgrammingError as e:
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
        return ("%s: not a registered suite."
                 % self.args[0])
