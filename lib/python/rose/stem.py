# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
"""Implementation of 'rose stem'"""

import os
import re
import sys

from rose.fs_util import FileSystemUtil
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Reporter, Event
from rose.suite_run import SuiteRunner

DEFAULT_TEST_DIR = 'rose-stem'
OPTIONS = ['group', 'source', 'task', ]
SUITE_RC_PREFIX = '[jinja2:suite.rc]'


class ConfigVariableSetEvent(Event):

   """Event to report a particular variable has been set."""

   LEVEL = Event.V

   def __repr__(self):
       return "Variable %s set to %s"%(self.args[0], self.args[1])

   __str__ = __repr__


class ConfigSourceTreeSetEvent(Event):

   """Event to report a source tree for config files."""

   LEVEL = Event.V

   def __repr__(self):
       return "Using config files from source %s"%(self.args[0])

   __str__ = __repr__


class ProjectNotFoundException(Exception):

    """Exception class when unable to determine project a source belongs to."""

    def __init__(self, source, error=None):
        self.source = source
        self.error = error

    def __repr__(self):
        if self.error is not None:
            return "Cannot ascertain project for source tree %s:\n%s"%(
                      self.source, self.error)
        else:
            return "Cannot ascertain project for source tree %s"%(
                    self.source)

    __str__ = __repr__


class RoseSuiteConfNotFoundException(Exception):

    """Exception class when unable to find rose-suite.conf."""

    def __init__(self, location):
        self.location = location

    def __repr__(self):
        if os.path.isdir(self.location):
            return "\nCannot find a suite to run in directory %s"%(
                    self.location)
        else:
            return "\nSuite directory %s is not a valid directory"%(
                    self.location)

    __str__ = __repr__


class SourceTreeAddedAsBranchEvent(Event):

   """Event to report a source tree has been added as a branch."""

   LEVEL = Event.DEFAULT

   def __repr__(self):
       return "Source tree %s added as branch"%(self.args[0])

   __str__ = __repr__


class SourceTreeAddedAsTrunkEvent(Event):

   """Event to report a source tree has been added as a trunk."""

   LEVEL = Event.DEFAULT

   def __repr__(self):
       return "Source tree %s added as trunk"%(self.args[0])

   __str__ = __repr__


class SuiteSelectionEvent(Event):

   """Event to report a source tree for config files."""

   LEVEL = Event.DEFAULT

   def __repr__(self):
       return "Will run suite from %s"%(self.args[0])

   __str__ = __repr__


