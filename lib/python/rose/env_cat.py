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
"""Implements "rose env-cat"."""


from rose.env import env_var_process, UnboundEnvironmentVariableError
from rose.opt_parse import RoseOptionParser
import sys


def main():
    """Implement "rose env-cat"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("unbound")
    opts, args = opt_parser.parse_args()
    if not args:
        args = ["-"]
    for arg in args:
        if arg == "-":
            f = sys.stdin
        else:
            f = open(arg)
        line_num = 0
        while True:
            line_num += 1
            line = f.readline()
            if not line:
                break
            try:
                sys.stdout.write(env_var_process(line, opts.unbound))
            except UnboundEnvironmentVariableError as e:
                name = arg
                if arg == "-":
                    name = "<STDIN>"
                sys.exit("%s:%s: %s" % (name, line_num, str(e)))
        f.close()


if __name__ == "__main__":
    main()
