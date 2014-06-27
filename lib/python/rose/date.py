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


class OffsetValueError(ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: bad offset value" % self.args[0]


class DiffError(ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: cannot be subtracted from earlier date: %s" % (
                                                self.args[0], self.args[1])


class RoseDateShifter(object):

    """A class to parse and print date string with an offset."""

    DUMP_FORMAT_CURRENT = u"CCYY-MM-DDThh:mm:ss±hh:mm"
    # strptime formats and their compatibility with the ISO 8601 parser.
    PARSE_FORMATS = [
        ("%a %b %d %H:%M:%S %Y", True),    # ctime
        ("%a %b %d %H:%M:%S %Z %Y", True), # Unix "date"
        ("%Y-%m-%dT%H:%M:%S", False),      # ISO8601, extended
        ("%Y%m%dT%H%M%S", False),          # ISO8601, basic
        ("%Y%m%d%H", False)                # Cylc (current)
    ]

    UNITS = {"w": "weeks",
             "d": "days",
             "h": "hours",
             "m": "minutes",
             "s": "seconds"}

    REC_OFFSET = re.compile(r"""\A[\+\-]?(?:\d+[wdhms])+\Z""", re.I)

    REC_OFFSET_FIND = re.compile(r"""(?P<num>\d+)(?P<unit>[wdhms])""")

    TASK_CYCLE_TIME_MODE_ENV = "ROSE_TASK_CYCLE_TIME"


    def __init__(self, parse_format=None, task_cycle_time_mode=None,
                 utc_mode=False, calendar_mode=None):
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
        if self.utc_mode:
            assumed_time_zone = (0, 0)
        else:
            assumed_time_zone = None

        if not calendar_mode: 
            calendar_mode = os.getenv("ROSE_CYCLING_MODE")

        if calendar_mode == "360day":
            isodatetime.data.set_360_calendar()
        elif calendar_mode == "gregorian":
            isodatetime.data.set_gregorian_calendar()

        self.isoparser = isodatetime.parsers.TimePointParser(
            assumed_time_zone=assumed_time_zone)

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
                return self.get_datetime_strftime(d, print_format)
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
            d.set_time_zone_to_local()
            parse_format = self.DUMP_FORMAT_CURRENT
        elif self.custom_parse_format is not None:
            parse_format = self.custom_parse_format
            d = self.strptime(ref_time, parse_format)
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
            if offset.startswith("P"):
                # Parse and apply.
                try:
                    interval = interval_parser.parse(offset)
                except ValueError:
                    raise OffsetValueError(offset)
                if sign == "-":
                    d -= interval
                else:
                    d += interval
            else:
                # Backwards compatibility for e.g. "-1h"
                if not self.is_offset(offset):
                    raise OffsetValueError(offset)
                for num, unit in self.REC_OFFSET_FIND.findall(offset.lower()):
                    num = int(num)
                    if sign == "-":
                        num = -num
                    key = self.UNITS[unit]
                    d += isodatetime.data.TimeInterval(**{key: num})

        # Format
        if parse_format is None:
            return str(d.to_calendar_date())
        if "%" in parse_format:
            return self.strftime(d, parse_format)
        return isodatetime.dumpers.TimePointDumper().dump(d, parse_format)

    __call__ = date_shift

    def date_diff(self, ref_time=None, target_time=None):
        """Return a TimeInterval for the difference between two dates."""
        ref = self.date_parse(ref_time)[0]
        target = self.date_parse(target_time)[0]
        diff = ref - target
        return diff

    def is_task_cycle_time_mode(self):
        """Return True if task_cycle_time_mode is True."""
        return (self.task_cycle_time is not None)

    def is_offset(self, offset):
        """Return True if the string offset can be parsed as an offset."""
        return (self.REC_OFFSET.match(offset) is not None)

    def strftime(self, d, print_format):
        """Use either the isodatetime or datetime strftime time formatting."""
        try:
            return d.strftime(print_format)
        except ValueError:
            return self.get_datetime_strftime(d, print_format)

    def strptime(self, ref_time, parse_format):
        """Use either the isodatetime or datetime strptime time parsing."""
        try:
            return self.isoparser.strptime(ref_time, parse_format)
        except ValueError:
            return self.get_datetime_strptime(ref_time, parse_format)

    def get_datetime_strftime(self, d, print_format):
        """Use the datetime library's strftime as a fallback."""
        year, month, day = d.copy().to_calendar_date().get_calendar_date()
        hour, minute, second = d.get_hour_minute_second()
        microsecond = int(1.0e6 * (second - int(second)))
        hour = int(hour)
        minute = int(minute)
        second = int(second)
        d = datetime(year, month, day, hour, minute, second, microsecond)
        return d.strftime(print_format)

    def get_datetime_strptime(self, ref_time, parse_format):
        """Use the datetime library's strptime as a fallback."""
        d = datetime.strptime(ref_time, parse_format)
        return self.isoparser.parse(d.isoformat())


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("calendar", "diff", "offsets", "parse_format",
                              "print_format", "task_cycle_time_mode", "utc")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    ref_time = None
    if args:
        ref_time = args[0]
    try:
        ds = RoseDateShifter(opts.parse_format, opts.task_cycle_time_mode,
                             opts.utc, opts.calendar_type)
        if opts.task_cycle_time_mode and ds.task_cycle_time is None:
            raise UnboundEnvironmentVariableError(ds.TASK_CYCLE_TIME_MODE_ENV)
        ref_time = ds(ref_time)
        if opts.offsets:
            for offset in opts.offsets:
                ref_time = ds(ref_time, offset)
        if opts.diff:
            del_time = ds.date_diff(ref_time, opts.diff)
            if ds.date_parse(opts.diff) > ds.date_parse(ref_time):
                raise DiffError(opts.diff, ref_time)
            if opts.print_format:
                delta_lookup = { "y" : del_time.years,
                                 "m" : del_time.months,
                                 "d" : del_time.days,
                                 "h" : del_time.hours,
                                 "M" : del_time.minutes,
                                 "s" : del_time.seconds }
                expression = ""
                for item in opts.print_format:
                    if delta_lookup.has_key(item):
                        expression += str(delta_lookup[item])
                    else:
                        expression += item
                print expression
            else:
                print del_time
            sys.exit()
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
