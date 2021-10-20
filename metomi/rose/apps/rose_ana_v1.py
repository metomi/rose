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
import glob
import inspect
import os
import re
import sqlite3
import sys
import time

# Rose modules
from metomi.rose.app_run import BuiltinApp
import metomi.rose.config
from metomi.rose.env import env_var_process
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Event, Reporter
from metomi.rose.resource import ResourceLocator

WARN = -1
PASS = 0
FAIL = 1

MAX_KGO_FILES = 100

OPTIONS = ["method_path"]

USRCOMPARISON_DIRNAME = "comparisons"
USRCOMPARISON_EXT = ".py"


class KGODatabase:
    """
    KGO Database object, stores comparison information for rose_ana apps.
    """

    # Stores retries of database creation and the maximum allowed number
    # of retries before an exception is raised
    RETRIES = 0
    MAX_RETRIES = 5

    def __init__(self):
        "Initialise the object."
        self.file_name = os.path.join(
            os.getenv("ROSE_SUITE_DIR"), "log", "rose-ana-comparisons.db"
        )
        self.conn = None
        self.create()

    def get_conn(self):
        "Return a connection to the database if it exists."
        if self.conn is None:
            self.conn = sqlite3.connect(self.file_name, timeout=60.0)
        return self.conn

    def create(self):
        "If the database doesn't exist, create it."
        conn = self.get_conn()
        # This SQL command ensures a "comparisons" table exists in the database
        # and then populates it with a series of columns (which in this case
        # are all storing strings/text). The primary key is the comparison name
        # (as it must uniquely identify each row)
        sql_statement = """
            CREATE TABLE IF NOT EXISTS comparisons (
            app_task TEXT,
            kgo_file TEXT,
            suite_file TEXT,
            status TEXT,
            comparison TEXT,
            PRIMARY KEY(app_task))
            """
        self.execute_sql_retry(conn, (sql_statement,))
        # This SQL command ensures a "tasks" table exists in the database
        # and then populates it with a pair of columns (the task name and
        # a completion status indicator). The primary key is the task name
        # (as it must uniquely identify each row)
        sql_statement = """
            CREATE TABLE IF NOT EXISTS tasks (
            task_name TEXT,
            completed INT,
            PRIMARY KEY(task_name))
            """
        self.execute_sql_retry(conn, (sql_statement,))
        conn.commit()

    def execute_sql_retry(self, conn, sql_args, retries=10, timeout=5.0):
        """
        Given a connection object and a tuple of the desired arguments;
        calls sql execute and retries multiple times, to handle
        concurrency issues

        """
        for _ in range(retries):
            try:
                conn.execute(*sql_args)
                return
            except sqlite3.Error:
                time.sleep(timeout)
        # In the event that the retries are exceeded, re-raise the final
        # exception for the calling application to handle
        raise

    def enter_comparison(
        self, app_task, kgo_file, suite_file, status, comparison
    ):
        "Insert a new comparison entry to the database."
        conn = self.get_conn()
        # This SQL command indicates that a single "row" is to be entered into
        # the "comparisons" table
        sql_statement = (
            "INSERT OR REPLACE INTO comparisons VALUES (?, ?, ?, ?, ?)"
        )
        sql_args = [app_task, kgo_file, suite_file, status, comparison]
        self.execute_sql_retry(conn, (sql_statement, sql_args))

        conn.commit()

    def enter_task(self, app_task, status):
        "Insert a new task entry to the database."
        conn = self.get_conn()
        # This SQL command indicates that a single "row" is to be entered into
        # the "tasks" table
        sql_statement = "INSERT OR REPLACE INTO tasks VALUES (?, ?)"
        sql_args = [app_task, status]
        self.execute_sql_retry(conn, (sql_statement, sql_args))

        conn.commit()


