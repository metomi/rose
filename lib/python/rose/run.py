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
"""Implement the "rose app-run" and "rose suite-run" commands."""

import ast
from datetime import datetime
from fnmatch import fnmatchcase
from glob import glob
import os
import re
from rose.config import ConfigDumper, ConfigLoader
from rose.env \
        import env_export, env_var_process, UnboundEnvironmentVariableError
from rose.config_processor import ConfigProcessorsManager
from rose.fs_util import FileSystemUtil
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter, ReporterContext
from rose.resource import ResourceLocator
from rose.run_source_vc import write_source_vc_info 
from rose.scheme_handler import SchemeHandlersManager
from rose.suite_engine_proc import SuiteEngineProcessor
from rose.suite_log_view import SuiteLogViewGenerator
from rose.task_env import get_prepend_paths
import socket
import shlex
import shutil
import sys
import tarfile
from tempfile import TemporaryFile
from time import localtime, sleep, strftime, time
from uuid import uuid4


class AlreadyRunningError(Exception):

    """An exception raised when a suite is already running."""

    def __str__(self):
        return "%s: is already running on %s" % self.args


class NotRunningError(Exception):

    """An exception raised when a suite is not running."""

    def __str__(self):
        return "%s: is not running" % (self.args)


class ConfigNotFoundError(Exception):

    """An exception raised when a config can't be found at or below cwd."""

    def __str__(self):
        return ("%s - no configuration found for this path." %
                self.args[0])


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


class PollTimeoutError(Exception):

    """An exception raised when time is out for polling."""

    def __str__(self):
        t, dt, items = self.args
        items_str = ""
        for item in items:
            items_str += "\n* " + item
        return "%s poll timeout after %ds:%s" % (
                strftime("%Y-%m-%dT%H:%M:%S", localtime(t)), dt, items_str)


class TaskAppNotFoundError(Exception):

    """Error: a task has no associated application configuration."""

    def __str__(self):
        return "%s (key=%s): task has no associated application." % self.args


class VersionMismatchError(Exception):

    """An exception raised when there is a version mismatch."""

    def __str__(self):
        return "Version expected=%s, actual=%s" % self.args


class CommandNotDefinedEvent(Event):

    """An event raised when a command is not defined for an app."""

    KIND = Event.KIND_ERR

    def __str__(self):
        return "command not defined"


class PollEvent(Event):

    """An event raised when polling for an application prerequisite."""

    LEVEL = Event.V

    def __str__(self):
        t, test, ok = self.args
        ok_str = "ATTEMPT"
        if ok:
            ok_str = "OK"
        return "[POLL %s] %s %s" % (
                ok_str, strftime("%Y-%m-%dT%H:%M:%S", localtime(t)), test)


class SuiteHostSelectEvent(Event):

    """An event raised to report the host for running a suite."""

    def __str__(self):
        return "%s: will %s on %s" % self.args


class SuiteLogArchiveEvent(Event):

    """An event raised to report the archiving of a suite log directory."""

    def __str__(self):
        return "%s <= %s" % self.args


