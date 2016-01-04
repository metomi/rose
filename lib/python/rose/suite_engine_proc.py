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
"""Suite engine processor management."""

from isodatetime.data import Duration
from isodatetime.parsers import DurationParser, ISO8601SyntaxError
from glob import glob
import os
import pwd
import re
from rose.date import RoseDateTimeOperator, OffsetValueError
from rose.fs_util import FileSystemUtil
from rose.host_select import HostSelector
from rose.popen import RosePopener
from rose.reporter import Event
from rose.resource import ResourceLocator
from rose.scheme_handler import SchemeHandlersManager
import sys
import webbrowser


class NoSuiteLogError(Exception):

    """An exception raised on a missing suite log."""

    def __str__(self):
        user_name, suite_name = self.args[0:2]
        arg = suite_name
        if user_name:
            arg += " ~" + user_name
        return "%s: suite log not found" % arg


class WebBrowserEvent(Event):

    """An event raised when a web browser is launched."""

    LEVEL = Event.V

    def __init__(self, *args):
        Event.__init__(self, *args)
        self.browser, self.url = args

    def __str__(self):
        return "%s %s" % self.args


class SuiteScanResult(Event):

    """Information on where a suite is running.

    name: suite name
    location: can be one of: "user@host:port", location of port file, etc

    """

    LEVEL = 0

    def __init__(self, name, location):
        Event.__init__(self, name, location)
        self.name = name
        self.location = location

    def __cmp__(self, other):
        return (cmp(self.name, other.name) or
                cmp(self.location, other.location))

    def __str__(self):
        return "%s %s\n" % (self.name, self.location)


class BaseCycleOffset(object):

    """Represent a cycle time offset."""

    def to_duration(self):
        """Convert to a Duration."""
        raise NotImplementedError()


