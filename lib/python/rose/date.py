# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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

from datetime import datetime
import os
from rose.opt_parse import RoseOptionParser


class DateTimeParser(object):
    """Parser of date time strings to datetime.datetime objects."""

    FORMAT_STRS = {}

    def __init__(self):
        self.format_strs = self.FORMAT_STRS

    def parse(self, s, format_str=None):
        """Parse string "s" and return a 3-element tuple.
        
        The elements in the tuple are (datetime_s, format_key, format_str):
        
        datetime_s is the datetime object representation of "s".
        format_key is the key of the format string used to parse "s".
        format_str is the format string used to parse "s".

        """
        pass # TODO

    __call__ = parse


class DateTimeFormatter(object):
    """Format datetime.datetime objects to ."""
    FORMAT_STR = "%a %b %d %H:%M:%S %Z %Y"

    def __init__(self, format_str=None, is_utc=False):
        if format_str is None:
            format_str = FORMAT_STR
        self.format_str = format_str
        self.is_utc = is_utc

    def format(self, d, format_str=None, is_utc=None):
        """Format datetime object "d" to a string."""
        if format_str is None:
            format_str = self.format_str
        if is_utc is None:
            is_utc = self.is_utc
        if is_utc:
            tz = os.getenv("TZ", None)
            os.environ["TZ"] = "UTC"
        try:
            return d.strftime(self.format_str)
        finally:
            if is_utc:
                if tz:
                    os.environ["TZ"] = tz
                else:
                    os.environ.pop("TZ")


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("offset", "parse_format", "parse_utc",
                              "print_format", "print_utc")
    opts, args = opt_parser.parse_args()

    if opts.parse_utc:
        tz = os.getenv("TZ", None)
        os.environ["TZ"] = "UTC"
    try:
        if args:
            d = DateTimeParser().parse(args[0], opts.parse_format)
        else:
            d = datetime.now()
    finally:
        if is_utc:
            if tz:
                os.environ["TZ"] = tz
            else:
                os.environ.pop("TZ")

    # TODO: d + offset
    if opts.offset:
        pass

    print DateTimeFormatter().format(
            d, format_str=opts.print_format, is_utc=opts.print_utc)


if __name__ == "__main__":
    main()
