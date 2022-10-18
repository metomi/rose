# Copyright (C) British Crown (Met Office) & Contributors.
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
import argparse
from inspect import signature
import os
from pathlib import Path
import sys

from pkg_resources import (
    DistributionNotFound,
    iter_entry_points,
)

from metomi.rose import (
    __file__ as rose_init_file,
    __version__,
)
from metomi.rose.scripts import (
    __file__ as script_init_file,
)


USAGE = f'''
Rose {__version__}

Rose is a toolkit for writing, editing and running application configurations.
'''


# fmt: off
DEAD_ENDS = {
    # messages to show for commands which have been removed or renamed
    # (ns, sub_cmd): message
    ('rosa', 'rpmbuild'):
        'Rosa RPM Builder has been removed.',
    ('rose', 'config-edit'): (
        'The Rose configuration editor has been removed. The old '
        'Rose 2019 GUI remains compatible with Rose 2 configurations.'
    ),
    ('rose', 'edit'): (
        'The Rose configuration editor has been removed. The old '
        'Rose 2019 GUI remains compatible with Rose 2 configurations.'
    ),
    ('rose', 'metadata-graph'):
        'This command has been removed pending re-implementation',
    ('rose', 'suite-clean'):
        'This command has been replaced by: "cylc clean".',
    ('rose', 'suite-cmp-vc'):
        'This command is awaiting re-implementation in Cylc 8',
    ('rose', 'suite-gcontrol'):
        'This command has been removed: use the Cylc GUI.',
    ('rose', 'sgc'):
        'This command has been removed: use the Cylc GUI.',
    ('rose', 'suite-hook'):
        'Command obsolete, use Cylc event handlers',
    ('rose', 'task-hook'):
        'Command obsolete, use Cylc event handlers',
    ('rose', 'suite-log-view'):
        'This command has been removed: use cylc review at Cylc 7 instead.',
    ('rose', 'suite-log'):
        'This command has been removed: use cylc review at Cylc 7 instead.',
    ('rose', 'slv'):
        'This command has been removed: use cylc review at Cylc 7 instead.',
    ('rose', 'suite-restart'):
        'This command has been replaced by: "cylc restart".',
    ('rose', 'suite-run'):
        'This command has been replaced by: "cylc install".',
    ('rose', 'suite-init'):
        'This command has been replaced by: "cylc install".',
    ('rose', 'suite-scan'):
        'This command has been replaced by: "cylc scan".',
    ('rose', 'suite-shutdown'):
        'This command has been replaced by: "cylc stop".',
    ('rose', 'suite-stop'):
        'This command has been replaced by: "cylc stop".',
    ('rosie', 'disco'):
        'Rosie Disco has been disabled pending fixes at a later release.',
    ('rosie', 'go'):
        'This command has been removed pending re-implementation',
}


ALIASES = {
    # aliases for commands
    # (ns, alias): (ns, sub_cmd)
    ('rosie', 'co'):
        ('rosie', 'checkout'),
    ('rosie', 'copy'):
        ('rosie', 'create')
}
# fmt: on


PYTHON_SUB_CMDS = {
    # python sub commands - extracted from entry points
    # (ns, sub_cmd): entry_point
    **{
        ('rose', entry_point.name): entry_point
        for entry_point in iter_entry_points('rose.commands')
    },
    **{
        ('rosie', entry_point.name): entry_point
        for entry_point in iter_entry_points('rosie.commands')
    }
}


BASH_SUB_CMDS = {
    # bash sub commands - hardcoded
    # NOTE: script must exist in the bin/ directory as `{ns}-{sub_cmd}`.
    # (ns, sub_cmd)
    ('rosa', 'db-create'),
    ('rosa', 'svn-post-commit'),
    ('rosa', 'svn-pre-commit'),
    ('rosa', 'ws'),
    ('rose', 'mpi-launch'),
    ('rose', 'tutorial'),
}


def exec_sub_cmd(ns, sub_cmd, args):
    # set env used by the ResourceLocator
    os.environ['ROSE_NS'] = ns
    os.environ['ROSE_UTIL'] = sub_cmd
    os.environ['ROSE_HOME'] = str(Path(rose_init_file).parent)

    if (ns, sub_cmd) in BASH_SUB_CMDS:
        # run bash cmd
        _exec_bash(ns, sub_cmd, args)
    elif (ns, sub_cmd) in PYTHON_SUB_CMDS:
        # run python cmd
        _exec_python(
            ns,
            sub_cmd,
            PYTHON_SUB_CMDS[(ns, sub_cmd)],
            args,
        )

    # invalid cmd (should be caught before this)
    print(f'No such command: {ns} {sub_cmd}', file=sys.stderr)
    sys.exit(1)