class OldFormatCycleOffset(BaseCycleOffset):

    """Represent a cycle time offset."""

    REC_TEXT = re.compile(r"\A"
                          r"(?P<sign>__)?"
                          r"(?P<is_time>T)?"
                          r"(?P<amount>\d+)"
                          r"(?P<unit>(?(is_time)[SMH]|[DW]))?"
                          r"\Z")
    SIGN_DEFAULT = ""

    def __init__(self, offset_text):
        """Parse offset_text into a Duration-convertible form.

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

    def to_duration(self):
        """Convert to a Duration."""
        KEYS = {"W": ("days", 7),
                "D": ("days", 1),
                "H": ("hours", 1),
                "M": ("minutes", 1)}
        date_time_unit, multiplier = KEYS[self.unit]
        amount = self.amount
        if self.sign == self.SIGN_DEFAULT:  # negative
            amount = -amount
        return Duration(**{date_time_unit: multiplier * amount})


class ISOCycleOffset(BaseCycleOffset):

    def __init__(self, offset_text):
        """Parse offset_text into a Duration-convertible form.

        Expect offset_text in this format:
        * A __ double underscore denotes an offset to the future.
          Otherwise, it is an offset to the past.
        * For the rest, use an ISO 8601 compatible duration.

        """
        if offset_text.startswith("__"):
            self.sign_factor = 1
        else:
            self.sign_factor = -1
        self.duration = DurationParser().parse(offset_text)
        self.duration *= self.sign_factor

    def __str__(self):
        duration_str = str(self.duration)
        if duration_str.startswith("-"):
            return duration_str[1:]
        return "__" + duration_str

    def to_duration(self):
        """Convert to a Duration."""
        return self.duration


class SuiteEngineGlobalConfCompatError(Exception):

    """An exception raised on incompatible global configuration."""

    def __str__(self):
        engine, key, value = self.args
        return ("%s global configuration incompatible to Rose: %s=%s" %
                (engine, key, value))


class SuiteStillRunningError(Exception):

    """An exception raised when a suite is still running."""

    FMT_HEAD = "Suite \"%(suite_name)s\" may still be running.\n"
    FMT_TAIL = "Try \"rose suite-shutdown --name=%(suite_name)s\" first?"
    FMT_BODY1 = "Host \"%(host)s\" has %(reason_key)s:\n"
    FMT_BODY2 = "    %(reason_value)s\n"

    def __str__(self):
        suite_name, reasons = self.args
        ret = self.FMT_HEAD % {"suite_name": suite_name}
        host = None
        reason_key = None
        for reason in reasons:
            reason_dict = dict(reason)
            if (reason_dict["host"] != host or
                    reason_dict["reason_key"] != reason_key):
                ret += self.FMT_BODY1 % reason_dict
                host = reason_dict["host"]
                reason_key = reason_dict["reason_key"]
            ret += self.FMT_BODY2 % reason_dict
        ret += self.FMT_TAIL % {"suite_name": suite_name}
        return ret


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
    cycling_mode: type of cycling used in the suite
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
             "cycling_mode": "ROSE_CYCLING_MODE",
             "task_cycle_time": "ROSE_TASK_CYCLE_TIME",
             "task_log_dir": "ROSE_TASK_LOG_DIR",
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
                        cycle_offset = get_cycle_offset(k.replace(prefix, ""))
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

    TASK_NAME_DELIM = {"prefix": "_", "suffix": "_"}
    SCHEME_HANDLER_MANAGER = None
    SCHEME_DEFAULT = "cylc"  # TODO: site configuration?
    TIMEOUT = 5  # seconds

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
        self.date_time_oper = RoseDateTimeOperator()

    def check_global_conf_compat(self):
        """Raise exception on suite engine specific incompatibity.

        Should raise SuiteEngineGlobalConfCompatError.

        """
        raise NotImplementedError()

    def check_suite_not_running(self, suite_name, hosts=None):
        """Raise SuiteStillRunningError if suite is still running."""
        reasons = self.is_suite_running(
            None, suite_name, self.get_suite_hosts(suite_name, hosts))
        if reasons:
            raise SuiteStillRunningError(suite_name, reasons)

    def clean_hook(self, suite_name=None):
        """Run suite engine dependent logic (at end of "rose suite-clean")."""
        raise NotImplementedError()

    def cmp_suite_conf(self, suite_name, strict_mode=False, debug_mode=False):
        """Compare current suite configuration with that in the previous run.

        An implementation of this method should:
        * Raise an exception on failure.
        * Return True if suite configuration is unmodified c.f. previous run.
        * Return False otherwise.

        """
        raise NotImplementedError()

    def get_suite_dir(self, suite_name, *paths):
        """Return the path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        return os.path.join(os.path.expanduser("~"),
                            self.get_suite_dir_rel(suite_name, *paths))

    def get_suite_dir_rel(self, suite_name, *paths):
        """Return the relative path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        raise NotImplementedError()

    def get_suite_hosts(self, suite_name=None, hosts=None):
        """Return names of potential suite hosts.

        If "suite_name" is specified, return all possible hosts including what
        is written in the "log/rose-suite-run.host" file.

        If "suite_name" is not specified and if "[rose-suite-run]hosts" is
        defined, split and return the setting.

        Otherwise, return ["localhost"].

        """
        conf = ResourceLocator.default().get_conf()
        hostnames = []
        if hosts:
            hostnames += hosts
        if suite_name:
            hostnames.append("localhost")
            # Get host name from "log/rose-suite-run.host" file
            host_file_path = self.get_suite_dir(
                suite_name, "log", "rose-suite-run.host")
            try:
                for line in open(host_file_path):
                    hostnames.append(line.strip())
            except IOError:
                pass
            # Scan-able list
            suite_hosts = conf.get_value(
                ["rose-suite-run", "scan-hosts"], "").split()
            if suite_hosts:
                hostnames += self.host_selector.expand(suite_hosts)[0]
        # Normal list
        suite_hosts = conf.get_value(["rose-suite-run", "hosts"], "").split()
        if suite_hosts:
            hostnames += self.host_selector.expand(suite_hosts)[0]
        hostnames = list(set(hostnames))
        return hostnames

    def get_suite_job_events(self, user_name, suite_name, cycles, tasks,
                             no_statuses, order, limit, offset):
        """Return suite job events.

        user -- A string containing a valid user ID
        suite -- A string containing a valid suite ID
        cycles -- Display only task jobs matching these cycles. A value in the
                  list can be a cycle, the string "before|after CYCLE", or a
                  glob to match cycles.
        tasks -- Display only jobs for task names matching these names. Values
                 can be a valid task name or a glob like pattern for matching
                 valid task names.
        no_statues -- Do not display jobs with these statuses. Valid values are
                      the keys of CylcProcessor.STATUSES.
        order -- Order search in a predetermined way. A valid value is one of
                 the keys in CylcProcessor.ORDERS.
        limit -- Limit number of returned entries
        offset -- Offset entry number

        Return (entries, of_n_entries) where:
        entries -- A list of matching entries
        of_n_entries -- Total number of entries matching query

        Each entry is a dict:
            {"cycle": cycle, "name": name, "submit_num": submit_num,
             "events": [time_submit, time_init, time_exit],
             "status": None|"submit|fail(submit)|init|success|fail|fail(%s)",
             "logs": {"script": {"path": path, "path_in_tar", path_in_tar,
                                 "size": size, "mtime": mtime},
                      "out": {...},
                      "err": {...},
                      ...}}

        """
        raise NotImplementedError()

    def get_suite_log_url(self, user_name, suite_name):
        """Return the "rose bush" URL for a user's suite."""
        prefix = "~"
        if user_name:
            prefix += user_name
        suite_d = os.path.join(prefix, self.get_suite_dir_rel(suite_name))
        suite_d = os.path.expanduser(suite_d)
        if not os.path.isdir(suite_d):
            raise NoSuiteLogError(user_name, suite_name)
        rose_bush_url = None
        for f_name in glob(os.path.expanduser("~/.metomi/rose-bush*.status")):
            status = {}
            for line in open(f_name):
                k, v = line.strip().split("=", 1)
                status[k] = v
            if status.get("host"):
                rose_bush_url = "http://" + status["host"]
                if status.get("port"):
                    rose_bush_url += ":" + status["port"]
            rose_bush_url += "/"
            break
        if not rose_bush_url:
            conf = ResourceLocator.default().get_conf()
            rose_bush_url = conf.get_value(["rose-suite-log", "rose-bush"])
        if not rose_bush_url:
            return "file://" + suite_d
        if not rose_bush_url.endswith("/"):
            rose_bush_url += "/"
        if not user_name:
            user_name = pwd.getpwuid(os.getuid()).pw_name
        return rose_bush_url + "/".join(["list", user_name, suite_name])

    def get_suite_logs_info(self, user_name, suite_name):
        """Return the information of the suite logs.

        Return a tuple that looks like:
            ("cylc-run",
             {"err": {"path": "log/suite/err", "mtime": mtime, "size": size},
              "log": {"path": "log/suite/log", "mtime": mtime, "size": size},
              "out": {"path": "log/suite/out", "mtime": mtime, "size": size}})

        """
        raise NotImplementedError()

    def get_suite_state_summary(self, user_name, suite_name):
        """Return a the state summary of a user's suite.

        Return {"last_activity_time": s, "is_running": b, "is_failed": b}
        where:
        * last_activity_time is a string in %Y-%m-%dT%H:%M:%S format,
          the time of the latest activity in the suite
        * is_running is a boolean to indicate if the suite is running
        * is_failed: a boolean to indicate if any tasks (submit) failed

        """
        raise NotImplementedError()

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

            try:
                cycle_offset = get_cycle_offset(kwargs["cycle"])
            except ISO8601SyntaxError:
                t.task_cycle_time = kwargs["cycle"]
            else:
                if t.task_cycle_time:
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
            t.dir_data_cycle = os.path.join(
                t.suite_dir, "share", "cycle", str(task_cycle_time))

            # Offset cycles
            if kwargs.get("cycle_offsets"):
                cycle_offset_strings = []
                for v in kwargs.get("cycle_offsets"):
                    cycle_offset_strings.extend(v.split(","))
                for v in cycle_offset_strings:
                    if t.cycling_mode == "integer":
                        cycle_offset = v
                        if cycle_offset.startswith("__"):
                            sign_factor = 1
                        else:
                            sign_factor = -1
                        offset_val = cycle_offset.replace("__", "")
                        cycle_time = str(
                            int(task_cycle_time) +
                            sign_factor * int(offset_val.replace("P", "")))
                    else:
                        cycle_offset = get_cycle_offset(v)
                        cycle_time = self._get_offset_cycle_time(
                            task_cycle_time, cycle_offset)
                    t.dir_data_cycle_offsets[str(cycle_offset)] = os.path.join(
                        t.suite_dir, "share", "cycle", cycle_time)

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

    def is_conf(self, path):
        """Return the file type if path is a config of this suite engine."""
        raise NotImplementedError()

    def is_suite_registered(self, suite_name):
        """Return whether or not a suite is registered."""
        raise NotImplementedError()

    def is_suite_running(self, user_name, suite_name, hosts=None):
        """Return a list of reasons if it looks like suite is running.

        Each reason should be a dict with the following keys:
        * "host": the host name where the suite appears to be running on.
        * "reason_key": a key, such as "process-id", "port-file", etc.
        * "reason_value": the value of the reason, e.g. the process ID, the
                          path to a port file, etc.

        """
        raise NotImplementedError()

    def job_logs_archive(self, suite_name, items):
        """Archive cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        raise NotImplementedError()

    def job_logs_db_create(self, suite_name, close=False):
        """Create the job logs database."""
        raise NotImplementedError()

    def job_logs_pull_remote(self, suite_name, items,
                             prune_remote_mode=False, force_mode=False):
        """Pull and housekeep the job logs on remote task hosts.

        suite_name -- The name of a suite.
        items -- A list of relevant items.
        prune_remote_mode -- Remove remote job logs after pulling them.
        force_mode -- Force retrieval, even if it may not be necessary.

        """
        raise NotImplementedError()

    def job_logs_remove_on_server(self, suite_name, items):
        """Remove cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        raise NotImplementedError()

    def launch_suite_log_browser(self, user_name, suite_name):
        """Launch web browser to view suite log.

        Return URL of suite log on success, None otherwise.

        """
        url = self.get_suite_log_url(user_name, suite_name)
        w = webbrowser.get()
        w.open(url, new=True, autoraise=True)
        self.handle_event(WebBrowserEvent(w.name, url))
        return url

    def parse_job_log_rel_path(self, f_name):
        """Return (cycle, task, submit_num, ext) for a job log rel path."""
        raise NotImplementedError()

    def ping(self, suite_name, hosts=None, timeout=10):
        """Return a list of host names where suite_name is running."""
        raise NotImplementedError()

    def run(self, suite_name, host=None, host_environ=None, restart_mode=False,
            args=None):
        """Start a suite (in a specified host)."""
        raise NotImplementedError()

    def scan(self, host_names=None, timeout=TIMEOUT):
        """Scan for running suites (in hosts).

        Return (suite_scan_results, exceptions) where
        suite_scan_results is a list of SuiteScanResult instances and
        exceptions is a list of exceptions resulting from any failed scans

        Default timeout for SSH and "cylc scan" command is 5 seconds.

        """
        raise NotImplementedError()

    def shutdown(self, suite_name, host=None, engine_version=None, args=None,
                 stderr=None, stdout=None):
        """Shut down the suite."""
        raise NotImplementedError()

    def _get_offset_cycle_time(self, cycle, cycle_offset):
        """Return the actual date time of an BaseCycleOffset against cycle.

        cycle: a YYYYmmddHH or ISO 8601 date/time string.
        cycle_offset: an instance of BaseCycleOffset.

        The returned date time would be an YYYYmmdd[HH[MM]] string.

        Note: It would be desirable to switch to a ISO 8601 format,
        but due to Cylc's YYYYmmddHH format, it would be too confusing to do so
        at the moment.

        """
        offset_str = str(cycle_offset.to_duration())
        try:
            time_point, parse_format = self.date_time_oper.date_parse(cycle)
            time_point = self.date_time_oper.date_shift(time_point, offset_str)
            return self.date_time_oper.date_format(parse_format, time_point)
        except OffsetValueError:
            raise
        except ValueError:
            raise CycleTimeError(cycle)


def get_cycle_offset(offset_text):
    """Return the correct BaseCycleOffset type for offset_text."""
    try:
        cycle_offset = OldFormatCycleOffset(offset_text)
    except CycleOffsetError:
        cycle_offset = ISOCycleOffset(offset_text)
    return cycle_offset
