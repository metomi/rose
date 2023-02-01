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
"""NAME
    rose date

SYNOPSIS
    # 1. Print date time point
    # 1.1 Current date time with an optional offset
    rose date [--offset=OFFSET]
    rose date now [--offset=OFFSET]
    rose date ref [--offset=OFFSET]
    # 1.2 Task cycle date time with an optional offset
    #     Assume: export ROSE_TASK_CYCLE_TIME=20371225T000000Z
    rose date -c [--offset=OFFSET]
    rose date -c ref [--offset=OFFSET]
    # 1.3 A specific date time with an optional offset
    rose date 20380119T031407Z [--offset=OFFSET]

    # 2. Print duration
    # 2.1 Between now (+ OFFSET1) and a future date time (+ OFFSET2)
    rose date now [--offset1=OFFSET1] 20380119T031407Z [--offset2=OFFSET2]
    # 2.2 Between a date time in the past and now
    rose date 19700101T000000Z now
    # 2.3 Between task cycle time (+ OFFSET1) and a future date time
    #     Assume: export ROSE_TASK_CYCLE_TIME=20371225T000000Z
    rose date -c ref [--offset1=OFFSET1] 20380119T031407Z
    # 2.4 Between task cycle time and now (+ OFFSET2)
    #     Assume: export ROSE_TASK_CYCLE_TIME=20371225T000000Z
    rose date -c ref now [--offset2=OFFSET2]
    # 2.5 Between a date time in the past and the task cycle date time
    #     Assume: export ROSE_TASK_CYCLE_TIME=20371225T000000Z
    rose date -c 19700101T000000Z ref
    # 2.6 Between 2 specific date times
    rose date 19700101T000000Z 20380119T031407Z

    # 3.  Convert ISO8601 duration
    # 3.1 Into the total number of hours (H), minutes (M) or seconds (S)
    #     it represents, preceed negative durations with a double backslash
    #     (e.g. \\-PT1H)
    rose date --as-total=s PT1H

DESCRIPTION
    Parse and print 1. a date time point or 2. a duration.

    1. With 0 or 1 argument. Print the current or the specified date time
       point with an optional offset.

    2. With 2 arguments. Print the duration between the 2 arguments.

OPTIONS
    --as-total=TIME_FORMAT
        Used to express an ISO8601 duration in the specified time format,
        hours `H`, minutes `M` or seconds `S`.
    --calendar=gregorian|360day|365day|366day
        Specify the calendar mode. See `CALENDAR MODE` below.
    --offset1=OFFSET, --offset=OFFSET, -s OFFSET, -1 OFFSET
        Specify 1 or more offsets to add to argument 1 or the current time.
        See `OFFSET FORMAT` below.
    --offset2=OFFSET, -2 OFFSET
        Specify 1 or more offsets to add to argument 2.
        See `OFFSET FORMAT` below.
    --parse-format=FORMAT, -p FORMAT
        Specify a format for parsing `DATE-TIME`. See `PARSE FORMAT` below.
    --print-format=FORMAT, --format=FORMAT, -f FORMAT
        Specify a format for printing the result. See `PRINT FORMAT` below.
    --use-task-cycle-time, -c
        Use the value of the `ROSE_TASK_CYCLE_TIME` environment variable as
        the reference time instead of the current time.
    --utc, -u
        Assume date time in UTC instead of local or other time zones.

CALENDAR MODE
    The calendar mode is determined (in order) by:

    1. The `--calendar=MODE` option.
    2. The `ROSE_CYCLING_MODE` or `ISODATETIMECALENDAR` environment variable.
          (ROSE_CYCLING_MODE over-rides if both set)
    3. Default to "gregorian".

ENVIRONMENT VARIABLES
    In both cases the ROSE.* variable will over-ride the ISODATETIME variable
    if both are set to ensure legacy behaviour for Rose.

    ROSE_CYCLING_MODE/ISODATETIMECALENDAR=gregorian|360day|365day|366day
        Specify the calendar mode.
    ROSE_TASK_CYCLE_TIME/ISODATETIMEREF
        Specify the current cycle time of a task in a suite. If the
        `--use-task-cycle-time` option is set, the value of this environment
        variable is used by the command as the reference time instead of the
        current time.

OFFSET FORMAT
    `OFFSET` must follow the ISO 8601 duration representations such as
    `PnW` or `PnYnMnDTnHnMnS - P` followed by a series of `nU` where `U` is
    the unit (`Y`, `M`, `D`, `H`, `M`, `S`) and `n` is a positive integer,
    where `T` delimits the date series from the time series if any time units
    are used. `n` may also have a decimal (e.g. `PT5.5M`) part for a unit
    provided no smaller units are supplied. It is not necessary to
    specify zero values for units. If `OFFSET` is negative, prefix a `-`.
    For example:

    * `P6D` - 6 day offset
    * `PT6H` - 6 hour offset
    * `PT1M` - 1 minute offset
    * `-PT1M` - (negative) 1 minute offset
    * `P3M` - 3 month offset
    * `P2W` - 2 week offset (note no other units may be combined with weeks)
    * `P2DT5.5H` - 2 day, 5.5 hour offset
    * `-P2YT4S` - (negative) 2 year, 4 second offset

PARSE FORMAT
    The format for parsing a date time point should be compatible with the
    POSIX strptime template format (see the strptime command help), with the
    following subset supported across all date/time ranges:

    `%F`, `%H`, `%M`, `%S`, `%Y`, `%d`, `%j`, `%m`, `%s`, `%z`

    If not specified, the system will attempt to parse `DATE-TIME` using
    the following formats:

    * ctime: `%a %b %d %H:%M:%S %Y`
    * Unix date: `%a %b %d %H:%M:%S %Z %Y`
    * Basic ISO8601: `%Y-%m-%dT%H:%M:%S`, `%Y%m%dT%H%M%S`
    * Cylc 5: `%Y%m%d%H` (deprecated)

    If none of these match, the date time point will be parsed according to
    the full ISO 8601 date/time standard.

PRINT FORMAT
    For printing a date time point, the print format will default to the same
    format as the parse format. Also supports the isodatetime library dump
    syntax for these operations which follows ISO 8601 example syntax - for
    example:

    * `CCYY-MM-DDThh:mm:ss` -> `1955-11-05T09:28:00`,
    * `CCYY` -> `1955`,
    * `CCYY-DDD` -> `1955-309`,
    * `CCYY-Www-D` -> `1955-W44-6`.

    Usage of this ISO 8601-like syntax should be as ISO 8601-compliant
    as possible.

    Note that specifying an explicit timezone in this format (e.g.
    `CCYY-MM-DDThh:mm:ss+0100` or `CCYYDDDThhmmZ` will automatically
    adapt the date/time to that timezone i.e. apply the correct
    hour/minute UTC offset.

    For printing a duration, the following can be used in format
    statements:

    * `y`: years
    * `m`: months
    * `d`: days
    * `h`: hours
    * `M`: minutes
    * `s`: seconds

    For example, for a duration `P57DT12H` - `y,m,d,h` -> `0,0,57,12`
"""

