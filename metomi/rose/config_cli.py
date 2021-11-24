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
"""Implements the "rose config" command."""

import os
import sys

from metomi.rose.config import (
    ConfigDumper,
    ConfigLoader,
    ConfigNode,
    ConfigSyntaxError,
)
from metomi.rose.env import env_var_process
import metomi.rose.macro
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Event, Reporter
from metomi.rose.resource import ResourceLocator


class MetadataNotFoundEvent(Event):

    """Warn when there is no metadata."""

    LEVEL = Event.WARN
    KIND = Event.KIND_ERR

    def __str__(self):
        return "%s: metadata not found" % str(self.args[0])


def get_meta_path(root_node, rel_path=None, meta_key=False):
    if meta_key:
        dir_path = None
    elif rel_path:
        dir_path = os.path.abspath(rel_path)
    else:
        dir_path = os.getcwd()
    meta_dir = metomi.rose.macro.load_meta_path(
        config=root_node, directory=dir_path
    )[0]
    if meta_dir is None:
        return None
    else:
        return os.path.join(meta_dir, "rose-meta.conf")


def main():
    """Implement the "rose config" command."""
    opt_parser = RoseOptionParser(
        description='''
Parse and print rose configuration files.

With no option and no argument, print the rose site + user configuration.

EXAMPLES
    # Print the value of OPTION in SECTION.
    rose config SECTION OPTION

    # Print the value of OPTION in SECTION in FILE.
    rose config --file=FILE SECTION OPTION

    # Print the value of OPTION in SECTION if exists, or VALUE otherwise.
    rose config --default=VALUE SECTION OPTION

    # Print the OPTION=VALUE pairs in SECTION.
    rose config SECTION

    # Print the value of a top level OPTION.
    rose config OPTION

    # Print the OPTION keys in SECTION.
    rose config --keys SECTION

    # Print the SECTION keys.
    rose config --keys

    # Exit with 0 if OPTION exists in SECTION, or 1 otherwise.
    rose config -q SECTION OPTION

    # Exit with 0 if SECTION exists, or 1 otherwise.
    rose config -q SECTION

    # Combine the configurations in FILE1 and FILE2, and dump the result.
    rose config --file=FILE1 --file=FILE2

    # Print the value of OPTION in SECTION of the metadata associated with
    # the specified config FILE
    rose config --file=FILE --meta SECTION OPTION

    # Print the value of a specified metadata KEY
    rose config --meta-key=KEY
        ''',
        epilog='''
ENVIRONMENT VARIABLES
    optional ROSE_META_PATH
        Prepend `$ROSE_META_PATH` to the metadata search path.
        '''
    )
    opt_parser.add_my_options(
        "default",
        "env_var_process_mode",
        "files",
        "keys",
        "meta",
        "meta_key",
        "no_ignore",
        "no_opts",
        "print_conf_mode",
    )
    # the quietness argument is non-standard for this command
    opt_parser.modify_option(
        'quietness',
        help=(
            "Exit with 0 if the specified `SECTION` and/or `OPTION` exist in"
            " the configuration, or 1 otherwise."
        ),
    )

    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)
    metomi.rose.macro.add_meta_paths()

    if opts.meta_key:
        opts.meta = True

    if opts.files and opts.meta_key:
        report(Exception("Cannot specify both a file and meta key."))
        sys.exit(1)

    config_loader = ConfigLoader()
    sources = []
    if opts.files:
        root_node = ConfigNode()
        for fname in opts.files:
            if fname == "-":
                sources.append(sys.stdin)
            else:
                if opts.meta:
                    try:
                        root_node = config_loader.load(fname)
                    except ConfigSyntaxError as exc:
                        report(exc)
                        sys.exit(1)
                    rel_path = os.sep.join(fname.split(os.sep)[:-1])
                    fpath = get_meta_path(root_node, rel_path)
                    if fpath is None:
                        report(MetadataNotFoundEvent(fname))
                    else:
                        sources.append(fpath)
                else:
                    sources.append(fname)
    elif opts.meta:
        root_node = ConfigNode()
        if opts.meta_key:
            root_node.set(["meta"], opts.meta_key)
        else:
            fname = os.path.join(os.getcwd(), metomi.rose.SUB_CONFIG_NAME)
            try:
                root_node = config_loader.load(fname)
            except ConfigSyntaxError as exc:
                report(exc)
                sys.exit(1)
        fpath = get_meta_path(root_node, meta_key=opts.meta_key)
        root_node.unset(["meta"])
        if fpath is None:
            report(Exception("Metadata not found"))
            sys.exit(1)
        else:
            sources.append(fpath)
    else:
        root_node = ResourceLocator.default().get_conf()

    for source in sources:
        try:
            if opts.meta or opts.no_opts:
                config_loader.load(source, root_node)
            else:
                config_loader.load_with_opts(source, root_node)
        except (ConfigSyntaxError, IOError) as exc:
            report(exc)
            sys.exit(1)
        if source is sys.stdin:
            source.close()

    if opts.quietness:
        sys.exit(root_node.get(args, opts.no_ignore) is None)

    if opts.keys_mode:
        try:
            keys = list(root_node.get(args, opts.no_ignore).value)
        except AttributeError:
            sys.exit(1)
        keys.sort()
        for key in keys:
            print(key)
        sys.exit()

    conf_dump = ConfigDumper()
    if len(args) == 0:
        conf_dump(root_node, concat_mode=opts.print_conf_mode)
        sys.exit()

    node = root_node.get(args, opts.no_ignore)

    if node is not None and isinstance(node.value, dict):
        if opts.print_conf_mode:
            conf_dump(ConfigNode().set(args, node.value), concat_mode=True)
            sys.exit()

        keys = list(node.value)
        keys.sort()
        for key in keys:
            node_of_key = node.get([key], opts.no_ignore)
            if node_of_key:
                value = node_of_key.value
                state = node_of_key.state
                string = "%s%s=%s" % (state, key, value)
                lines = string.splitlines()
                print(lines[0])
                i_equal = len(state + key) + 1
                for line in lines[1:]:
                    print(" " * i_equal + line)
        sys.exit()

    if node is None:
        if opts.default is None:
            sys.exit(1)
        value = opts.default
    elif opts.env_var_process_mode:
        value = env_var_process(node.value)
    else:
        value = node.value
    if opts.print_conf_mode:
        conf_dump(ConfigNode().set(args, value), concat_mode=True)
    else:
        print(value)
    sys.exit()


if __name__ == "__main__":
    main()
