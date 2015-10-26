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
"""Builtin application: rose_bunch: run multiple commands in parallel."""


import os
import shlex
import sqlite3
from multiprocessing import Pool
from time import sleep

from rose.env import env_var_process
from rose.app_run import (
    BuiltinApp,
    ConfigValueError,
    CompulsoryConfigValueError)
from rose.popen import RosePopener
import rose.job_runner
from rose.reporter import Event


class AbortEvent(Event):

    """An event raised when a task failure will stop further task running"""

    LEVEL = Event.V
    KIND = Event.KIND_ERR

    def __str__(self):
        return "Closing task pool, no further commands will be run."


class FailEvent(Event):

    """An event used to report failure of a task in the pool."""

    KIND = Event.KIND_ERR

    def __str__(self):
        name, rc = self.args
        return "Command %s failed with return code %s" % (name, rc)


class LaunchEvent(Event):

    """An event raised when adding a command to the task pool."""

    LEVEL = Event.V
    KIND = Event.KIND_OUT

    def __str__(self):
        name, cmd = self.args
        return "Adding command %s to pool: %s" % (name, cmd)


class SucceededEvent(Event):

    """An event used to report success of a task in the pool."""

    LEVEL = Event.V
    KIND = Event.KIND_OUT

    def __str__(self):
        name, rc = self.args
        return "Command %s completed successfully # rc = %s" % (name, rc)


class SkippingEvent(Event):

    """Event raised when a command is skipped in incremental mode"""
    LEVEL = Event.V
    KIND = Event.KIND_OUT

    def __str__(self):
        name = self.args
        return "Skipping %s: previously ran and succeeded" % (name)


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


    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """ Run multiple instaces of a command using sets of specified args"""

        # Allow naming of individual calls
        self.invocation_names = conf_tree.node.get_value(
                                            [self.BUNCH_SECTION, "names"])
        if self.invocation_names:
            self.invocation_names = shlex.split(self.invocation_names)
            if len(set(self.invocation_names)) != len(self.invocation_names):
                raise ConfigValueError([self.BUNCH_SECTION, "names"],
                                       self.invocation_names,
                                       "names must be unique")

        self.fail_mode = conf_tree.node.get_value([self.BUNCH_SECTION,
                                              "fail-mode"],
                                             self.TYPE_CONTINUE_ON_FAIL)

        if self.fail_mode not in self.FAIL_MODE_TYPES:
            raise ConfigValueError([self.BUNCH_SECTION, "fail-mode"],
                                   fail_mode,
                                   "not a valid setting")

        self.incremental = conf_tree.node.get_value([self.BUNCH_SECTION,
                                                "incremental"], False)

        multi_args = conf_tree.node.get_value([self.ARGS_SECTION])
        if not multi_args:
            raise CompulsoryConfigValueError(
                                        [self.ARGS_SECTION, "command-format"],
                                        None,
                                        KeyError(self.ARGS_SECTION))

        self.command_format = conf_tree.node.get_value(
                                    [self.BUNCH_SECTION, "command-format"])

        if not self.command_format:
            raise CompulsoryConfigValueError(
                                    [self.BUNCH_SECTION, "command-format"],
                                     None, KeyError("command-format"))

        # Validate runlists
        if not self.invocation_names:
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

        # Set up command-instances if needed
        instances = conf_tree.node.get_value([self.BUNCH_SECTION, "command-instances"])

        if instances:
            try:
                instances = range(int(instances))
            except ValueError as err:
                raise ConfigValueError([self.BUNCH_SECTION, "command-instances"],
                                       instances,
                                       "not an integer value")
            if arglength != len(instances):
                raise ConfigValueError([self.BUNCH_SECTION, "command-instances"],
                                       instances,
                                       "inconsitent arg lengths")

        # Set max number of processes to run at once
        max_procs = int(conf_tree.node.get_value(
                                        [self.BUNCH_SECTION, "pool-size"]))
        if max_procs:
            self.MAX_PROCS = int(max_procs)
        else:
            self.MAX_PROCS = arglength


        if self.incremental:
            self.dao = RoseBunchDAO(conf_tree)
        else:
            self.dao = None

        commands = {}
        for index, name in enumerate(self.invocation_names):
            invocation = RoseBunchCmd(name, self.command_format, index)
            for key, vals in sorted(multi_args.items()):
                invocation.argsdict[key] = shlex.split(vals.value)[index]
            if instances:
                invocation.argsdict["instances"] = instances[index]
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
                        app_runner.handle_event(
                                        FailEvent(key, proc.returncode))
                        if self.dao:
                            self.dao.update_command_state(key, self.dao.S_FAIL)
                        if self.fail_mode == self.TYPE_ABORT_ON_FAIL:
                            abort = True
                            app_runner.handle_event(AbortEvent())
                    else:
                        app_runner.handle_event(
                                    SucceededEvent(key, proc.returncode))
                        if self.dao:
                            self.dao.update_command_state(key, self.dao.S_PASS)

            while len(procs) < self.MAX_PROCS and commands and not abort:
                key = self.invocation_names[0]
                command = commands.pop(key)
                self.invocation_names.pop(0)
                cmd = command.get_command()
                cmd_stdout = log_format % command.get_out_file()
                cmd_stderr = log_format % command.get_err_file()

                if self.dao:
                    if self.dao.check_has_succeeded(key):
                        app_runner.handle_event(SkippingEvent(key))
                        continue
                    else:
                        self.dao.add_command(key)

                app_runner.handle_event(LaunchEvent(key, cmd))
                procs[key] = app_runner.popen.run_bg(
                                                cmd,
                                                shell=True,
                                                stdout=open(cmd_stdout, 'w'),
                                                stderr=open(cmd_stderr, 'w'))
            sleep(self.SLEEP_DURATION)

        if abort and commands:
            for command in commands:
                cmd = command.get_command()
                print "Not run: %s" % cmd

        if self.dao:
            self.dao.close()

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
        self.name = name
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

        for row in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type=='table' ORDER BY name"):
            existing.append(row[0])

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
        i_stmt = "INSERT OR REPLACE INTO " + self.TABLE_COMMANDS + " VALUES (?, ?)"
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
        u_stmt = "UPDATE " + self.TABLE_COMMANDS + " SET status=? WHERE name==?"
        self.conn.execute(u_stmt, [state, name])
        self.conn.commit()
        return

    def check_has_succeeded(self, name):
        """See if a named command reached the "pass" state"""
        s_stmt = ("SELECT * FROM " + self.TABLE_COMMANDS +
                  " WHERE name==? AND status==?")
        s_stmt_args = [name, self.S_PASS]
        has_succeeded = False
        for s_row in self.conn.execute(s_stmt, s_stmt_args):
            has_succeeded = True
        return has_succeeded

    def flatten_config(self, config):
        """Flatten down a config node to set of keys and values for recording"""
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

        i_stmt = "INSERT OR REPLACE INTO " + self.TABLE_CONFIG + " VALUES (?, ?)"
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
                    no_change = False
                    break
                else:
                    current.pop(key)
            else:
                no_change = False
                break
        # If the two configs match there should be no entries left
        if current:
            unchanged = False
        return unchanged
