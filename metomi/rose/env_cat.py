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
"""Implements "rose env-cat"."""


import sys

from metomi.rose.reporter import Reporter
from metomi.rose.env import UnboundEnvironmentVariableError, env_var_process
from metomi.rose.opt_parse import RoseOptionParser


def rose_env_cat(args, opts):
    if not args:
        args = ["-"]
    if not opts.output_file or opts.output_file == "-":
        out_handle = sys.stdout
    else:
        out_handle = open(opts.output_file, "w")
    for arg in args:
        if arg == "-":
            in_handle = sys.stdin
        else:
            try:
                in_handle = open(arg)
            except FileNotFoundError as exc:
                Reporter().report(exc)
                if opts.debug_mode:
                    raise exc
                return
        line_num = 0
        while True:
            line_num += 1
            line = in_handle.readline()
            if not line:
                break
            try:
                out_handle.write(
                    env_var_process(
                        line, opts.unbound, opts.match_mode
                    )
                )
            except UnboundEnvironmentVariableError as exc:
                name = arg
                if arg == "-":
                    name = "<STDIN>"
                sys.exit("%s:%s: %s" % (name, line_num, str(exc)))
        in_handle.close()
    out_handle.close()


def main():
    """Implement "rose env-cat"."""
    opt_parser = RoseOptionParser(
        usage='rose env-cat [OPTIONS] [FILE ...]',
        description=r'''
Substitute environment variables in input files and print.

If no argument is specified, read from STDIN. One `FILE` argument may be
`-`, which means read from STDIN.

In `match-mode=default`, the command will look for `$NAME` or `${NAME}`
syntax and substitute them with the value of the environment variable
`NAME`. A backslash in front of the syntax, e.g. `\$NAME` or `\${NAME}`
will escape the substitution.

In `match-mode=brace`, the command will look for `${NAME}` syntax only.

EXAMPLES
    rose env-cat [OPTIONS] [FILE ...]
        '''
    )
    opt_parser.add_my_options("match_mode", "output_file", "unbound")
    opt_parser.modify_option(
        'output_file',
        help=(
            "Specify an output file."
            "\nIf no output file is specified or if `FILE`"
            "is `-`, write output to STDOUT."
        ),
    )
    opts, args = opt_parser.parse_args()
    rose_env_cat(args, opts)


if __name__ == "__main__":
    main()
