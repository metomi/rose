# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
"""Implementation of 'rose stem'"""

import os
import re
import sys

import metomi.rose.config
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.host_select import HostSelector
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopener, RosePopenError
from metomi.rose.reporter import Reporter, Event
from metomi.rose.resource import ResourceLocator
from metomi.rose.suite_run import SuiteRunner

DEFAULT_TEST_DIR = 'rose-stem'
OPTIONS = ['group', 'source', 'task', ]
ROSE_STEM_VERSION = 1
SUITE_RC_PREFIX = '[jinja2:suite.rc]'


class ConfigVariableSetEvent(Event):

    """Event to report a particular variable has been set."""

    LEVEL = Event.V

    def __repr__(self):
        return "Variable %s set to %s" % (self.args[0], self.args[1])

    __str__ = __repr__


class ConfigSourceTreeSetEvent(Event):

    """Event to report a source tree for config files."""

    LEVEL = Event.V

    def __repr__(self):
        return "Using config files from source %s" % (self.args[0])

    __str__ = __repr__


class NameSetEvent(Event):

    """Event to report a name for the suite being set."""

    LEVEL = Event.V

    def __repr__(self):
        return "Suite is named %s" % (self.args[0])

    __str__ = __repr__


class ProjectNotFoundException(Exception):

    """Exception class when unable to determine project a source belongs to."""

    def __init__(self, source, error=None):
        Exception.__init__(self, source, error)
        self.source = source
        self.error = error

    def __repr__(self):
        if self.error is not None:
            return "Cannot ascertain project for source tree %s:\n%s" % (
                self.source, self.error)
        else:
            return "Cannot ascertain project for source tree %s" % (
                self.source)

    __str__ = __repr__


class RoseStemVersionException(Exception):

    """Exception class when running the wrong metomi.rose-stem version."""

    def __init__(self, version):
        Exception.__init__(self, version)
        if version is None:
            self.suite_version = "not metomi.rose-stem compatible"
        else:
            self.suite_version = "at version %s" % (version)

    def __repr__(self):
        return "Running metomi.rose-stem version %s but suite is %s" % (
            ROSE_STEM_VERSION, self.suite_version)

    __str__ = __repr__


class RoseSuiteConfNotFoundException(Exception):

    """Exception class when unable to find metomi.rose-suite.conf."""

    def __init__(self, location):
        Exception.__init__(self, location)
        self.location = location

    def __repr__(self):
        if os.path.isdir(self.location):
            return "\nCannot find a suite to run in directory %s" % (
                self.location)
        else:
            return "\nSuite directory %s is not a valid directory" % (
                self.location)

    __str__ = __repr__


class SourceTreeAddedAsBranchEvent(Event):

    """Event to report a source tree has been added as a branch."""

    LEVEL = Event.DEFAULT

    def __repr__(self):
        return "Source tree %s added as branch" % (self.args[0])

    __str__ = __repr__


class SourceTreeAddedAsTrunkEvent(Event):

    """Event to report a source tree has been added as a trunk."""

    LEVEL = Event.DEFAULT

    def __repr__(self):
        return "Source tree %s added as trunk" % (self.args[0])

    __str__ = __repr__


