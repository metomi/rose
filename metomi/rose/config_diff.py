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
# ----------------------------------------------------------------------------
"""Implements the "rose config-diff" command."""

import ast
import io
import os
import re
import shlex
import sys
import tempfile
from typing import List, Tuple

import metomi.rose.config
import metomi.rose.fs_util
import metomi.rose.macro
import metomi.rose.opt_parse
import metomi.rose.popen
import metomi.rose.resource
import metomi.rose.run


class ConfigDiffDefaults:

    """Store default settings for the rose config-diff command."""

    PROPERTIES = ",".join(
        [
            metomi.rose.META_PROP_TITLE,
            metomi.rose.META_PROP_NS,
            metomi.rose.META_PROP_DESCRIPTION,
            metomi.rose.META_PROP_HELP,
        ]
    )
    SHORTHAND: List[Tuple[str]] = []


_DEFAULTS = ConfigDiffDefaults()


def annotate_config_with_metadata(
    config, meta_config, ignore_regexes=None, metadata_properties=None
):
    """Add metadata to the metomi.rose.config.ConfigNode.comments attribute.

    config -- a metomi.rose.config.ConfigNode instance, containing app or
              suite data.
    meta_config -- a metomi.rose.config.ConfigNode instance, containing
                   metadata for config.
    ignore_regexes -- (default None) a list of uncompiled regular
                      expressions - if a setting contains any of these,
                      don't include it in the annotated output.

    """

    if ignore_regexes is None:
        ignore_regexes = []
    ignore_recs = [re.compile(_) for _ in ignore_regexes]
    unset_keys = []
    for keylist, node in config.walk():
        section = keylist[0]
        option = None
        if len(keylist) > 1:
            option = keylist[1]
        id_ = metomi.rose.macro.get_id_from_section_option(section, option)
        if any(_.search(id_) for _ in ignore_recs):
            unset_keys.append(keylist)
            continue
        metadata = metomi.rose.macro.get_metadata_for_config_id(
            id_, meta_config
        )
        metadata_text = format_metadata_as_text(
            metadata, only_these_options=metadata_properties
        )
        metadata_lines = [" " + line for line in metadata_text.splitlines()]
        node.comments = metadata_lines + node.comments
    for keylist in unset_keys:
        config.unset(keylist)
    return config


def expand_regexes_shorthands(in_regexes):
    """Expand any shorthand patterns in in_regexes."""
    if in_regexes is None:
        return None
    in_regexes = list(in_regexes)
    regexes = []
    while in_regexes:
        regex = in_regexes.pop(0)
        is_shorthand = False
        for shorthand, regexes in _DEFAULTS.SHORTHAND:
            if shorthand == regex:
                in_regexes.extend(regexes)
                is_shorthand = True
        if not is_shorthand:
            regexes.append(regex)
    return regexes


def format_metadata_as_text(metadata, only_these_options=None):
    """Convert a metadata dictionary to a block of text.

    metadata -- a dictionary with metadata keys and values.
    only_these_options -- (default None) if given, only output these
    metadata keys. Otherwise, output all metadata keys.

    """
    id_node = metomi.rose.config.ConfigNode()
    if only_these_options is None:
        # Default to every option.
        only_these_options = sorted(metadata.keys())
    for property_ in only_these_options:
        value = metadata.get(property_)
        if value is None:
            continue
        id_node.set([property_], value=value)
    string_file = io.StringIO()
    metomi.rose.config.dump(id_node, target=string_file)
    return string_file.getvalue()


