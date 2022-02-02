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
"""Suite engine processor management."""

import os
import re
import sys
from typing import Optional

from metomi.isodatetime.data import Duration
from metomi.isodatetime.parsers import DurationParser, ISO8601SyntaxError
from metomi.rose.date import OffsetValueError, RoseDateTimeOperator
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.host_select import HostSelector
from metomi.rose.popen import RosePopener
from metomi.rose.reporter import Event
from metomi.rose.scheme_handler import SchemeHandlersManager


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


class BaseCycleOffset:

    """Represent a cycle time offset."""

    def to_duration(self):
        """Convert to a Duration."""
        raise NotImplementedError()


class OldFormatCycleOffset(BaseCycleOffset):

    """Represent a cycle time offset, back compat syntax."""

    KEYS = {
        "W": ("days", 7),
        "D": ("days", 1),
        "H": ("hours", 1),
        "M": ("minutes", 1),
    }
    REC_TEXT = re.compile(
        r"\A"
        r"(?P<sign>__)?"
        r"(?P<is_time>T)?"
        r"(?P<amount>\d+)"
        r"(?P<unit>(?(is_time)[SMH]|[DW]))?"
        r"\Z"
    )
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
        BaseCycleOffset.__init__(self)
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
        date_time_unit, multiplier = self.KEYS[self.unit]
        amount = self.amount
        if self.sign == self.SIGN_DEFAULT:  # negative
            amount = -amount
        return Duration(**{date_time_unit: multiplier * amount})


class ISOCycleOffset(BaseCycleOffset):

    """Represent a cycle time offset, ISO8601 syntax."""

    def __init__(self, offset_text):
        """Parse offset_text into a Duration-convertible form.

        Expect offset_text in this format:
        * A __ double underscore denotes an offset to the future.
          Otherwise, it is an offset to the past.
        * For the rest, use an ISO 8601 compatible duration.

        """
        BaseCycleOffset.__init__(self)
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


class CycleOffsetError(ValueError):
    """Unrecognised cycle time offset format."""

    def __str__(self):
        return self.args[0] + ": unrecognised cycle time offset format."


class CycleTimeError(ValueError):
    """Unrecognised cycle time format."""

    def __str__(self):
        return self.args[0] + ": unrecognised cycle time format."


class CyclingModeError(ValueError):
    """Unrecognised cycling mode."""

    def __str__(self):
        return self.args[0] + ": unrecognised cycling mode."


class TaskProps:

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

    ATTRS = {
        "suite_name": "ROSE_SUITE_NAME",
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
        "dir_etc": "ROSE_ETC",
    }

    def __init__(self, **kwargs):
        for attr_key, env_key in self.ATTRS.items():
            if kwargs.get(attr_key) is not None:
                setattr(self, attr_key, kwargs.get(attr_key))
            elif env_key.endswith("%s"):
                setattr(self, attr_key, {})
                prefix = env_key.replace("%s", "")
                for key, value in os.environ.items():
                    if key == prefix or not key.startswith(prefix):
                        continue
                    try:
                        cycle_offset = get_cycle_offset(
                            key.replace(prefix, "")
                        )
                    except ValueError:
                        continue
                    getattr(self, attr_key)[cycle_offset] = value
            elif os.getenv(env_key) is not None:
                setattr(self, attr_key, os.getenv(env_key))
            else:
                setattr(self, attr_key, None)

    def __iter__(self):
        for attr_key, env_key in sorted(self.ATTRS.items()):
            attr_value = getattr(self, attr_key)
            if attr_value is not None:
                if isinstance(attr_value, dict):
                    for key, value in attr_value.items():
                        yield (env_key % key, str(value))
                else:
                    yield (env_key, str(attr_value))

    def __str__(self):
        ret = ""
        for name, value in self:
            if value is not None:
                ret += "%s=%s\n" % (name, str(value))
        return ret