class RoseAnaV1App(BuiltinApp):

    """Run rosa ana as an application."""

    # SCHEME = "rose_ana_v1"

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """Implement the "rose ana" command"""
        # Get config file option for user-specified method paths
        method_paths = [
            os.path.join(os.path.dirname(__file__), USRCOMPARISON_DIRNAME)
        ]
        conf = ResourceLocator.default().get_conf()

        my_conf = conf.get_value(["rose-ana", "method-path"])
        if my_conf:
            for item in my_conf.split():
                method_paths.append(item)

        # Initialise the analysis engine
        engine = Analyse(
            conf_tree.node,
            opts,
            args,
            method_paths,
            reporter=app_runner.event_handler,
            popen=app_runner.popen,
        )

        # Initialise a database session
        rose_ana_task_name = os.getenv("ROSE_TASK_NAME")
        kgo_db = KGODatabase()

        # Add an entry for this task, with a non-zero status code
        kgo_db.enter_task(rose_ana_task_name, 1)

        # Run the analysis
        num_failed, tasks = engine.analyse()

        # Update the database to indicate that the task succeeded
        kgo_db.enter_task(rose_ana_task_name, 0)

        # Update the database
        for task in tasks:
            # The primary key in the database is composed from both the
            # rose_ana app name and the task index (to make it unique)
            app_task = "{0} ({1})".format(rose_ana_task_name, task.name)
            # Include an indication of what extract/comparison was performed
            comparison = "{0} : {1} : {2}".format(
                task.comparison, task.extract, getattr(task, "subextract", "")
            )
            kgo_db.enter_comparison(
                app_task,
                task.kgo1file,
                task.resultfile,
                task.userstatus,
                comparison,
            )

        if num_failed != 0:
            raise TestsFailedException(num_failed)


class DataLengthError(Exception):

    """An exception if KGO and result data are of different lengths."""

    def __init__(self, task):
        self.resultlen = len(task.resultdata)
        self.kgolen = len(task.kgo1data)
        self.taskname = task.name

    def __repr__(self):
        return "Mismatch in data lengths in %s (%s and %s)" % (
            self.taskname,
            self.resultlen,
            self.kgolen,
        )

    __str__ = __repr__


class TaskCompletionEvent(Event):

    """Event for completing a comparison from AnalysisTask."""

    def __init__(self, task):
        self.message = task.message
        self.userstatus = task.userstatus
        self.level = Event.DEFAULT
        self.kind = Event.KIND_OUT

    def __repr__(self):
        return " %s" % (self.message)

    __str__ = __repr__


class TestsFailedException(Exception):

    """Exception raised if any rose-ana comparisons fail."""

    def __init__(self, num_failed):
        self.ret_code = num_failed

    def __repr__(self):
        return "%s tests did not pass" % (self.ret_code)

    __str__ = __repr__


