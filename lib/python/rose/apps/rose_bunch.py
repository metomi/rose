# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
"""Builtin application: rose_bunch: run multiple commands in parallel."""


import os
import shlex
import sqlite3
from time import sleep

from rose.app_run import (
    BuiltinApp,
    ConfigValueError,
    CompulsoryConfigValueError)
from rose.popen import RosePopenError
import rose.job_runner
from rose.reporter import Event


class AbortEvent(Event):
    """An event raised when a task failure will stop further task running"""

    LEVEL = Event.V
    KIND = Event.KIND_ERR

    def __str__(self):
        return "Closing task pool, no further commands will be run."


class LaunchEvent(Event):
    """An event raised when adding a command to the task pool."""

    KIND = Event.KIND_OUT

    def __str__(self):
        name, cmd = self.args
        return "%s: added to pool\n\t%s" % (name, cmd)


class SucceededEvent(Event):
    """An event used to report success of a task in the pool."""

    LEVEL = Event.V
    KIND = Event.KIND_OUT

    def __str__(self):
        name = self.args
        return " %s " % (name)


class PreviousSuccessEvent(Event):
    """Event raised when a command is not run in incremental mode"""

    LEVEL = Event.V
    KIND = Event.KIND_OUT

    def __str__(self):
        name = self.args
        return " %s" % (name)


class SummaryEvent(Event):
    """Event for reporting bunch counts at end of job"""

    KIND = Event.KIND_OUT

    def __str__(self):
        n_ok, n_fail, n_skip, n_notconsidered = self.args
        total = n_ok + n_fail + n_skip + n_notconsidered
        msg_template = ("BUNCH TASK TOTALS:\n" +
                        "OK: %s\nFAIL: %s\nSKIP: %s\nNOT CONSIDERED: %s\n" +
                        "TOTAL: %s")
        return msg_template % (n_ok, n_fail, n_skip, n_notconsidered, total)


class NotRunEvent(Event):
    """An event used to report commands that will not be run."""

    KIND = Event.KIND_OUT

    def __str__(self):
        name, cmd = self.args
        return " %s: %s" % (name, cmd)


