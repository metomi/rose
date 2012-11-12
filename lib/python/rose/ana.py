# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
"""Implementation of 'rose ana', a comparison engine for Rose. """


# Standard Python modules
import glob
import inspect
import os
import re
import sys

# Rose modules
import rose.config
import rose.env
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Reporter, Event

WARN = -1
PASS = 0
FAIL = 1

OPTIONS = [ 'method_path' ]

USRCOMPARISON_DIRNAME = 'comparisons'
USRCOMPARISON_EXT = '.py'


class DataLengthError(Exception):

    """An exception if KGO and result data are of different lengths"""

    def __init__(self, task):
        self.resultlen = len(task.resultdata)
        self.kgolen = len(task.kgo1data)
        self.taskname = task.name

    def __repr__(self):
        return "Task '%s': Result data has length %s "%( 
            self.taskname, self.resultlen) + "but KGO data is of length %s"%(
            self.kgolen)
               
    __str__ = __repr__


class SystemCommandException(Exception):

    """Exception for failures running system commands."""
    
    def __init__(self, command, error):
        self.error = error
        self.command = command
        
    def __repr__(self):
        return "Problem running command '%s': %s"%(self.command, self.error)
      
    __str__ = __repr__


class TaskCompletionEvent(Event):

    """Event for completing a comparison from AnalysisTask."""
 
    def __init__(self, task):
        self.message = task.message
        self.userstatus = task.userstatus
        self.level = Event.DEFAULT
        self.type = Event.TYPE_OUT
        
    def __repr__(self):
        return "[%s] %s"%(self.userstatus, self.message)
        
    __str__ = __repr__