class Analyse:

    """A comparison engine for Rose."""

    def __init__(
        self, config, opts, args, method_paths, reporter=None, popen=None
    ):
        if reporter is None:
            self.reporter = Reporter(opts.verbosity - opts.quietness)
        else:
            self.reporter = reporter
        if popen is None:
            self.popen = RosePopener(event_handler=self.reporter)
        else:
            self.popen = popen
        self.opts = opts
        self.args = args
        self.config = config
        self.tasks = self.load_tasks()
        modules = []
        for path in method_paths:
            for filename in glob.glob(path + "/*.py"):
                modules.append(filename)
        self.load_user_comparison_modules(modules)

    def analyse(self):
        """Perform comparisons given a list of tasks."""
        ret_code = 0
        for task in self.tasks:

            if self.check_extract(task):
                # Internal AnalysisEngine extract+comparison test

                # Extract data from results and from kgoX
                task = self.do_extract(task, "result")

                for i in range(task.numkgofiles):
                    var = "kgo" + str(i + 1)
                    task = self.do_extract(task, var)

                task = self.do_comparison(task)
            else:
                # External program(s) doing test

                # Command to run
                command = task.extract

                result = re.search(r"\$file", command)
                # If the command contains $file, it is run separately for both
                # the KGO and the result files
                if result:
                    # Replace $file token with resultfile or kgofile
                    resultcommand = self._expand_tokens(
                        command, task, "result"
                    )
                    kgocommand = self._expand_tokens(command, task, "kgo1")

                    # Run the command on the resultfile
                    task.resultdata = self._run_command(resultcommand)

                    # Run the command on the KGO file
                    task.kgo1data = self._run_command(kgocommand)
                else:
                    # The command works on both files at the same time
                    # Replace tokens $kgofile and $resultfile for actual values
                    command = self._expand_tokens(command, task)

                    # Run the command
                    task.resultdata = self._run_command(command)

                # Run the comparison
                task = self.do_comparison(task)

            self.reporter(
                TaskCompletionEvent(task), prefix="[%s]" % (task.userstatus)
            )
            if task.numericstatus != PASS:
                ret_code += 1
        return ret_code, self.tasks

    def check_extract(self, task):
        """Check if an extract name is present in a user method."""
        for _, class_name, _, _ in self.user_methods:
            if task.extract == class_name:
                return True
        return False

    def do_comparison(self, task):
        """Run the comparison."""
        for module_name, class_name, _, _ in self.user_methods:
            if task.comparison == class_name:
                for module in self.modules:
                    if module.__name__ == module_name:
                        comparison_inst = getattr(module, class_name)()
                        getattr(comparison_inst, "run")(task)
        return task

    def do_extract(self, task, var):
        """Extract the specified data."""
        for module_name, class_name, _, _ in self.user_methods:
            if task.extract == class_name:
                for module in self.modules:
                    if module.__name__ == module_name:
                        extract_inst = getattr(module, class_name)()
                        getattr(extract_inst, "run")(task, var)
        return task

    def _run_command(self, command):
        """Run an external command using metomi.rose.popen."""
        output = self.popen.run_ok(command, shell=True)[0]
        output = "".join(output).splitlines()
        return output

    def _expand_tokens(self, inputstring, task, var=None):
        """Expands tokens $resultfile, $file and $kgoXfile."""
        filename = ''
        if var:
            filename = getattr(task, var + "file")
        expansions = {'resultfile': task.resultfile, 'file': filename}
        for i in range(1, task.numkgofiles + 1):
            key = "kgo" + str(i) + "file"
            value = getattr(task, key)
            expansions[key] = value
        inputstring = inputstring.format(**expansions)
        return inputstring

    def _find_file(self, var, task):
        """Finds a file given a variable name containing the filename.

        Given a variable name and task object, this returns the filename it
        points to, including expanding any * characters with glob.
        """

        filevar = var + "file"
        if hasattr(task, filevar):
            configvar = var + "fileconfig"
            setattr(task, configvar, getattr(task, filevar))
            filenames = glob.glob(env_var_process(getattr(task, filevar)))
            if len(filenames) > 0:
                setattr(task, filevar, os.path.abspath(filenames[0]))
        return task

    def load_tasks(self):
        """Loads AnalysisTasks from files.

        Given a list of files, return AnalysisTasks generated from those files.
        This also expands environment variables in filenames, but saves the
        original contents for use when writing out config files
        """

        tasks = []
        for task in self.config.value.keys():
            if task == "env":
                continue
            if task.startswith("file:"):
                continue
            newtask = AnalysisTask()
            newtask.name = task
            value = self.config.get_value([task, "resultfile"])

            # If the task is ignored, this will be None, so continue
            # on to the next task
            if value is None:
                continue

            if "{}" in value:
                newtask.resultfile = value.replace("{}", self.args[0])
            else:
                newtask.resultfile = value
            newtask = self._find_file("result", newtask)
            newtask.extract = self.config.get_value([task, "extract"])
            result = re.search(r":", newtask.extract)
            if result:
                newtask.subextract = ":".join(newtask.extract.split(":")[1:])
                newtask.extract = newtask.extract.split(":")[0]
            newtask.comparison = self.config.get_value([task, "comparison"])
            newtask.tolerance = env_var_process(
                self.config.get_value([task, "tolerance"])
            )
            newtask.warnonfail = self.config.get_value(
                [task, "warnonfail"]
            ) in ["yes", "true"]

            # Allow for multiple KGO, e.g. kgo1file, kgo2file, for
            # statistical comparisons of results
            newtask.numkgofiles = 0
            for i in range(1, MAX_KGO_FILES):
                kgovar = "kgo" + str(i)
                kgofilevar = kgovar + "file"
                if self.config.get([task, kgofilevar]):
                    value = self.config.get([task, kgofilevar])[:]
                    if "{}" in value:
                        setattr(
                            newtask,
                            kgofilevar,
                            value.replace("{}", self.args[0]),
                        )
                    else:
                        setattr(newtask, kgofilevar, value)
                    newtask.numkgofiles += 1
                    newtask = self._find_file(kgovar, newtask)
                else:
                    break
            tasks.append(newtask)
        return tasks

    def load_user_comparison_modules(self, files):
        """Import comparison modules and store them."""
        modules = []
        for filename in files:
            directory = os.path.dirname(filename)
            if not directory.endswith(
                USRCOMPARISON_DIRNAME
            ) or not filename.endswith(USRCOMPARISON_EXT):
                continue
            comparison_name = os.path.basename(filename).rpartition(
                USRCOMPARISON_EXT
            )[0]
            sys.path.insert(0, os.path.abspath(directory))
            try:
                modules.append(__import__(comparison_name))
            except ImportError as exc:
                self.reporter(exc)
            sys.path.pop(0)
        modules.sort(key=str)
        self.modules = modules

        user_methods = []
        for module in modules:
            comparison_name = module.__name__
            contents = inspect.getmembers(module, inspect.isclass)
            for obj_name, obj in contents:
                att_name = "run"
                if hasattr(obj, att_name) and callable(getattr(obj, att_name)):
                    doc_string = obj.__doc__
                    user_methods.append(
                        (comparison_name, obj_name, att_name, doc_string)
                    )
        self.user_methods = user_methods
        return user_methods

    def write_config(self, filename, tasks):
        """Write an analysis config file based on a list of tasks provided"""
        config = metomi.rose.config.ConfigNode()

        for task in tasks:
            sectionname = task.name
            if task.resultfileconfig:
                config.set([sectionname, "resultfile"], task.resultfileconfig)
            for i in range(1, task.numkgofiles + 1):
                origvar = "kgo" + str(i) + "fileconfig"
                valvar = "kgo" + str(i) + "file"
                if hasattr(task, origvar):
                    config.set([sectionname, valvar], getattr(task, origvar))
            if task.extract:
                config.set([sectionname, "extract"], task.extract)
            if task.subextract:
                config.set(
                    [sectionname, "extract"],
                    task.extract + ":" + task.subextract,
                )
            if task.comparison:
                config.set([sectionname, "comparison"], task.comparison)
            if task.tolerance:
                config.set([sectionname, "tolerance"], task.tolerance)
            if task.warnonfail:
                config.set([sectionname, "warnonfail"], "true")
        metomi.rose.config.dump(config, filename)


