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
"""Parse and format date and time."""

from datetime import datetime
import os
import re
import sys

from metomi.isodatetime.data import Calendar, Duration, get_timepoint_for_now
from metomi.isodatetime.dumpers import TimePointDumper
from metomi.isodatetime.parsers import DurationParser, TimePointParser
from metomi.rose.env import UnboundEnvironmentVariableError
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Reporter


LEGACY_OFFSET = re.compile(r'-?(?P<value>\d+)(?P<unit>[wdhms])')
CYLC5_FORMAT = re.compile(r'\d{10}')
UNIX_FORMAT = re.compile(
    r'\w{3} \w{3} \d{1,2} \d\d:\d\d:\d\d (?P<timezone>\w*\/?\w*) \d{4}'
)


class OffsetValueError(ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: bad offset value" % self.args[0]


class RoseDateTimeOperator:

    """A class to parse and print date string with an offset."""

    CURRENT_TIME_DUMP_FORMAT = "CCYY-MM-DDThh:mm:ss+hh:mm"
    CURRENT_TIME_DUMP_FORMAT_Z = "CCYY-MM-DDThh:mm:ssZ"

    NEGATIVE = "-"

    # strptime formats and their compatibility with the ISO 8601 parser.
    PARSE_FORMATS = [
        ("%a %b %d %H:%M:%S %Y", True),  # ctime
        ("%a %b %d %H:%M:%S %Z %Y", True),  # Unix "date"
        ("%Y-%m-%dT%H:%M:%S", False),  # ISO8601, extended
        ("%Y%m%dT%H%M%S", False),  # ISO8601, basic
        ("%Y%m%d%H", False),  # Cylc (current)
    ]

    REC_OFFSET = re.compile(r"""\A[\+\-]?(?:\d+[wdhms])+\Z""", re.I)

    REC_OFFSET_FIND = re.compile(r"""(?P<num>\d+)(?P<unit>[wdhms])""")

    STR_NOW = "now"
    STR_REF = "ref"

    TASK_CYCLE_TIME_ENV = "ROSE_TASK_CYCLE_TIME"

    UNITS = {
        "w": "weeks",
        "d": "days",
        "h": "hours",
        "m": "minutes",
        "s": "seconds",
    }

    def __init__(
        self,
        parse_format=None,
        utc_mode=False,
        calendar_mode=None,
        ref_point_str=None,
    ):
        """Constructor.

        parse_format -- If specified, parse with the specified format.
                        Otherwise, parse with one of the format strings in
                        self.PARSE_FORMATS. The format should be a string
                        compatible to strptime(3).

        utc_mode -- If True, parse/print in UTC mode rather than local or
                    other timezones.

        calendar_mode -- Set calendar mode for
                         metomi.isodatetime.data.Calendar.

        ref_point_str -- Set the reference time point for operations.
                         If not specified, operations use current date time.

        """
        self.parse_formats = self.PARSE_FORMATS
        self.custom_parse_format = parse_format
        self.utc_mode = utc_mode
        if self.utc_mode:
            assumed_time_zone = (0, 0)
        else:
            assumed_time_zone = None

        self.set_calendar_mode(calendar_mode)

        self.time_point_dumper = TimePointDumper()
        self.time_point_parser = TimePointParser(
            assumed_time_zone=assumed_time_zone
        )
        self.duration_parser = DurationParser()

        self.ref_point_str = ref_point_str

    def date_format(self, print_format, time_point=None):
        """Reformat time_point according to print_format.

        time_point -- The time point to format.
                      Otherwise, use ref date time.

        """
        if time_point is None:
            time_point = self.date_parse()[0]
        if print_format is None:
            return str(time_point)
        if "%" in print_format:
            try:
                return time_point.strftime(print_format)
            except ValueError:
                return self.get_datetime_strftime(time_point, print_format)
        return self.time_point_dumper.dump(time_point, print_format)

    def date_parse(self, time_point_str=None):
        """Parse time_point_str.

        Return (t, format) where t is a metomi.isodatetime.data.TimePoint
        object and format is the format that matches time_point_str.

        time_point_str -- The time point string to parse.
                          Otherwise, use ref time.

        """
        if time_point_str is None or time_point_str == self.STR_REF:
            time_point_str = self.ref_point_str
        if time_point_str is None or time_point_str == self.STR_NOW:
            time_point = get_timepoint_for_now()
            if self.utc_mode or time_point.get_time_zone_utc():  # is in UTC
                parse_format = self.CURRENT_TIME_DUMP_FORMAT_Z
            else:
                parse_format = self.CURRENT_TIME_DUMP_FORMAT
        elif self.custom_parse_format is not None:
            parse_format = self.custom_parse_format
            time_point = self.strptime(time_point_str, parse_format)
        else:
            parse_formats = list(self.parse_formats)
            time_point = None
            while parse_formats:
                parse_format, should_use_datetime = parse_formats.pop(0)
                try:
                    if should_use_datetime:
                        time_point = self.get_datetime_strptime(
                            time_point_str, parse_format
                        )
                    else:
                        time_point = self.time_point_parser.strptime(
                            time_point_str, parse_format
                        )
                    break
                except ValueError:
                    pass
            if time_point is None:
                time_point = self.time_point_parser.parse(
                    time_point_str, dump_as_parsed=True
                )
                parse_format = time_point.dump_format
        if self.utc_mode:
            time_point = time_point.to_utc()
        return time_point, parse_format

    def date_shift(self, time_point=None, offset=None):
        """Return a date string with an offset.

        time_point -- A time point or time point string.
                      Otherwise, use current time.

        offset -- If specified, it should be a string containing the offset
                  that has the format "[+/-]nU[nU...]" where "n" is an
                  integer, and U is a unit matching a key in self.UNITS.

        """
        if time_point is None:
            time_point = self.date_parse()[0]
        # Offset
        if offset:
            sign = "+"
            if offset.startswith("-") or offset.startswith("+"):
                sign = offset[0]
                offset = offset[1:]
            if offset.startswith("P"):
                # Parse and apply.
                try:
                    duration = self.duration_parser.parse(offset)
                except ValueError:
                    raise OffsetValueError(offset)
                if sign == "-":
                    time_point -= duration
                else:
                    time_point += duration
            else:
                # Backwards compatibility for e.g. "-1h"
                if not self.is_offset(offset):
                    raise OffsetValueError(offset)
                for num, unit in self.REC_OFFSET_FIND.findall(offset.lower()):
                    num = int(num)
                    if sign == "-":
                        num = -num
                    key = self.UNITS[unit]
                    time_point += Duration(**{key: num})

        return time_point

    def date_diff(self, time_point_1=None, time_point_2=None):
        """Return (duration, is_negative) between two TimePoint objects.

        duration -- is a Duration instance.
        is_negative -- is a RoseDateTimeOperator.NEGATIVE if time_point_2 is
                       in the past of time_point_1.
        """
        if time_point_2 < time_point_1:
            return (time_point_1 - time_point_2, self.NEGATIVE)
        else:
            return (time_point_2 - time_point_1, "")

    @classmethod
    def date_diff_format(cls, print_format, duration, sign):
        """Format a duration."""
        if print_format:
            delta_lookup = {
                "y": duration.years,
                "m": duration.months,
                "d": duration.days,
                "h": duration.hours,
                "M": duration.minutes,
                "s": duration.seconds,
            }
            expression = ""
            for item in print_format:
                if item in delta_lookup:
                    if float(delta_lookup[item]).is_integer():
                        expression += str(int(delta_lookup[item]))
                    else:
                        expression += str(delta_lookup[item])
                else:
                    expression += item
            return sign + expression
        else:
            return sign + str(duration)

    @staticmethod
    def get_calendar_mode():
        """Get current calendar mode."""
        return Calendar.default().mode

    def is_offset(self, offset):
        """Return True if the string offset can be parsed as an offset."""
        return self.REC_OFFSET.match(offset) is not None

    @staticmethod
    def set_calendar_mode(calendar_mode=None):
        """Set calendar mode for subsequent operations.

        Raise KeyError if calendar_mode is invalid.

        """
        if not calendar_mode:
            calendar_mode = os.getenv("ROSE_CYCLING_MODE")

        if calendar_mode and calendar_mode in Calendar.MODES:
            Calendar.default().set_mode(calendar_mode)

    def strftime(self, time_point, print_format):
        """Use either the metomi.isodatetime or datetime strftime time
        formatting.
        """
        try:
            return time_point.strftime(print_format)
        except ValueError:
            return self.get_datetime_strftime(time_point, print_format)

    def strptime(self, time_point_str, parse_format):
        """Use either the isodatetime or datetime strptime time parsing."""
        try:
            return self.time_point_parser.strptime(
                time_point_str, parse_format
            )
        except ValueError:
            return self.get_datetime_strptime(time_point_str, parse_format)

    @classmethod
    def get_datetime_strftime(cls, time_point, print_format):
        """Use the datetime library's strftime as a fallback."""
        year, month, day = time_point.get_calendar_date()
        hour, minute, second = time_point.get_hour_minute_second()
        microsecond = int(1.0e6 * (second - int(second)))
        hour = int(hour)
        minute = int(minute)
        second = int(second)
        date_time = datetime(
            year, month, day, hour, minute, second, microsecond
        )
        return date_time.strftime(print_format)

    def get_datetime_strptime(self, time_point_str, parse_format):
        """Use the datetime library's strptime as a fallback."""
        date_time = datetime.strptime(time_point_str, parse_format)
        return self.time_point_parser.parse(date_time.isoformat())


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options(
        "calendar",
        "diff",
        "offsets1",
        "offsets2",
        "parse_format",
        "print_format",
        "task_cycle_time_mode",
        "as_total",
        "utc_mode",
    )
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)

    ref_point_str = None
    if opts.task_cycle_time_mode:
        ref_point_str = os.getenv(RoseDateTimeOperator.TASK_CYCLE_TIME_ENV)
        if ref_point_str is None:
            exc = UnboundEnvironmentVariableError(
                RoseDateTimeOperator.TASK_CYCLE_TIME_ENV
            )
            report(exc)
            if opts.debug_mode:
                raise exc
            sys.exit(1)

    date_time_oper = RoseDateTimeOperator(
        parse_format=opts.parse_format,
        utc_mode=opts.utc_mode,
        calendar_mode=opts.calendar,
        ref_point_str=ref_point_str,
    )

    try:
        if len(args) < 2:
            if opts.duration_print_format:
                _convert_duration(date_time_oper, opts, args)
            else:
                _print_time_point(date_time_oper, opts, args)
        else:
            _print_duration(date_time_oper, opts, args)
    except OffsetValueError as exc:
        report(exc)
        if opts.debug_mode:
            raise exc
        sys.exit(1)


