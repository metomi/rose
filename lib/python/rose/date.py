# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
#-----------------------------------------------------------------------------
"""Parse and format date and time."""

from datetime import datetime, timedelta
import isodatetime.data
import isodatetime.parsers
import isodatetime.timezone
import os
import re
from rose.env import UnboundEnvironmentVariableError
from rose.opt_parse import RoseOptionParser
from rose.reporter import Reporter
import sys


class RoseDateShifter(object):

    """A class to parse and print date string with an offset."""

    # strptime formats and their compatibility with the ISO 8601 parser.
    PARSE_FORMATS = [
        ("%a %b %d %H:%M:%S %Y", True),    # ctime
        ("%a %b %d %H:%M:%S %Z %Y", True), # Unix "date"
        ("%Y-%m-%dT%H:%M:%S", False),      # ISO8601, extended
        ("%Y%m%dT%H%M%S", False),          # ISO8601, basic
        ("%Y%m%d%H", False)                # Cylc (current)
    ]

    TASK_CYCLE_TIME_MODE_ENV = "ROSE_TASK_CYCLE_TIME"


    def __init__(self, parse_format=None, task_cycle_time_mode=None,
                 utc_mode=False):
        """Constructor.

        parse_format -- If specified, parse with the specified format.
                        Otherwise, parse with one of the format strings in
                        self.PARSE_FORMATS. The format should be a string
                        compatible to strptime(3).

        task_cycle_time_mode -- If True, use the value of the environment
                                variable ROSE_TASK_CYCLE_TIME (if it is
                                specified) instead of the current time as the
                                reference time.

        utc_mode -- If True, parse/print in UTC mode rather than local or
                    other timezones.

        """
        self.parse_formats = self.PARSE_FORMATS
        self.custom_parse_format = parse_format
        self.task_cycle_time = None
        if task_cycle_time_mode:
            self.task_cycle_time = os.getenv(self.TASK_CYCLE_TIME_MODE_ENV)
        self.utc_mode = utc_mode
        self.isoparser = isodatetime.parsers.TimePointParser(
            assume_utc=utc_mode)

    def date_format(self, print_format, ref_time=None):
        """Reformat ref_time according to print_format.

        ref_time -- If specified, use as the reference date-time string. If not
                    specified and if self.task_cycle_time_mode is True, use
                    ROSE_TASK_CYCLE_TIME environment variable if it is defined.
                    Otherwise, use current time.

        """
        d = self.date_parse(ref_time)[0]
        if "%" in print_format:
            try:
                return d.strftime(print_format)
            except ValueError:
                return 
        return isodatetime.dumpers.TimePointDumper().dump(d, print_format)

    def date_parse(self, ref_time=None):
        """Parse ref_time.

        Return (t, format) where t is a datetime.datetime object and format is
        the format that matches ref_time.

        ref_time -- If specified, use as the reference date-time string. If not
                    specified and if self.task_cycle_time_mode is True, use
                    ROSE_TASK_CYCLE_TIME environment variable if it is defined.
                    Otherwise, use current time.

        """
        if not ref_time and self.task_cycle_time is not None:
            ref_time = self.task_cycle_time
        if not ref_time or ref_time == "now":
            d = isodatetime.data.get_timepoint_for_now()
            parse_format = None
        elif self.custom_parse_format is not None:
            parse_format = self.custom_parse_format
            try:
                d = self.isoparser.strptime(ref_time, parse_format)
            except ValueError:
                d = self.get_datetime_strptime(ref_time, parse_format)
        else:
            parse_formats = list(self.parse_formats)
            d = None
            while parse_formats:
                parse_format, should_use_datetime = parse_formats.pop(0)
                try:
                    if should_use_datetime:
                        d = self.get_datetime_strptime(ref_time, parse_format)
                    else:
                        d = self.isoparser.strptime(ref_time, parse_format)
                    break
                except ValueError:
                    pass
            if d is None:
                d = self.isoparser.parse(ref_time, dump_as_parsed=True)
                parse_format = None
        if self.utc_mode:
            d.set_time_zone_to_utc()
        return d, parse_format

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
        d, parse_format = self.date_parse(ref_time)

        # Offset
        if offset:
            interval_parser = isodatetime.parsers.TimeIntervalParser()
            sign = "+"
            if offset.startswith("-") or offset.startswith("+"):
                sign = offset[0]
                offset = offset[1:]
            # Backwards compatibility for e.g. "-1h"
            if not offset.startswith("P"):
                offset = "P" + offset
            offset = offset.upper()
            
            # Parse and apply.
            interval = interval_parser.parse(offset)
            if sign == "-":
                d -= interval
            else:
                d += interval

        # Format
        if parse_format is None:
            return str(d.to_calendar_date())
        if "%" in parse_format:
            return d.strftime(parse_format)
        return isodatetime.dumpers.TimePointDumper().dump(d, parse_format)

    __call__ = date_shift

    def is_task_cycle_time_mode(self):
        """Return True if task_cycle_time_mode is True."""
        return (self.task_cycle_time is not None)

    def is_offset(self, offset):
        """Return True if the string offset can be parsed as an offset."""
        return (self.REC_OFFSET.match(offset) is not None)

    def get_datetime_strftime(self, d, print_format):
        """Use the datetime library's strftime as a fallback."""
        year, month, day = d.copy().to_calendar_date().get_calendar_date()
        hour, minute, second = d.get_hour_minute_second()
        d = datetime(year, month, day, hour, minute, second)
        return d.strftime(print_format)

    def get_datetime_strptime(self, ref_time, parse_format):
        """Use the datetime library's strptime as a fallback."""
        d = datetime.strptime(ref_time, parse_format)
        return self.isoparser.parse(d.isoformat())


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("offsets", "parse_format", "print_format",
                              "task_cycle_time_mode", "utc")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    ref_time = None
    if args:
        ref_time = args[0]
    try:
        ds = RoseDateShifter(opts.parse_format, opts.task_cycle_time_mode,
                             opts.utc)
        if opts.task_cycle_time_mode and ds.task_cycle_time is None:
            raise UnboundEnvironmentVariableError(ds.TASK_CYCLE_TIME_MODE_ENV)
        ref_time = ds(ref_time)
        if opts.offsets:
            for offset in opts.offsets:
                ref_time = ds(ref_time, offset)
        if opts.print_format:
            print ds.date_format(opts.print_format, ref_time)
        else:
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
