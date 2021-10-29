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
"""Builtin application: rose_bunch: run multiple commands in parallel.
"""

import itertools
import os
import shlex
import sqlite3
from time import sleep

from metomi.rose.app_run import BuiltinApp, ConfigValueError
import metomi.rose.job_runner
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Event


class CommandNotDefinedError(Exception):
    """An exception raised when no command to run is defined."""

    def __str__(self):
        return "command to run not defined"


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
        msg_template = (
            "BUNCH TASK TOTALS:\n"
            + "OK: %s\nFAIL: %s\nSKIP: %s\nNOT CONSIDERED: %s\n"
            + "TOTAL: %s"
        )
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
    SLEEP_DURATION = 0.5
    TYPE_ABORT_ON_FAIL = "abort"
    TYPE_CONTINUE_ON_FAIL = "continue"
    FAIL_MODE_TYPES = [TYPE_CONTINUE_ON_FAIL, TYPE_ABORT_ON_FAIL]
    PREFIX_OK = "[OK] "
    PREFIX_PASS = "[PASS] "
    PREFIX_NOTRUN = "[SKIP] "
    DEFAULT_ARGUMENT_MODE = "Default"
    # @TODO: Match ACCEPTED_ARGUMENT_MODES to what python is actually doing
    ACCEPTED_ARGUMENT_MODES = [
        DEFAULT_ARGUMENT_MODE,
        "izip",
        "zip",
        "izip_longest",
        "zip_longest",
        "product",
    ]

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """Run multiple instances of a command using sets of specified args"""

        # Counts for reporting purposes
        run_ok = 0
        run_fail = 0
        run_skip = 0
        notrun = 0

        # Allow naming of individual calls
        self.invocation_names = conf_tree.node.get_value(
            [self.BUNCH_SECTION, "names"]
        )
        if self.invocation_names:
            self.invocation_names = shlex.split(
                metomi.rose.env.env_var_process(self.invocation_names)
            )
            if len(set(self.invocation_names)) != len(self.invocation_names):
                raise ConfigValueError(
                    [self.BUNCH_SECTION, "names"],
                    self.invocation_names,
                    "names must be unique",
                )

        self.fail_mode = metomi.rose.env.env_var_process(
            conf_tree.node.get_value(
                [self.BUNCH_SECTION, "fail-mode"], self.TYPE_CONTINUE_ON_FAIL
            )
        )

        if self.fail_mode not in self.FAIL_MODE_TYPES:
            raise ConfigValueError(
                [self.BUNCH_SECTION, "fail-mode"],
                self.fail_mode,
                "not a valid setting",
            )

        self.incremental = conf_tree.node.get_value(
            [self.BUNCH_SECTION, "incremental"], "true"
        )
        if self.incremental:
            self.incremental = metomi.rose.env.env_var_process(
                self.incremental
            )

        self.isformatted = True
        self.command = metomi.rose.env.env_var_process(
            conf_tree.node.get_value([self.BUNCH_SECTION, "command-format"])
        )

        if not self.command:
            self.isformatted = False
            self.command = app_runner.get_command(conf_tree, opts, args)

        if not self.command:
            raise CommandNotDefinedError()

        # Set up command-instances if needed
        instances = conf_tree.node.get_value(
            [self.BUNCH_SECTION, "command-instances"]
        )

        if instances:
            try:
                instances = range(
                    int(metomi.rose.env.env_var_process(instances))
                )
            except ValueError:
                raise ConfigValueError(
                    [self.BUNCH_SECTION, "command-instances"],
                    instances,
                    "not an integer value",
                )

        # Argument lists
        multi_args = conf_tree.node.get_value([self.ARGS_SECTION], {})
        bunch_args_names = []
        bunch_args_values = []
        for key, val in multi_args.items():
            bunch_args_names.append(key)
            bunch_args_values.append(
                shlex.split(metomi.rose.env.env_var_process(val.value))
            )

        # Update the argument values based on the argument-mode
        argument_mode = conf_tree.node.get_value(
            [self.BUNCH_SECTION, "argument-mode"], self.DEFAULT_ARGUMENT_MODE
        )
        if argument_mode == self.DEFAULT_ARGUMENT_MODE:
            pass
        elif argument_mode in self.ACCEPTED_ARGUMENT_MODES:
            # The behaviour of of izip and izip_longest are special cases
            # because:
            # * izip was deprecated in Python3 use zip
            # * itertools.izip_longest was renamed and requires the fillvalue
            #     kwarg
            if argument_mode in ['zip', 'izip']:
                _permutations = zip(*bunch_args_values)
            elif argument_mode in ['zip_longest', 'izip_longest']:
                _permutations = itertools.zip_longest(
                    *bunch_args_values, fillvalue=""
                )
            else:
                iteration_cmd = getattr(itertools, argument_mode)
                _permutations = iteration_cmd(*bunch_args_values)

            # Reconstruct the bunch_args_values
            _permutations = list(_permutations)
            for index, _ in enumerate(bunch_args_values):
                bunch_args_values[index] = [v[index] for v in _permutations]
        else:
            raise ConfigValueError(
                [self.BUNCH_SECTION, "argument-mode"],
                argument_mode,
                "must be one of %s" % self.ACCEPTED_ARGUMENT_MODES,
            )

        # Validate runlists
        if not self.invocation_names:
            if instances:
                arglength = len(instances)
            else:
                arglength = len(bunch_args_values[0])
            self.invocation_names = list(range(0, arglength))
        else:
            arglength = len(self.invocation_names)

        for item, vals in zip(bunch_args_names, bunch_args_values):
            if len(vals) != arglength:
                raise ConfigValueError(
                    [self.ARGS_SECTION, item],
                    conf_tree.node.get_value([self.ARGS_SECTION, item]),
                    "inconsistent arg lengths",
                )

        if conf_tree.node.get_value([self.ARGS_SECTION, "command-instances"]):
            raise ConfigValueError(
                [self.ARGS_SECTION, "command-instances"],
                conf_tree.node.get_value(
                    [self.ARGS_SECTION, "command-instances"]
                ),
                "reserved keyword",
            )

        if conf_tree.node.get_value([self.ARGS_SECTION, "COMMAND_INSTANCES"]):
            raise ConfigValueError(
                [self.ARGS_SECTION, "COMMAND_INSTANCES"],
                conf_tree.node.get_value(
                    [self.ARGS_SECTION, "COMMAND_INSTANCES"]
                ),
                "reserved keyword",
            )

        if instances and arglength != len(instances):
            raise ConfigValueError(
                [self.BUNCH_SECTION, "command-instances"],
                instances,
                "inconsistent arg lengths",
            )

        # Set max number of processes to run at once
        max_procs = conf_tree.node.get_value([self.BUNCH_SECTION, "pool-size"])

        if max_procs:
            max_procs = int(metomi.rose.env.env_var_process(max_procs))
        else:
            max_procs = arglength

        if self.incremental == "true":
            self.dao = RoseBunchDAO(conf_tree)
        else:
            self.dao = None

        commands = {}
        for vals in zip(
            range(arglength), self.invocation_names, *bunch_args_values
        ):
            index, name, bunch_args_vals = vals[0], vals[1], vals[2:]
            argsdict = dict(zip(bunch_args_names, bunch_args_vals))
            if instances:
                if self.isformatted:
                    argsdict["command-instances"] = instances[index]
                else:
                    argsdict["COMMAND_INSTANCES"] = str(instances[index])
            commands[name] = RoseBunchCmd(
                name, self.command, argsdict, self.isformatted
            )

        procs = {}
        if 'ROSE_TASK_LOG_DIR' in os.environ:
            log_format = os.path.join(os.environ['ROSE_TASK_LOG_DIR'], "%s")
        else:
            log_format = os.path.join(os.getcwd(), "%s")

        failed = {}
        abort = False

        while procs or (commands and not abort):
            for key, proc in list(procs.items()):
                if proc.poll() is not None:
                    procs.pop(key)
                    if proc.returncode:
                        failed[key] = proc.returncode
                        run_fail += 1
                        app_runner.handle_event(
                            RosePopenError(
                                str(key), proc.returncode, None, None
                            )
                        )
                        if self.dao:
                            self.dao.update_command_state(key, self.dao.S_FAIL)
                        if self.fail_mode == self.TYPE_ABORT_ON_FAIL:
                            abort = True
                            app_runner.handle_event(AbortEvent())
                    else:
                        run_ok += 1
                        app_runner.handle_event(
                            SucceededEvent(key), prefix=self.PREFIX_OK
                        )
                        if self.dao:
                            self.dao.update_command_state(key, self.dao.S_PASS)

            while len(procs) < max_procs and commands and not abort:
                key = self.invocation_names[0]
                command = commands.pop(key)
                self.invocation_names.pop(0)
                cmd = command.get_command()
                cmd_stdout = log_format % command.get_out_file()
                cmd_stderr = log_format % command.get_err_file()
                prefix = command.get_log_prefix()
                bunch_environ = os.environ
                if not command.isformatted:
                    bunch_environ.update(command.argsdict)
                bunch_environ['ROSE_BUNCH_LOG_PREFIX'] = prefix

                if self.dao:
                    if self.dao.check_has_succeeded(key):
                        run_skip += 1
                        app_runner.handle_event(
                            PreviousSuccessEvent(key), prefix=self.PREFIX_PASS
                        )
                        continue
                    else:
                        self.dao.add_command(key)

                app_runner.handle_event(LaunchEvent(key, cmd))
                procs[key] = app_runner.popen.run_bg(
                    cmd,
                    shell=True,
                    stdout=open(cmd_stdout, 'w'),
                    stderr=open(cmd_stderr, 'w'),
                    env=bunch_environ,
                )

            sleep(self.SLEEP_DURATION)

        if abort and commands:
            for key in self.invocation_names:
                notrun += 1
                cmd = commands.pop(key).get_command()
                app_runner.handle_event(
                    NotRunEvent(key, cmd), prefix=self.PREFIX_NOTRUN
                )

        if self.dao:
            self.dao.close()

        # Report summary data in job.out file
        app_runner.handle_event(
            SummaryEvent(run_ok, run_fail, run_skip, notrun)
        )

        if failed:
            return 1
        else:
            return 0


