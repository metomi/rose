# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
"""Implements "rose env-cat"."""


from metomi.rose.env import env_var_process, UnboundEnvironmentVariableError
from metomi.rose.opt_parse import RoseOptionParser
import sys


def main():
    """Implement "rose env-cat"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("match_mode", "output_file", "unbound")
    opts, args = opt_parser.parse_args()
    if not args:
        args = ["-"]
    if not opts.output_file or opts.output_file == "-":
        out_handle = sys.stdout
    else:
        out_handle = open(opts.output_file, "wb")
    for arg in args:
        if arg == "-":
            in_handle = sys.stdin
        else:
            in_handle = open(arg)
        line_num = 0
        while True:
            line_num += 1
            line = in_handle.readline()
            if not line:
                break
            try:
                out_handle.write(
                    env_var_process(line, opts.unbound, opts.match_mode))
            except UnboundEnvironmentVariableError as exc:
                name = arg
                if arg == "-":
                    name = "<STDIN>"
                sys.exit("%s:%s: %s" % (name, line_num, str(exc)))
        in_handle.close()
    out_handle.close()


if __name__ == "__main__":
    main()