class RoseBunchApp(BuiltinApp):
    """Run multiple commands under one app"""

    SCHEME = "rose_bunch"
    ARGS_SECTION = "bunch-args"
    BUNCH_SECTION = "bunch"
    MAX_PROCS = None
    SLEEP_DURATION = 0.5
    TYPE_ABORT_ON_FAIL = "abort"
    TYPE_CONTINUE_ON_FAIL = "continue"
    FAIL_MODE_TYPES = [TYPE_CONTINUE_ON_FAIL, TYPE_ABORT_ON_FAIL]
    PREFIX_OK = "[OK] "
    PREFIX_PASS = "[PASS] "
    PREFIX_NOTRUN = "[SKIP] "

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """ Run multiple instaces of a command using sets of specified args"""

        # Counts for reporting purposes
        run_ok = 0
        run_fail = 0
        run_skip = 0
        notrun = 0

        # Allow naming of individual calls
        self.invocation_names = conf_tree.node.get_value([self.BUNCH_SECTION,
                                                         "names"])
        if self.invocation_names:
            self.invocation_names = shlex.split(
                rose.env.env_var_process(self.invocation_names))
            if len(set(self.invocation_names)) != len(self.invocation_names):
                raise ConfigValueError([self.BUNCH_SECTION, "names"],
                                       self.invocation_names,
                                       "names must be unique")

        self.fail_mode = rose.env.env_var_process(conf_tree.node.get_value(
            [self.BUNCH_SECTION, "fail-mode"], self.TYPE_CONTINUE_ON_FAIL))

        if self.fail_mode not in self.FAIL_MODE_TYPES:
            raise ConfigValueError([self.BUNCH_SECTION, "fail-mode"],
                                   self.fail_mode,
                                   "not a valid setting")

        self.incremental = conf_tree.node.get_value([self.BUNCH_SECTION,
                                                    "incremental"],
                                                    "true")
        if self.incremental:
            self.incremental = rose.env.env_var_process(self.incremental)

        multi_args = conf_tree.node.get_value([self.ARGS_SECTION], {})
        for key, val in multi_args.items():
            multi_args[key].value = rose.env.env_var_process(val.value)

        self.command_format = rose.env.env_var_process(
            conf_tree.node.get_value([self.BUNCH_SECTION, "command-format"]))

        if not self.command_format:
            raise CompulsoryConfigValueError([self.BUNCH_SECTION,
                                             "command-format"],
                                             None,
                                             KeyError("command-format"))

        # Set up command-instances if needed
        instances = conf_tree.node.get_value([self.BUNCH_SECTION,
                                              "command-instances"])

        if instances:
            try:
                instances = range(int(rose.env.env_var_process(instances)))
            except ValueError:
                raise ConfigValueError([self.BUNCH_SECTION,
                                        "command-instances"],
                                       instances,
                                       "not an integer value")

        # Validate runlists
        if not self.invocation_names:
            if instances:
                arglength = len(instances)
            else:
                item, val = sorted(multi_args.items())[0]
                arglength = len(shlex.split(val.value))
            self.invocation_names = range(0, arglength)
        else:
            arglength = len(self.invocation_names)

        for item, val in sorted(multi_args.items()):
            if len(shlex.split(val.value)) != arglength:
                raise ConfigValueError([self.ARGS_SECTION, item],
                                       conf_tree.node.get_value(
                                       [self.ARGS_SECTION, item]),
                                       "inconsistent arg lengths")

        if conf_tree.node.get_value([self.ARGS_SECTION, "command-instances"]):
            raise ConfigValueError([self.ARGS_SECTION, "command-instances"],
                                   conf_tree.node.get_value(
                                   [self.ARGS_SECTION, "command-instances"]),
                                   "reserved keyword")

        if instances and arglength != len(instances):
            raise ConfigValueError([self.BUNCH_SECTION, "command-instances"],
                                   instances, "inconsistent arg lengths")

        # Set max number of processes to run at once
        max_procs = conf_tree.node.get_value([self.BUNCH_SECTION, "pool-size"])

        if max_procs:
            self.MAX_PROCS = int(rose.env.env_var_process(max_procs))
        else:
            self.MAX_PROCS = arglength

        if self.incremental == "true":
            self.dao = RoseBunchDAO(conf_tree)
        else:
            self.dao = None

        commands = {}
        for index, name in enumerate(self.invocation_names):
            invocation = RoseBunchCmd(name, self.command_format, index)
            for key, vals in sorted(multi_args.items()):
                invocation.argsdict[key] = shlex.split(vals.value)[index]
            if instances:
                invocation.argsdict["command-instances"] = instances[index]
            commands[name] = invocation

        procs = {}
        if 'ROSE_TASK_LOG_DIR' in os.environ:
            log_format = os.path.join(os.environ['ROSE_TASK_LOG_DIR'], "%s")
        else:
            log_format = os.path.join(os.getcwd(), "%s")

        failed = {}
        abort = False

        while procs or (commands and not abort):
            for key, proc in procs.items():
                if proc.poll() is not None:
                    procs.pop(key)
                    if proc.returncode:
                        failed[key] = proc.returncode
                        run_fail += 1
                        app_runner.handle_event(RosePopenError(str(key),
                                                proc.returncode,
                                                None, None))
                        if self.dao:
                            self.dao.update_command_state(key, self.dao.S_FAIL)
                        if self.fail_mode == self.TYPE_ABORT_ON_FAIL:
                            abort = True
                            app_runner.handle_event(AbortEvent())
                    else:
                        run_ok += 1
                        app_runner.handle_event(SucceededEvent(key),
                                                prefix=self.PREFIX_OK)
                        if self.dao:
                            self.dao.update_command_state(key, self.dao.S_PASS)

            while len(procs) < self.MAX_PROCS and commands and not abort:
                key = self.invocation_names[0]
                command = commands.pop(key)
                self.invocation_names.pop(0)
                cmd = command.get_command()
                cmd_stdout = log_format % command.get_out_file()
                cmd_stderr = log_format % command.get_err_file()
                prefix = command.get_log_prefix()
                bunch_environ = os.environ
                bunch_environ['ROSE_BUNCH_LOG_PREFIX'] = prefix

                if self.dao:
                    if self.dao.check_has_succeeded(key):
                        run_skip += 1
                        app_runner.handle_event(PreviousSuccessEvent(key),
                                                prefix=self.PREFIX_PASS)
                        continue
                    else:
                        self.dao.add_command(key)

                app_runner.handle_event(LaunchEvent(key, cmd))
                procs[key] = app_runner.popen.run_bg(
                    cmd,
                    shell=True,
                    stdout=open(cmd_stdout, 'w'),
                    stderr=open(cmd_stderr, 'w'),
                    env=bunch_environ)

            sleep(self.SLEEP_DURATION)

        if abort and commands:
            for key in self.invocation_names:
                notrun += 1
                cmd = commands.pop(key).get_command()
                app_runner.handle_event(NotRunEvent(key, cmd),
                                        prefix=self.PREFIX_NOTRUN)

        if self.dao:
            self.dao.close()

        # Report summary data in job.out file
        app_runner.handle_event(SummaryEvent(
                                run_ok, run_fail, run_skip, notrun))

        if failed:
            return 1
        else:
            return 0