class StemRunner(object):

    """Set up options for running a STEM job through Rose."""

    def __init__(self, opts, reporter=None, popen=None, fs_util=None):
        self.opts = opts
        if reporter is None:
            self.reporter = Reporter(opts.verbosity - opts.quietness)
        else:
            self.reporter = reporter
        if popen is None:
            self.popen = RosePopener(event_handler = self.reporter)
        else:
            self.popen = popen
        if fs_util is None:
            self.fs_util = FileSystemUtil(event_handler = self.reporter)
        else:
            self.fs_util = fs_util

    def _add_define_option(self, var, val):
        """Add a define option passed to the SuiteRunner."""

        if self.opts.defines:
            self.opts.defines.append(SUITE_RC_PREFIX + var + '=' + val )
        else:
            self.opts.defines= [ SUITE_RC_PREFIX + var + '=' + val ]
        self.reporter(ConfigVariableSetEvent(var, val))
        return

    def _get_base_dir(self, item):
        """Given a source tree return the following from 'fcm loc-layout':
           * url
           * sub_tree
           * peg_rev
           * root
           * project
        """
        
        
        rc, output, stderr = self.popen.run('fcm', 'loc-layout', item)
        if rc != 0:
            raise ProjectNotFoundException(item, stderr)

        ret = {}
        for line in output.splitlines():
            if not ":" in line:
              continue
            key, value = line.split(":", 1)
            if key:
                if value:
                    ret[key] = value.strip()

        return ret

    def _get_project_from_url(self, source_dict):
        """Run 'fcm keyword-print' to work out the project name."""

        repo = source_dict['root']
        if source_dict['project']:
            repo += '/' + source_dict['project']

        rc, kpoutput, stderr = self.popen.run('fcm', 'kp', source_dict['url'])

        project = None
        for line in kpoutput.splitlines():
            if line.rstrip().endswith(repo):
                kpresult = re.search(r'^location{primary}\[(.*)\]', line)
                if kpresult:
                    project = kpresult.group(1)
                    break
        return project

    def _ascertain_project(self, item):
        """Set the project name and top-level from 'fcm loc-layout'.
        Returns:
            * project name
            * top-level location of the source tree with revision number
            * top-level location of the source tree without revision number
            * revision number
        """

        project = ''
        if re.search(r'^\.', item):
            item = os.path.abspath(os.path.join(os.getcwd(), item))

        source_dict =  self._get_base_dir(item)
        project = self._get_project_from_url(source_dict)

        if not project:
            raise ProjectNotFoundException(item)

        if 'peg_rev' in source_dict and '@' in item:
            revision = '@' + source_dict['peg_rev']
            base = re.sub(r'@.*', r'', item)
        else:
            revision = ''
            base = item    

        # Remove subtree from base and item
        if 'sub_tree' in source_dict:
            item = item.replace(source_dict['sub_tree'], '', 1)
            base = base.replace(source_dict['sub_tree'], '', 1)

        # Remove trailing forwards-slash
        item = re.sub(r'/$',r'',item)
        base = re.sub(r'/$',r'',base)

        return project, item, base, revision

    def _generate_name(self):
        """Generate a suite name from the name of the first source tree."""
        dummy, basedir, dummy2, dummy3 = self._ascertain_project(os.getcwd())
        name = os.path.basename(basedir)
        return name

    def _this_suite(self):
        """Find the location of the suite in the first source tree."""

        # Get base of first source
        basedir = ''
        if self.opts.source:
            basedir = self.opts.source[0]
        else:
            dummy, basedir, dum2, dum3 = self._ascertain_project(os.getcwd())

        suitedir = os.path.join(basedir, DEFAULT_TEST_DIR)
        suitefile = os.path.join(suitedir, "rose-suite.conf")

        if not os.path.isfile(suitefile):
            raise RoseSuiteConfNotFoundException(suitedir)
        return suitedir

    def process(self):
        """Process STEM options into 'rose suite-run' options."""

        # Generate options for source trees
        repos = {}
        if not self.opts.source:
            self.opts.source = ['.']
        self.opts.project = list()

        for i, url in enumerate(self.opts.source):
            project, url, base, rev = self._ascertain_project(url)
            self.opts.source[i] = url
            self.opts.project.append(project)
            if project in repos:
                repos[project].append(url)
            else:
                repos[project] = [ url ]
                self._add_define_option('SOURCE_' + project.upper() + '_REV', 
                                        '"' + rev + '"')
                self._add_define_option('SOURCE_' + project.upper() + '_BASE', 
                                        '"' + base + '"')
            self.reporter(SourceTreeAddedAsBranchEvent(url))
        for project, branches in repos.iteritems():
            var = 'SOURCE_' + project.upper()
            branchstring = RosePopener.list_to_shell_str(branches)
            self._add_define_option(var, '"' + branchstring + '"')

        # Generate the variable containing tasks to run
        if self.opts.group:
            if not self.opts.defines:
                self.opts.defines = []
            self.opts.defines.append(SUITE_RC_PREFIX + 'RUN_NAMES=' +
                                     str(self.opts.group))

        # Change into the suite directory
        if self.opts.conf_dir:
            self.fs_util.chdir(self.opts.conf_dir)
            self.reporter(SuiteSelectionEvent(self.opts.conf_dir))
        else:
            thissuite = self._this_suite()
            self.fs_util.chdir(thissuite)
            self.opts.conf_dir = thissuite
            self.reporter(SuiteSelectionEvent(thissuite))

        # Create a default name for the suite; allow override by user
        if not self.opts.name:
            self.opts.name = self._generate_name()

        return self.opts


def main():
    """Launcher for command line invokation of rose stem."""

    # Process options
    opt_parser = RoseOptionParser()

    option_keys = SuiteRunner.OPTIONS + OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args()

    # Set up a runner instance and process the options
    stem = StemRunner(opts)
    if opts.debug_mode:
        opts = stem.process()
    else:
        try:
            opts = stem.process()
        except Exception as e:
            stem.reporter(e)
            sys.exit(1)

    # Get the suiterunner object and execute
    runner = SuiteRunner(event_handler=stem.reporter,
                         popen=stem.popen,
                         fs_util=stem.fs_util)
    if opts.debug_mode:
        sys.exit(runner(opts, args))
    try:
        sys.exit(runner(opts, args))
    except Exception as e:
        runner.handle_event(e)
        if isinstance(e, RosePopenError):
            sys.exit(e.rc)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
