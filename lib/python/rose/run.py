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
"""Implement the "rose app-run" and "rose suite-run" commands."""

import ast
from fnmatch import fnmatchcase
from glob import glob
import os
import re
import rose.config
from rose.env import env_export, env_var_process
from rose.config_processor import ConfigProcessorsManager
from rose.fs_util import FileSystemUtil
from rose.host_select import HostSelector
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopener, RosePopenError
from rose.reporter import Event, Reporter, ReporterContext
from rose.resource import ResourceLocator
from rose.suite_engine_proc import SuiteEngineProcessor
from rose.suite_log_view import SuiteLogViewGenerator
import socket
import shutil
import sys
from tempfile import TemporaryFile
from time import sleep
from uuid import uuid4


class AlreadyRunningError(Exception):
    """An exception raised when a suite is already running."""
    def __str__(self):
        return "%s: is already running on %s" % self.args


class CommandNotDefinedError(Exception):

    """An exception raised when a command is not defined for an app."""

    def __str__(self):
        return "command not defined"


class ConfigurationNotFoundError(Exception):

    """An exception raised when a config can't be found at or below cwd."""

    def __str__(self):
        return ("%s - no configuration found for this path." %
                self.args[0])


class NewModeError(Exception):

    """An exception raised for --new when cwd is the config directory."""

    def __str__(self):
        s = "%s: is the configuration directory, --new mode not supported."
        return s % self.args[0]


class SuiteHostSelectEvent(Event):

    """An event raised to report the host for running a suite."""

    def __str__(self):
        return "%s: will run on %s" % self.args


class SuitePingTryMaxEvent(Event):

    """An event raised when the suite ping did not succeed after the maximum
    number of attempts.
    """

    TYPE = Event.TYPE_ERR

    def __str__(self):
        return "Suite ping did not succeed after %d attempts" % self.args[0]