class SuiteEngineProcessor:
    """An abstract suite engine processor."""

    TASK_NAME_DELIM = {"prefix": "_", "suffix": "_"}
    SCHEME: Optional[str] = None
    SCHEME_HANDLER_MANAGER: Optional[str] = None
    SCHEME_DEFAULT = "cylc"  # TODO: site configuration?
    TIMEOUT = 5  # seconds

    @classmethod
    def get_processor(
        cls,
        key=None,
        event_handler=None,
        popen=None,
        fs_util=None,
        host_selector=None,
    ):
        """Return a processor for the suite engine named by "key"."""

        if cls.SCHEME_HANDLER_MANAGER is None:
            path = os.path.dirname(
                os.path.dirname(sys.modules["metomi.rose"].__file__)
            )
            cls.SCHEME_HANDLER_MANAGER = SchemeHandlersManager(
                [path],
                ns="rose.suite_engine_procs",
                attrs=["SCHEME"],
                can_handle=None,
                event_handler=event_handler,
                popen=popen,
                fs_util=fs_util,
                host_selector=host_selector,
            )
        if key is None:
            key = cls.SCHEME_DEFAULT
        x = cls.SCHEME_HANDLER_MANAGER.get_handler(key)
        return x

    def __init__(
        self,
        event_handler=None,
        popen=None,
        fs_util=None,
        host_selector=None,
        **_
    ):
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

    def get_suite_dir(self, suite_name, *paths):
        """Return the path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        return os.path.join(
            os.path.expanduser("~"), self.get_suite_dir_rel(suite_name, *paths)
        )

    def get_suite_dir_rel(self, suite_name, *paths):
        """Return the relative path to the suite running directory.

        paths -- if specified, are added to the end of the path.

        """
        raise NotImplementedError()

    def get_task_auth(self, suite_name, task_name):
        """Return [user@]host for a remote task in a suite."""
        raise NotImplementedError()

    def get_task_props(self, *args, **kwargs):
        """Return a TaskProps object containing suite task's attributes."""
        calendar_mode = self.date_time_oper.get_calendar_mode()
        try:
            return self._get_task_props(*args, **kwargs)
        finally:
            # Restore calendar mode if changed
            self.date_time_oper.set_calendar_mode(calendar_mode)

    def _get_task_props(self, *_, **kwargs):
        """Helper for get_task_props."""
        tprops = TaskProps()
        # If suite_name and task_id are defined, we can assume that the rest
        # are defined as well.
        if tprops.suite_name is not None and tprops.task_id is not None:
            return tprops

        tprops = self.get_task_props_from_env()
        # Modify calendar mode, if possible
        self.date_time_oper.set_calendar_mode(tprops.cycling_mode)

        if kwargs["cycle"] is not None:

            try:
                cycle_offset = get_cycle_offset(kwargs["cycle"])
            except ISO8601SyntaxError:
                tprops.task_cycle_time = kwargs["cycle"]
            else:
                if tprops.task_cycle_time:
                    tprops.task_cycle_time = self._get_offset_cycle_time(
                        tprops.task_cycle_time, cycle_offset
                    )
                else:
                    tprops.task_cycle_time = kwargs["cycle"]

        # Etc directory
        if os.path.exists(os.path.join(tprops.suite_dir, "etc")):
            tprops.dir_etc = os.path.join(tprops.suite_dir, "etc")

        # Data directory: generic, current cycle, and previous cycle
        tprops.dir_data = os.path.join(tprops.suite_dir, "share", "data")
        if tprops.task_cycle_time is not None:
            task_cycle_time = tprops.task_cycle_time
            tprops.dir_data_cycle = os.path.join(
                tprops.suite_dir, "share", "cycle", str(task_cycle_time)
            )

            # Offset cycles
            if kwargs.get("cycle_offsets"):
                cycle_offset_strings = []
                for value in kwargs.get("cycle_offsets"):
                    cycle_offset_strings.extend(value.split(","))
                for value in cycle_offset_strings:
                    if tprops.cycling_mode == "integer":
                        cycle_offset = value
                        if cycle_offset.startswith("__"):
                            sign_factor = 1
                        else:
                            sign_factor = -1
                        offset_val = cycle_offset.replace("__", "")
                        cycle_time = str(
                            int(task_cycle_time)
                            + sign_factor * int(offset_val.replace("P", ""))
                        )
                    else:
                        cycle_offset = get_cycle_offset(value)
                        cycle_time = self._get_offset_cycle_time(
                            task_cycle_time, cycle_offset
                        )
                    tprops.dir_data_cycle_offsets[
                        str(cycle_offset)
                    ] = os.path.join(
                        tprops.suite_dir, "share", "cycle", cycle_time
                    )

        # Create data directories if necessary
        # Note: should we create the offsets directories?
        for dir_ in [tprops.dir_data, tprops.dir_data_cycle] + list(
            tprops.dir_data_cycle_offsets.values()
        ):
            if dir_ is None:
                continue
            if os.path.exists(dir_) and not os.path.isdir(dir_):
                self.fs_util.delete(dir_)
            self.fs_util.makedirs(dir_)

        # Task prefix and suffix
        for key, split, index in [
            ("prefix", str.split, 0),
            ("suffix", str.rsplit, 1),
        ]:
            delim = self.TASK_NAME_DELIM[key]
            if kwargs.get(key + "_delim"):
                delim = kwargs.get(key + "_delim")
            if delim in tprops.task_name:
                res = split(tprops.task_name, delim, 1)
                setattr(tprops, "task_" + key, res[index])

        return tprops

    def get_task_props_from_env(self):
        """Return a TaskProps object.

        This method should not be used directly. Call get_task_props() instead.

        """
        raise NotImplementedError()

    def handle_event(self, *args, **kwargs):
        """Call self.event_handler if it is callable."""
        if callable(self.event_handler):
            return self.event_handler(*args, **kwargs)

    def job_logs_archive(self, suite_name, items):
        """Archive cycle job logs.

        suite_name -- The name of a suite.
        items -- A list of relevant items.

        """
        raise NotImplementedError()

    def job_logs_housekeep_remote(
        self, suite_name, items, prune_remote_mode=False, force_mode=False
    ):
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

    def parse_job_log_rel_path(self, f_name):
        """Return (cycle, task, submit_num, ext) for a job log rel path."""
        raise NotImplementedError()

    def _get_offset_cycle_time(self, cycle, cycle_offset):
        """Return the actual date time of an BaseCycleOffset against cycle.

        cycle: a YYYYmmddHH or ISO 8601 date/time string.
        cycle_offset: an instance of BaseCycleOffset.

        Return date time in the same format as cycle.

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
