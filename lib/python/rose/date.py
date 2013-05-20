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


FORMATS = ["%a %b %d %H:%M:%S %Y",    # ctime
           "%a %b %d %H:%M:%S %Z %Y", # Unix "date"
           "%Y-%m-%dT%H:%M:%S",       # ISO8601, normal
           "%Y%m%dT%H%M%S",           # ISO8601, abbr
           "%Y%m%d%H"];               # Cylc


UNITS = {"w": "weeks",
         "d": "days",
         "h": "hours",
         "m": "minutes",
         "s": "seconds"}


REC_OFFSET = re.compile(
        r"""\A(?P<sign>[\+\-])?(?P<num>\d+)(?P<unit>[wdhms])\Z""", re.I)


def date_shift(offsets=None, parse_format=None, print_format=None,
               task_cycle_time_mode=None, *args):
    """Return a date string with an offset.

    If args specified, use args[0] as the date-time string. If args not
    specified and if task_cycle_time_mode is True, use ROSE_TASK_CYCLE_TIME
    environment variable if it is defined. Otherwise, use current time.

    If offsets is specified, it should be a list of offsets that have the
    format "[+/-]nU" where "n" is an integer, and U is a unit matching a key in
    rose.date.UNITS.

    If parse_format is specified, parse args[0] with the specified format.
    Otherwise, parse args[0] with one of the format strings in
    rose.date.FORMATS. The format should be a string compatible to strptime(3).

    If print_format is specified, return a string as specified in the format.
    Otherwise, use the parse_format.

    """
    # Parse
    parse_formats = FORMATS
    if parse_format:
        parse_formats = [parse_format]
    if not args and task_cycle_time_mode:
        arg = os.getenv("ROSE_TASK_CYCLE_TIME")
        if arg is None:
            raise UnboundEnvironmentVariableError("ROSE_TASK_CYCLE_TIME")
        args = [arg]
    if not args or args[0] == "now":
        d, parse_format = (datetime.now(), parse_formats[0])
    else:
        while parse_formats:
            parse_format = parse_formats.pop(0)
            try:
                d = datetime.strptime(args[0], parse_format)
                break
            except ValueError as e:
                if not parse_formats:
                    raise e

    # Offset
    if offsets is not None:
        for offset in offsets:
            match = REC_OFFSET.match(offset.lower())
            if not match:
                raise ValueError(offset)
            sign, num, unit = match.group("sign", "num", "unit")
            num = int(num)
            if sign == "-":
                num = -num
            key = UNITS[unit]
            d += timedelta(**{key: num})

    # Format
    if print_format is None:
        print_format = parse_format
    return d.strftime(print_format)


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("offsets", "parse_format", "print_format",
                              "task_cycle_time_mode")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    try:
        print date_shift(opts.offsets, opts.parse_format, opts.print_format,
                         opts.task_cycle_time_mode, *args)
    except Exception as e:
        if opts.debug_mode:
            import traceback
            traceback.print_exc(e)
        else:
            report(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
