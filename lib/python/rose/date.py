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
"""Parse and format date and time."""

from datetime import datetime, timedelta
import os
import re
from rose.env import UnboundEnvironmentVariableError
from rose.opt_parse import RoseOptionParser
from rose.reporter import Reporter
import sys


class OffsetValueError(ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: bad offset value" % self.args[0]


class RoseDateShifter(object):

    """A class to parse and print date string with an offset."""

    PARSE_FORMATS = ["%a %b %d %H:%M:%S %Y",    # ctime
                     "%a %b %d %H:%M:%S %Z %Y", # Unix "date"
                     "%Y-%m-%dT%H:%M:%S",       # ISO8601, normal
                     "%Y%m%dT%H%M%S",           # ISO8601, abbr
                     "%Y%m%d%H"];               # Cylc


    UNITS = {"w": "weeks",
             "d": "days",
             "h": "hours",
             "m": "minutes",
             "s": "seconds"}


    REC_OFFSET = re.compile(r"""\A[\+\-]?(?:\d+[wdhms])+\Z""", re.I)

    REC_OFFSET_FIND = re.compile(r"""(?P<num>\d+)(?P<unit>[wdhms])""")

    TASK_CYCLE_TIME_MODE_ENV = "ROSE_TASK_CYCLE_TIME"


    def __init__(self, parse_format=None, print_format=None,
                 task_cycle_time_mode=None):
        """Constructor.

        parse_format -- If specified, parse with the specified format.
                        Otherwise, parse with one of the format strings in
                        self.PARSE_FORMATS. The format should be a string
                        compatible to strptime(3).

        print_format -- If specified, return a string as specified in the
                        format. Otherwise, use the parse_format.

        task_cycle_time_mode -- If True, use the value of the environment
                                variable ROSE_TASK_CYCLE_TIME (if it is
                                specified) instead of the current time as the
                                reference time.

        """
        self.parse_formats = self.PARSE_FORMATS
        if parse_format:
            self.parse_formats = [parse_format]
        self.print_format = print_format
        self.task_cycle_time = None
        if task_cycle_time_mode:
            self.task_cycle_time = os.getenv(self.TASK_CYCLE_TIME_MODE_ENV)

    def date_shift(self, ref_time=None, offset=None):
        """Return a date string with an offset.

        ref_time -- If specified, use as the reference date-time string. If not
                    specified and if self.task_cycle_time_mode is True, use
                    ROSE_TASK_CYCLE_TIME environment variable if it is defined.
                    Otherwise, use current time.

        offset -- If specified, it should be a string containing the offset
                  that has the format "[+/-]nU[nU...]" where "n" is an
                  integer, and U is a unit matching a key in self.UNITS.

        """
        # Parse
        if not ref_time and self.task_cycle_time is not None:
            ref_time = self.task_cycle_time
        if not ref_time or ref_time == "now":
            d, parse_format = (datetime.now(), self.parse_formats[0])
        else:
            parse_formats = list(self.parse_formats)
            while parse_formats:
                parse_format = parse_formats.pop(0)
                try:
                    d = datetime.strptime(ref_time, parse_format)
                    break
                except ValueError as e:
                    if not parse_formats:
                        raise e

        # Offset
        if offset:
            if not self.is_offset(offset):
                raise OffsetValueError(offset)
            sign = "+"
            if offset.startswith("-") or offset.startswith("+"):
                sign = offset[0]
                offset = offset[1:]
            for num, unit in self.REC_OFFSET_FIND.findall(offset.lower()):
                num = int(num)
                if sign == "-":
                    num = -num
                key = self.UNITS[unit]
                d += timedelta(**{key: num})

        # Format
        print_format = self.print_format
        if print_format is None:
            print_format = parse_format
        return d.strftime(print_format)

    __call__ = date_shift

    def is_task_cycle_time_mode(self):
        """Return True if task_cycle_time_mode is True."""
        return (self.task_cycle_time is not None)

    def is_offset(self, offset):
        """Return True if the string offset can be parsed as an offset."""
        return (self.REC_OFFSET.match(offset) is not None)


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("offsets", "parse_format", "print_format",
                              "task_cycle_time_mode")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    ref_time = None
    if args:
        ref_time = args[0]
    try:
        ds = RoseDateShifter(opts.parse_format, opts.print_format,
                             opts.task_cycle_time_mode)
        if opts.task_cycle_time_mode and ds.task_cycle_time is None:
            raise UnboundEnvironmentVariableError(ds.TASK_CYCLE_TIME_MODE_ENV)
        ref_time = ds(ref_time)
        if opts.offsets:
            for offset in opts.offsets:
                ref_time = ds(ref_time, offset)
        print ref_time
    except Exception as e:
        if opts.debug_mode:
            import traceback
            traceback.print_exc(e)
        else:
            report(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