def _print_time_point(date_time_oper, opts, args):
    """Implement usage 1 of "rose date", print time point."""

    time_point_str = None
    if args:
        time_point_str = args[0]
    time_point, parse_format = date_time_oper.date_parse(time_point_str)
    if opts.offsets1:
        for offset in opts.offsets1:
            time_point = date_time_oper.date_shift(time_point, offset)
    if opts.print_format:
        print(date_time_oper.date_format(opts.print_format, time_point))
    elif parse_format:
        print(date_time_oper.date_format(parse_format, time_point))
    else:
        print(str(time_point))


def _print_duration(date_time_oper, opts, args):
    """Implement usage 2 of "rose date", print duration."""
    time_point_str_1, time_point_str_2 = args
    time_point_1 = date_time_oper.date_parse(time_point_str_1)[0]
    time_point_2 = date_time_oper.date_parse(time_point_str_2)[0]
    if opts.offsets1:
        for offset in opts.offsets1:
            time_point_1 = date_time_oper.date_shift(time_point_1, offset)
    if opts.offsets2:
        for offset in opts.offsets2:
            time_point_2 = date_time_oper.date_shift(time_point_2, offset)
    duration, sign = date_time_oper.date_diff(time_point_1, time_point_2)
    out = date_time_oper.date_diff_format(opts.print_format, duration, sign)
    if opts.duration_print_format:
        _convert_duration(date_time_oper, opts, [out])
        sys.exit(0)
    print(out)