class RoseBunchCmd:
    """A command instance to run."""

    OUTPUT_TEMPLATE = "bunch.%s.%s"

    def __init__(self, name, command, argsdict, isformatted):
        self.name = str(name)
        self.command = command
        self.argsdict = argsdict
        self.isformatted = isformatted

    def get_command(self):
        """Return the command that will be run"""

        if self.isformatted:
            return self.command % self.argsdict
        return self.command

    def get_out_file(self):
        """Return output file name"""

        return self.OUTPUT_TEMPLATE % (self.name, "out")

    def get_err_file(self):
        """Return error file name"""

        return self.OUTPUT_TEMPLATE % (self.name, "err")

    def get_log_prefix(self):
        """Return log prefix"""

        return self.name


class RoseBunchDAO:
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
        first_run = os.environ.get("CYLC_TASK_TRY_NUMBER") == "1"

        for row in self.conn.execute(
            "SELECT name FROM sqlite_master " + "WHERE type=='table'"
        ):
            existing.append(row[0])

        if first_run:
            for tablename in existing:
                self.conn.execute("""DELETE FROM """ + tablename)

        self.new_run = not existing

        if self.TABLE_COMMANDS not in existing:
            self.conn.execute(
                """CREATE TABLE """
                + self.TABLE_COMMANDS
                + """ (
                              name TEXT,
                              status TEXT,
                              PRIMARY KEY(name))"""
            )

        if self.TABLE_CONFIG not in existing:
            self.conn.execute(
                """CREATE TABLE """
                + self.TABLE_CONFIG
                + """ (
                              key TEXT,
                              value TEXT,
                              PRIMARY KEY(key))"""
            )
        self.conn.commit()
        return

    def add_command(self, name):
        """Add a command to the commands table"""
        i_stmt = (
            "INSERT OR REPLACE INTO " + self.TABLE_COMMANDS + " VALUES (?, ?)"
        )
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
        u_stmt = (
            "UPDATE " + self.TABLE_COMMANDS + " SET status=? WHERE name==?"
        )
        self.conn.execute(u_stmt, [state, name])
        self.conn.commit()
        return

    def check_has_succeeded(self, name):
        """See if a named command reached the "pass" state"""
        s_stmt = (
            "SELECT * FROM "
            + self.TABLE_COMMANDS
            + " WHERE name==? AND status==?"
        )
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

        i_stmt = (
            "INSERT OR REPLACE INTO " + self.TABLE_CONFIG + " VALUES (?, ?)"
        )
        self.conn.executemany(i_stmt, args)
        self.conn.commit()
        return

    def same_prev_config(self, current):
        """See if the current config is the same as the last one used"""
        s_stmt = "SELECT key, value FROM " + self.TABLE_CONFIG
        unchanged = True
        current = self.flatten_config(current)
        for key, value in self.conn.execute(s_stmt):
            if key == 'env_PATH':
                # due to re-invocation the PATH may have changed in-between
                # runs - only re-run jobs if the PATH has changed in a way
                # that could actually make a difference
                if simplify_path(current[key]) != simplify_path(value):
                    break
                else:
                    current.pop(key)
            elif key in current:
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


def simplify_path(path):
    """Removes duplication in paths whilst maintaining integrity.

    If duplicate items are present in a path this keeps the first item and
    removes any subsequent duplicates.

    Examples:
        >>> simplify_path('')
        ''
        >>> simplify_path('a')
        'a'
        >>> simplify_path('a:a:a')
        'a'
        >>> simplify_path('a:b:a')
        'a:b'
        >>> simplify_path('a:b:b:a')
        'a:b'
        >>> simplify_path('a:b:a:b:c:d:a:b:c:d:e')
        'a:b:c:d:e'

    """
    return ':'.join(dict.fromkeys(path.split(':')).keys())
