# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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
"""Shared utilities for app/suite/task run."""

import os
import re
from rose.config import ConfigLoader
from rose.config_processor import ConfigProcessorsManager
from rose.fs_util import FileSystemUtil
from rose.popen import RosePopener
from rose.suite_engine_proc import SuiteEngineProcessor
import shlex
import shutil
from tempfile import TemporaryFile
from uuid import uuid4


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
    runner_classes = {}

    @classmethod
    def get_runner_class(cls, name):
        """Return the class for a named runner."""

        if cls.runner_classes.has_key(name):
            return cls.runner_classes[name]
        # Try values already imported into globals
        for c in globals().values():
            if isinstance(c, type) and c != cls and issubclass(c, cls):
                if c.NAME == name:
                    cls.runner_classes[name] = c
                    return c
        raise KeyError(name)

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

    def handle_event(self, *args, **kwargs):
        """Handle an event using the runner's event handler."""

        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def config_load(self, opts):
        """Combine main config file with optional ones and defined ones.

        Return a ConfigNode.

        """

        # Main configuration file
        conf_dir = opts.conf_dir
        if conf_dir is None:
            conf_dir = os.getcwd()
        source = os.path.join(conf_dir, "rose-" + self.CONF_NAME + ".conf")

        # Optional configuration files
        opt_conf_keys = []
        opt_conf_keys_env_name = "ROSE_" + self.CONF_NAME.upper() + "_OPT_CONF_KEYS"
        opt_conf_keys_env = os.getenv(opt_conf_keys_env_name)
        if opt_conf_keys_env:
            opt_conf_keys += shlex.split(opt_conf_keys_env)
        if opts.opt_conf_keys:
            opt_conf_keys += opts.opt_conf_keys

        config_loader = ConfigLoader()
        node = config_loader.load_with_opts(source, more_keys=opt_conf_keys)

        # Optional defines
        # N.B. In theory, we should write the values in "opts.defines" to
        # "node" directly. However, the values in "opts.defines" may contain
        # "ignore" flags. Rather than replicating the logic for parsing ignore
        # flags in here, it is actually easier to write the values in
        # "opts.defines" to a file and pass it to the loader to parse it.
        if opts.defines:
            source = TemporaryFile()
            for define in opts.defines:
                section, key, value = self.REC_OPT_DEFINE.match(define).groups()
                if section is None:
                    section = ""
                if value is None:
                    value = ""
                source.write("[%s]\n" % section)
                if key is not None:
                    source.write("%s=%s\n" % (key, value))
            source.seek(0)
            config_loader.load(source, node)
        return node

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