def _convert_duration(date_time_oper, opts, args):
    """Implement usage 3 of "rose date", convert ISO8601 duration."""
    time_in_8601 = date_time_oper.duration_parser.parse(
        args[0].replace('\\', '')
    )  # allows parsing of negative durations
    time = time_in_8601.get_seconds()
    options = {'S': time, 'M': time / 60, 'H': time / 3600}
    if opts.duration_print_format.upper() in options:
        # supplied duration format is valid (upper removes case-sensitivity)
        print(options[opts.duration_print_format.upper()])
    else:
        # supplied duration format not valid
        print(
            'Invalid date/time format, please use one of H, M, S '
            + '(hours, minutes, seconds)'
        )
        sys.exit(1)


def upgrade_offset(offset: str) -> str:
    """Convert offset values in the legacy format

    Args:
        offset: offset matching [0-9]+[wdhms]

    Returns: Offset in isodate compatible format.

    URL:
        https://github.com/metomi/rose/issues/2577

    Examples:
        >>> upgrade_offset('1w')
        'P7DT0H0M0S'
        >>> upgrade_offset('1w1d1h')
        'P8DT1H0M0S'
        >>> upgrade_offset('1h1d')
        'P1DT1H0M0S'
    """

    sign = '-' if offset[0] == '-' else ''
    offsets = LEGACY_OFFSET.findall(offset)
    offsets = {unit.upper(): number for number, unit in offsets}

    # Rose 2019 did not make any distinction between 1s1m and 1m1s,
    # so we do an implicit sort here:
    weeks, days, hours, minutes, seconds = [0 for _ in range(5)]
    for unit, value in offsets.items():
        if unit == 'W':
            weeks = int(value)
        if unit == 'D':
            days = int(value)
        if unit == 'H':
            hours = int(value)
        if unit == 'M':
            minutes = int(value)
        if unit == 'S':
            seconds = int(value)

    days = days + weeks * 7

    result = f'{sign}P{days}DT{hours}H{minutes}M{seconds}S'

    print(
        f'[WARN] This offset syntax {offset} is deprecated: Using {result}',
        file=sys.stderr,
    )

    return result