class RoseBunchCmd(object):
    """A command instance to run."""

    OUTPUT_TEMPLATE = "bunch.%s.%s"

    def __init__(self, name, command, index):
        self.command_format = command
        self.argsdict = {}
        self.name = str(name)
        self.index = index

    def get_command(self):
        """Return the command that will be run"""

        return self.command_format % self.argsdict

    def get_out_file(self):
        """Return output file name"""

        return self.OUTPUT_TEMPLATE % (self.name, "out")

    def get_err_file(self):
        """Return error file name"""

        return self.OUTPUT_TEMPLATE % (self.name, "err")

    def get_log_prefix(self):
        """Return log prefix"""

        return self.name


class RoseBunchDAO(object):
    """Database object for rose_bunch"""

    TABLE_COMMANDS = "commands"
    TABLE_CONFIG = "config"

    S_PASS = "pass"
    S_FAIL = "fail"
    S_STARTED = "started"

    CONN_TIMEOUT = 0.1
    FILE_NAME = ".rose-bunch.db"

    def __init__(self, config):
        self.conn = None
        self.new_run = True
        self.db_file_name = os.path.abspath(self.FILE_NAME)
        self.connect()
        self.create_tables()

        if self.new_run:
            self.record_config(config)
        elif not self.same_prev_config(config):
            self.clear_command_states()
            self.record_config(config, clear_db=True)

    def connect(self):
        """Connect to the database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file_name, self.CONN_TIMEOUT)
        return

    def create_tables(self):
        """Create tables as appropriate"""
        existing = []
        first_run = os.environ.get("CYLC_TASK_SUBMIT_NUMBER") == "1"

        for row in self.conn.execute("SELECT name FROM sqlite_master " +
                                     "WHERE type=='table'"):
            existing.append(row[0])

        if first_run:
            for tablename in existing:
                self.conn.execute("""DELETE FROM """ + tablename)

        self.new_run = not existing

        if self.TABLE_COMMANDS not in existing:
            self.conn.execute("""CREATE TABLE """ + self.TABLE_COMMANDS + """ (
                              name TEXT,
                              status TEXT,
                              PRIMARY KEY(name))""")

        if self.TABLE_CONFIG not in existing:
            self.conn.execute("""CREATE TABLE """ + self.TABLE_CONFIG + """ (
                              key TEXT,
                              value TEXT,
                              PRIMARY KEY(key))""")
        self.conn.commit()
        return

    def add_command(self, name):
        """Add a command to the commands table"""
        i_stmt = ("INSERT OR REPLACE INTO " + self.TABLE_COMMANDS +
                  " VALUES (?, ?)")
        self.conn.execute(i_stmt, [name, self.S_STARTED])
        self.conn.commit()
        return

    def clear_command_states(self):
        """Deletes all recorded command entries"""
        d_stmt = "DELETE FROM " + self.TABLE_COMMANDS
        self.conn.execute(d_stmt)
        self.conn.commit()
        return

    def close(self):
        """Close database connection"""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def update_command_state(self, name, state):
        """Update command state in CMDS table"""
        u_stmt = ("UPDATE " + self.TABLE_COMMANDS +
                  " SET status=? WHERE name==?")
        self.conn.execute(u_stmt, [state, name])
        self.conn.commit()
        return

    def check_has_succeeded(self, name):
        """See if a named command reached the "pass" state"""
        s_stmt = ("SELECT * FROM " + self.TABLE_COMMANDS +
                  " WHERE name==? AND status==?")
        s_stmt_args = [name, self.S_PASS]
        if self.conn.execute(s_stmt, s_stmt_args).fetchone():
            return True
        return False

    @staticmethod
    def flatten_config(config):
        """Flatten down a config node to set of keys and values to record"""
        flat = {}
        keys_and_nodes = list(config.node.walk())
        for keys, node in keys_and_nodes:
            if not isinstance(node.value, dict):
                if not node.is_ignored():
                    flat["_".join(keys)] = node.value
        return flat

    def record_config(self, config, clear_db=False):
        """Take in a conf_tree object and record the entries"""

        if clear_db:
            d_stmt = "DELETE FROM " + self.TABLE_CONFIG
            self.conn.execute(d_stmt)
            self.conn.commit()

        res = self.flatten_config(config)

        args = []

        for key, value in res.items():
            args.append((key, value))

        i_stmt = ("INSERT OR REPLACE INTO " + self.TABLE_CONFIG +
                  " VALUES (?, ?)")
        self.conn.executemany(i_stmt, args)
        self.conn.commit()
        return

    def same_prev_config(self, current):
        """See if the current config is the same as the last one used"""
        s_stmt = ("SELECT key, value FROM " + self.TABLE_CONFIG)
        unchanged = True
        current = self.flatten_config(current)
        for key, value in self.conn.execute(s_stmt):
            if key in current:
                if current[key] != value:
                    break
                else:
                    current.pop(key)
            else:
                break
        # If the two configs match there should be no entries left
        if current:
            unchanged = False
        return unchanged
