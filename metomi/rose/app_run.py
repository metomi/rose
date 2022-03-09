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
"""Implement "rose app-run"."""

from glob import glob
import os
import shlex
import sys
from time import localtime, sleep, strftime, time
import traceback
from typing import Optional

from metomi.isodatetime.data import get_timepoint_for_now
from metomi.isodatetime.parsers import ISO8601SyntaxError
from metomi.rose.config import ConfigDumper
from metomi.rose.date import RoseDateTimeOperator
from metomi.rose.env import UnboundEnvironmentVariableError, env_var_process
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.popen import RosePopenError
from metomi.rose.reporter import Event, Reporter
from metomi.rose.run import Runner
from metomi.rose.scheme_handler import SchemeHandlersManager


class ConfigValueError(Exception):

    """An exception raised when a config value is incorrect."""

    DURATION_LEGACY_MIX = "ISO8601 duration mixed with legacy duration"
    SYNTAX = "syntax"
    ERROR_FORMAT = "%s=%s: configuration value error: %s"

    def __str__(self):
        keys, value, exc = self.args
        keys = list(keys)
        key = keys.pop()
        if keys:
            key = "[" + "][".join(keys) + "]" + key
        return self.ERROR_FORMAT % (key, value, str(exc))


class CompulsoryConfigValueError(ConfigValueError):

    """An exception raised if a compulsory configuration is missing."""

    ERROR_FORMAT = "%s=%s: missing configuration error: %s"


class NewModeError(Exception):

    """An exception raised for --new mode is not supported."""

    def __str__(self):
        return "%s --new mode not supported on $PWD." % self.args


class PollTimeoutError(Exception):

    """An exception raised when time is out for polling."""

    def __str__(self):
        time_point, delay, items = self.args
        items_str = ""
        for item in items:
            items_str += "\n* " + item
        return "%s poll timeout after %s:%s" % (time_point, delay, items_str)


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
        sec, test, is_ok = self.args
        ok_str = "ATTEMPT"
        if is_ok:
            ok_str = "OK"
        return "[POLL %s] %s %s" % (
            ok_str,
            strftime("%Y-%m-%dT%H:%M:%S", localtime(sec)),
            test,
        )