class Dummy(object):

    """Convert a dict into an object."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Runner(object):

    """Invoke a Rose application or a Rose suite."""

    CONFIG_IS_OPTIONAL = False
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
        config = rose.config.ConfigNode()
        source = os.path.join(conf_dir, "rose-" + self.NAME + ".conf")
        if self.CONFIG_IS_OPTIONAL:
            try:
                rose.config.load(source, config)
            except IOError as e:
                pass
        else:
            rose.config.load(source, config)

        # Optional configuration files
        if opts.opt_conf_keys:
            for key in opts.opt_conf_keys:
                source_base = "rose-" + self.NAME + "-" + key + ".conf"
                source = os.path.join(conf_dir, "opt", source_base)
                rose.config.load(source, config)

        # Optional defines
        # N.B. In theory, we should write the values in "opts.defines" to
        # "config" directly. However, the values in "opts.defines" may contain
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
            rose.config.load(source, config)
        return config

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
    OPTIONS = ["command_key", "conf_dir", "defines", "install_only_mode",
               "new_mode", "no_overwrite_mode", "opt_conf_keys"]

    def run_impl(self, opts, args, uuid, work_files):
        """The actual logic for a run."""

        config = self.config_load(opts)
        self.run_impl_prep(config, opts, args, uuid, work_files)
        return self.run_impl_main(config, opts, args, uuid, work_files)

    def run_impl_prep(self, config, opts, args, uuid, work_files):
        """Prepare to run the application."""

        if opts.new_mode:
            conf_dir = opts.conf_dir
            if not conf_dir or os.path.abspath(conf_dir) == os.getcwd():
                raise NewModeError(os.getcwd())
            for p in os.listdir("."):
                self.fs_util.delete(p)

        # Dump the actual configuration as rose-app-run.conf
        rose.config.dump(config, "rose-app-run.conf")

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
        # TODO: review location
        conf_file_dir = os.path.join(conf_dir, rose.SUB_CONFIG_FILE_DIR)
        file_section_prefix = self.config_pm.get_processor("file").PREFIX
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

    def run_impl_main(self, config, opts, args, uuid, work_files):
        """Run the command. May be overridden by sub-classes."""

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
                raise CommandNotDefinedError()
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

    SLEEP_PING = 1.0
    SLEEP_PIPE = 0.05
    NAME = "suite"
    NUM_LOG_MAX = 5
    NUM_PING_TRY_MAX = 3
    OPTIONS = ["conf_dir", "defines", "force_mode", "gcontrol_mode", "host",
               "install_only_mode", "name", "new_mode",
               "no_overwrite_mode", "opt_conf_keys", "remote"]

    REC_DONT_SYNC = re.compile(r"\A(?:\..*|log(?:\..*)*|state|share|work)\Z")

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
                    raise ConfigurationNotFoundError(os.getcwd())
        if opts.conf_dir != os.getcwd():
            self.fs_util.chdir(opts.conf_dir)
            opts.conf_dir = None

        # Automatic Rose constants
        for k, v in {"ROSE_ORIG_HOST": socket.gethostname()}.items():
            config.set(["env", k], v)
            config.set(["jinja2:" + self.suite_engine_proc.SUITE_CONF, k],
                       '"' + v + '"')

        suite_name = opts.name
        if not opts.name:
            suite_name = os.path.basename(os.getcwd())

        # See if suite is running or not
        hosts = []
        if opts.host:
            hosts.append(opts.host)
        conf = ResourceLocator.default().get_conf()
        node = conf.get(["rose-suite-run", "hosts"], no_ignore=True)
        if node is None:
            known_hosts = ["localhost"]
        else:
            known_hosts = self.host_selector.expand(node.value.split())[0]
        for known_host in known_hosts:
            if known_host not in hosts:
                hosts.append(known_host)
        if self.suite_engine_proc.ping(suite_name, hosts):
            if opts.force_mode:
                opts.install_only_mode = True
            else:
                raise AlreadyRunningError(suite_name, hosts[0])

        # Install the suite to its run location
        suite_dir_rel = self._suite_dir_rel(suite_name)
        suite_dir = os.path.join(os.path.expanduser("~"), suite_dir_rel)

        suite_conf_dir = os.getcwd()
        if os.getcwd() == suite_dir:
            if opts.new_mode:
                raise NewModeError(os.getcwd())
        else:
            if opts.new_mode:
                self.fs_util.delete(suite_dir)
            self.fs_util.makedirs(suite_dir)
            cmd = self._get_cmd_rsync(suite_dir)
            self.popen(*cmd)
            os.chdir(suite_dir)

        # Housekeep log files
        if not opts.install_only_mode:
            self._run_init_dir_log(opts, suite_name, config)
        self.fs_util.makedirs("log/suite")

        # Dump the actual configuration as rose-suite-run.conf
        rose.config.dump(config, "log/rose-suite-run.conf")

        # Install version information file
        f = open("log/rose-suite.version", "wb")
        for cmd in ["info", "status", "diff"]:
            rc, out, err = self.popen.run("svn", cmd, suite_conf_dir)
            if out:
                ruler = "#" * 80 + "\n"
                f.write(ruler + "# SVN %s\n" % cmd.upper() + ruler + out)
            if rc: # If cmd fails once, chances are, it will fail again
                break
        f.close()

        # Move temporary log to permanent log
        if hasattr(self.event_handler, "contexts"):
            log_base = "rose-suite-run.log"
            log_file = open(os.path.join(os.getcwd(), "log", log_base), "w")
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
        self.suite_engine_proc.validate(suite_name)

        # Install suite files to each remote [user@]host
        for name in ["", "log/", "share/", "work/"]:
            uuid_file = os.path.abspath(name + uuid)
            open(uuid_file, "w").close()
            work_files.append(uuid_file)

        # Install items to user@host
        auths = self.suite_engine_proc.get_remote_auths(suite_name)
        queue = [] # [[pipe, command, stdin], ...]
        for user, host in sorted(auths):
            auth = user + "@" + host
            command = self.popen.get_cmd("ssh", auth, "bash")
            rose_bin = "rose"
            for h in [host, "*"]:
                rose_home_node = conf.get(["rose-home-at", h],
                                          no_ignore=True)
                if rose_home_node is not None:
                    rose_bin = "%s/bin/rose" % (rose_home_node.value)
                    break
            # Build remote "rose suite-run" command
            rose_sr = rose_bin + " suite-run -v -v"
            rose_sr += " --name=" + suite_name
            for key in ["new", "debug", "install-only"]:
                attr = key.replace("-", "_") + "_mode"
                if getattr(opts, attr, None) is not None:
                    rose_sr += " --" + key
            host_confs = ["num-log-max",
                          "root-dir-share",
                          "root-dir-work"]
            rose_sr += " --remote=uuid=" + uuid
            for key in host_confs:
                value = self._run_conf(key, host=host, config=config)
                if value is not None:
                    v = self.popen.list_to_shell_str([str(value)])
                    rose_sr += "," + key + "=" + v
            stdin = ". /etc/profile 1>/dev/null 2>&1\n" + rose_sr
            f = TemporaryFile()
            f.write(stdin)
            f.seek(0)
            pipe = self.popen.run_bg(*command, stdin=f)
            queue.append([pipe, command, stdin])

        while queue:
            sleep(self.SLEEP_PIPE)
            pipe, command, stdin = queue.pop(0)
            if pipe.poll() is None:
                queue.append([pipe, command, stdin]) # put it back at the end
                continue
            rc = pipe.wait()
            out, err = pipe.communicate()
            if rc:
                raise RosePopenError(command, rc, out, err, stdin)
            self.handle_event(out, level=Event.VV)
            if stdin is None: # is the rsync command
                continue
            for line in out.split("\n"):
                if "/" + uuid == line.strip():
                    break
            else:
                filters = {"excludes": [], "includes": []}
                for name in ["", "log/", "share/", "work/"]:
                    filters["excludes"].append(name + uuid)
                target = auth + ":" + suite_dir_rel
                cmd = self._get_cmd_rsync(target, **filters)
                queue.append([self.popen.run_bg(*cmd), cmd, None])

        # Start the suite
        self.fs_util.chdir("log")
        ret = 0
        host = hosts[0]
        if not opts.install_only_mode:
            # FIXME: should sync files to suite host?
            if opts.host:
                hosts = [host]
            if hosts == ["localhost"]:
                host = hosts[0]
            else:
                host = self.host_selector(hosts)[0][0]
            self.handle_event(SuiteHostSelectEvent(suite_name, host))
            # FIXME: values in environ were expanded in the localhost
            self.suite_engine_proc.run(suite_name, host, environ, *args)
            open("rose-suite-run.host", "w").write(host + "\n")

            # Check that the suite is running
            keys = ["rose-suite-run", "num-ping-try-max"]
            num_ping_try_max = conf.get_value(keys, self.NUM_PING_TRY_MAX)
            num_ping_try_max = int(num_ping_try_max)
            for num_ping_try in range(1, num_ping_try_max + 1):
                if self.suite_engine_proc.ping(suite_name, [host]):
                    break
                elif num_ping_try < num_ping_try_max:
                    sleep(self.SLEEP_PING)
                else:
                    event = SuitePingTryMaxEvent(num_ping_try_max)
                    self.event_handler(event)
            suite_log_view_gen = SuiteLogViewGenerator(self.event_handler)
            suite_log_view_gen()

        # Launch the monitoring tool
        # Note: maybe use os.ttyname(sys.stdout.fileno())?
        if os.getenv("DISPLAY") and opts.gcontrol_mode:
            self.suite_engine_proc.launch_gcontrol(suite_name, host)
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
            node = conf.get(keys + [key], no_ignore=True)
            if node is None:
                continue
            for line in node.value.split("\n"):
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
        """Create the suite's log/ directory. Rotate old ones."""
        num_log_max = self._run_conf(
                "num-log-max", default=self.NUM_LOG_MAX,
                config=config, r_opts=r_opts)
        num_log_max = int(num_log_max)
        for dir in glob("log.*"):
            try:
                if int(dir[4:]) >= num_log_max:
                    self.fs_util.delete(dir)
            except ValueError:
                pass
        for num_log in reversed(range(num_log_max + 1)):
            name_log = "log"
            if num_log:
                name_log = "log." + str(num_log)
            if os.path.exists(name_log):
                if num_log >= num_log_max:
                    self.fs_util.delete(name_log)
                else:
                    name_log_1 = "log." + str(num_log + 1)
                    self.fs_util.rename(name_log, name_log_1)

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
            "app_key", "auto_util_mode", "cycle", "cycle_offsets",
            "path_globs", "prefix_delim", "suffix_delim", "util_key"]
    PATH_GLOBS = ["share/fcm[_-]make*/*/bin"]

    def run_impl(self, opts, args, uuid, work_files):
        t = self.suite_engine_proc.get_task_props(
                cycle=opts.cycle,
                cycle_offsets=opts.cycle_offsets,
                prefix_delim=opts.prefix_delim,
                suffix_delim=opts.suffix_delim)

        # Prepend PATH-like variable, site/user configuration
        conf = ResourceLocator.default().get_conf()
        my_conf = conf.get(["rose-task-run"], no_ignore=True)
        for key, node in sorted(my_conf.value.items()):
            if node.is_ignored() or not key.startswith("path-prepend"):
                continue
            env_key = "PATH"
            if key != "path-prepend":
                env_key = key[len("path-prepend."):]
            values = []
            for v in node.value.split():
                if os.path.exists(v):
                    values.append(v)
            if os.getenv(env_key):
                values.append(os.getenv(env_key))
            if values:
                env_export(env_key, os.pathsep.join(values), self.event_handler)

        # Prepend PATH with paths determined by default or specified globs
        paths = []
        path_globs = list(self.PATH_GLOBS)
        if opts.path_globs:
            path_globs.extend(opts.path_globs)
        for path_glob in path_globs:
            if path_glob:
                if not os.path.isabs(path_glob):
                    path_glob = os.path.join(t.suite_dir, path_glob)
                for path in glob(path_glob):
                    paths.append(path)
            else:
                paths = [] # empty value resets
        if paths:
            if os.getenv("PATH"):
                paths.append(os.getenv("PATH"))
            env_export("PATH", os.pathsep.join(paths), self.event_handler)

        # Add ROSE_* environment variables
        for name, value in t:
            if os.getenv(name) != value:
                env_export(name, value, self.event_handler)

        # Determine what app config to use
        if not opts.conf_dir:
            app_key = t.task_name
            if opts.app_key:
                app_key = opts.app_key
            elif os.getenv("ROSE_TASK_APP"):
                app_key = os.getenv("ROSE_TASK_APP")
            opts.conf_dir = os.path.join(t.suite_dir, "app", app_key)

        # Run a task util or an app
        util = None
        if opts.util_key:
            util = self._get_task_util(opts.util_key)
        elif os.getenv("ROSE_TASK_UTIL"):
            util = self._get_task_util(os.getenv("ROSE_TASK_UTIL"))
        if opts.auto_util_mode and util is None:
            for key, u in reversed(sorted(self._get_task_utils().items())):
                if u.can_handle(t.task_name):
                    util = u
                    break
        if util is None:
            return self._run_app(opts, args)
        else:
            return util(opts, args)

    def _get_task_util(self, key):
        if not hasattr(self, "task_utils"):
            self.task_utils = {}
        if not self.task_utils.has_key(key):
            ns = "rose.task_utils"
            try:
                mod = __import__(ns + "." + key, fromlist=ns)
            except ImportError as e:
                raise KeyError(key)
            for c in vars(mod).values():
                if isinstance(c, type):
                    if hasattr(c, "can_handle") and hasattr(c, "run"):
                        self.task_utils[key] = c(
                                event_handler=self.event_handler,
                                popen=self.popen,
                                config_pm=self.config_pm,
                                fs_util=self.fs_util,
                                suite_engine_proc=self.suite_engine_proc)
        return self.task_utils[key]

    def _get_task_utils(self):
        if not getattr(self, "task_utils_loaded", False):
            if not hasattr(self, "task_utils"):
                self.task_utils = {}
            task_utils_dir = os.path.join(os.path.dirname(__file__),
                                          "task_utils")
            cwd = os.getcwd()
            os.chdir(task_utils_dir)
            try:
                for name in glob("*.py"):
                    if name.startswith("__"):
                        continue
                    try:
                        self._get_task_util(name[0:-3])
                    except KeyError as e:
                        continue
            finally:
                os.chdir(cwd)
            self.task_utils_loaded = True
        return self.task_utils

    def _run_app(self, opts, args):
        if not hasattr(self, "app_runner"):
            runner_class = Runner.get_runner_class("app")
            self.app_runner = runner_class(
                    event_handler=self.event_handler,
                    popen=self.popen,
                    config_pm=self.config_pm,
                    fs_util=self.fs_util,
                    suite_engine_proc=self.suite_engine_proc)
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