class Analyse(object):

    """A comparison engine for Rose."""

    def __init__(self, opts, reporter=None, popen=None):
        if reporter is None:
            self.reporter = Reporter(opts.verbosity - opts.quietness)
        else:
            self.reporter = reporter
        if popen is None:
            self.popen = RosePopener(event_handler = self.reporter)
        else:
            self.popen = popen
        self.opts = opts
        
        modules = []
        for path in self.opts.method_path:
            for filename in glob.glob(path + '/*.py'):
                modules.append(filename)
        self.load_user_comparison_modules(modules)

    def analyse(self):
        """Perform comparisons given a list of tasks."""
        rc = 0
        for task in self.tasks:  
            if self.check_extract(task):
            # Internal AnalysisEngine extract+comparison test

                # Extract data from results and from kgoX
                task = self.do_extract(task, "result")
                for i in range(1, task.numkgofiles + 1):
                    var = "kgo" + str(i)
                    task = self.do_extract(task, var)

                task = self.do_comparison(task)
            else:
            # External program(s) doing test

                # Command to run    
                command         = task.extract

                result = re.search(r"\$file", command)
                # If the command contains $file, it is run separately for both
                # the KGO and the result files
                if result:
                    # Replace $file token with resultfile or kgofile
                    resultcommand = self._expand_tokens(command, task, 
                                                        "result")
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
                
            self.reporter(TaskCompletionEvent(task))
            if task.numericstatus != PASS:
                rc += 1
        return rc, self.tasks

    def check_extract(self, task):
        """Check if an extract name is present in a user method."""
        for module_name, class_name, method, help in self.user_methods:
            if task.extract == class_name:
                return True
        return False

    def do_comparison(self, task):
        """Run the comparison."""
        for module_name, class_name, method, help in self.user_methods:
            comparison_name = ".".join([module_name, class_name])
            if task.comparison == class_name:
                for module in self.modules:
                    if module.__name__ == module_name:
                        comparison_inst = getattr(module, class_name)()
                        comparison_meth = getattr(comparison_inst, 'run')(task)
        return task    

    def do_extract(self, task, var):
        """Extract the specified data."""
        for module_name, class_name, method, help in self.user_methods:
            extract_name = ".".join([module_name, class_name])
            if task.extract == class_name:
                for module in self.modules:
                    if module.__name__ == module_name:
                        extract_inst = getattr(module, class_name)()
                        extract_meth = getattr(extract_inst, 'run')(task, var)
        return task

    def _run_command(self, command):
        """Run an external command using rose.popen."""
        rc, output, stderr = self.popen.run(command, shell=True)
        if rc != 0:
            raise SystemCommandException(command, stderr)
        output = "".join(output).splitlines()      
        return output

    def _expand_tokens(self, inputstring, task, var="none"):
        """Expands tokens $resultfile, $file and $kgoXfile."""
        # Replace result file
        inputstring    = re.sub(r"\$resultfile", task.resultfile, inputstring)

        # $kgofile should map to $kgo1file for backwards compatibility
        inputstring    = re.sub(r"\$kgofile", task.kgo1file, inputstring)

        # Do KGO files
        for i in range(1, task.numkgofiles + 1):
            var = "kgo" + str(i) + "file"
            token = "$" + var
            value = getattr(task, var)
            inputstring = re.sub(token, value, inputstring)

        result = re.search(r"\$file", inputstring)
        if result:
            filevar = var+"file"
            filename = getattr(task, filevar)
            inputstring    = re.sub(r"\$file", filename, inputstring)
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
            filenames = glob.glob(rose.env.env_var_process(getattr(task, 
                        filevar)))
            if len(filenames) > 0:
                setattr(task, filevar, filenames[0])
        return task

    def load_tasks(self, files):
        """Loads AnalysisTasks from files.

        Given a list of files, return AnalysisTasks generated from those files.
        This also expands environment variables in filenames, but saves the
        original contents for use when writing out config files
        """

        tasks = []
        for filename in files:
            config = rose.config.load(filename)
            for task in config.value.keys():
                newtask = AnalysisTask()
                newtask.name = task
                if config.get([task, "resultfile"]):
                    newtask.resultfile = config.get([task, "resultfile"])[:]
                    newtask = self._find_file("result", newtask)
                if config.get([task, "extract"]):
                    newtask.extract = config.get([task, "extract"])[:]
                if config.get([task,"comparison"]):
                    newtask.comparison = config.get([task, "comparison"])[:]
                if config.get([task, "tolerance"]):
                    newtask.tolerance = config.get([task, "tolerance"])[:]
                if config.get([task, "warnonfail"]):
                    value = config.get([task, "warnonfail"])[:]
                    if value.find("yes") > -1:
                        newtask.warnonfail = True
                    elif value.find("true") > -1:
                        newtask.warnonfail = True
                    else:
                        newtask.warnonfail = False

                # Allow for multiple KGO, e.g. kgo1file, kgo2file, for 
                # statistical comparisons of results
                for i in range(1, 100):
                    kgovar = "kgo" + str(i)
                    kgofilevar = kgovar + "file"
                    if config.get([task, kgofilevar]):
                        tempvar = config.get([task, kgofilevar])[:]
                        setattr(newtask, kgofilevar, tempvar)
                        newtask.numkgofiles += 1
                        newtask = self._find_file(kgovar, newtask)
                    else:
                        break
                tasks.append(newtask)
        self.tasks = tasks        
        return tasks

    def load_user_comparison_modules(self, files):
        """Import comparison modules and store them."""
        modules = []
        for filename in files:
            directory = os.path.dirname(filename)
            if (not directory.endswith(USRCOMPARISON_DIRNAME) or
                not filename.endswith(USRCOMPARISON_EXT)):
                continue
            comparison_name = os.path.basename(filename).rpartition(
                                USRCOMPARISON_EXT)[0]
            sys.path.append(os.path.abspath(directory))
            try:
                modules.append(__import__(comparison_name))
            except Exception as e:
                self.reporter(e)
            sys.path.pop()
        modules.sort()
        self.modules = modules

        user_methods = []
        for module in modules:
            comparison_name = module.__name__
            contents = inspect.getmembers(module)
            for obj_name, obj in contents:
                if not inspect.isclass:
                    continue
                att_name = 'run'
                if (hasattr(obj, att_name) and 
                    callable(getattr(obj,att_name))):
                    doc_string = obj.__doc__
                    user_methods.append((comparison_name, obj_name, att_name, 
                                        doc_string))
        self.user_methods = user_methods      
        return user_methods

    def write_config(self, filename, tasks):
        """Write an analysis config file based on a list of tasks provided"""
        config = rose.config.ConfigNode()

        for task in tasks:
            sectionname = task.name
            if task.resultfileconfig:
                config.set([sectionname, "resultfile"], task.resultfileconfig)
            for i in range(1, task.numkgofiles + 1):
                origvar = "kgo" + str(i) + "fileconfig"
                valvar  = "kgo" + str(i) + "file"
                if hasattr(task, origvar):
                    config.set([sectionname, valvar], getattr(task, origvar) )
            if task.extract:
                config.set([sectionname, "extract"], task.extract)
            if task.comparison:
                config.set([sectionname, "comparison"], task.comparison)
            if task.tolerance:
                config.set([sectionname,"tolerance"], task.tolerance)
            if task.warnonfail:
                config.set([sectionname, "warnonfail"], "true")
        rose.config.dump(config, filename)