class Poller:

    """Handle the [poll] functionality for AppRunner."""

    OLD_DURATION_UNITS = {"h": 3600, "m": 60, "s": 1}

    def __init__(self, popen, handle_event_func):
        self.popen = popen
        self.handle_event = handle_event_func
        self.date_time_oper = RoseDateTimeOperator()

    @staticmethod
    def _get_tests(conf_tree):
        """Return the poll tests configuration."""
        poll_test = conf_tree.node.get_value(["poll", "test"])
        poll_all_files_value = conf_tree.node.get_value(["poll", "all-files"])
        poll_all_files = []
        if poll_all_files_value:
            try:
                poll_all_files = shlex.split(
                    env_var_process(poll_all_files_value)
                )
            except UnboundEnvironmentVariableError as exc:
                raise ConfigValueError(
                    ["poll", "all-files"], poll_all_files_value, exc
                )
        poll_any_files_value = conf_tree.node.get_value(["poll", "any-files"])
        poll_any_files = []
        if poll_any_files_value:
            try:
                poll_any_files = shlex.split(
                    env_var_process(poll_any_files_value)
                )
            except UnboundEnvironmentVariableError as exc:
                raise ConfigValueError(
                    ["poll", "any-files"], poll_any_files_value, exc
                )
        poll_file_test = None
        if poll_all_files or poll_any_files:
            poll_file_test = conf_tree.node.get_value(["poll", "file-test"])
            if poll_file_test and "{}" not in poll_file_test:
                raise ConfigValueError(
                    ["poll", "file-test"],
                    poll_file_test,
                    ConfigValueError.SYNTAX,
                )

        return poll_test, poll_file_test, poll_all_files, poll_any_files

    def _get_delays(self, conf_tree):
        """Return the poll delays from the configuration."""
        # Parse something like this: delays=10,4*PT30S,PT2M30S,2*PT1H
        # R*DURATION: repeat the value R times
        conf_keys = ["poll", "delays"]
        poll_delays_value = conf_tree.node.get_value(
            conf_keys, default=""
        ).strip()
        if not poll_delays_value:
            return [0]  # poll once without a delay

        poll_delays = []
        is_legacy0 = None
        for item in poll_delays_value.split(","):
            value = item.strip()
            repeat = 1
            if "*" in value:
                repeat, value = value.split("*", 1)
                try:
                    repeat = int(repeat)
                except ValueError:
                    raise ConfigValueError(
                        conf_keys, poll_delays_value, ConfigValueError.SYNTAX
                    )
            try:
                value = self.date_time_oper.duration_parser.parse(
                    value
                ).get_seconds()
                is_legacy = False
            except ISO8601SyntaxError:
                # Legacy mode: nnnU
                # nnn is a float, U is the unit
                # No unit or s: seconds
                # m: minutes
                # h: hours
                unit = None
                if value[-1].lower() in self.OLD_DURATION_UNITS:
                    unit = self.OLD_DURATION_UNITS[value[-1].lower()]
                    value = value[:-1]
                try:
                    value = float(value)
                except ValueError:
                    raise ConfigValueError(
                        conf_keys, poll_delays_value, ConfigValueError.SYNTAX
                    )
                if unit:
                    value *= unit
                is_legacy = True
            if is_legacy0 is None:
                is_legacy0 = is_legacy
            elif is_legacy0 != is_legacy:
                raise ConfigValueError(
                    conf_keys,
                    poll_delays_value,
                    ConfigValueError.DURATION_LEGACY_MIX,
                )
            poll_delays += [value] * repeat
        return poll_delays

    def poll(self, conf_tree):
        """Poll for prerequisites of applications."""
        # Get the poll configuration.
        (
            poll_test,
            poll_file_test,
            poll_all_files,
            poll_any_files,
        ) = self._get_tests(conf_tree)
        poll_delays = []
        if poll_test or poll_all_files or poll_any_files:
            poll_delays = self._get_delays(conf_tree)

        # Launch the polling.
        t_init = get_timepoint_for_now()
        poll_test, poll_any_files, poll_all_files = self._run_poll(
            poll_test,
            poll_all_files,
            poll_any_files,
            poll_delays,
            poll_file_test=poll_file_test,
        )
        t_finish = get_timepoint_for_now()

        # Handle any failures.
        failed_items = []
        if poll_test:
            failed_items.append("test")
        if poll_any_files:
            failed_items.append("any-files")
        if poll_all_files:
            failed_items.append(
                "all-files:" + self.popen.list_to_shell_str(poll_all_files)
            )
        if failed_items:
            now = get_timepoint_for_now()
            raise PollTimeoutError(now, t_finish - t_init, failed_items)

    def _run_poll(
        self,
        poll_test,
        poll_all_files,
        poll_any_files,
        poll_delays,
        poll_file_test=None,
    ):
        """Poll, including waiting for delays."""
        while poll_delays and (poll_test or poll_any_files or poll_all_files):
            poll_delay = poll_delays.pop(0)
            if poll_delay:
                sleep(poll_delay)
            if poll_test:
                ret_code = self.popen.run(
                    poll_test, shell=True, stdout=sys.stdout, stderr=sys.stderr
                )[0]
                self.handle_event(PollEvent(time(), poll_test, ret_code == 0))
                if ret_code == 0:
                    poll_test = None
            any_files = list(poll_any_files)
            for file_ in any_files:
                if self._poll_file(file_, poll_file_test):
                    self.handle_event(PollEvent(time(), "any-files", True))
                    poll_any_files = []
                    break
            all_files = list(poll_all_files)
            for file_ in all_files:
                if self._poll_file(file_, poll_file_test):
                    poll_all_files.remove(file_)
            if all_files and not poll_all_files:
                self.handle_event(PollEvent(time(), "all-files", True))
        # Return any remaining test-failing files.
        return poll_test, poll_any_files, poll_all_files

    def _poll_file(self, file_: str, poll_file_test: str) -> bool:
        """Poll for existence of a file."""
        is_done = False
        if poll_file_test:
            test = poll_file_test.replace(
                r'{}', self.popen.list_to_shell_str([file_])
            )
            is_done = (
                self.popen.run(
                    test, shell=True, stdout=sys.stdout, stderr=sys.stderr
                )[0]
                == 0
            )
        else:
            is_done = bool(glob(file_))
        self.handle_event(PollEvent(time(), "file:" + file_, is_done))
        return is_done