def upgrade_cylc5_datetime(datetime: str) -> str:
    """Replace a Cylc 5 style (%Y%m%d%h) datetime with a ISO8601 datetime.

    Examples:
        >>> upgrade_cylc5_datetime('2022010101')
        '20220101T01'
    """
    upgraded = f'{datetime[:-2]}T{datetime[-2:]}'

    print(
        f'[WARN] This datetime syntax {datetime}'
        f' is deprecated. Use {upgraded} instead',
        file=sys.stderr
    )

    return upgraded


def upgrade_unix_datetime(datetime_str: str) -> str:
    """Replace a Unix Style Datetime string with an ISO8601 Datetime String.

    Examples:
        >>> upgrade_unix_datetime('Tue May 10 22:09:01 GMT 2022')
        '2022-05-10T22:09:01'

    Note:
        Support of Timezones seems to be dependent on system setup and
        may be very variable.
    """
    upgraded = datetime.strptime(
        datetime_str, "%a %b %d %H:%M:%S %Z %Y"
    ).strftime("%Y-%m-%dT%H:%M:%S%z")

    print(
        f'[WARN] This datetime syntax {datetime_str} '
        f'is deprecated. Use {upgraded} instead',
        file=sys.stderr
    )

    return upgraded


if __name__ == "__main__":
    main()