def main():
    """Implement the "rose config-diff" command."""
    opt_parser = metomi.rose.opt_parse.RoseOptionParser(
        usage=(
            'rose config-diff [OPTIONS] FILE1 FILE2'
            ' [-- [DIFF_OPTIONS] [DIFF_ARGUMENTS]]'
        ),
        description='''
Display the metadata-annotated difference between two Rose config files.

EXAMPLES
    # Display the metadata-annotated diff between two Rose config files.
    rose config-diff FILE1 FILE2

    # Display the metadata-annotated diff between two Rose config dirs.
    rose config-diff DIR1 DIR2

    # Display the diff, ignoring particular setting patterns
    rose config-diff --ignore=namelist:foo FILE1 FILE2

    # Display the diff with a particular diff tool
    rose config-diff --diff-tool=kdiff3 FILE1 FILE2

    # Display the diff with some diff tool specific options/arguments
    rose config-diff FILE1 FILE2 -- [DIFF_OPTIONS] [DIFF_ARGUMENTS]
        ''',
        epilog='''
ENVIRONMENT VARIABLES
    optional ROSE_META_PATH
        Prepend `$ROSE_META_PATH` to the metadata search path.

ARGUMENTS
    PATH1, PATH2
        Two Rose configuration files or directories to compare.
        If the path is a directory, look underneath for a Rose configuration
        file. '-' for `PATH1` or `PATH2` denotes read in from standard input.
    ``--``
        Options and arguments after a `--` token are passed directly to the
        diff tool.

CONFIGURATION
    [external]diff-tool, [external]gdiff-tool
       You can override the default non-graphical and graphical diff tools
       by setting e.g::

          [external]
          diff-tool=diff3
          gdiff-tool=kompare

       in your site or user Rose configuration (`rose.conf`).

    [rose-config-diff]properties, [rose-config-diff]ignore{...}
       You can override the default metadata properties to display by
       setting e.g::

          [rose-config-diff]
          properties=title,ns,description,help

       in your site or user Rose configuration (`rose.conf`).
       You can also set shorthand ignore patterns by setting e.g.::

         [rose-config-diff]
         ignore{foo}=namelist:bar,namelist:baz

       in the same location. This will allow you to run::

          rose config-diff --ignore=foo ...

       instead of::

          rose config-diff --ignore=namelist:bar --ignore=namelist:baz ...
        '''
    )
    opt_parser.add_my_options(
        "diff_tool",
        "graphical",
        "ignore",
        "meta_path",
        "properties",
        "opt_conf_keys_1",
        "opt_conf_keys_2",
    )

    opts, args = opt_parser.parse_args()
    metomi.rose.macro.add_meta_paths()
    metomi.rose.macro.add_opt_meta_paths(opts.meta_path)

    paths, diff_args = args[:2], args[2:]

    if len(paths) != 2:
        sys.exit(opt_parser.get_usage())

    config_loader = metomi.rose.config.ConfigLoader()

    if opts.properties is None:
        properties = _DEFAULTS.PROPERTIES.split(",")
    else:
        properties = opts.properties.split(",")

    ignore_regexes = expand_regexes_shorthands(opts.ignore_patterns)

    # get file paths
    output_filenames = []
    config_type = metomi.rose.SUB_CONFIG_NAME
    file_paths = []
    for path in paths:
        if path == "-":
            file_paths.append(path)
            continue
        path = os.path.abspath(path)
        if os.path.isdir(path):
            for filename in metomi.rose.CONFIG_NAMES:
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path):
                    config_type = filename
                    file_paths.append(file_path)
                    break
            else:
                raise metomi.rose.run.ConfigNotFoundError(
                    path, metomi.rose.GLOB_CONFIG_FILE
                )
        else:
            config_type = os.path.basename(path)
            file_paths.append(path)

    # get opt_conf_keys for each file
    opt_conf_list = [[]] * len(file_paths)
    if opts.opt_conf_keys_1 is not None:
        opt_conf_list[0] = opts.opt_conf_keys_1
    if opts.opt_conf_keys_2 is not None:
        opt_conf_list[1] = opts.opt_conf_keys_2

    # get diffs
    for path, opt_conf_keys in zip(file_paths, opt_conf_list):
        if path == "-":
            path = sys.stdin
            filename = config_type
            directory = None
        else:
            directory, filename = path.rsplit(os.sep, 1)
        config = config_loader.load_with_opts(
            path, mark_opt_confs=True, more_keys=opt_conf_keys
        )
        meta_config_tree = metomi.rose.macro.load_meta_config_tree(
            config, directory=directory, config_type=filename
        )
        if meta_config_tree is None:
            meta_config = metomi.rose.config.ConfigNode()
        else:
            meta_config = meta_config_tree.node
        annotated_config = annotate_config_with_metadata(
            config,
            meta_config,
            ignore_regexes=ignore_regexes,
            metadata_properties=properties,
        )
        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, filename)
        metomi.rose.config.dump(annotated_config, target=output_path)
        output_filenames.append(output_path)
    popener = metomi.rose.popen.RosePopener()
    cmd_opts_args = diff_args + output_filenames
    if opts.diff_tool is None:
        if opts.graphical_mode:
            diff_cmd = popener.get_cmd("gdiff_tool", *cmd_opts_args)
        else:
            diff_cmd = popener.get_cmd("diff_tool", *cmd_opts_args)
    else:
        diff_cmd = shlex.split(opts.diff_tool) + cmd_opts_args
    return_code = 1
    try:
        return_code, stdout, stderr = popener.run(*diff_cmd)
        sys.stdout.buffer.write(stdout.encode())
        sys.stderr.buffer.write(stderr.encode())
    finally:
        fs_util = metomi.rose.fs_util.FileSystemUtil()
        for path in output_filenames:
            fs_util.delete(os.path.dirname(path))
    sys.exit(return_code)


def load_override_config():
    """Load user or site options for the config_diff command."""
    conf = (
        metomi.rose.resource.ResourceLocator.default()
        .get_conf()
        .get(["rose-config-diff"])
    )
    if conf is None:
        return
    for key, node in conf.value.items():
        if node.is_ignored():
            continue
        try:
            cast_value = ast.literal_eval(node.value)
        except (SyntaxError, ValueError):
            cast_value = node.value
        var_key = key.replace("-", "_").upper()
        if hasattr(_DEFAULTS, var_key):
            setattr(_DEFAULTS, var_key, cast_value)
        elif key.startswith("ignore{"):
            key = key.replace("ignore{", "").rstrip("}")
            _DEFAULTS.SHORTHAND.append((key, node.value.split(",")))


load_override_config()


if __name__ == "__main__":
    main()