class BuiltinApp:

    """An abstract base class for a builtin application.

    Instance of sub-classes are expected to be managed by
    metomi.rose.scheme_handler.SchemeHandlersManager.

    """

    SCHEME: Optional[str] = None

    def __init__(self, *args, **kwargs):
        manager = kwargs.pop("manager")
        self.manager = manager

    def can_handle(self, key):
        """Can this built-in application handle the "key" scheme?"""
        return key.startswith(self.SCHEME)

    def get_app_key(self, name):
        """Return the application key for a given (task) name."""
        return None

    def run(self, app_runner, conf_tree, opts, args, uuid, work_files):
        """Run the logic of a builtin application.

        conf_tree -- ConfigTree of the application configuration.
        See Runner.run and Runner.run_impl for definitions for opts, args,
        uuid, work_files.

        """
        raise NotImplementedError()


class AppRunner(Runner):

    """Invoke a Rose application."""

    NAME = "app"
    OPTIONS = [
        "app_mode",
        "command_key",
        "conf_dir",
        "defines",
        "install_only_mode",
        "new_mode",
        "no_overwrite_mode",
        "opt_conf_keys",
    ]

    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        path = os.path.dirname(
            os.path.dirname(sys.modules["metomi.rose"].__file__)
        )
        self.builtins_manager = SchemeHandlersManager(
            [path], "rose.apps", ["run"], None, *args, **kwargs
        )
        self.date_time_oper = RoseDateTimeOperator()

    def run_impl(self, opts, args, uuid, work_files):
        """The actual logic for a run."""

        # Preparation.
        conf_tree = self.config_load(opts)
        self._prep(conf_tree, opts)
        self._poll(conf_tree)

        # Run the application or the command.
        app_mode = conf_tree.node.get_value(["mode"])
        if app_mode is None:
            app_mode = opts.app_mode
        if app_mode is None:
            app_mode = os.getenv("ROSE_APP_MODE")
        if app_mode in [None, "command"]:
            return self._command(conf_tree, opts, args)
        else:
            builtin_app = self.builtins_manager.get_handler(app_mode)
            if builtin_app is None:
                raise UnknownBuiltinAppError(app_mode)
            return builtin_app.run(
                self, conf_tree, opts, args, uuid, work_files
            )

    def get_command(self, conf_tree, opts, args):
        """Get command to run."""
        command = self.popen.list_to_shell_str(args)
        if not command:
            names = [
                opts.command_key,
                os.getenv("ROSE_APP_COMMAND_KEY"),
                os.getenv("ROSE_TASK_NAME"),
                "default",
            ]
            for name in names:
                if not name:
                    continue
                command = conf_tree.node.get_value(["command", name])
                if command is not None:
                    break
        return command

    def _prep(self, conf_tree, opts):
        """Prepare to run the application."""

        if opts.new_mode:
            self._prep_new(opts)

        # Dump the actual configuration as rose-app-run.conf
        ConfigDumper()(conf_tree.node, "rose-app-run.conf")

        # Environment variables: PATH
        self._prep_path(conf_tree)

        # Free format files not defined in the configuration file
        file_section_prefix = self.config_pm.get_handler("file").PREFIX
        for rel_path, conf_dir in conf_tree.files.items():
            if not rel_path.startswith("file" + os.sep):
                continue
            name = rel_path[len("file" + os.sep) :]
            # No sub-directories, very slow otherwise
            if os.sep in name:
                name = name.split(os.sep, 1)[0]
            target_key = file_section_prefix + name
            target_node = conf_tree.node.get([target_key])
            if target_node is None:
                conf_tree.node.set([target_key])
                target_node = conf_tree.node.get([target_key])
            elif target_node.is_ignored():
                continue
            source_node = target_node.get(["source"])
            if source_node is None:
                target_node.set(
                    ["source"], os.path.join(conf_dir, "file", name)
                )
            elif source_node.is_ignored():
                continue

        # Process Environment Variables
        self.config_pm(conf_tree, "env")

        # Process Files
        self.config_pm(
            conf_tree, "file", no_overwrite_mode=opts.no_overwrite_mode
        )

    def _prep_new(self, opts):
        """Clear out run directory on a --new option if possible."""
        conf_dir = opts.conf_dir
        if not conf_dir or os.path.abspath(conf_dir) == os.getcwd():
            raise NewModeError(os.getcwd())
        for path in os.listdir("."):
            self.fs_util.delete(path)

    @staticmethod
    def _prep_path(conf_tree):
        """Add bin directories to the PATH seen by the app command."""
        paths = []
        for conf_dir in conf_tree.conf_dirs:
            conf_bin_dir = os.path.join(conf_dir, "bin")
            if os.path.isdir(conf_bin_dir):
                paths.append(conf_bin_dir)
        if paths:
            value = os.pathsep.join(paths + [os.getenv("PATH")])
            conf_tree.node.set(["env", "PATH"], value)
        else:
            conf_tree.node.set(["env", "PATH"], os.getenv("PATH"))

    def _poll(self, conf_tree):
        """Run any configured file polling."""
        poller = Poller(self.popen, self.handle_event)
        poller.poll(conf_tree)

    def _command(self, conf_tree, opts, args):
        """Run the command."""
        command = self.get_command(conf_tree, opts, args)
        if not command:
            self.handle_event(CommandNotDefinedEvent())
            return
        if os.access("STDIN", os.F_OK | os.R_OK):
            command += " <STDIN"
        self.handle_event("command: %s" % command)
        if opts.install_only_mode:
            return
        self.popen(
            command,
            shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
        )


