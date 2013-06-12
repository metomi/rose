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
"""Suite engine processor management."""

from datetime import datetime, timedelta
import os
import re
from rose.env import env_var_process
from rose.fs_util import FileSystemUtil
from rose.host_select import HostSelector
from rose.popen import RosePopener
from rose.resource import ResourceLocator
from rose.scheme_handler import SchemeHandlersManager
import sys

class SuiteScanResult(object):

    """Information on where a suite is running.

    suite_name: suite name
    user: suite owner's user ID
    host: host name of running suite
    port: port at host name of running suite

    """

    def __init__(self, suite_name, user, host, port=None):
        self.suite_name = suite_name
        self.user = user
        self.host = host
        self.port = port

    def __str__(self):
        port = ""
        if self.port:
            port = ":" + self.port
        return "%s %s@%s%s" % (self.suite_name, self.user, self.host, port)

class CycleOffset(object):
    """Represent a cycle time offset."""

    REC_TEXT = re.compile(r"\A"
                          r"(?P<sign>__)?"
                          r"(?P<is_time>T)?"
                          r"(?P<amount>\d+)"
                          r"(?P<unit>(?(is_time)[SMH]|[DW]))?"
                          r"\Z")
    SIGN_DEFAULT = ""

    def __init__(self, offset_text):
        """Parse offset_text into an instance of CycleOffset.
        
        Expect offset_text in this format:
        * A __ double underscore denotes an offset to the future.
          Otherwise, it is an offset to the past.
        * For the rest:
          nW denotes n weeks.
          n or nD denotes n days.
          Tn or TnH denotes n hours.
          TnM denotes n minutes.
          TnS denotes n seconds.

        """
        match = self.REC_TEXT.match(offset_text.upper())
        if not match:
            raise CycleOffsetError(offset_text)
        self.is_time = match.group("is_time")
        if self.is_time is None:
            self.is_time = ""
        self.sign = match.group("sign")
        if not self.sign:
            self.sign = self.SIGN_DEFAULT
        self.amount = int(match.group("amount"))
        self.unit = match.group("unit")
        if not self.unit:
            if self.is_time:
                self.unit = "H"
            else:
                self.unit = "D"

    def __str__(self):
        return "%s%s%d%s" % (self.sign, self.is_time, self.amount, self.unit)

    def to_timedelta(self):
        KEYS = {"W": ("days", 7),
                "D": ("days", 1),
                "H": ("seconds", 3600),
                "M": ("seconds", 60)}
        timedelta_unit, multiplier = KEYS[self.unit]
        amount = self.amount
        if self.sign == self.SIGN_DEFAULT: # negative
            amount = -amount
        return timedelta(**{timedelta_unit: multiplier * amount})


class StillRunningError(Exception):

    """An exception raised when trying to clean a running suite."""

    def __str__(self):
        return "%s: cannot clean, still running on %s" % self.args


class CycleOffsetError(ValueError):
    """Unrecognised cycle time offset format."""

    def __str__(self):
        return self.args[0] + ": unrecognised cycle time offset format."


class CycleTimeError(ValueError):
    """Unrecognised cycle time format."""

    def __str__(self):
        return self.args[0] + ": unrecognised cycle time format."


