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
from fnmatch import fnmatch
from glob import glob
import os
import pwd
import re
from rose.fs_util import FileSystemEvent
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter
from rose.suite_engine_proc import (
    SuiteEngineProcessor, SuiteScanResult,
    SuiteEngineGlobalConfCompatError, TaskProps)
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

    """Logic specific to the Cylc suite engine."""

    CYCLE_ORDERS = {"time_desc": " DESC", "time_asc": " ASC"}
    EVENTS = {"submission succeeded": "submit",
              "submission failed": "fail(submit)",
              "submitting now": "submit-init",
              "incrementing submit number": "submit-init",
              "started": "init",
              "succeeded": "success",
              "failed": "fail",
              "execution started": "init",
              "execution succeeded": "success",
              "execution failed": "fail",
              "signaled": "fail(%s)"}
    EVENT_TIME_INDICES = {
        "submit-init": 0, "init": 1, "success": 2, "fail": 2, "fail(%s)": 2}
    EVENT_RANKS = {"submit-init": 0, "submit": 1, "fail(submit)": 1, "init": 2,
                   "success": 3, "fail": 3, "fail(%s)": 4}
    JOB_LOGS_DB = "log/rose-job-logs.db"
    JOB_ORDERS_OLD = {
        "time_desc": "time DESC, submit_num DESC, name DESC, cycle DESC",
        "time_asc": "time ASC, submit_num ASC, name ASC, cycle ASC",
        "cycle_desc_name_asc": "cycle DESC, name ASC, submit_num DESC",
        "cycle_desc_name_desc": "cycle DESC, name DESC, submit_num DESC",
        "cycle_asc_name_asc": "cycle ASC, name ASC, submit_num DESC",
        "cycle_asc_name_desc": "cycle ASC, name DESC, submit_num DESC",
        "name_asc_cycle_asc": "name ASC, cycle ASC, submit_num DESC",
        "name_desc_cycle_asc": "name DESC, cycle ASC, submit_num DESC",
        "name_asc_cycle_desc": "name ASC, cycle DESC, submit_num DESC",
        "name_desc_cycle_desc": "name DESC, cycle DESC, submit_num DESC"}
    JOB_ORDERS = dict(JOB_ORDERS_OLD)
    JOB_ORDERS.update({
        "time_submit_desc": (
            "time_submit DESC, submit_num DESC, name DESC, cycle DESC"),
        "time_submit_asc": (
            "time_submit ASC, submit_num DESC, name DESC, cycle DESC"),
        "time_run_desc": (
            "time_run DESC, submit_num DESC, name DESC, cycle DESC"),
        "time_run_asc": (
            "time_run ASC, submit_num DESC, name DESC, cycle DESC"),
        "time_run_exit_desc": (
            "time_run_exit DESC, submit_num DESC, name DESC, cycle DESC"),
        "time_run_exit_asc": (
            "time_run_exit ASC, submit_num DESC, name DESC, cycle DESC"),
        "duration_queue_desc": (
            "(CAST(strftime('%s', time_run) AS NUMERIC) -" +
            " CAST(strftime('%s', time_submit) AS NUMERIC)) DESC, " +
            "submit_num DESC, name DESC, cycle DESC"),
        "duration_queue_asc": (
            "(CAST(strftime('%s', time_run) AS NUMERIC) -" +
            " CAST(strftime('%s', time_submit) AS NUMERIC)) ASC, " +
            "submit_num DESC, name DESC, cycle DESC"),
        "duration_run_desc": (
            "(CAST(strftime('%s', time_run_exit) AS NUMERIC) -" +
            " CAST(strftime('%s', time_run) AS NUMERIC)) DESC, " +
            "submit_num DESC, name DESC, cycle DESC"),
        "duration_run_asc": (
            "(CAST(strftime('%s', time_run_exit) AS NUMERIC) -" +
            " CAST(strftime('%s', time_run) AS NUMERIC)) ASC, " +
            "submit_num DESC, name DESC, cycle DESC"),
        "duration_queue_run_desc": (
            "(CAST(strftime('%s', time_run_exit) AS NUMERIC) -" +
            " CAST(strftime('%s', time_submit) AS NUMERIC)) DESC, " +
            "submit_num DESC, name DESC, cycle DESC"),
        "duration_queue_run_asc": (
            "(CAST(strftime('%s', time_run_exit) AS NUMERIC) -" +
            " CAST(strftime('%s', time_submit) AS NUMERIC)) ASC, " +
            "submit_num DESC, name DESC, cycle DESC"),
    })
    PGREP_CYLC_RUN = r"python.*cylc-(run|restart)( | .+ )%s( |$)"
    REASON_KEY_PROC = "process"
    REASON_KEY_FILE = "port-file"
    REC_BUNCH_LOG = re.compile(r"\A(bunch\.)(.+)(\.out|\.err)\Z")
    REC_CYCLE_TIME = re.compile(
        r"\A[\+\-]?\d+(?:W\d+)?(?:T\d+(?:Z|[+-]\d+)?)?\Z")  # Good enough?
    REC_SEQ_LOG = re.compile(r"\A(.*\.)(\d+)(\.html)?\Z")
    REC_SIGNALLED = re.compile(r"Task\sjob\sscript\sreceived\ssignal\s(\S+)")
    SCHEME = "cylc"
    STATUSES = {"active": ["ready", "queued", "submitting", "submitted",
                           "submit-retrying", "running", "retrying"],
                "fail": ["submission failed", "failed"],
                "success": ["expired", "succeeded"]}
    SUITE_CONF = "suite.rc"
    SUITE_DB = "cylc-suite.db"
    SUITE_DIR_REL_ROOT = "cylc-run"
    TASK_ID_DELIM = "."
    TIMEOUT = 60  # seconds

    def __init__(self, *args, **kwargs):
        SuiteEngineProcessor.__init__(self, *args, **kwargs)
        self.daos = {self.SUITE_DB: {}, self.JOB_LOGS_DB: {}}
        # N.B. Should be considered a constant after initialisation
        self.state_of = {}
        for status, names in self.STATUSES.items():
            for name in names:
                self.state_of[name] = status
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
        """Run "cylc refresh --unregister" (at end of "rose suite-clean")."""
        self.popen.run("cylc", "refresh", "--unregister")
        passphrase_dir_root = os.path.expanduser(os.path.join("~", ".cylc"))
        for name in os.listdir(passphrase_dir_root):
            path = os.path.join(passphrase_dir_root, name)
            if os.path.islink(path) and not os.path.exists(path):
                self.fs_util.delete(path)

    def cmp_suite_conf(self, suite_name, strict_mode=False, debug_mode=False):
        """Parse and compare current "suite.rc" with that in the previous run.

        (Re-)register and validate the "suite.rc" file.
        Raise RosePopenError on failure.
        Return True if "suite.rc.processed" is unmodified c.f. previous run.
        Return False otherwise.

        """
        suite_dir = self.get_suite_dir(suite_name)
        out = self.popen.run("cylc", "get-directory", suite_name)[1]
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
        suite_rc_processed = os.path.join(suite_dir, "suite.rc.processed")
        old_suite_rc_processed = None
        if os.path.exists(suite_rc_processed):
            f_desc, old_suite_rc_processed = mkstemp(
                dir=suite_dir,
                prefix="suite.rc.processed.")
            os.close(f_desc)
            os.rename(suite_rc_processed, old_suite_rc_processed)
        try:
            self.popen.run_simple(*command, stdout_level=Event.V)
            return (old_suite_rc_processed and
                    filecmp.cmp(old_suite_rc_processed, suite_rc_processed))
        finally:
            if old_suite_rc_processed:
                os.unlink(old_suite_rc_processed)

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

    def get_suite_broadcast_states(self, user_name, suite_name):
        """Return broadcast states of a suite.

        [[point, name, key, value], ...]

        """
        # Check if "broadcast_states" table is available or not
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT name FROM sqlite_master WHERE name==?",
                ["broadcast_states"]):
            break
        else:
            return

        broadcast_states = []
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT point,namespace,key,value FROM broadcast_states" +
                " ORDER BY point ASC, namespace ASC, key ASC"):
            point, namespace, key, value = row
            broadcast_states.append([point, namespace, key, value])
        return broadcast_states

    def get_suite_broadcast_events(self, user_name, suite_name):
        """Return broadcast events of a suite.

        [[time, change, point, name, key, value], ...]

        """
        # Check if "broadcast_events" table is available or not
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT name FROM sqlite_master WHERE name==?",
                ["broadcast_events"]):
            break
        else:
            return {}

        broadcast_events = []
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT time,change,point,namespace,key,value" +
                " FROM broadcast_events" +
                " ORDER BY time DESC, point DESC, namespace DESC, key DESC"):
            time, change, point, namespace, key, value = row
            broadcast_events.append(
                (time, change, point, namespace, key, value))
        return broadcast_events

    def get_suite_dir_rel(self, suite_name, *paths):
        """Return the relative path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        return os.path.join(self.SUITE_DIR_REL_ROOT, suite_name, *paths)

    def get_suite_job_events(
            self, user_name, suite_name, cycles, tasks, no_statuses, order,
            limit, offset):
        """Return suite task job events.

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
        # Check if "task_jobs" table is available or not
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT name FROM sqlite_master WHERE name==?", ["task_jobs"]):
            break
        else:
            return self._get_suite_job_events_old(
                user_name, suite_name, cycles, tasks, no_statuses, order,
                limit, offset)

        # Build the WHERE expression to filter by cycles, tasks, statuses
        where_exprs = []
        where_args = []
        if cycles:
            cycle_where_exprs = []
            for cycle in cycles:
                if cycle.startswith("before "):
                    where_args.append(cycle.split(None, 1)[-1])
                    cycle_where_exprs.append("cycle <= ?")
                elif cycle.startswith("after "):
                    where_args.append(cycle.split(None, 1)[-1])
                    cycle_where_exprs.append("cycle >= ?")
                else:
                    where_args.append(cycle)
                    cycle_where_exprs.append("cycle GLOB ?")
            where_exprs.append(" OR ".join(cycle_where_exprs))
        if tasks:
            where_exprs.append(" OR ".join(["name GLOB ?"] * len(tasks)))
            where_args += tasks
        if no_statuses:
            for no_status in no_statuses:
                statuses = self.STATUSES.get(no_status, [])
                where_exprs.append(
                    " AND ".join(["status != ?"] * len(statuses)))
                where_args += statuses
        if where_exprs:
            where_expr = " WHERE (" + ") AND (".join(where_exprs) + ")"
        else:
            where_expr = ""

        # Get number of entries
        of_n_entries = 0
        stmt = ("SELECT COUNT(*)" +
                " FROM task_jobs JOIN task_states USING (name, cycle)" +
                where_expr)
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name, stmt, where_args):
            of_n_entries = row[0]
            break
        else:
            self._db_close(self.SUITE_DB, user_name, suite_name)
            return ([], 0)

        # Get entries
        entries = []
        entry_of = {}
        stmt = ("SELECT" +
                " task_states.time_updated AS time," +
                " cycle, name," +
                " task_jobs.submit_num AS submit_num," +
                " task_states.submit_num AS submit_num_max," +
                " time_submit, submit_status," +
                " time_run, time_run_exit, run_signal, run_status," +
                " user_at_host, batch_sys_name, batch_sys_job_id" +
                " FROM task_jobs JOIN task_states USING (cycle, name)" +
                where_expr +
                " ORDER BY " +
                self.JOB_ORDERS.get(order, self.JOB_ORDERS["time_desc"]))
        limit_args = []
        if limit:
            stmt += " LIMIT ? OFFSET ?"
            limit_args = [limit, offset]
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name, stmt,
                where_args + limit_args):
            (
                cycle, name, submit_num, submit_num_max,
                time_submit, submit_status,
                time_run, time_run_exit, run_signal, run_status,
                user_at_host, batch_sys_name, batch_sys_job_id
            ) = row[1:]
            entry = {
                "cycle": cycle,
                "name": name,
                "submit_num": submit_num,
                "submit_num_max": submit_num_max,
                "events": [time_submit, time_run, time_run_exit],
                "status": None,
                "host": user_at_host,
                "submit_method": batch_sys_name,
                "submit_method_id": batch_sys_job_id,
                "logs": {},
                "seq_logs_indexes": {}}
            if run_status and run_signal:
                entry["status"] = "fail(%s)" % (run_signal)
            elif run_status:
                entry["status"] = "fail"
            elif run_status == 0:
                entry["status"] = "success"
            elif submit_status:
                entry["status"] = "fail(submit)"
            elif submit_status == 0 and time_run:
                entry["status"] = "init"
            elif submit_status == 0:
                entry["status"] = "submit"
            else:
                entry["status"] = "submit-init"
            entries.append(entry)
            entry_of[(cycle, name, submit_num)] = entry
        self._db_close(self.SUITE_DB, user_name, suite_name)
        if not entries:
            return (entries, of_n_entries)

        # Job logs DB
        stmt = (
            "SELECT cycle, name, submit_num, filename, location, mtime, size" +
            " FROM task_job_logs")

        prefix = "~"
        if user_name:
            prefix += user_name
        user_suite_dir = os.path.expanduser(os.path.join(
            prefix, self.get_suite_dir_rel(suite_name)))
        try:
            current_cycles = os.listdir(
                os.path.join(user_suite_dir, "log", "job"))
        except OSError:
            current_cycles = []
        targzip_cycles = []
        for name in glob(os.path.join(user_suite_dir, "log", "job-*.tar.gz")):
            targzip_cycles.append(os.path.basename(name)[4:-7])
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt):
            cycle, name, submit_num, filename, location, mtime, size = row
            try:
                entry = entry_of[(cycle, name, int(submit_num))]
            except KeyError:
                continue
            if cycle in current_cycles:
                path = os.path.join("log", "job", location)
                path_in_tar = None
                exists = True
            elif cycle in targzip_cycles:
                path = os.path.join("log", "job-%s.tar.gz" % (cycle))
                path_in_tar = os.path.join("job", location)
                exists = True
            else:
                path = os.path.join("log", "job", location)
                path_in_tar = None
                exists = False
            entry["logs"][filename] = {
                "path": path,
                "path_in_tar": path_in_tar,
                "mtime": mtime,
                "size": size,
                "exists": exists,
                "seq_key": None}
            for seq_log_matcher in self.REC_SEQ_LOG, self.REC_BUNCH_LOG:
                seq_log_match = seq_log_matcher.match(filename)
                if seq_log_match:
                    head, index_str, tail = seq_log_match.groups()
                    if not tail:
                        tail = ""
                    seq_key = head + "*" + tail
                    entry["logs"][filename]["seq_key"] = seq_key
                    if seq_key not in entry["seq_logs_indexes"]:
                        entry["seq_logs_indexes"][seq_key] = {}
                    entry["seq_logs_indexes"][seq_key][index_str] = filename
                    break
        self._db_close(self.SUITE_DB, user_name, suite_name)

        for entry in entries:
            # job.out and job.err are expected for completed jobs
            for filename in ["job.out", "job.err"]:
                if (filename in entry["logs"] or
                        entry["status"] not in ["success", "fail"]):
                    continue
                path = os.path.join(
                    "log", "job",
                    "%(cycle)s/%(name)s/%(submit_num)02d" % entry,
                    filename)
                mtime = "?"
                size = "?"
                if entry["cycle"] in current_cycles:
                    try:
                        size, _, mtime = os.stat(
                            os.path.join(user_suite_dir, path))[6:9]
                    except (IndexError, OSError):
                        continue
                    path_in_tar = None
                    exists = True
                elif entry["cycle"] in targzip_cycles:
                    path_in_tar = path
                    path = os.path.join("log", "job-%(cycle)s.tar.gz" % entry)
                    exists = True
                else:
                    path_in_tar = None
                    exists = False
                entry["logs"][filename] = {
                    "path": path,
                    "path_in_tar": path_in_tar,
                    "mtime": mtime,
                    "size": size,
                    "exists": exists,
                    "seq_key": None}
            # Sequential logs
            for seq_key, indexes in entry["seq_logs_indexes"].items():
                if len(indexes) <= 1:
                    entry["seq_logs_indexes"].pop(seq_key)
            for filename, log_dict in entry["logs"].items():
                if log_dict["seq_key"] not in entry["seq_logs_indexes"]:
                    log_dict["seq_key"] = None

        return (entries, of_n_entries)

    def _get_suite_job_events_old(
            self, user_name, suite_name, cycles, tasks, no_statuses, order,
            limit, offset):
        """The "get_suite_job_events" method for older cylc versions."""
        # Build WHERE expression to select by cycles and/or task names
        where = ""
        stmt_args = []
        if cycles:
            where_fragments = []
            for cycle in cycles:
                if cycle.startswith("before "):
                    stmt_args.append(cycle.split(None, 1)[-1])
                    where_fragments.append("cycle <= ?")
                elif cycle.startswith("after "):
                    stmt_args.append(cycle.split(None, 1)[-1])
                    where_fragments.append("cycle >= ?")
                else:
                    stmt_args.append(cycle)
                    where_fragments.append("cycle GLOB ?")
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
                " WHERE event==? OR event==?")
        if where:
            stmt += " " + where
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name, stmt,
                ["submitting now", "incrementing submit number"] + stmt_args):
            of_n_entries = row[0]
            break
        if not of_n_entries:
            return ([], 0)
        # Execute query to get entries
        entries = []
        stmt = (
            "SELECT" +
            " cycle, name, task_events.submit_num AS submit_num," +
            " group_concat(time), group_concat(event)," +
            " group_concat(message) " +
            " FROM" +
            " task_events JOIN task_states USING (cycle,name)" +
            " WHERE" +
            " (event==? OR event==? OR event==? OR" +
            "  event==? OR event==? OR event==? OR event==?)" +
            where +
            " GROUP BY cycle, name, task_events.submit_num" +
            " ORDER BY " +
            self.JOB_ORDERS_OLD.get(order, self.JOB_ORDERS_OLD["time_desc"]))
        stmt_args_head = [
            "submitting now", "incrementing submit number",
            "submission failed", "started", "succeeded", "failed", "signaled"]
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
            event_rank = -1
            for event, time_ in zip(events, times):
                my_event = self.EVENTS.get(event)
                if self.EVENT_TIME_INDICES.get(my_event) is not None:
                    entry["events"][self.EVENT_TIME_INDICES[my_event]] = time_
                if (self.EVENT_RANKS.get(my_event) is not None and
                        self.EVENT_RANKS[my_event] > event_rank):
                    entry["status"] = my_event
                    event_rank = self.EVENT_RANKS[my_event]
                    if my_event == "fail(%s)":
                        match = self.REC_SIGNALLED.search(messages_str)
                        if match:
                            entry["status"] = "fail(%s)" % match.group(1)
                        else:
                            entry["status"] = "fail(SIGNAL)"

        other_info_of = {}
        for entry in entries:
            cycle = entry["cycle"]
            name = entry["name"]
            if (cycle, name) not in other_info_of:
                stmt = ("SELECT" +
                        " submit_num,host,submit_method,submit_method_id" +
                        " FROM task_states" +
                        " WHERE cycle==? AND name==?")
                for row in self._db_exec(self.SUITE_DB, user_name, suite_name,
                                         stmt, [cycle, name]):
                    other_info_of[(cycle, name)] = list(row)
                    break
            entry["submit_num_max"] = other_info_of[(cycle, name)][0]
            if entry["submit_num"] == entry["submit_num_max"]:
                entry["host"] = other_info_of[(cycle, name)][1]
                entry["submit_method"] = other_info_of[(cycle, name)][2]
                entry["submit_method_id"] = other_info_of[(cycle, name)][3]

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
                for seq_log_match in [self.REC_SEQ_LOG.match(key),
                                      self.REC_BUNCH_LOG.match(key)]:
                    if seq_log_match:
                        head, index_str, tail = seq_log_match.groups()
                        if not tail:
                            tail = ""
                        seq_key = head + "*" + tail
                        entry["logs"][key]["seq_key"] = seq_key
                        if seq_key not in entry["seq_logs_indexes"]:
                            entry["seq_logs_indexes"][seq_key] = {}
                        entry["seq_logs_indexes"][seq_key][index_str] = key

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
        dir_ = os.path.expanduser(os.path.join(prefix, d_rel))
        for key in ["cylc-suite-env",
                    "log/suite/err", "log/suite/log", "log/suite/out",
                    "suite.rc", "suite.rc.processed"]:
            f_name = os.path.join(dir_, key)
            if os.path.isfile(f_name):
                f_stat = os.stat(f_name)
                logs_info[key] = {"path": key,
                                  "mtime": f_stat.st_mtime,
                                  "size": f_stat.st_size}
        return ("cylc", logs_info)

    def get_suite_cycles_summary(
            self, user_name, suite_name, order, limit, offset):
        """Return a the state summary (of each cycle) of a user's suite.

        user -- A string containing a valid user ID
        suite -- A string containing a valid suite ID
        limit -- Limit number of returned entries
        offset -- Offset entry number

        Return (entries, of_n_entries), where entries is a data structure that
        looks like:
            [   {   "cycle": cycle,
                    "n_states": {
                        "active": N, "success": M, "fail": L, "job_fails": K,
                    },
                    "max_time_updated": T2,
                },
                # ...
            ]
        where:
        * cycle is a date-time cycle label
        * N, M, L, K are the numbers of tasks in given states
        * T2 is the time when last update time of (a task in) the cycle

        and of_n_entries is the total number of entries.

        """
        of_n_entries = 0
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT COUNT(DISTINCT cycle) FROM task_states"):
            of_n_entries = row[0]
            break
        if not of_n_entries:
            return ([], 0)

        # FIXME: Not strictly correct, if cycle is in basic date-only format
        integer_mode = False
        stmt = "SELECT cycle FROM task_states LIMIT 1"
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt):
            integer_mode = row[0].isdigit()
            break

        states_stmt = {}
        for key, names in self.STATUSES.items():
            states_stmt[key] = " OR ".join(
                ["status=='%s'" % (name) for name in names])
        stmt = (
            "SELECT" +
            " cycle," +
            " max(time_updated)," +
            " sum(" + states_stmt["active"] + ") AS n_active," +
            " sum(" + states_stmt["success"] + ") AS n_success,"
            " sum(" + states_stmt["fail"] + ") AS n_fail"
            " FROM task_states" +
            " GROUP BY cycle")
        if integer_mode:
            stmt += " ORDER BY cast(cycle as number)"
        else:
            stmt += " ORDER BY cycle"
        stmt += self.CYCLE_ORDERS.get(order, self.CYCLE_ORDERS["time_desc"])
        stmt_args = []
        if limit:
            stmt += " LIMIT ? OFFSET ?"
            stmt_args += [limit, offset]
        entry_of = {}
        entries = []
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name, stmt, stmt_args):
            cycle, max_time_updated, n_active, n_success, n_fail = row
            entry_of[cycle] = {
                "cycle": cycle,
                "max_time_updated": max_time_updated,
                "n_states": {
                    "active": n_active,
                    "success": n_success,
                    "fail": n_fail,
                    "job_fails": 0,
                },
            }
            entries.append(entry_of[cycle])

        # Check if "task_jobs" table is available or not
        can_use_task_jobs_table = False
        for row in self._db_exec(
                self.SUITE_DB, user_name, suite_name,
                "SELECT name FROM sqlite_master WHERE name==?", ["task_jobs"]):
            can_use_task_jobs_table = True
            break

        # Note: A single query with a JOIN is probably a more elegant solution.
        # However, timing tests suggest that it is cheaper with 2 queries.
        # This 2nd query may return more results than is necessary, but should
        # be a very cheap query as it does not have to do a lot of work.
        if can_use_task_jobs_table:
            stmt = (
                "SELECT cycle," +
                " sum(submit_status==1 OR run_status==1) AS n_job_fail" +
                " FROM task_jobs GROUP BY cycle")
        else:
            fail_events_stmt = " OR ".join(
                ["event=='%s'" % (name) for name in self.STATUSES["fail"]])
            stmt = (
                "SELECT cycle," +
                " sum(" + fail_events_stmt + ") AS n_job_fail" +
                " FROM task_events GROUP BY cycle")
        for cycle, n_job_fail in self._db_exec(
                self.SUITE_DB, user_name, suite_name, stmt):
            try:
                entry_of[cycle]["n_states"]["job_fails"] = n_job_fail
            except KeyError:
                pass

        return entries, of_n_entries

    def get_suite_state_summary(self, user_name, suite_name):
        """Return a the state summary of a user's suite.

        Return {"last_activity_time": s, "is_running": b, "is_failed": b}
        where:
        * last_activity_time is a string in %Y-%m-%dT%H:%M:%S format,
          the time of the latest activity in the suite
        * is_running is a boolean to indicate if the suite is running
        * is_failed: a boolean to indicate if any tasks (submit) failed
        * server: host:port of server, if available

        """
        ret = {
            "last_activity_time": None,
            "is_running": False,
            "is_failed": False,
            "server": None}
        dao = self._db_init(self.SUITE_DB, user_name, suite_name)
        if not os.access(dao.db_f_name, os.F_OK | os.R_OK):
            return ret
        stmt = "SELECT time FROM task_events ORDER BY time DESC LIMIT 1"
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt):
            ret["last_activity_time"] = row[0]
            break

        port_file_path = os.path.expanduser(
            os.path.join("~" + user_name, ".cylc", "ports", suite_name))
        try:
            port_str, host = open(port_file_path).read().splitlines()
        except (IOError, ValueError):
            ret["is_running"] = bool(
                self.is_suite_running(user_name, suite_name))
        else:
            ret["is_running"] = True
            ret["server"] = host.split(".", 1)[0] + ":" + port_str

        stmt = "SELECT status FROM task_states WHERE status GLOB ? LIMIT 1"
        stmt_args = ["*failed"]
        for row in self._db_exec(self.SUITE_DB, user_name, suite_name, stmt,
                                 stmt_args):
            ret["is_failed"] = True
            break

        return ret

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

        suite_name = os.environ["CYLC_SUITE_REG_NAME"]
        suite_dir_rel = self.get_suite_dir_rel(suite_name)
        suite_dir = self.get_suite_dir(suite_name)
        task_id = os.environ["CYLC_TASK_ID"]
        task_name = os.environ["CYLC_TASK_NAME"]
        task_cycle_time = os.environ["CYLC_TASK_CYCLE_TIME"]
        cycling_mode = os.environ.get("CYLC_CYCLING_MODE", "gregorian")
        if task_cycle_time == "1" and not cycling_mode == "integer":
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
                         task_log_dir=os.path.dirname(task_log_root),
                         task_log_root=task_log_root,
                         task_is_cold_start=task_is_cold_start,
                         cycling_mode=cycling_mode)

    def get_version(self):
        """Return Cylc's version."""
        return self.popen("cylc", "--version")[0].strip()

    def is_conf(self, path):
        """Return "cylc-suite-rc" if path is a Cylc suite.rc file."""
        if fnmatch(os.path.basename(path), "suite*.rc*"):
            return "cylc-suite-rc"

    def is_suite_registered(self, suite_name):
        """See if a suite is registered
            Return True directory for a suite if it is registered
            Return False otherwise
        """
        return self.popen.run("cylc", "get-directory", suite_name)[0] == 0

    def is_suite_running(self, user_name, suite_name, hosts=None):
        """Return the reasons if it looks like suite is running.

        return [
            {
                "host": host,
                "reason_key": reason_key,
                "reason_value": reason_value
            },
            # ...
        ]

        If not running, return an empty list.

        """
        if not hosts:
            hosts = ["localhost"]

        # localhost pgrep
        if user_name is None:
            user_name = pwd.getpwuid(os.getuid()).pw_name
        pgrep = ["pgrep", "-f", "-l", "-u", user_name,
                 self.PGREP_CYLC_RUN % (suite_name)]
        ret_code, out, _ = self.popen.run(*pgrep)
        if ret_code == 0:
            proc_reasons = []
            for line in out.splitlines():
                proc_reasons.append({
                    "host": "localhost",
                    "reason_key": self.REASON_KEY_PROC,
                    "reason_value": line})
            if proc_reasons:
                return proc_reasons

        # remote hosts pgrep and ls port file
        host_proc_dict = {}
        prefix = "~"
        if user_name:
            prefix += user_name
        port_file = os.path.join(prefix, ".cylc", "ports", suite_name)
        opt_user = "-u `whoami`"
        if user_name:
            opt_user = "-u " + user_name
        for host in sorted(hosts):
            if self.host_selector.is_local_host(host):
                continue
            r_cmd_tmpl = (
                r"pgrep -f -l %s '" + self.PGREP_CYLC_RUN + r"' || ls '%s'")
            r_cmd = r_cmd_tmpl % (opt_user, suite_name, port_file)
            cmd = self.popen.get_cmd("ssh", host, r_cmd)
            host_proc_dict[host] = self.popen.run_bg(*cmd)
        proc_reasons = []
        file_reasons = []
        while host_proc_dict:
            for host, proc in host_proc_dict.items():
                ret_code = proc.poll()
                if ret_code is None:
                    continue
                host_proc_dict.pop(host)
                if ret_code != 0:
                    continue
                out = proc.communicate()[0]
                for line in out.splitlines():
                    cols = line.split()
                    if cols[0].isdigit():
                        proc_reasons.append({
                            "host": host,
                            "reason_key": self.REASON_KEY_PROC,
                            "reason_value": line})
                    else:
                        file_reasons.append({
                            "host": host,
                            "reason_key": self.REASON_KEY_FILE,
                            "reason_value": line})
            if host_proc_dict:
                sleep(0.1)

        if proc_reasons:
            return proc_reasons

        # localhost ls port file
        # N.B. This logic means that on shared file systems, only the localhost
        #      port file is reported.
        if ("localhost" in hosts and
                os.path.exists(os.path.expanduser(port_file))):
            return [{"host": "localhost",
                     "reason_key": self.REASON_KEY_FILE,
                     "reason_value": port_file}]

        return file_reasons

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
        cwd = os.getcwd()
        self.fs_util.chdir(self.get_suite_dir(suite_name))
        try:
            stmt = ("UPDATE log_files SET path=?, path_in_tar=? " +
                    "WHERE cycle==? AND task==? AND submit_num==? AND key==?")
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
                    cycle, task, s_n, ext = self.parse_job_log_rel_path(name)
                    if s_n == "NN" or ext == "job.status":
                        continue
                    tar.add(name, name.replace("log/", "", 1))
                tar.close()
                # N.B. Python's gzip is slow
                self.popen.run_simple("gzip", "-f", archive_file_name0)
                self.handle_event(FileSystemEvent(FileSystemEvent.CREATE,
                                                  archive_file_name))
                self.fs_util.delete(os.path.join("log", "job", cycle))
                for name in names:
                    # cycle, task, submit_num, extension
                    cycle, task, s_n, ext = self.parse_job_log_rel_path(name)
                    if s_n == "NN" or ext == "job.status":
                        continue
                    stmt_args = [
                        os.path.join(archive_file_name),
                        name.replace("log/", "", 1),
                        cycle,
                        task,
                        int(s_n),
                        ext]
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

        # Update job log DB
        dao = self.job_logs_db_create(suite_name)
        dir_ = self.get_suite_dir(suite_name)
        stmt = ("REPLACE INTO log_files VALUES(?, ?, ?, ?, ?, ?, ?, ?)")
        for item in items:
            cycle, name = self._parse_task_cycle_id(item)
            if not cycle:
                cycle = "*"
            if not name:
                name = "*"
            logs_prefix = self.get_suite_dir(
                suite_name,
                "log/job/%(cycle)s/%(name)s/*/*" % {
                    "cycle": cycle, "name": name})
            for f_name in glob(logs_prefix + "*"):
                if f_name.endswith("/job.status"):
                    continue
                stat = os.stat(f_name)
                rel_f_name = f_name[len(dir_) + 1:]
                # cycle, task, submit_num, extension
                cycle, task, s_n, ext = self.parse_job_log_rel_path(rel_f_name)
                if s_n == "NN":
                    continue
                stmt_args = [cycle, task, int(s_n), ext, rel_f_name, "",
                             stat.st_mtime, stat.st_size]
                dao.execute(stmt, stmt_args)
        dao.commit()
        dao.close()

    def job_logs_remove_on_server(self, suite_name, items):
        """Remove cycle job logs.

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

    def ping(self, suite_name, hosts=None, timeout=10):
        """Return a list of host names where suite_name is running."""
        host_proc_dict = {}
        for host in sorted(self.get_suite_hosts(suite_name, hosts)):
            proc = self.popen.run_bg(
                "cylc", "ping", "--host=" + host, suite_name,
                "--pyro-timeout=" + str(timeout))
            host_proc_dict[host] = proc
        ping_ok_hosts = []
        while host_proc_dict:
            for host, proc in host_proc_dict.items():
                ret_code = proc.poll()
                if ret_code is not None:
                    host_proc_dict.pop(host)
                    if ret_code == 0:
                        ping_ok_hosts.append(host)
            if host_proc_dict:
                sleep(0.1)
        return ping_ok_hosts

    @classmethod
    def process_suite_hook_args(cls, *args, **_):
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
        procs = {}
        procs[(_PORT_SCAN, None, tuple(cmd))] = self.popen.run_bg(*cmd)
        for host in sorted(hosts):
            sh_cmd = "whoami && cd ~/.cylc/ports/ && ls || true"
            if self.host_selector.is_local_host(host):
                cmd = ["bash", "-c", sh_cmd]
            else:
                cmd = self.popen.get_cmd("ssh", "-n", host, sh_cmd)
            procs[(_PORT_FILE, host, tuple(cmd))] = self.popen.run_bg(
                *cmd, preexec_fn=os.setpgrp)
        results = {}
        exceptions = []
        end_time = time() + timeout
        while procs and time() < end_time:
            for keys, proc in procs.items():
                ret_code = proc.poll()
                if ret_code is None:
                    continue
                procs.pop(keys)
                key, host, cmd = keys
                if ret_code == 0:
                    if key == _PORT_SCAN:
                        for line in proc.communicate()[0].splitlines():
                            try:
                                # Releases after cylc 6.5.0
                                name, location = line.split()
                                host = location.split("@")[1].split(":")[0]
                                results[(name, host, key)] = SuiteScanResult(
                                    name, location)
                            except ValueError:
                                # Backward compat cylc 6.5.0 or before
                                name, user, host, port = line.split()
                                results[(name, host, key)] = SuiteScanResult(
                                    name, "%s@%s:%s" % (user, host, port))
                            # N.B. Trust port-scan over port-file
                            for i_host in hosts:
                                try:
                                    results.pop((name, i_host, _PORT_FILE))
                                except KeyError:
                                    pass
                    else:  # if key == _PORT_FILE:
                        lines = proc.communicate()[0].splitlines()
                        user = lines.pop(0)
                        for name in lines:
                            # N.B. Trust port-scan over port-file
                            if (name, host, _PORT_SCAN) in results:
                                continue
                            results[(name, host, key)] = SuiteScanResult(
                                name, "%s@%s:%s" % (
                                    user, host, "~/.cylc/ports/" + name))
                else:
                    out, err = proc.communicate()
                    exceptions.append(RosePopenError(cmd, ret_code, out, err))
            if procs:
                sleep(0.1)
        # Timed out, kill remaining processes
        for key, proc in procs.items():
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            else:
                ret_code = proc.wait()
                out, err = proc.communicate()
                exceptions.append(RosePopenError(keys[2], ret_code, out, err))
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

    def _db_close(self, db_name, user_name, suite_name):
        """Close a named database connection."""
        key = (user_name, suite_name)
        if self.daos[db_name].get(key) is not None:
            self.daos[db_name][key].close()

    def _db_exec(self, db_name, user_name, suite_name, stmt, stmt_args=None,
                 commit=False):
        """Execute a query on a named database connection."""
        dao = self._db_init(db_name, user_name, suite_name)
        return dao.execute(stmt, stmt_args, commit)

    def _db_init(self, db_name, user_name, suite_name):
        """Initialise a named database connection."""
        key = (user_name, suite_name)
        if key not in self.daos[db_name]:
            prefix = "~"
            if user_name:
                prefix += user_name
            db_f_name = os.path.expanduser(os.path.join(
                prefix, self.get_suite_dir_rel(suite_name, db_name)))
            self.daos[db_name][key] = DAO(db_f_name)
        return self.daos[db_name][key]

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
        for _ in range(self.N_CONNECT_TRIES):
            try:
                self.conn = sqlite3.connect(self.db_f_name)
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