class AnalysisTask:

    """Class to completely describe an analysis task.

    Attributes:
        name                    # Short description of test for the user
        resultfile              # File generated by suite
        kgo1file                # Known Good output file
        comparison              # Comparison type
        extract                 # Extract method
        subextract              # Extract sub-type (if any)
        tolerance               # Tolerance (optional in file)
        warnonfail              # True if failure is just a warning
        numkgofiles             # Number of KGO files
        resultdata              # Data from result file
        kgo1data                # Data from KGO file
        good                    # True if test didn"t fail
        message                 # User message
        userstatus              # User status
        numericstatus           # Numeric status
    """

    def __init__(self):

        # Variables defined in config file
        self.name = None
        self.resultfile = None
        self.kgo1file = None
        self.comparison = None
        self.extract = None
        self.tolerance = None
        self.warnonfail = False
        self.numkgofiles = 0

        # Variables to save settings before environment variable expansion (for
        # writing back to config file, rerunning, etc)
        self.resultfileconfig = self.resultfile
        self.kgofileconfig = self.kgo1file

        # Data variables filled by extract methods
        self.resultdata = []
        self.kgo1data = []

        # Variables set by comparison methods
        self.good = False

        self.message = None
        self.userstatus = "UNTESTED"
        self.numericstatus = WARN

    # Methods for setting pass/fail/warn; all take an object of one of the
    # success/ failure/warning classes as an argument, which all have a
    # sensible user message as the string representation of them.
    def set_failure(self, message):
        """Sets the status of the task to "FAIL"."""

        if self.warnonfail:
            self.set_warning(message)
        else:
            self.good = False
            self.message = message
            self.userstatus = "FAIL"
            self.numericstatus = FAIL

    def set_pass(self, message):
        """Sets the status of the task to " OK "."""

        self.good = True
        self.message = message
        self.userstatus = " OK "
        self.numericstatus = PASS

    def set_warning(self, message):
        """Sets the status of the task to "WARN"."""

        self.good = True
        self.message = message
        self.userstatus = "WARN"
        self.numericstatus = WARN

    def __repr__(self):
        return "%s: %s" % (self.name, self.userstatus)

    __str__ = __repr__


def data_from_regexp(regexp, filename):
    """Returns a list of text matching a regexp from a given file."""
    numbers = []
    for line in open(filename):
        result = re.search(regexp, line)
        if result:
            numbers.append(result.group(1))
    return numbers
