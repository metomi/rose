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
"""Implement "rose app-run"."""

import os
from rose.config import ConfigDumper
from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.opt_parse import RoseOptionParser
from rose.popen import RosePopenError
from rose.reporter import Event, Reporter
from rose.run import Runner
from rose.scheme_handler import SchemeHandlersManager
import shlex
import sys
from time import localtime, sleep, strftime, time
import traceback
from uuid import uuid4


class ConfigValueError(Exception):

    """An exception raised when a config value is incorrect."""

    SYNTAX = "syntax"
    ERROR_FORMAT = "%s=%s: configuration value error: %s"

    def __str__(self):
        keys, value, e = self.args
        keys = list(keys)
        key = keys.pop()
        if keys:
            key = "[" + "][".join(keys) + "]" + key
        return self.ERROR_FORMAT % (key, value, str(e))


class CompulsoryConfigValueError(ConfigValueError):

    ERROR_FORMAT = "%s=%s: missing configuration error: %s"


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


class UnknownBuiltinAppError(Exception):

    """An exception raised on attempt to run an unknown builtin application."""

    def __str__(self):
        return "%s: no such built-in application" % self.args


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
            if builtin_app is None:
                raise UnknownBuiltinAppError(app_mode)
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


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser()
    option_keys = AppRunner.OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args(sys.argv[1:])
    event_handler = Reporter(opts.verbosity - opts.quietness)
    runner = AppRunner(event_handler)
    try:
        sys.exit(runner(opts, args))
    except Exception as e:
        runner.handle_event(e)
        if opts.debug_mode:
            traceback.print_exc(e)
        if isinstance(e, RosePopenError):
            sys.exit(e.rc)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