class SuiteSelectionEvent(Event):

    """Event to report a source tree for config files."""

    LEVEL = Event.DEFAULT

    def __repr__(self):
        return "Will run suite from %s" % (self.args[0])

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
            self.popen = RosePopener(event_handler=self.reporter)
        else:
            self.popen = popen
        if fs_util is None:
            self.fs_util = FileSystemUtil(event_handler=self.reporter)
        else:
            self.fs_util = fs_util
        self.host_selector = HostSelector(event_handler=self.reporter,
                                          popen=self.popen)

    def _add_define_option(self, var, val):
        """Add a define option passed to the SuiteRunner."""

        if self.opts.defines:
            self.opts.defines.append(SUITE_RC_PREFIX + var + '=' + val)
        else:
            self.opts.defines = [SUITE_RC_PREFIX + var + '=' + val]
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

        ret_code, output, stderr = self.popen.run('fcm', 'loc-layout', item)
        output = output.decode()
        if ret_code != 0:
            raise ProjectNotFoundException(item, stderr)

        ret = {}
        for line in output.splitlines():
            if ":" not in line:
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

        kpoutput = self.popen.run('fcm', 'kp', source_dict['url'])[1]

        project = None
        for line in kpoutput.splitlines():
            if line.rstrip().endswith(repo.encode('UTF-8')):
                kpresult = re.search(r'^location{primary}\[(.*)\]',
                                     line.decode())
                if kpresult:
                    project = kpresult.group(1)
                    break
        return project

    def _deduce_mirror(self, source_dict, project):
        """Deduce the mirror location of this source tree."""

        # Root location for project
        proj_root = source_dict['root'] + '/' + source_dict['project']

        # Swap project to mirror
        project = re.sub(r'\.x$', r'.xm', project)
        mirror_repo = "fcm:" + project

        # Generate mirror location
        mirror = re.sub(proj_root, mirror_repo, source_dict['url'])

        # Remove any sub-tree
        mirror = re.sub(source_dict['sub_tree'], r'', mirror)
        mirror = re.sub(r'/@', r'@', mirror)

        # Add forwards slash after .xm if missing
        if '.xm/' not in mirror:
            mirror = re.sub(r'\.xm', r'.xm/', mirror)
        return mirror

    def _ascertain_project(self, item):
        """Set the project name and top-level from 'fcm loc-layout'.
        Returns:
            * project name
            * top-level location of the source tree with revision number
            * top-level location of the source tree without revision number
            * revision number
        """

        project = None
        try:
            project, item = item.split("=", 1)
        except ValueError:
            pass

        if re.search(r'^\.', item):
            item = os.path.abspath(os.path.join(os.getcwd(), item))

        if project is not None:
            print("[WARN] Forcing project for '{0}' to be '{1}'".format(
                item, project))
            return project, item, item, '', ''

        source_dict = self._get_base_dir(item)
        project = self._get_project_from_url(source_dict)
        if not project:
            raise ProjectNotFoundException(item)

        mirror = self._deduce_mirror(source_dict, project)

        if 'peg_rev' in source_dict and '@' in item:
            revision = '@' + source_dict['peg_rev']
            base = re.sub(r'@.*', r'', item)
        else:
            revision = ''
            base = item

        # Remove subtree from base and item
        if 'sub_tree' in source_dict:
            item = re.sub(
                r'(.*)%s/?$' % (source_dict['sub_tree']), r'\1', item, count=1)
            base = re.sub(
                r'(.*)%s/?$' % (source_dict['sub_tree']), r'\1', base, count=1)

        # Remove trailing forwards-slash
        item = re.sub(r'/$', r'', item)
        base = re.sub(r'/$', r'', base)

        # Remove anything after a point
        project = re.sub(r'\..*', r'', project)
        return project, item, base, revision, mirror

    def _generate_name(self):
        """Generate a suite name from the name of the first source tree."""
        try:
            basedir = self._ascertain_project(os.getcwd())[1]
        except ProjectNotFoundException:
            if self.opts.conf_dir:
                basedir = os.path.abspath(self.opts.conf_dir)
            else:
                basedir = os.getcwd()
        name = os.path.basename(basedir)
        self.reporter(NameSetEvent(name))
        return name

    def _this_suite(self):
        """Find the location of the suite in the first source tree."""

        # Get base of first source
        basedir = ''
        if self.opts.source:
            basedir = self.opts.source[0]
        else:
            basedir = self._ascertain_project(os.getcwd())[1]

        suitedir = os.path.join(basedir, DEFAULT_TEST_DIR)
        suitefile = os.path.join(suitedir, "rose-suite.conf")

        if not os.path.isfile(suitefile):
            raise RoseSuiteConfNotFoundException(suitedir)

        self._check_suite_version(suitefile)

        return suitedir

    def _read_auto_opts(self):
        """Read the site metomi.rose.conf file."""
        return ResourceLocator.default().get_conf().get_value(
            ["rose-stem", "automatic-options"])

    def _check_suite_version(self, fname):
        """Check the suite is compatible with this version of metomi.rose-stem.
        """
        if not os.path.isfile(fname):
            raise RoseSuiteConfNotFoundException(os.path.dirname(fname))
        config = metomi.rose.config.load(fname)
        suite_rose_stem_version = config.get(['ROSE_STEM_VERSION'])
        if suite_rose_stem_version:
            suite_rose_stem_version = int(suite_rose_stem_version.value)
        else:
            suite_rose_stem_version = None
        if not suite_rose_stem_version == ROSE_STEM_VERSION:
            raise RoseStemVersionException(suite_rose_stem_version)

    def _prepend_localhost(self, url):
        """Prepend the local hostname to urls which do not point to repository
        locations."""
        if ':' not in url or url.split(':', 1)[0] not in ['svn', 'fcm', 'http',
                                                          'https', 'svn+ssh']:
            url = self.host_selector.get_local_host() + ':' + url
        return url

    def process(self):
        """Process STEM options into 'rose suite-run' options."""

        # Generate options for source trees
        repos = {}
        repos_with_hosts = {}
        if not self.opts.source:
            self.opts.source = ['.']
        self.opts.project = list()

        for i, url in enumerate(self.opts.source):
            project, url, base, rev, mirror = self._ascertain_project(url)
            self.opts.source[i] = url
            self.opts.project.append(project)

            # Versions of variables with hostname prepended for working copies
            url_host = self._prepend_localhost(url)
            base_host = self._prepend_localhost(base)

            if project in repos:
                repos[project].append(url)
                repos_with_hosts[project].append(url_host)
            else:
                repos[project] = [url]
                repos_with_hosts[project] = [url_host]
                self._add_define_option('SOURCE_' + project.upper() + '_REV',
                                        '"' + rev + '"')
                self._add_define_option('SOURCE_' + project.upper() + '_BASE',
                                        '"' + base + '"')
                self._add_define_option('HOST_SOURCE_' + project.upper() +
                                        '_BASE', '"' + base_host + '"')
                self._add_define_option('SOURCE_' + project.upper() +
                                        '_MIRROR', '"' + mirror + '"')
            self.reporter(SourceTreeAddedAsBranchEvent(url))
        for project, branches in repos.items():
            var = 'SOURCE_' + project.upper()
            branchstring = RosePopener.list_to_shell_str(branches)
            self._add_define_option(var, '"' + branchstring + '"')
        for project, branches in repos_with_hosts.items():
            var_host = 'HOST_SOURCE_' + project.upper()
            branchstring = RosePopener.list_to_shell_str(branches)
            self._add_define_option(var_host, '"' + branchstring + '"')

        # Generate the variable containing tasks to run
        if self.opts.group:
            if not self.opts.defines:
                self.opts.defines = []
            expanded_groups = []
            for i in self.opts.group:
                expanded_groups.extend(i.split(','))
            self.opts.defines.append(SUITE_RC_PREFIX + 'RUN_NAMES=' +
                                     str(expanded_groups))

        # Load the config file and return any automatic-options
        auto_opts = self._read_auto_opts()
        if auto_opts:
            automatic_options = auto_opts.split()
            for option in automatic_options:
                elements = option.split("=")
                if len(elements) == 2:
                    self._add_define_option(
                        elements[0], '"' + elements[1] + '"')

        # Change into the suite directory
        if self.opts.conf_dir:
            self.reporter(SuiteSelectionEvent(self.opts.conf_dir))
            self._check_suite_version(
                os.path.join(self.opts.conf_dir, 'rose-suite.conf'))
        else:
            thissuite = self._this_suite()
            self.fs_util.chdir(thissuite)
            self.reporter(SuiteSelectionEvent(thissuite))

        # Create a default name for the suite; allow override by user
        if not self.opts.name:
            self.opts.name = self._generate_name()

        return self.opts


def main():
    """Launcher for command line invokation of metomi.rose stem."""

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
        except Exception as exc:
            stem.reporter(exc)
            sys.exit(1)

    # Get the suiterunner object and execute
    runner = SuiteRunner(event_handler=stem.reporter,
                         popen=stem.popen,
                         fs_util=stem.fs_util)
    if opts.debug_mode:
        sys.exit(runner(opts, args))
    try:
        sys.exit(runner(opts, args))
    except Exception as exc:
        runner.handle_event(exc)
        if isinstance(exc, RosePopenError):
            sys.exit(exc.ret_code)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