class Dummy(object):

    """Convert a dict into an object."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class BuiltinApp(object):

    """An abstract base class for a builtin application.

    Instance of sub-classes are expected to be managed by
    rose.scheme_handler.SchemeHandlersManager.

    """

    SCHEME = None

    def __init__(self, *args, **kwargs):
        manager = kwargs.pop("manager")
        self.manager = manager

    def can_handle(self, key):
        return key.startswith(self.SCHEME)

    def get_app_key(self, name):
        """Return the application key for a given (task) name."""
        return None

    def run(self, config, opts, args, uuid, work_files):
        """Run the logic of a builtin application.

        config -- root node of the application configuration file.
        See Runner.run and Runner.run_impl for definitions for opts, args,
        uuid, work_files.

        """
        raise NotImplementedError()


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
                 fs_util=None, host_selector=None, suite_engine_proc=None):
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
        if host_selector is None:
            host_selector = HostSelector(event_handler, popen)
        self.host_selector = host_selector
        if suite_engine_proc is None:
            suite_engine_proc = SuiteEngineProcessor.get_processor(
                    event_handler=event_handler, popen=popen, fs_util=fs_util,
                    host_selector=host_selector)
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


class AppRunner(Runner):

    """Invoke a Rose application."""

    NAME = "app"
    OPTIONS = ["app_mode", "command_key", "conf_dir", "defines",
               "install_only_mode", "new_mode", "no_overwrite_mode",
               "opt_conf_keys"]

    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        p = os.path.dirname(os.path.dirname(sys.modules["rose"].__file__))
        self.builtins_manager = SchemeHandlersManager(
                [p], "rose.apps", ["run"], None, *args, **kwargs)

    def run_impl(self, opts, args, uuid, work_files):
        """The actual logic for a run."""

        # Preparation.
        config = self.config_load(opts)
        self._prep(config, opts, args, uuid, work_files)
        self._poll(config, opts, args, uuid, work_files)

        # Run the application or the command.
        app_mode = config.get_value(["mode"])
        if app_mode is None:
            app_mode = opts.app_mode
        if app_mode in [None, "command"]:
            return self._command(config, opts, args, uuid, work_files)
        else:
            builtin_app = self.builtins_manager.get_handler(app_mode)
            return builtin_app.run(self, config, opts, args, uuid, work_files)

    def _poll(self, config, opts, args, uuid, work_files):
        """Poll for prerequisites of applications."""
        # Poll configuration
        poll_test = config.get_value(["poll", "test"])
        poll_all_files_value = config.get_value(["poll", "all-files"])
        poll_all_files = []
        if poll_all_files_value:
            try:
                poll_all_files = shlex.split(
                        env_var_process(poll_all_files_value))
            except UnboundEnvironmentVariableError as e:
                raise ConfigValueError(["poll", "all-files"],
                                       poll_all_files_value, e)
        poll_any_files_value = config.get_value(["poll", "any-files"])
        poll_any_files = []
        if poll_any_files_value:
            try:
                poll_any_files = shlex.split(
                        env_var_process(poll_any_files_value))
            except UnboundEnvironmentVariableError as e:
                raise ConfigValueError(["poll", "any-files"],
                                       poll_any_files_value, e)
        poll_file_test = None
        if poll_all_files or poll_any_files:
            poll_file_test = config.get_value(["poll", "file-test"])
            if poll_file_test and "{}" not in poll_file_test:
                raise ConfigValueError(["poll", "file-test"], poll_file_test,
                                       ConfigValueError.SYNTAX)
        poll_delays = []
        if poll_test or poll_all_files or poll_any_files:
            # Parse something like this: delays=10,4*30s,2.5m,2*1h
            # No unit or s: seconds
            # m: minutes
            # h: hours
            # N*: repeat the value N times
            poll_delays_value = config.get_value(["poll", "delays"]).strip()
            units = {"h": 3600, "m": 60, "s": 1}
            if poll_delays_value:
                for item in poll_delays_value.split(","):
                    value = item.strip()
                    repeat = 1
                    if "*" in value:
                        repeat, value = value.split("*", 1)
                        try:
                            repeat = int(repeat)
                        except ValueError as e:
                            raise ConfigValueError(["poll", "delays"],
                                                   poll_delays_value,
                                                   ConfigValueError.SYNTAX)
                    unit = None
                    if value[-1].lower() in units.keys():
                        unit = units[value[-1]]
                        value = value[:-1]
                    try:
                        value = float(value)
                    except ValueError as e:
                        raise ConfigValueError(["poll", "delays"],
                                               poll_delays_value,
                                               ConfigValueError.SYNTAX)
                    if unit:
                        value *= unit
                    for i in range(repeat):
                        poll_delays.append(value)
            else:
                poll_delays = [0] # poll once without a delay

        # Poll
        t_init = time()
        while poll_delays and (poll_test or poll_any_files or poll_all_files):
            poll_delay = poll_delays.pop(0)
            if poll_delay:
                sleep(poll_delay)
            if poll_test:
                rc, out, err = self.popen.run(poll_test, shell=True,
                                              stdout=sys.stdout,
                                              stderr=sys.stderr)
                self.handle_event(PollEvent(time(), poll_test, rc == 0))
                if rc == 0:
                    poll_test = None
            any_files = list(poll_any_files)
            for file in any_files:
                if self._poll_file(file, poll_file_test):
                    self.handle_event(PollEvent(time(), "any-files", True))
                    poll_any_files = []
                    break
            all_files = list(poll_all_files)
            for file in all_files:
                if self._poll_file(file, poll_file_test):
                    poll_all_files.remove(file)
            if all_files and not poll_all_files:
                self.handle_event(PollEvent(time(), "all-files", True))
        failed_items = []
        if poll_test:
            failed_items.append("test")
        if poll_any_files:
            failed_items.append("any-files")
        if poll_all_files:
            failed_items.append("all-files:" +
                                self.popen.list_to_shell_str(poll_all_files))
        if failed_items:
            now = time()
            raise PollTimeoutError(now, now - t_init, failed_items)

    def _poll_file(self, file, poll_file_test):
        ok = False
        if poll_file_test:
            test = poll_file_test.replace(
                    "{}", self.popen.list_to_shell_str([file]))
            rc, out, err = self.popen.run(test, shell=True,
                                          stdout=sys.stdout, stderr=sys.stderr)
            ok = rc == 0
        else:
            ok = os.path.exists(file)
        self.handle_event(PollEvent(time(), "file:" + file, ok))
        return ok

    def _prep(self, config, opts, args, uuid, work_files):
        """Prepare to run the application."""

        if opts.new_mode:
            conf_dir = opts.conf_dir
            if not conf_dir or os.path.abspath(conf_dir) == os.getcwd():
                raise NewModeError(os.getcwd())
            for p in os.listdir("."):
                self.fs_util.delete(p)

        # Dump the actual configuration as rose-app-run.conf
        ConfigDumper()(config, "rose-app-run.conf")

        # Environment variables: PATH
        conf_dir = opts.conf_dir
        if conf_dir is None:
            conf_dir = os.getcwd()
        conf_bin_dir = os.path.join(conf_dir, "bin")
        if os.path.isdir(conf_bin_dir):
            value = conf_bin_dir + os.pathsep + os.getenv("PATH")
            config.set(["env", "PATH"], value)
        else:
            config.set(["env", "PATH"], os.getenv("PATH"))

        # Free format files not defined in the configuration file
        conf_file_dir = os.path.join(conf_dir, "file")
        file_section_prefix = self.config_pm.get_handler("file").PREFIX
        if os.path.isdir(conf_file_dir):
            dirs = []
            files = []
            for dirpath, dirnames, filenames in os.walk(conf_file_dir):
                for dirname in dirnames:
                    if dirname.startswith("."):
                        dirnames.remove(dirname)
                dir = dirpath[len(conf_file_dir) + 1 :]
                files += [os.path.join(dir, filename) for filename in filenames]
                if dirpath != conf_file_dir:
                    dirs.append(dir)
            for target in dirs:
                section = file_section_prefix + target
                if config.get([section], no_ignore=True) is None:
                    config.set([section, "mode"], "mkdir")
            for target in files:
                section = file_section_prefix + target
                if config.get([section], no_ignore=True) is None:
                    source = os.path.join(conf_file_dir, target)
                    config.set([section, "source"], source)

        # Process Environment Variables
        self.config_pm(config, "env")

        # Process Files
        self.config_pm(config, "file",
                       no_overwrite_mode=opts.no_overwrite_mode)

    def _command(self, config, opts, args, uuid, work_files):
        """Run the command."""

        command = self.popen.list_to_shell_str(args)
        if not command:
            names = [opts.command_key, os.getenv("ROSE_TASK_NAME"), "default"]
            for name in names:
                if not name:
                    continue
                node = config.get(["command", name], no_ignore=True)
                if node is not None:
                    break
            else:
                self.handle_event(CommandNotDefinedEvent())
                return
            command = node.value
        if os.access("STDIN", os.F_OK | os.R_OK):
            command += " <STDIN"
        self.handle_event("command: %s" % command)
        if opts.install_only_mode:
            return
        # TODO: allow caller of app_run to specify stdout and stderr?
        self.popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)


class SuiteRunner(Runner):

    """Invoke a Rose suite."""

    SLEEP_PIPE = 0.05
    NAME = "suite"
    OPTIONS = ["conf_dir", "defines", "defines_suite", "force_mode",
               "gcontrol_mode", "host", "install_only_mode",
               "log_archive_mode", "log_keep", "log_name", "name", "new_mode",
               "no_overwrite_mode", "opt_conf_keys", "reload_mode", "remote",
               "restart_mode", "run_mode", "strict_mode"]

    REC_DONT_SYNC = re.compile(
            r"\A(?:\..*|cylc-suite\.db.*|log(?:\..*)*|state|share|work)\Z")

    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self.suite_log_view_gen = SuiteLogViewGenerator(
                event_handler=self.event_handler,
                fs_util=self.fs_util,
                popen=self.popen,
                suite_engine_proc=self.suite_engine_proc)

    def run_impl(self, opts, args, uuid, work_files):
        # Log file, temporary
        if hasattr(self.event_handler, "contexts"):
            f = TemporaryFile()
            log_context = ReporterContext(None, self.event_handler.VV, f)
            self.event_handler.contexts[uuid] = log_context

        # Suite name from the current working directory
        if opts.conf_dir:
            self.fs_util.chdir(opts.conf_dir)
        opts.conf_dir = os.getcwd()

        if opts.defines_suite:
            suite_section = "jinja2:" + self.suite_engine_proc.SUITE_CONF
            if not opts.defines:
                opts.defines = []
            for define in opts.defines_suite:
                opts.defines.append("[" + suite_section + "]" + define)

        # --remote=KEY=VALUE,...
        if opts.remote:
            # opts.name always set for remote.
            return self._run_remote(opts, opts.name)

        while True:
            try:
                config = self.config_load(opts)
                break
            except (OSError, IOError) as e:
                opts.conf_dir = self.fs_util.dirname(opts.conf_dir)
                if opts.conf_dir == self.fs_util.dirname(opts.conf_dir):
                    raise ConfigNotFoundError(os.getcwd())
        if opts.conf_dir != os.getcwd():
            self.fs_util.chdir(opts.conf_dir)
            opts.conf_dir = None

        suite_name = opts.name
        if not opts.name:
            suite_name = os.path.basename(os.getcwd())

        # Automatic Rose constants
        # ROSE_ORIG_HOST: originating host
        # ROSE_VERSION: Rose version (not retained in run_mode=="reload")
        # Suite engine version
        jinja2_section = "jinja2:" + self.suite_engine_proc.SUITE_CONF
        my_rose_version = ResourceLocator.default().get_version()
        suite_engine_key = self.suite_engine_proc.get_version_env_name()
        if opts.run_mode == "reload":
            prev_config_path = self.suite_engine_proc.get_suite_dir(
                    suite_name, "log", "rose-suite-run.conf")
            prev_config = ConfigLoader()(prev_config_path)
            suite_engine_version = prev_config.get_value(
                    ["env", suite_engine_key])
        else:
            suite_engine_version = self.suite_engine_proc.get_version()
        auto_items = {"ROSE_ORIG_HOST": socket.gethostname(),
                      "ROSE_VERSION": ResourceLocator.default().get_version(),
                      suite_engine_key: suite_engine_version}
        for k, v in auto_items.items():
            requested_value = config.get_value(["env", k])
            if requested_value:
                if k == "ROSE_VERSION" and v != requested_value:
                    e = VersionMismatchError(requested_value, v)
                    raise ConfigValueError(["env", k], requested_value, e)
                v = requested_value
            else:
                config.set(["env", k], v)
            config.set([jinja2_section, k], '"' + v + '"')

        # See if suite is running or not
        hosts = []
        if opts.host:
            hosts.append(opts.host)
        conf = ResourceLocator.default().get_conf()
        
        known_hosts = self.host_selector.expand(
              ["localhost"] +
              conf.get_value(["rose-suite-run", "hosts"], "").split() +
              conf.get_value(["rose-suite-run", "scan-hosts"], "").split())[0]
        known_hosts = list(set(known_hosts))
        
        for known_host in known_hosts:
            if known_host not in hosts:
                hosts.append(known_host)
        if opts.run_mode == "reload":
            suite_run_hosts = self.suite_engine_proc.ping(suite_name, hosts)
            if not suite_run_hosts:
                raise NotRunningError(suite_name)
            hosts = suite_run_hosts
        else:
            if self.suite_engine_proc.is_suite_running(suite_name, hosts):
                if opts.force_mode:
                    opts.install_only_mode = True
                    suite_run_hosts = self.suite_engine_proc.ping(suite_name,
                                                                  hosts)
                else:
                    raise AlreadyRunningError(suite_name, 
                                              suite_run_hosts[0])

        # Install the suite to its run location
        suite_dir_rel = self._suite_dir_rel(suite_name)
        suite_dir = os.path.join(os.path.expanduser("~"), suite_dir_rel)

        suite_conf_dir = os.getcwd()
        if opts.new_mode:
            if os.getcwd() == suite_dir:
                raise NewModeError("PWD", os.getcwd())
            elif opts.run_mode in ["reload", "restart"]:
                raise NewModeError("--run", opts.run_mode)
            self.fs_util.delete(suite_dir)
        if os.getcwd() != suite_dir:
            self.fs_util.makedirs(suite_dir)
            cmd = self._get_cmd_rsync(suite_dir)
            self.popen(*cmd)
            os.chdir(suite_dir)

        # Housekeep log files
        if not opts.install_only_mode:
            self._run_init_dir_log(opts, suite_name, config)
        self.fs_util.makedirs("log/suite")

        # Rose configuration and version logs
        self.fs_util.makedirs("log/rose-conf")
        run_mode = opts.run_mode
        if run_mode not in ["reload", "restart", "run"]:
            run_mode = "run"
        prefix = "rose-conf/%s-%s" % (strftime("%Y%m%dT%H%M%S"), run_mode)

        # Dump the actual configuration as rose-suite-run.conf
        ConfigDumper()(config, "log/" + prefix + ".conf")

        # Install version information file
        write_source_vc_info(
                suite_conf_dir, "log/" + prefix + ".version", self.popen)

        # If run through rose-stem, install version information files for
        # each source tree if they're a working copy
        if hasattr(opts, 'source') and hasattr(opts, 'project'):
            for i, url in enumerate(opts.source):
                if os.path.isdir(url):
                    write_source_vc_info(
                        url, "log/" + opts.project[i] + "-" + str(i) + 
                        ".version", self.popen)

        for ext in [".conf", ".version"]:
            self.fs_util.symlink(prefix + ext, "log/rose-suite-run" + ext)

        # Move temporary log to permanent log
        if hasattr(self.event_handler, "contexts"):
            log_file_path = os.path.abspath(
                    os.path.join("log", "rose-suite-run.log"))
            log_file = open(log_file_path, "ab")
            temp_log_file = self.event_handler.contexts[uuid].handle
            temp_log_file.seek(0)
            log_file.write(temp_log_file.read())
            self.event_handler.contexts[uuid].handle = log_file
            temp_log_file.close()

        # Install share/work directories (local)
        for name in ["share", "work"]:
            self._run_init_dir_work(opts, suite_name, name, config)

        # Process Environment Variables
        environ = self.config_pm(config, "env")

        # Process Files
        self.config_pm(config, "file",
                       no_overwrite_mode=opts.no_overwrite_mode)

        # Process Jinja2 configuration
        self.config_pm(config, "jinja2")

        # Register the suite
        self.suite_engine_proc.validate(suite_name, opts.strict_mode)

        # Install suite files to each remote [user@]host
        for name in ["", "log/", "share/", "work/"]:
            uuid_file = os.path.abspath(name + uuid)
            open(uuid_file, "w").close()
            work_files.append(uuid_file)

        # Install items to user@host
        auths = self.suite_engine_proc.get_tasks_auths(suite_name)
        queue = [] # [[pipe, command, "ssh"|"rsync", auth], ...]
        for auth in sorted(auths):
            host = auth
            if "@" in auth:
                host = auth.split("@", 1)[1]
            command = self.popen.get_cmd("ssh", auth, "bash", "--login", "-c")
            rose_bin = "rose"
            for h in [host, "*"]:
                rose_home_node = conf.get(["rose-home-at", h],
                                          no_ignore=True)
                if rose_home_node is not None:
                    rose_bin = "%s/bin/rose" % (rose_home_node.value)
                    break
            # Build remote "rose suite-run" command
            rose_sr = "ROSE_VERSION=%s %s" % (my_rose_version, rose_bin)
            rose_sr += " suite-run -v -v --name=%s" % suite_name
            for key in ["new", "debug", "install-only"]:
                attr = key.replace("-", "_") + "_mode"
                if getattr(opts, attr, None) is not None:
                    rose_sr += " --" + key
            if opts.log_keep:
                rose_sr += " --log-keep=" + opts.log_keep
            if opts.log_name:
                rose_sr += " --log-name=" + opts.log_name
            if not opts.log_archive_mode:
                rose_sr += " --no-log-archive"
            rose_sr += " --run=" + opts.run_mode
            host_confs = ["root-dir-share",
                          "root-dir-work"]
            rose_sr += " --remote=uuid=" + uuid
            for key in host_confs:
                value = self._run_conf(key, host=host, config=config)
                if value is not None:
                    v = self.popen.list_to_shell_str([str(value)])
                    rose_sr += "," + key + "=" + v
            command += ["'" + rose_sr + "'"]
            pipe = self.popen.run_bg(*command)
            queue.append([pipe, command, "ssh", auth])

        while queue:
            sleep(self.SLEEP_PIPE)
            pipe, command, mode, auth = queue.pop(0)
            if pipe.poll() is None:
                queue.append([pipe, command, mode, auth]) # put it back
                continue
            rc = pipe.wait()
            out, err = pipe.communicate()
            if rc:
                raise RosePopenError(command, rc, out, err)
            if mode == "rsync":
                self.handle_event(out, level=Event.VV)
                continue
            else:
                self.handle_event(out, level=Event.VV, prefix="[%s] " % auth)
            for line in out.split("\n"):
                if "/" + uuid == line.strip():
                    break
            else:
                filters = {"excludes": [], "includes": []}
                for name in ["", "log/", "share/", "work/"]:
                    filters["excludes"].append(name + uuid)
                target = auth + ":" + suite_dir_rel
                cmd = self._get_cmd_rsync(target, **filters)
                queue.append([self.popen.run_bg(*cmd), cmd, "rsync", auth])

        # Start the suite
        self.fs_util.chdir("log")
        ret = 0
        if opts.install_only_mode:
            host = None
            if suite_run_hosts:
                host = suite_run_hosts[0]
        else:
            host = hosts[0]
            # FIXME: should sync files to suite host?
            if opts.host:
                hosts = [host]
            
            #use the list of hosts on which you can run
            if opts.run_mode != "reload" and not opts.host:
                hosts = []
                v = conf.get_value(["rose-suite-run", "hosts"], "localhost")
                known_hosts = self.host_selector.expand(v.split())[0]
                for known_host in known_hosts:
                    if known_host not in hosts:
                        hosts.append(known_host)    
                
            if hosts == ["localhost"]:
                host = hosts[0]
            else:
                host = self.host_selector(hosts)[0][0]
            self.handle_event(SuiteHostSelectEvent(suite_name, run_mode, host))
            # FIXME: values in environ were expanded in the localhost
            self.suite_engine_proc.run(
                    suite_name, host, environ, opts.run_mode, args)
            open("rose-suite-run.host", "w").write(host + "\n")

        # Launch the monitoring tool
        # Note: maybe use os.ttyname(sys.stdout.fileno())?
        if os.getenv("DISPLAY") and host and opts.gcontrol_mode:
            self.suite_engine_proc.gcontrol(suite_name, host)

        # Create the suite log view
        self.suite_log_view_gen(suite_name)

        return ret

    def _run_conf(
            self, key, default=None, host=None, config=None, r_opts=None):
        """Return the value of a setting given by a key for a given host. If
        r_opts is defined, we are alerady in a remote host, so there is no need
        to do a host match. Otherwise, the setting may be found in the run time
        configuration, or the default (i.e. site/user configuration). The value
        of each setting in the configuration would be in a line delimited list
        of PATTERN=VALUE pairs.
        """
        if r_opts is not None:
            return r_opts.get(key, default)
        if host is None:
            host = "localhost"
        for conf, keys in [
                (config, []),
                (ResourceLocator.default().get_conf(), ["rose-suite-run"])]:
            if conf is None:
                continue
            node_value = conf.get_value(keys + [key])
            if node_value is None:
                continue
            for line in node_value.strip().splitlines():
                pattern, value = line.strip().split("=", 1)
                if pattern.startswith("jinja2:"):
                    section, key = pattern.rsplit(":", 1)
                    p_node = conf.get([section, key], no_ignore=True)
                    # Values in "jinja2:*" section are quoted.
                    pattern = ast.literal_eval(p_node.value)
                if fnmatchcase(host, pattern):
                    return value.strip()
        return default

    def _run_init_dir_log(self, opts, suite_name, config=None, r_opts=None):
        """Create the suite's log/ directory. Housekeep, archive old ones."""
        # Do nothing in log append mode if log directory already exists
        if opts.run_mode in ["reload", "restart"] and os.path.isdir("log"):
            return

        # Log directory of this run
        now_str = datetime.now().strftime("%Y%m%dT%H%M%S")
        now_log = "log." + now_str
        self.fs_util.makedirs(now_log)
        self.fs_util.symlink(now_log, "log")
        now_log_name = getattr(opts, "log_name", None)
        if now_log_name:
            self.fs_util.symlink(now_log, "log." + now_log_name)

        # Keep log for this run and named logs
        logs = set(glob("log.*") + ["log"])
        for log in list(logs):
            if os.path.islink(log):
                logs.remove(log)
                log_link = os.readlink(log)
                if log_link in logs:
                    logs.remove(log_link)

        # Housekeep old logs, if necessary
        log_keep = getattr(opts, "log_keep", None)
        if log_keep:
            t = time() - abs(float(log_keep)) * 86400.0
            for log in list(logs):
                if os.path.isfile(log):
                    if t > os.stat(log).st_mtime:
                        self.fs_util.delete(log)
                        logs.remove(log)
                else:
                    for root, dirs, files in os.walk(log):
                        keep = False
                        for file in files:
                            path = os.path.join(root, file)
                            if (os.path.exists(path) and
                                os.stat(path).st_mtime >= t):
                                keep = True
                                break
                        if keep:
                            break
                    else:
                        self.fs_util.delete(log)
                        logs.remove(log)

        # Archive old logs, if necessary
        if getattr(opts, "log_archive_mode", True):
            for log in list(logs):
                if os.path.isfile(log):
                    continue
                log_tar_gz = log + ".tar.gz"
                f = tarfile.open(log_tar_gz, "w:gz")
                f.add(log)
                f.close()
                self.handle_event(SuiteLogArchiveEvent(log_tar_gz, log))
                self.fs_util.delete(log)

    def _run_init_dir_work(self, opts, suite_name, name, config=None,
                           r_opts=None):
        """Create a named suite's directory."""
        item_path = os.path.realpath(name)
        item_path_source = item_path
        key = "root-dir-" + name
        item_root = self._run_conf(key, config=config, r_opts=r_opts)
        if item_root is not None:
            item_root = env_var_process(item_root)
            suite_dir_rel = self._suite_dir_rel(suite_name)
            item_path_source = os.path.join(item_root, suite_dir_rel, name)
            item_path_source = os.path.realpath(item_path_source)
        if item_path == item_path_source:
            if opts.new_mode:
                self.fs_util.delete(name)
            self.fs_util.makedirs(name)
        else:
            if opts.new_mode:
                self.fs_util.delete(item_path_source)
            self.fs_util.makedirs(item_path_source)
            self.fs_util.symlink(item_path_source, name, opts.no_overwrite_mode)

    def _run_remote(self, opts, suite_name):
        """rose suite-run --remote=KEY=VALUE,..."""
        suite_dir_rel = self._suite_dir_rel(suite_name)
        r_opts = {}
        for item in opts.remote.split(","):
            k, v = item.split("=", 1)
            r_opts[k] = v
        uuid_file = os.path.join(suite_dir_rel, r_opts["uuid"])
        if os.path.exists(uuid_file):
            self.handle_event("/" + r_opts["uuid"] + "\n", level=0)
        elif opts.new_mode:
            self.fs_util.delete(suite_dir_rel)
        self.fs_util.makedirs(suite_dir_rel)
        os.chdir(suite_dir_rel)
        for name in ["share", "work"]:
            uuid_file = os.path.join(name, r_opts["uuid"])
            if os.path.exists(uuid_file):
                self.handle_event(name + "/" + r_opts["uuid"] + "\n", level=0)
            else:
                self._run_init_dir_work(opts, suite_name, name, r_opts=r_opts)
        if not opts.install_only_mode:
            uuid_file = os.path.join("log", r_opts["uuid"])
            if os.path.exists(uuid_file):
                self.handle_event("log/" + r_opts["uuid"] + "\n", level=0)
            else:
                self._run_init_dir_log(opts, suite_name, r_opts=r_opts)
        self.fs_util.makedirs("log/suite")

    def _get_cmd_rsync(self, target, excludes=None, includes=None):
        """rsync relevant suite items to target."""
        if excludes is None:
            excludes = []
        if includes is None:
            includes = []
        c = self.popen.get_cmd("rsync", "--delete-excluded")
        for exclude in excludes:
            c.append("--exclude=" + exclude)
        for include in includes:
            c.append("--include=" + include)
        for item in os.listdir("."):
            if not self.REC_DONT_SYNC.match(item) or item in excludes:
                c.append(item)
        c.append(target)
        return c

    def _suite_dir_rel(self, suite_name):
        """Return the relative path to the suite running directory."""
        return self.suite_engine_proc.get_suite_dir_rel(suite_name)