def main():
    """Launcher for the CLI."""
    opt_parser = RoseOptionParser(
        usage='%prog [OPTIONS] [--] [COMMAND ...]',
        description='''
Run an application according to its configuration.

May run a builtin application (if the `mode` setting in the configuration
specifies the name of a builtin application) or a command.

Determine the command to run in this order:

1. If `COMMAND` is specified, invoke the command.
2. If the `--command-key=KEY` option is defined, invoke the command
   specified in `[command]KEY`.
3. If the `ROSE_APP_COMMAND_KEY` environment variable is set, the command
   specified in the `[command]KEY` setting in the application
   configuration whose `KEY` matches it is used.
4. If the environment variable `ROSE_TASK_NAME` is defined and a setting
   in the `[command]` section has a key matching the value of the
   environment variable, then the value of the setting is used as the
   command.
5. Invoke the command specified in `[command]default`.
        ''',
        epilog='''
ENVIRONMENT VARIABLES
    optional ROSE_APP_COMMAND_KEY
        Switch to a particular command specified in `[command]KEY`.
    optional ROSE_APP_MODE
        Specifies a builtin application to run.
    optional ROSE_APP_OPT_CONF_KEYS
        Each `KEY` in this space delimited list switches on an optional
        configuration. The configurations are applied first-to-last.
    optional ROSE_FILE_INSTALL_ROOT
        If specified, change to the specified directory to install files.
        '''
    )
    option_keys = AppRunner.OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args()
    event_handler = Reporter(opts.verbosity - opts.quietness)
    runner = AppRunner(event_handler)
    try:
        sys.exit(runner(opts, args))
    except Exception as exc:
        runner.handle_event(exc)
        if opts.debug_mode:
            traceback.print_exc()
        if isinstance(exc, RosePopenError):
            sys.exit(exc.ret_code)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
