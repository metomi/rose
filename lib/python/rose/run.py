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
"""Shared utilities for app/suite/task run."""

import os
import re
from rose.config_processor import ConfigProcessorsManager
from rose.config_tree import ConfigTreeLoader
from rose.fs_util import FileSystemUtil
from rose.popen import RosePopener
from rose.reporter import Event
from rose.suite_engine_proc import SuiteEngineProcessor
import shlex
import shutil
from tempfile import TemporaryFile
from uuid import uuid4


class RunConfigLoadEvent(Event):

    """An event to notify the user of the loading of a run configuration."""

    LEVEL = Event.V

    def __str__(self):
        conf_dir, conf_name, opt_conf_keys, opt_defines = self.args
        ret = "Configuration: %s/\n" % (conf_dir)
        ret += "    file: %s\n" % (conf_name)
        for opt_conf_key in opt_conf_keys:
            ret += "    optional key: %s\n" % (opt_conf_key)
        if opt_defines:
            for opt_define in opt_defines:
                ret += "    optional define: %s\n" % (opt_define)
        return ret


class ConfigNotFoundError(Exception):

    """An exception raised when a config cannot be found at or below cwd."""

    def __str__(self):
        return "%s: %s not found." % self.args


class ConfigValueError(Exception):

    """An exception raised when a config value is incorrect."""

    SYNTAX = "syntax"

    def __str__(self):
        keys, value, e = self.args
        key = keys.pop()
        if keys:
            key = "[" + "][".join(keys) + "]" + key
        return "%s=%s: configuration value error: %s" % (key, value, str(e))


class NewModeError(Exception):

    """An exception raised for --new mode is not supported."""

    def __str__(self):
        return "%s=%s, --new mode not supported." % self.args


class Dummy(object):

    """Convert a dict into an object."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Runner(object):

    """Invoke a Rose application or a Rose suite."""

    CONF_NAME = None
    NAME = None
    OPTIONS = []
    REC_OPT_DEFINE = re.compile(r"\A(?:\[([^\]]+)\])?([^=]+)?(?:=(.*))?\Z")

    def __init__(self, event_handler=None, popen=None, config_pm=None,
                 fs_util=None, suite_engine_proc=None):
        if not self.CONF_NAME:
            self.CONF_NAME = self.NAME
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        self.fs_util = fs_util
        if config_pm is None:
            config_pm = ConfigProcessorsManager(event_handler, popen, fs_util)
        self.config_pm = config_pm
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                event_handler=event_handler, popen=popen, fs_util=fs_util)
        self.suite_engine_proc = suite_engine_proc
        self.conf_tree_loader = ConfigTreeLoader()

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""

        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def config_load(self, opts):
        """Combine main config file with optional ones and defined ones.

        Return an instance of rose.config_tree.ConfigTree.

        """

        # Main configuration file
        conf_dir = opts.conf_dir
        if conf_dir is None:
            conf_dir = os.getcwd()
        conf_dir_orig = conf_dir
        conf_name = "rose-" + self.CONF_NAME + ".conf"
        while not os.access(os.path.join(conf_dir, conf_name),
                            os.F_OK | os.R_OK):
            conf_dir = self.fs_util.dirname(conf_dir)
            if conf_dir == self.fs_util.dirname(conf_dir):  # is root
                raise ConfigNotFoundError(conf_dir_orig, conf_name)

        # Optional configuration files
        opt_conf_keys = []
        opt_conf_keys_env = os.getenv("ROSE_%s_OPT_CONF_KEYS" %
                                      self.CONF_NAME.upper())
        if opt_conf_keys_env:
            opt_conf_keys += shlex.split(opt_conf_keys_env)
        if opts.opt_conf_keys:
            opt_conf_keys += opts.opt_conf_keys

        self.handle_event(RunConfigLoadEvent(
            conf_dir, conf_name, opt_conf_keys, opts.defines))

        conf_tree = self.conf_tree_loader.load(conf_dir, conf_name,
                                               opt_keys=opt_conf_keys)

        # Optional defines
        # N.B. In theory, we should write the values in "opts.defines" to
        # "conf_tree.node" directly. However, the values in "opts.defines" may
        # contain "ignore" flags. Rather than replicating the logic for parsing
        # ignore flags in here, it is actually easier to write the values in
        # "opts.defines" to a file and pass it to the loader to parse it.
        if opts.defines:
            source = TemporaryFile()
            for define in opts.defines:
                sect, key, value = self.REC_OPT_DEFINE.match(define).groups()
                if sect is None:
                    sect = ""
                if value is None:
                    value = ""
                source.write("[%s]\n" % sect)
                if key is not None:
                    source.write("%s=%s\n" % (key, value))
            source.seek(0)
            self.conf_tree_loader.node_loader.load(source, conf_tree.node)
        return conf_tree

    def run(self, opts, args):

        """Initiates a run with this runner, using the options and arguments.

        opts is a dict or object with relevant flags
        args is a list of strings.

        """

        if isinstance(opts, dict):
            opts = Dummy(**opts)
        cwd = os.getcwd()
        environ = {}
        for k, v in os.environ.items():
            environ[k] = v
        uuid = str(uuid4())
        work_files = []
        try:
            return self.run_impl(opts, args, uuid, work_files)
        finally:
            # Close handle on specific log file
            try:
                self.event_handler.contexts.get(uuid).handle.close()
            except:
                pass
            # Remove work files
            for work_file in work_files:
                try:
                    if os.path.isfile(work_file) or os.path.islink(work_file):
                        os.unlink(work_file)
                    elif os.path.isdir(work_file):
                        shutil.rmtree(work_file)
                except:
                    pass
            # Change back to original working directory
            try:
                os.chdir(cwd)
            except:
                pass
            # Reset os.environ
            os.environ = {}
            for k, v in environ.items():
                os.environ[k] = v

    __call__ = run

    def run_impl(self, opts, args, uuid, work_files):

        """Sub-class should implement the actual logic for a run.
        uuid is a unique identifier for a run.
        work_files is a list of files, which are removed at the end of a run.
        """

        raise NotImplementedError()