class AnalysisTask(object):

    """Class completely describes an analysis task."""

    def __init__(self):

# Variables defined in config file  
        self.name = None            # Short description of test for the user
        self.resultfile = None      # File generated by suite
        self.kgofile = None         # Known Good output file
        self.comparison = None      # Comparison type
        self.extract = None         # Extract method
        self.tolerance = None       # Tolerance (optional in file)
        self.warnonfail = False     # True if failure is just a warning 
        self.numkgofiles = 0        # Number of KGO files for multiple KGO 
                                    # processing

# Variables to save settings before environment variable expansion (for 
# writing back to config file, rerunning, etc)
        self.resultfileconfig = self.resultfile
        self.kgofileconfig = self.kgofile

# Data variables filled by extract methods
        self.resultdata = []        # Data from result file
        self.kgo1data = []          # Data from KGO file

# Variables set by comparison methods
        self.ok = False             # True if test didn't fail (useful as 
                                    # logical on whether to continue or abort)
        self.message = None         # User message
        self.userstatus = "UNTESTED"# User status
        self.numericstatus = WARN   # Numeric status (-1 = warn, 
                                    #                  0 = pass, 
                                    #                  1 = fail)

# Methods for setting pass/fail/warn; all take an object of one of the 
# success/ failure/warning classes as an argument, which all have a sensible 
# user message as the string representation of them.
    def set_failure(self, message):
        """Sets the status of the task to 'FAIL'."""

        if self.warnonfail:
            self.set_warning(message)
        else:
            self.ok = False
            self.message = message
            self.userstatus = "FAIL"
            self.numericstatus = FAIL

    def set_pass(self, message):
        """Sets the status of the task to ' OK '"""

        self.ok = True
        self.message = message
        self.userstatus = " OK "
        self.numericstatus = PASS

    def set_warning(self, message):
        """Sets the status of the task to 'WARN'"""

        self.ok = True
        self.message = message
        self.userstatus = "WARN"    
        self.numericstatus = WARN

    def __repr__(self):
        return "%s: %s"%(self.name, self.userstatus)

    __str__ = __repr__


def data_from_regexp(regexp, filename):
    """Returns a list of text matching a regexp from a given file."""
    numbers = []
    for line in open(filename):
        result = re.search(regexp, line)
        if result:
            numbers.append(result.group(1))
    return numbers


def main():
    """Implement the "rose ana" command"""

    # Get config file option for user-specified method paths
    method_paths = [ os.path.join(os.getenv('ROSE_HOME'), 'lib', 'python',
                    'rose', USRCOMPARISON_DIRNAME) ]
    conf = rose.config.default_node()
    my_conf = conf.get(["rose-ana"], no_ignore=True)
    for key, node in sorted(my_conf.value.items()):
        if node.is_ignored() or key != "method-path":
            continue
        for item in node.value.split():
            method_paths.append(item)

    # Process options
    opt_parser = RoseOptionParser()
    option_keys = OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args()
    if opts.method_path:
        opts.method_path += method_paths
    else:
        opts.method_path = method_paths

    # Get filenames of .test files from command line
    # Maybe replace with proper options?
    files = args

    # Initialise the analysis engine
    engine = Analyse(opts)

    # Load analysis tasks from files
    engine.load_tasks(files)
    
    rc = 0
    # Run the analysis
    
    if opts.debug_mode:
        rc, tasks = engine.analyse()
    else:
        try:
            rc, tasks = engine.analyse()
        except Exception as e:
            engine.reporter(e)
            if rc == 0:
                rc = 1
            
    sys.exit(rc)

if __name__ == "__main__":
    main()