def _exec_bash(ns, sub_cmd, args):
    script_file = Path(
        script_init_file,
    ).parent.joinpath(
        f'{ns}-{sub_cmd}',
    ).resolve()
    os.execv(
        script_file,
        ['bash', *args]  # note the first argument is ignored
    )
    sys.exit(0)


def _exec_python(ns, sub_cmd, entry_point, args):
    # load the entry point
    fcn = load_entry_point(entry_point)

    # set the argv for the sub command
    sys.argv = [f'{ns}-{sub_cmd}', *args]

    # run the entry point
    if signature(fcn).parameters:
        fcn(args)
    else:
        fcn()
    sys.exit(0)


def load_entry_point(entry_point):
    try:
        return entry_point.load()
    except DistributionNotFound:
        print(
            (
                'This functionality requires optional dependencies:'
                f' {", ".join(entry_point.extras)}'
                '\n(e.g. pip install metomi-rose'
                f' [{",".join(entry_point.extras)}])'
            ),
            file=sys.stderr
        )
        sys.exit(1)


def _get_sub_cmds(ns):
    for ns_, sub_cmd in set(PYTHON_SUB_CMDS) | BASH_SUB_CMDS:
        if ns_ == ns:
            yield sub_cmd


def get_arg_parser(description, sub_cmds, ns):
    epilog = f'Commands:\n  {ns} ' + f'\n  {ns} '.join(sorted(sub_cmds))
    parser = argparse.ArgumentParser(
        add_help=False,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--help', '-h',
        action='store_true',
        default=False,
        dest='help_'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        default=False,
        dest='version'
    )
    return parser


def rose():
    main(
        'rose',
        (
            f'Rose {__version__}:'
            ' A toolkit for writing, editing'
            ' and running application configurations.'
        ),
    )


def rosie():
    main(
        'rosie',
        (
            f'Rosie {__version__}:'
            ' An SVN version control system for suites of scientific'
            ' applications.'
        ),
    )


def rosa():
    main(
        'rosa',
        (
            f'Rosa {__version__}:'
            ' Admin utilities for Rosie.'
        ),
    )


def _version(ns, long=False):
    print(
        f'{ns} {__version__}'
        + (
            f' ({Path(sys.executable).parent.parent})'
            if long
            else ''
        )
    )
    sys.exit(0)


def _doc(ns):
    for ns_, sub_cmd in sorted(set(PYTHON_SUB_CMDS) | BASH_SUB_CMDS):
        if ns_ != ns:
            continue
        if (ns, sub_cmd) in DEAD_ENDS:
            continue
        print('\n==================================================')
        print(f'{ns} {sub_cmd}')
        print('==================================================\n')
        from subprocess import Popen, PIPE, DEVNULL
        proc = Popen(
            [ns, sub_cmd, '--help'],
            stdin=DEVNULL,
            stdout=PIPE,
            text=True
        )
        print(proc.communicate()[0])
    sys.exit(0)


def _help(ns, parser=None, sub_cmd=None):
    if parser:
        parser.print_help()
    elif sub_cmd:
        exec_sub_cmd(ns, sub_cmd, ('--help',))
    sys.exit(0)


def _check_dead_ends(*key):  # (ns, sub_cmd)
    if key in DEAD_ENDS:
        print(DEAD_ENDS[key], file=sys.stderr)
        sys.exit(1)


def _check_aliases(*key):  # (ns, sub_cmd)
    if key in ALIASES:
        return ALIASES[key]
    return key


def main(ns, desc):
    parser = get_arg_parser(desc, _get_sub_cmds(ns), ns)
    opts, cmd_args = parser.parse_known_args()

    if not cmd_args:
        if opts.version:
            _version(ns)
        else:
            _help(ns, parser)

    sub_cmd, *cmd_args = cmd_args

    if sub_cmd in ('help', 'h', '?'):
        try:
            ns, sub_cmd = _check_aliases(ns, cmd_args[0])
            _help(ns, sub_cmd=sub_cmd)
        except IndexError:
            _help(ns, parser)

    if sub_cmd == 'version':
        _version(ns, '--long' in cmd_args)

    if sub_cmd == 'doc':
        _doc(ns)

    if opts.help_:
        # the --help opt gets stripped by this parser so we must put it back
        cmd_args.append('--help')

    _check_dead_ends(ns, sub_cmd)
    ns, sub_cmd = _check_aliases(ns, sub_cmd)

    exec_sub_cmd(ns, sub_cmd, cmd_args)