class TaskProps(object):

    """Task properties.

    suite_name: name of the suite
    suite_dir_rel: path to suite directory relative to $HOME
    suite_dir: path to suite directory
    task_id: task ID, may contain both the name and the cycle time
    task_name: task name
    task_prefix: prefix in task name (optional)
    task_suffix: suffix in task name (optional)
    task_cycle_time: task cycle time
    task_log_root: path to the task log without file extension
    task_is_cold_start: string "true" for a cold start task
    dir_data: path to suite data directory
    dir_data_cycle: path to suite data directory in this cycle time
    dir_data_cycle_offsets: dict of time offsets: paths to suite data directory
    dir_etc: path to etc directory

    """

    ATTRS = {"suite_name": "ROSE_SUITE_NAME",
             "suite_dir_rel": "ROSE_SUITE_DIR_REL",
             "suite_dir": "ROSE_SUITE_DIR",
             "task_id": "ROSE_TASK_ID",
             "task_name": "ROSE_TASK_NAME",
             "task_prefix": "ROSE_TASK_PREFIX",
             "task_suffix": "ROSE_TASK_SUFFIX",
             "task_cycle_time": "ROSE_TASK_CYCLE_TIME",
             "task_log_root": "ROSE_TASK_LOG_ROOT",
             "task_is_cold_start": "ROSE_TASK_IS_COLD_START",
             "dir_data": "ROSE_DATA",
             "dir_data_cycle": "ROSE_DATAC",
             "dir_data_cycle_offsets": "ROSE_DATAC%s",
             "dir_etc": "ROSE_ETC"}

    def __init__(self, **kwargs):
        for key, env_key in self.ATTRS.items():
            if kwargs.get(key) is not None:
                setattr(self, key, kwargs.get(key))
            elif env_key.endswith("%s"):
                setattr(self, key, {})
                prefix = env_key.replace("%s", "")
                for k, v in os.environ.items():
                    if k == prefix or not k.startswith(prefix):
                        continue
                    try:
                        cycle_offset = CycleOffset(k.replace(prefix, ""))
                    except ValueError as e:
                        continue
                    getattr(self, key)[cycle_offset] = v
            elif os.getenv(env_key) is not None:
                setattr(self, key, os.getenv(env_key))
            else:
                setattr(self, key, None)

    def __iter__(self):
         for key, env_key in sorted(self.ATTRS.items()):
             value = getattr(self, key)
             if value is not None:
                 if isinstance(value, dict):
                     for k, v in value.items():
                         yield (env_key % k, str(v))
                 else:
                     yield (env_key, str(value))

    def __str__(self):
         ret = ""
         for name, value in self:
             if value is not None:
                 ret += "%s=%s\n" % (name, str(value))
         return ret