class TaskRunner(Runner):

    """A wrapper to a Rose task."""

    NAME = "task"
    OPTIONS = AppRunner.OPTIONS + [
            "app_key", "cycle", "cycle_offsets", "path_globs", "prefix_delim",
            "suffix_delim"]

    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self.app_runner = Runner.get_runner_class("app")(
                event_handler=self.event_handler,
                popen=self.popen,
                config_pm=self.config_pm,
                fs_util=self.fs_util,
                suite_engine_proc=self.suite_engine_proc)

    def run_impl(self, opts, args, uuid, work_files):
        # "rose task-env"
        t = self.suite_engine_proc.get_task_props(
                cycle=opts.cycle,
                cycle_offsets=opts.cycle_offsets,
                prefix_delim=opts.prefix_delim,
                suffix_delim=opts.suffix_delim)
        is_changed = False
        for k, v in t:
            if os.getenv(k) != v:
                env_export(k, v, self.event_handler)
                is_changed = True

        path_globs = opts.path_globs
        if path_globs is None:
            path_globs = []
        prepend_paths_map = get_prepend_paths(self.event_handler,
                                              t.suite_dir,
                                              path_globs,
                                              full_mode=is_changed)
        for k, prepend_paths in prepend_paths_map.items():
            orig_paths = []
            orig_v = os.getenv(k, "")
            if orig_v:
                orig_paths = orig_v.split(os.pathsep)
            v = os.pathsep.join(prepend_paths + orig_paths)
            env_export(k, v, self.event_handler)

        # Name association with builtin applications
        builtin_app = None
        if opts.app_mode is None:
            builtin_apps_manager = self.app_runner.builtins_manager
            builtin_app = builtin_apps_manager.guess_handler(t.task_name)
            if builtin_app is not None:
                opts.app_mode = builtin_app.SCHEME

        # Determine what app config to use
        if not opts.conf_dir:
            for app_key in [opts.app_key, os.getenv("ROSE_TASK_APP")]:
                if app_key is not None:
                    conf_dir = os.path.join(t.suite_dir, "app", app_key)
                    if not os.path.isdir(conf_dir):
                        raise TaskAppNotFoundError(t.task_name, app_key)
                    break
            else:
                app_key = t.task_name
                conf_dir = os.path.join(t.suite_dir, "app", t.task_name)
                if (not os.path.isdir(conf_dir) and
                    builtin_app is not None and
                    builtin_app.get_app_key(t.task_name)):
                    # A builtin application may select a different app_key
                    # based on the task name.
                    app_key = builtin_app.get_app_key(t.task_name)
                    conf_dir = os.path.join(t.suite_dir, "app", app_key)
                if not os.path.isdir(conf_dir):
                    raise TaskAppNotFoundError(t.task_name, app_key)
            opts.conf_dir = conf_dir

        return self.app_runner(opts, args)


def main():
    """Launcher for the CLI functions."""
    argv = sys.argv[1:]
    if not argv:
        return sys.exit(1)
    name = argv[0]
    try:
        runner_class = Runner.get_runner_class(name)
    except KeyError:
        sys.exit("rose.run: %s: incorrect usage" % argv[0])
    option_keys = runner_class.OPTIONS
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args(argv[1:])
    event_handler = Reporter(opts.verbosity - opts.quietness)
    runner = runner_class(event_handler)
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