import sys
import os

from metomi.isodatetime.main import main as iso_main

from metomi.rose.date import (
    LEGACY_OFFSET, upgrade_offset,
    CYLC5_FORMAT, upgrade_cylc5_datetime,
    UNIX_FORMAT, upgrade_unix_datetime
)


def _handle_old_offsets(args: list) -> list:
    """Handle Legacy Rose date --offset values:

    # https://github.com/metomi/rose/issues/2577


    Examples:
    >>> _handle_old_offsets(['rose-date', '--offset=1d1s'])
    ['rose-date', '--offset=P1DT0H0M1S']
    >>> _handle_old_offsets(['rose-date', '-s', '1d1s'])
    ['rose-date', '-s', 'P1DT0H0M1S']
    """
    for index, arg in enumerate(args):
        if arg.startswith(('--offset', '-s')):
            # Case: --offset=<offset> is a single item in args list:
            if (
                '=' in arg
                and LEGACY_OFFSET.match(arg.split('=')[1])
            ):
                offset = upgrade_offset(arg.split("=")[1])
                args[index] = f'{arg.split("=")[0]}={offset}'
            # Case: --offset <offset> is two items in args list:
            elif (
                index + 1 < len(args)
                and LEGACY_OFFSET.match(args[index + 1])
            ):
                args[index] = args[index].replace('=', '')
                args[index + 1] = upgrade_offset(args[index + 1])
    return args


def _handle_old_datetimes(args: list) -> list:
    """Handle Legacy Rose date formats

    # https://github.com/metomi/rose/issues/2589

    Examples

    """
    for i, arg in enumerate(args[1:], start=1):
        if (
            not (
                args[i - 1].startswith('--')
                and '=' not in args[i - 1]
            )
            and not arg.startswith('--')
        ):
            if CYLC5_FORMAT.match(arg):
                args[i] = upgrade_cylc5_datetime(arg)
            elif UNIX_FORMAT.match(arg):
                args[i] = upgrade_unix_datetime(arg)
    return args


def _main(argv):
    """Implement rose date."""
    if sys.stdin.isatty():
        print(
            'WARNING: "rose date" is deprecated, use the "isodatetime" '
            'command.',
            file=sys.stderr
        )

    if '--help' in argv:
        print('\n' + __doc__)
        return 0

    argv = _handle_old_datetimes(argv)
    argv = _handle_old_offsets(argv)

    # Handle Legacy Rose-date -c functionality
    if '-c' in argv or '--use-task-cycle-time' in argv:
        if os.getenv('ROSE_TASK_CYCLE_TIME'):
            os.environ['ISODATETIMEREF'] = os.getenv('ROSE_TASK_CYCLE_TIME')
        elif not os.getenv('ISODATETIMEREF'):
            return (
                "[FAIL] [UNDEFINED ENVIRONMENT VARIABLE] ROSE_TASK_CYCLE_TIME"
            )

        for opt in ('-c', '--use-task-cycle-time'):
            if opt in argv:
                sys.argv.remove(opt)
        if 'ref' not in argv:
            argv.append('ref')

    # Convert ROSE_CYCLING_MODE to ISODATETIMECALENDAR
    if os.getenv('ROSE_CYCLING_MODE') not in ['integer', None]:
        os.environ['ISODATETIMECALENDAR'] = os.getenv('ROSE_CYCLING_MODE')

    sys.argv = argv
    return iso_main()


def main():
    sys.exit(
        _main(sys.argv)
    )
