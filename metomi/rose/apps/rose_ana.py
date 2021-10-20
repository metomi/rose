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
# -----------------------------------------------------------------------------
"""Builtin application: "rose ana", a comparison engine for Rose."""


# Standard Python modules
import abc
from contextlib import contextmanager
import fcntl
import glob
import inspect
import os
import re
import sqlite3
import sys
import threading
import time
import traceback

# Rose modules
from metomi.rose import TYPE_LOGICAL_VALUE_TRUE
from metomi.rose.app_run import BuiltinApp
from metomi.rose.env import env_var_process
from metomi.rose.reporter import Reporter
from metomi.rose.resource import ResourceLocator


def timestamp():
    """
    Return the time in a more concise form then time.asctime

    """
    return time.strftime("%H:%M:%S")


class KGODatabase:
    """
    KGO Database object, stores comparison information for metomi.rose_ana
    apps.

    """

    # This SQL command ensures a "comparisons" table exists in the database
    # and then populates it with a series of columns (which in this case
    # are all storing strings/text). The primary key is the comparison name
    # (as it must uniquely identify each row)
    CREATE_COMPARISON_TABLE = """
        CREATE TABLE IF NOT EXISTS comparisons (
        comp_task TEXT,
        kgo_file TEXT,
        suite_file TEXT,
        status TEXT,
        comparison TEXT,
        PRIMARY KEY(comp_task))
        """
    # This SQL command ensures a "tasks" table exists in the database
    # and then populates it with a pair of columns (the task name and
    # a completion status indicator). The primary key is the task name
    # (as it must uniquely identify each row)
    CREATE_TASKS_TABLE = """
        CREATE TABLE IF NOT EXISTS tasks (
        task_name TEXT,
        completed INT,
        PRIMARY KEY(task_name))
        """

    # Task statuses
    TASK_STATUS_RUNNING = 1
    TASK_STATUS_SUCCEEDED = 0

    def __init__(self):
        "Initialise the object."
        self.statement_buffer = []
        self.task_name = "task_name not set"

    def enter_comparison(
        self, comp_task, kgo_file, suite_file, status, comparison
    ):
        """Add a command to insert a new comparison entry to the database."""
        # This SQL command indicates that a single "row" is to be entered into
        # the "comparisons" table
        sql_statement = (
            "INSERT OR REPLACE INTO comparisons VALUES (?, ?, ?, ?, ?)"
        )
        # Prepend the task_name onto each entry, to try and ensure it is
        # unique (the individual comparison names may not be, but the
        # rose task name + the comparison task name should)
        sql_args = [
            self.task_name + " - " + comp_task,
            kgo_file,
            suite_file,
            status,
            comparison,
        ]
        # Add the command and arguments to the buffer
        self.statement_buffer.append((sql_statement, sql_args))

    def enter_task(self, task_name, status):
        """Add a command to insert a new task entry to the database."""
        # This SQL command indicates that a single "row" is to be entered into
        # the "tasks" table
        sql_statement = "INSERT OR REPLACE INTO tasks VALUES (?, ?)"
        sql_args = [task_name, status]
        # Add the command and arguments to the buffer
        self.statement_buffer.append((sql_statement, sql_args))
        # Save the name for use in any comparisons later
        self.task_name = task_name

    @contextmanager
    def database_lock(self, lockfile, reporter=None):
        """Context manager which obtains an exclusive file-based lock."""
        lock = open(lockfile, "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
        if reporter is not None:
            reporter("Acquired DB lock at: " + timestamp())
        lock.write("{0}".format(os.getpid()))
        if reporter is not None:
            reporter("Writing to KGO Database...")
        yield
        fcntl.flock(lock, fcntl.LOCK_UN)
        if reporter is not None:
            reporter("Released DB lock at: " + timestamp())
        lock.close()

    def buffer_to_db(self, reporter=None):
        """Flush the buffer; executing all the commands in one transaction."""
        # If the buffer is empty, there isn't anything to do
        if len(self.statement_buffer) == 0:
            return
        # Otherwise locate the database
        file_name = os.path.join(
            os.getenv("ROSE_SUITE_DIR"), "log", "rose-ana-comparisons.db"
        )
        lock_name = file_name + ".lock"

        if reporter is not None:
            for statement in self.statement_buffer:
                reporter(str(statement), level=reporter.V)

        # Acquire a file lock to ensure exclusive access, then connect to the
        # database and commit each command from the buffer
        with self.database_lock(lock_name, reporter):
            conn = sqlite3.connect(file_name, timeout=60.0)
            # Ensure that the tables exist
            conn.execute(self.CREATE_COMPARISON_TABLE)
            conn.execute(self.CREATE_TASKS_TABLE)
            # Apply each command from the buffer
            for statement, args in self.statement_buffer:
                conn.execute(statement, args)
            # Finalise the database
            conn.commit()
        # Empty the buffer in case it gets re-used
        self.statement_buffer = []


class AnalysisTask(object, metaclass=abc.ABCMeta):
    """Base class for an analysis task.

    All custom user tasks should inherit from this class and override
    the ``run_analysis`` method to perform whatever analysis is required.

    This class provides the following attributes:

    Attributes:
        self.config:
            A dictionary containing any Rose Ana configuration options.
        self.reporter:
            A reference to the :py:class:`metomi.rose.reporter.Reporter`
            instance used by the parent app (for printing to stderr/stdout).
        self.kgo_db:
            A reference to the KGO database object created by the parent app
            (for adding entries to the database).
        self.popen:
            A reference to the :py:class:`metomi.rose.popen.RosePopener`
            instance used by the parent app (for spawning subprocesses).

    """

    def __init__(self, parent_app, task_options):
        """
        Initialise the analysis task, storing the user specified options
        dictionary and a few references to useful objects from the parent app.

        """
        self.options = task_options

        # This attribute gives access to the parent task; but it is only
        # included for backwards compatibility and will be remove in the
        # future (please instead use the other attributes below!)
        self.parent = parent_app

        # Attributes to access some helpful/relevant parts of the parent
        # task environment for printing, running tasks, etc.
        self.config = parent_app.ana_config
        self.reporter = parent_app.reporter
        self.kgo_db = parent_app.kgo_db
        self.popen = parent_app.app_runner.popen

        self.passed = False
        self.skipped = False

    @abc.abstractmethod
    def run_analysis(self):
        """
        Will be called to start the analysis code; this method should be
        overridden by the user's class to perform the desired analysis.

        """
        msg = "Abstract analysis task class should never be called directly"
        raise ValueError(msg)

    def process_opt_unhandled(self):
        """
        Options should be removed from the options dictionary as they are
        processed; this method may then be called to catch and unknown options

        """
        unhandled = []
        for option in self.options:
            if option not in ["full_task_name", "description"]:
                unhandled.append(option)
        if unhandled:
            msg = (
                "Options provided but not understood for this "
                "analysis type: {0}"
            )
            raise ValueError(msg.format(unhandled))


class TaskRunner(threading.Thread):
    def __init__(self, app, index, task):
        threading.Thread.__init__(self)
        self.name = "Task-{0}".format(index + 1)
        self.app = app
        self.index = index
        self.task = task

        self.skips = 0
        self.failures = 0
        self.task_error = False
        self.summary_status = []
        self.reporter_args = []

    def run(self):
        # Create a temporary handler for the reporter class
        reporter = Reporter(self.app.opts.verbosity - self.app.opts.quietness)

        def handler(message, kind, level, prefix, clip):
            self.reporter_args.append((message, kind, level, prefix, clip))

        reporter.event_handler = handler
        self.task.reporter = reporter

        # Report the name of the task and a banner line to aid readability.
        self.app.titlebar("Running task #{0}".format(self.index + 1), reporter)
        reporter("Method: {0}".format(self.task.options["full_task_name"]))
        reporter(
            "Thread ID {0} starting at {1}".format(self.ident, timestamp())
        )

        # Since the run_analysis method is out of rose's control in many
        # cases the safest thing to do is a blanket try/except; since we
        # have no way of knowing what exceptions might be raised.
        try:
            self.task.run_analysis()
            # In the case that the task didn't raise any exception,
            # we can now check whether it passed or failed.
            if self.task.passed:
                msg = "Task #{0} passed at {1}".format(
                    self.index + 1, timestamp()
                )
                self.summary_status.append(
                    (
                        "{0} ({1})".format(
                            msg, self.task.options["full_task_name"]
                        ),
                        self.app._prefix_pass,
                    )
                )
                reporter(msg, prefix=self.app._prefix_pass)
            elif self.task.skipped:
                self.skips = 1
                msg = "Task #{0} skipped by method".format(self.index + 1)
                self.summary_status.append(
                    (
                        "{0} ({1})".format(
                            msg, self.task.options["full_task_name"]
                        ),
                        self.app._prefix_skip,
                    )
                )
                reporter(msg, prefix=self.app._prefix_skip)
            else:
                self.failures = 1
                msg = "Task #{0} did not pass at {1}".format(
                    self.index + 1, timestamp()
                )
                self.summary_status.append(
                    (
                        "{0} ({1})".format(
                            msg, self.task.options["full_task_name"]
                        ),
                        self.app._prefix_fail,
                    )
                )
                reporter(msg, prefix=self.app._prefix_fail)
        except Exception:
            # If an exception was raised, print a traceback and treat it
            # as a failure.
            self.task_error = True
            self.failures = 1
            msg = "Task #{0} encountered an error at {1}".format(
                self.index + 1, timestamp()
            )
            self.summary_status.append(
                (
                    "{0} ({1})".format(
                        msg, self.task.options["full_task_name"]
                    ),
                    self.app._prefix_fail,
                )
            )
            reporter(msg + " (see stderr)", prefix=self.app._prefix_fail)
            exception = traceback.format_exc()
            reporter(msg, prefix=self.app._prefix_fail, kind=reporter.KIND_ERR)
            reporter(
                exception, prefix=self.app._prefix_fail, kind=reporter.KIND_ERR
            )


class RoseAnaApp(BuiltinApp):

    """Run rosa ana as an application."""

    SCHEME = "rose_ana"
    _prefix_pass = "[ OK ] "
    _prefix_skip = "[SKIP] "
    _prefix_fail = "[FAIL] "
    _printbar_width = 80

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """Implement the "rose ana" command"""
        # Initialise properties which will be needed later.
        self._task = app_runner.suite_engine_proc.get_task_props()
        self.task_name = self._task.task_name
        self.opts = opts
        self.args = args
        self.config = conf_tree.node
        self.app_runner = app_runner

        # Attach to the main rose config (for retrieving settings from
        # things like the user's ~/.metomi/rose.conf)
        self.rose_conf = ResourceLocator.default().get_conf()

        # Attach to a reporter instance for sending messages.
        self._init_reporter(app_runner.event_handler)

        # As part of the introduction of a re-written rose_ana,
        # backwards compatibility is maintained here by detecting the lack of
        # the newer syntax in the app config and falling back to the old
        # version of the rose_ana app (renamed to rose_ana_v1)
        # **Once the old behaviour is removed the below block can be too**.
        new_style_app = False
        for keys, _ in self.config.walk(no_ignore=True):
            task = keys[0]
            if task.startswith("ana:"):
                new_style_app = True
                break
        if not new_style_app:
            # Use the previous app by instantiating and calling it explicitly
            self.reporter(
                "!!WARNING!! - Detected old style rose_ana app; "
                "Using previous rose_ana version..."
            )
            from metomi.rose.apps.rose_ana_v1 import RoseAnaV1App

            old_app = RoseAnaV1App(manager=self.manager)
            return old_app.run(
                app_runner, conf_tree, opts, args, uuid, work_files
            )

        # Load any rose_ana specific configuration settings either from
        # the site defaults or the user's personal config
        self._get_global_ana_config()

        # If the user's config indicates that it should be used - attach
        # to the KGO database instance in case it is needed later.
        use_kgo = self.ana_config.get("kgo-database", ".false.")
        self.kgo_db = None
        if use_kgo == TYPE_LOGICAL_VALUE_TRUE:
            self.kgo_db = KGODatabase()
            self.kgo_db.enter_task(
                self.task_name, self.kgo_db.TASK_STATUS_RUNNING
            )
            self.titlebar("Initialising KGO database")
            self.kgo_db.buffer_to_db(self.reporter)

        self.titlebar("Launching rose_ana")

        # Load available methods for analysis and the tasks in the app.
        self._load_analysis_modules()
        self._load_analysis_methods()
        self._load_tasks()

        # Get the number of desired threads from the ana config (if set).
        # If this is not set or set to 1 then fall back to the old behaviour
        # and don't use threads at all
        n_threads = int(self.ana_config.get("threads", 1))

        if n_threads == 1:
            self.reporter("Running in SERIAL mode")
            # Single threaded case - run the tasks in serial
            number_of_failures = 0
            number_of_skips = 0
            task_error = False
            summary_status = []
            for itask, task in enumerate(self.analysis_tasks):
                # Report the name of the task and a banner line to aid
                # readability
                self.titlebar("Running task #{0}".format(itask + 1))
                self.reporter(
                    "Method: {0}".format(task.options["full_task_name"])
                )

                # Since the run_analysis method is out of rose's control in
                # many cases the safest thing to do is a blanket try/except;
                # since we have no way of knowing what exceptions might be
                # raised.
                try:
                    task.run_analysis()
                    # In the case that the task didn't raise any exception,
                    # we can now check whether it passed or failed.
                    if task.passed:
                        msg = "Task #{0} passed at {1}".format(
                            itask + 1, timestamp()
                        )
                        summary_status.append(
                            (
                                "{0} ({1})".format(
                                    msg, task.options["full_task_name"]
                                ),
                                self._prefix_pass,
                            )
                        )
                        self.reporter(msg, prefix=self._prefix_pass)
                    elif task.skipped:
                        number_of_skips += 1
                        msg = "Task #{0} skipped by method".format(itask + 1)
                        summary_status.append(
                            (
                                "{0} ({1})".format(
                                    msg, task.options["full_task_name"]
                                ),
                                self._prefix_skip,
                            )
                        )
                        self.reporter(msg, prefix=self._prefix_skip)
                    else:
                        number_of_failures += 1
                        msg = "Task #{0} did not pass at {1}".format(
                            itask + 1, timestamp()
                        )
                        summary_status.append(
                            (
                                "{0} ({1})".format(
                                    msg, task.options["full_task_name"]
                                ),
                                self._prefix_fail,
                            )
                        )
                        self.reporter(msg, prefix=self._prefix_fail)

                except Exception:
                    # If an exception was raised, print a traceback and treat
                    # it as a failure.
                    task_error = True
                    number_of_failures += 1
                    msg = "Task #{0} encountered an error at {1}".format(
                        itask + 1, timestamp()
                    )
                    summary_status.append(
                        (
                            "{0} ({1})".format(
                                msg, task.options["full_task_name"]
                            ),
                            self._prefix_fail,
                        )
                    )
                    self.reporter(
                        msg + " (see stderr)", prefix=self._prefix_fail
                    )
                    exception = traceback.format_exc()
                    self.reporter(
                        msg,
                        prefix=self._prefix_fail,
                        kind=self.reporter.KIND_ERR,
                    )
                    self.reporter(
                        exception,
                        prefix=self._prefix_fail,
                        kind=self.reporter.KIND_ERR,
                    )

        elif n_threads > 1:
            self.reporter(
                "Running in THREADED mode, with {0} threads".format(n_threads)
            )
            # Multithreaded case
            # Create threading objects for each comparison task
            threads = []
            for itask, task in enumerate(self.analysis_tasks):
                threads.append(TaskRunner(self, itask, task))

            # Start threads within the set number of concurrent threads until
            # all have been started
            itask = 0
            running = []
            while itask < len(threads):
                if len(running) < n_threads:
                    self.reporter(
                        "Starting thread for task {0} at {1}".format(
                            itask + 1, timestamp()
                        )
                    )
                    running.append(threads[itask])
                    threads[itask].start()
                    itask += 1
                for thread in running:
                    if not thread.is_alive():
                        running.remove(thread)

            # Gather up the results
            number_of_failures = 0
            number_of_skips = 0
            task_error = False
            summary_status = []
            for thread in threads:
                # If any threads haven't finished yet make sure to wait
                thread.join()
                number_of_failures += thread.failures
                number_of_skips += thread.skips
                task_error = task_error or thread.task_error
                summary_status += thread.summary_status
                # And print the output via the main reporter
                for args in thread.reporter_args:
                    self.reporter(*args)

        else:
            # Negative threads?
            msg = "Number of threads given to rose_ana cannot be negative"
            raise ValueError(msg)

        # The KGO database (if needed by the task) also stores its status - to
        # indicate whether there was some unexpected exception above.
        if self.kgo_db is not None and not task_error:
            self.kgo_db.enter_task(
                self.task_name, self.kgo_db.TASK_STATUS_SUCCEEDED
            )
            self.titlebar("Updating KGO database")
            self.kgo_db.buffer_to_db(self.reporter)

        # Summarise the results of the tasks
        self.titlebar("Summary")
        for line, prefix in summary_status:
            self.reporter(line, prefix=prefix)

        # And a final 1-line summary
        total = len(summary_status)
        plural = {1: ""}

        prefix = self._prefix_pass
        passed = total - number_of_failures - number_of_skips
        msg = "{0} Task{1} Passed".format(passed, plural.get(passed, "s"))

        if number_of_failures > 0:
            msg += ", {0} Task{1} Failed".format(
                number_of_failures, plural.get(number_of_failures, "s")
            )
            prefix = self._prefix_fail

        if number_of_skips > 0:
            msg += ", {0} Task{1} Skipped".format(
                number_of_skips, plural.get(number_of_skips, "s")
            )

        msg += " (of {0} processed)".format(total)
        self.titlebar("Final status")
        self.reporter(msg, prefix=prefix)

        self.titlebar("Completed rose_ana")

        # Finally if there were legitimate test failures raise an exception
        # so that the task is caught by cylc as failed.  Also fail if it looks
        # like every single task has been skipped
        if number_of_failures > 0 or number_of_skips == total:
            raise TestsFailedException(number_of_failures)

    def titlebar(self, title, reporter=None):
        if reporter is None:
            reporter = self.reporter
        sidebarlen = (self._printbar_width - len(title) + 1) / 2 - 1
        reporter("{0} {1} {0}".format("*" * int(sidebarlen), title))

    def _get_global_ana_config(self):
        """Retrieves all rose_ana config options; these could be from
        the site's settings or the user's personal settings."""
        self.ana_config = {}
        user_config = self.rose_conf.get_value(["rose-ana"])
        if user_config is not None:
            for name, obj in user_config.items():
                if obj.state == "":
                    self.ana_config[name] = obj.value

    def _init_reporter(self, reporter=None):
        """Attach a reporter instance to the class."""
        if reporter is None:
            self.reporter = Reporter(self.opts.verbosity - self.opts.quietness)
        else:
            self.reporter = reporter

    def _load_analysis_modules(self):
        """Populate the list of modules containing analysis methods."""
        # Find the possible paths that could contain modules
        method_paths = self._get_method_paths()

        # Report the paths that were found
        self.reporter("Method module search-paths:")
        for path in method_paths:
            self.reporter(" * {0}".format(path))

        self.modules = set([])
        for path in method_paths:
            # Add the method path to the start of the sys.path
            sys.path.insert(0, os.path.abspath(path))
            for filename in glob.glob(os.path.join(path, "*.py")):
                # Find python files and attempt to import them; if a module
                # fails to import report it but don't crash (the module may
                # not actually be needed by this task)
                module_name = os.path.splitext(os.path.basename(filename))[0]
                try:
                    self.modules.add(__import__(module_name))
                except ImportError:
                    # Note: We intentionally don't re-raise the exception
                    # here, as we want to avoid a single mistake in a user
                    # supplied method bringing down the entire task
                    msg = "Failed to import module: {0} ".format(module_name)
                    self.reporter(
                        msg, prefix="[WARN] ", kind=self.reporter.KIND_ERR
                    )
                    exception = traceback.format_exc().split("\n")
                    for line in exception:
                        self.reporter(
                            line,
                            prefix="[WARN]   ",
                            kind=self.reporter.KIND_ERR,
                        )

            # Remove the method path from the sys.path
            sys.path.pop(0)
        self.modules = list(self.modules)
        self.modules.sort(key=str)

        # Report the modules which were loaded
        self.reporter("Method modules loaded:")
        for module in self.modules:
            self.reporter(" * {0}".format(module))

    def _load_analysis_methods(self):
        """Populate the list of analysis methods."""
        self.methods = {}
        for module in self.modules:
            module_name = module.__name__
            method_classes = inspect.getmembers(module, inspect.isclass)
            for method_class_name, method_class in method_classes:
                if hasattr(method_class, "run_analysis"):
                    name = ".".join([module_name, method_class_name])
                    self.methods[name] = method_class

        # Report the methods which were loaded
        self.reporter("Methods available:")
        for method in sorted(self.methods):
            self.reporter(" * {0}".format(method))

    def _load_tasks(self):
        """Populate the list of analysis tasks from the app config."""
        # Fill a dictionary of tasks and extract their options and values
        # - skipping any which are user/trigger-ignored
        _tasks = {}
        for keys, node in self.config.walk(no_ignore=True):
            task = keys[0]
            if task.startswith("ana:"):
                # Capture the options only and save them to the tasks dict
                task = task.split(":", 1)[1]
                if len(keys) == 2:

                    # The app may define a section containing rose_ana
                    # config settings; add these to the config dictionary (if
                    # any) of the names match existing config options from the
                    # global config it will be overwritten)
                    if task == "config":
                        # Process any environment variables first
                        value = env_var_process(node.value)
                        self.ana_config[keys[1]] = value
                        continue

                    _tasks.setdefault(task, {})
                    # If the value contains newlines, split it into a list
                    # and either way remove any quotation marks and process
                    # any environment variables
                    value = env_var_process(node.value)
                    values = value.split("\n")
                    for ival, value in enumerate(values):
                        values[ival] = re.sub(
                            r"^((?:'|\")*)(.*)(\1)$", r"\2", value
                        )

                    # If the user passed a blank curled-braces expression
                    # it should be expanded to contain each of the arguments
                    # passed to rose_ana
                    new_values = []
                    for value in values:
                        if "{}" in value:
                            if self.args is not None and len(self.args) > 0:
                                for arg in self.args:
                                    new_values.append(value.replace("{}", arg))
                            else:
                                new_values.append(value)
                        else:
                            new_values.append(value)
                    values = new_values

                    if len(values) == 1:
                        values = values[0]
                    _tasks[task][keys[1]] = values

        # Can now populate the output task list with analysis objects
        self.analysis_tasks = []
        for name in sorted(_tasks.keys()):
            options = _tasks[name]
            options["full_task_name"] = name
            # Create an analysis object for each task, passing through
            # all options given to the section in the app, the given name
            # starts with the comparison type and then optionally a
            # name/description, extract this here
            match = re.match(r"(?P<atype>[\w\.]+)(?:\((?P<descr>.*)\)|)", name)
            if match:
                options["description"] = match.group("descr")
                atype = match.group("atype")

            # Assuming this analysis task has been loaded by the app, create
            # an instance of the task, passing the options to it
            if atype in self.methods:
                self.analysis_tasks.append(self.methods[atype](self, options))
            else:
                # If the analysis type isn't matched by one of the loaded
                # methods, report the error and return a placeholder
                # in its place (so that this tasks' main method can show
                # the task as "failed")
                msg = "Unrecognised analysis type: {0}"
                self.reporter(msg.format(atype), prefix="[FAIL]   ")
                # Create a simple object to return - when the run_analysis
                # method is called by the main loop it will simply raise
                # an exception, triggering the "error" trap

                class Dummy(AnalysisTask):
                    def run_analysis(self):
                        raise ImportError(msg.format(atype))

                self.analysis_tasks.append(Dummy(self, options))

    def _get_method_paths(self):
        """Create a listing of paths for analysis methods."""
        # Setup the return list - the order of preference is earliest-first,
        # allowing methods to be overridden if sharing the same namespace
        method_paths = []

        # The app may defines an "ana" directory specific to the app
        app_dir_var = "ROSE_TASK_APP"
        suite_dir = os.environ["ROSE_SUITE_DIR"]
        if app_dir_var not in os.environ:
            app_dir_var = "ROSE_TASK_NAME"
        app_dir = os.path.join(
            suite_dir, "app", os.environ[app_dir_var], "ana"
        )
        if os.path.exists(app_dir):
            method_paths.append(app_dir)

        # The suite can have an "ana" directory which the apps may use
        ana_dir = os.path.join(suite_dir, "ana")
        if os.path.exists(ana_dir):
            method_paths.append(ana_dir)

        # The rose config can specify a directory for site-specific
        # methods
        config_paths = self.rose_conf.get_value(["rose-ana", "method-path"])
        if config_paths:
            for config_dir in config_paths.split():
                if os.path.exists(config_dir):
                    method_paths.append(config_dir)

        # Finally there are some built-in methods within Rose itself
        method_paths.append(
            os.path.join(os.path.dirname(__file__), "ana_builtin")
        )

        return method_paths


class TestsFailedException(Exception):

    """Exception raised if any rose-ana comparisons fail."""

    def __init__(self, num_failed):
        self.failed = num_failed

    def __repr__(self):
        msg = "{0} test{1} did not pass".format(
            self.failed, {1: ""}.get(self.failed, "s")
        )
        return msg

    __str__ = __repr__