class SuiteEngineProcessor(object):
    """An abstract suite engine processor."""

    CYCLE_INTERVAL = 6
    RUN_DIR_REL_ROOT = None
    TASK_NAME_DELIM = {"prefix": "_", "suffix": "_"}
    SCHEME_HANDLER_MANAGER = None
    SCHEME_DEFAULT = "cylc" # TODO: site configuration?
    TASK_ID_DELIM = None # Delimiter of task ID
    TASK_LOG_DELIM = None # Delimiter of task ID in log files

    @classmethod
    def get_processor(cls, key=None, event_handler=None, popen=None,
                      fs_util=None, host_selector=None):
        """Return a processor for the suite engine named by "key"."""

        if cls.SCHEME_HANDLER_MANAGER is None:
            p = os.path.dirname(os.path.dirname(sys.modules["rose"].__file__))
            cls.SCHEME_HANDLER_MANAGER = SchemeHandlersManager(
                    [p], ns="rose.suite_engine_procs", attrs=["SCHEME"],
                    can_handle=None, event_handler=event_handler, popen=popen,
                    fs_util=fs_util, host_selector=host_selector)
        if key is None:
            key = cls.SCHEME_DEFAULT
        return cls.SCHEME_HANDLER_MANAGER.get_handler(key)

    def __init__(self, event_handler=None, popen=None, fs_util=None,
                 host_selector=None, **kwargs):
        self.event_handler = event_handler
        if popen is None:
            popen = RosePopener(event_handler)
        self.popen = popen
        if fs_util is None:
            fs_util = FileSystemUtil(event_handler)
        self.fs_util = fs_util
        if host_selector is None:
            host_selector = HostSelector(event_handler, popen)
        self.host_selector = host_selector

    def clean(self, suite_name, host=None):
        """Remove items created by the previous run of a suite."""
        raise NotImplementedError()

    def get_cycle_log_archive_name(self, cycle):
        """Return the jobs log archive file name of a given cycle time."""
        raise NotImplementedError()

    def get_suite_db_file(self, suite_name):
        """Return the path to the suite runtime database file."""
        raise NotImplementedError()

    def get_suite_dir(self, suite_name, *args):
        """Return the path to the suite running directory.

        Extra args, if specified, are added to the end of the path.

        """
        return os.path.join(os.path.expanduser("~"),
                            self.get_suite_dir_rel(suite_name, *args))

    def get_suite_dir_rel(self, suite_name, *args):
        """Return the relative path to the suite running directory.

        Extra args, if specified, are added to the end of the path.

        """
        raise NotImplementedError()

    def get_suite_events(self, suite_name, items=None):
        """Get suite task events.

        suite_name -- The name of the suite.
        items -- A list of relevant cycle times or task IDs. Only suite task
                 events for tasks in the specified list are retured.

        Assume current working directory is suite's log directory.

        Return a  data structure that looks like:
        {   <cycle time string>: {
                "cycle_time": <cycle time>,
                "tasks": {
                    <task name>: [
                        {   "events": {
                                "submit": <seconds-since-epoch>,
                                "init": <seconds-since-epoch>,
                                "exit": <seconds-since-epoch>,
                            },
                            "files": {
                                "script": {"n_bytes": <n_bytes>},
                                "out": {"n_bytes": <n_bytes>},
                                "err": {"n_bytes": <n_bytes>},
                                # ... more files
                            },
                            "signal": <signal-name-if-job-killed-by-signal>,
                            "status": <"pass"|"fail">,
                        },
                        # ... more re-submits of the task
                    ],
                    # ... more relevant task names
                }
            }
            # ... more relevant cycle times
        }
        """
        raise NotImplementedError()

    def get_suite_log_url(self, suite_name):
        """Return the URL to the suite log directory.

        Use the "home-public-html" setting in the site/user configuration to
        determine the URL.
        If no such setting is defined, return the suite running directory as a
        "file://" URL.

        """
        log_index = self.get_suite_dir(suite_name, "log", "index.html")
        if not os.path.exists(log_index):
            return None
        conf = ResourceLocator.default().get_conf()
        value = conf.get_value(["rose-suite-log-view", "home-public-html"])
        if value is None:
            return "file://" + log_index
        values = env_var_process(value).split(None, 1)
        if len(values) == 1:
            url_prefix = values[0]
            public_html = ""
        else:
            url_prefix, public_html = values
        home = os.path.expanduser("~")
        dir_rel = self.get_suite_dir_rel(suite_name, "log")
        if os.path.exists(os.path.join(home, public_html, dir_rel)):
            return url_prefix + "/" + dir_rel
        else:
            return "file://" + log_index

    def get_task_auth(self, suite_name, task_name):
        """Return [user@]host for a remote task in a suite."""
        raise NotImplementedError()

    def get_tasks_auths(self, suite_name):
        """Return a list of [user@]host for remote tasks in a suite."""
        raise NotImplementedError()

    def get_task_props(self, *args, **kwargs):
        """Return a TaskProps object containing the attributes of a suite task.
        """

        t = TaskProps()
        # If suite_name and task_id are defined, we can assume that the rest
        # are defined as well.
        if t.suite_name is not None and t.task_id is not None:
            return t

        t = self.get_task_props_from_env()
        
        if kwargs["cycle"] is not None:
        
            #If no unit is specified for the cycle and the length is at least 
            #10 it is assumed to be in YYYYmmddHH format (length 10)
            if (not CycleOffset.REC_TEXT.match(kwargs["cycle"]).group("unit") 
                and len(kwargs["cycle"]) >= 10):
                t.task_cycle_time = kwargs["cycle"]
            else:
                if t.task_cycle_time:
                    try:
                        cycle_offset = CycleOffset(kwargs["cycle"])
                    except CycleOffsetError as e:
                        t.task_cycle_time = kwargs["cycle"]
                    else:
                        t.task_cycle_time = self._get_offset_cycle_time(
                                t.task_cycle_time, cycle_offset)
                else:
                    t.task_cycle_time = kwargs["cycle"]

        # Etc directory
        if os.path.exists(os.path.join(t.suite_dir, "etc")):
            t.dir_etc = os.path.join(t.suite_dir, "etc")

        # Data directory: generic, current cycle, and previous cycle
        t.dir_data = os.path.join(t.suite_dir, "share", "data")
        if t.task_cycle_time is not None:
            task_cycle_time = t.task_cycle_time
            t.dir_data_cycle = os.path.join(t.dir_data, str(task_cycle_time))

            # Offset cycles
            if kwargs.get("cycle_offsets"):
                cycle_offset_strings = []
                for v in kwargs.get("cycle_offsets"):
                    cycle_offset_strings.extend(v.split(","))
                for v in cycle_offset_strings:
                    cycle_offset = CycleOffset(v)
                    cycle_time = self._get_offset_cycle_time(
                            task_cycle_time, cycle_offset)
                    t.dir_data_cycle_offsets[str(cycle_offset)] = os.path.join(
                            t.dir_data, cycle_time)

        # Create data directories if necessary
        # Note: should we create the offsets directories?
        for d in ([t.dir_data, t.dir_data_cycle] +
                  t.dir_data_cycle_offsets.values()):
            if d is None:
                continue
            if os.path.exists(d) and not os.path.isdir(d):
                self.fs_util.delete(d)
            self.fs_util.makedirs(d)

        # Task prefix and suffix
        for key, split, index in [("prefix", str.split, 0),
                                  ("suffix", str.rsplit, 1)]:
            delim = self.TASK_NAME_DELIM[key]
            if kwargs.get(key + "_delim"):
                delim = kwargs.get(key + "_delim")
            if delim in t.task_name:
                res = split(t.task_name, delim, 1)
                setattr(t, "task_" + key, res[index])

        return t

    def get_task_props_from_env(self):
        """Return a TaskProps object.

        This method should not be used directly. Call get_task_props() instead.

        """
        raise NotImplementedError()

    def get_version(self):
        """Return the version string of the suite engine."""
        raise NotImplementedError()

    def get_version_env_name(self):
        """Return the name of the suite engine version environment variable."""
        return self.SCHEME.upper() + "_VERSION"

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler if it is callable."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def gcontrol(self, suite_name, host=None, engine_version=None, args=None):
        """Launch control GUI for a suite_name running at a host."""
        raise NotImplementedError()

    def job_logs_archive(self, suite_name, items):
        """Archive cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        raise NotImplementedError()

    def job_logs_pull_remote(self, suite_name, items=None,
                             tidy_remote_mode=False):
        """Pull and housekeep the job logs on remote task hosts.

        suite_name -- The name of a suite.
        items -- A list of relevant items.
        tidy_remote_mode -- Remove remote job logs after pulling them.

        """
        raise NotImplementedError()

    def ping(self, suite_name, host_names=None):
        """Return a list of host names where suite_name is running."""
        raise NotImplementedError()

    def process_task_hook_args(self, *args, **kwargs):
        """Rearrange args for TaskHook.run. Return the rearranged list."""
        raise NotImplementedError()

    def run(self, suite_name, host=None, host_environ=None, restart_mode=False,
            args=None):
        """Start a suite (in a specified host)."""
        raise NotImplementedError()

    def scan(self, host_names=None):
        """Return a list of SuiteScanResult for suites running in host_names.
        """
        raise NotImplementedError()

    def shutdown(self, suite_name, host=None, engine_version=None, args=None):
        """Shut down the suite."""
        raise NotImplementedError()

    def validate(self, suite_name, strict_mode=False):
        """Validate a suite."""
        raise NotImplementedError()

    def _get_offset_cycle_time(self, cycle, cycle_offset):
        """Return the actual date time of an CycleOffset against cycle.

        cycle: a YYYYmmddHH string.
        cycle_offset: an instance of CycleOffset

        The returned date time would be an YYYYmmdd[HH[MM]] string.

        Note: It would be desirable to switch to a ISO 8601 format,
        but due to Cylc's YYYYmmddHH format, it would be too confusing to do so
        at the moment.

        """
        dt = cycle_offset.to_timedelta()
        for fmt in ["%Y%m%d", "%Y%m%d%H", "%Y%m%d%H%M"]:
            try:
                return (datetime.strptime(cycle, fmt) + dt).strftime(fmt)
            except ValueError as e:
                continue
        raise CycleTimeError(cycle)

