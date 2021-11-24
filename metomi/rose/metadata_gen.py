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
"""
Module to automatically generate metadata from a Rose configuration.
"""

import os
import sys

import metomi.rose.config
import metomi.rose.config_tree
import metomi.rose.formats.namelist
import metomi.rose.macro
import metomi.rose.macros.value
import metomi.rose.meta_type
import metomi.rose.opt_parse
import metomi.rose.resource


def metadata_gen(config, meta_config=None, auto_type=False, prop_map=None):
    """Automatically guess the metadata for an application configuration."""
    if prop_map is None:
        prop_map = {}
    metomi.rose.macro.standard_format_config(config)
    if meta_config is None:
        meta_config = metomi.rose.config.ConfigNode()
    for keylist, node in config.walk():
        sect = keylist[0]
        if len(keylist) == 1:
            option = None
        else:
            option = keylist[1]
        if sect in [metomi.rose.CONFIG_SECT_CMD]:
            continue
        if keylist == [
            metomi.rose.CONFIG_SECT_TOP,
            metomi.rose.CONFIG_OPT_META_TYPE,
        ]:
            continue
        meta_sect = metomi.rose.macro.REC_ID_STRIP.sub("", sect)
        modifier_sect = metomi.rose.macro.REC_ID_STRIP_DUPL.sub("", sect)
        if sect and option is None:
            if (
                modifier_sect != meta_sect
                and modifier_sect != sect
                and meta_config.get([modifier_sect]) is None
                and auto_type
            ):
                meta_config.set(
                    [modifier_sect, metomi.rose.META_PROP_DUPLICATE],
                    metomi.rose.META_PROP_VALUE_TRUE,
                )
            if meta_config.get([meta_sect]) is not None:
                continue
            meta_config.set([meta_sect])
            if meta_sect != sect and auto_type:
                # Add duplicate = true at base and modifier level (if needed).
                meta_config.set(
                    [meta_sect, metomi.rose.META_PROP_DUPLICATE],
                    metomi.rose.META_PROP_VALUE_TRUE,
                )
            for prop_key, prop_value in prop_map.items():
                meta_config.set([meta_sect, prop_key], prop_value)
        if option is None:
            continue
        meta_key = metomi.rose.macro.REC_ID_STRIP_DUPL.sub('', option)
        meta_opt = meta_sect + "=" + meta_key
        if meta_config.get([meta_opt]) is not None:
            continue
        meta_config.set([meta_opt])
        for prop_key, prop_value in prop_map.items():
            meta_config.set([meta_opt, prop_key], prop_value)
        if auto_type:
            opt_type, length = type_gen(node.value)
            if opt_type is not None:
                meta_config.set(
                    [meta_opt, metomi.rose.META_PROP_TYPE], opt_type
                )
            if int(length) > 1:
                meta_config.set(
                    [meta_opt, metomi.rose.META_PROP_LENGTH], length
                )
    return meta_config


def type_gen(value):
    """Guess the type of a value.

    Returns a tuple of type and length metadata values.

    """
    types = []
    length = 0
    if not value:
        return None, str(length)
    for val in metomi.rose.variable.array_split(value):
        length += 1
        val_meta_type = "raw"
        for meta_type in [
            "integer",
            "real",
            "quoted",
            "character",
            "logical",
            "boolean",
        ]:
            is_ok = metomi.rose.meta_type.meta_type_checker(val, meta_type)[0]
            if is_ok:
                val_meta_type = meta_type
                break
        types.append(val_meta_type)
    if not any(t != "raw" for t in types):
        length = 1
        return None, str(length)
    if all([t == types[0] for t in types]):
        return types[0], str(length)
    length = 1
    # Now make sure derived type arrays are correctly guessed.
    # For example, types = ["A", "B", "A", "B"], length = 1
    # should be types = ["A", "B"], length = 2
    for i in range(2, len(types)):
        if types[:i] * (len(types) // i) == types:
            length = len(types) // i
            types = types[:i]
            break
    return ", ".join(types), str(length)


def main():
    opt_parser = metomi.rose.opt_parse.RoseOptionParser(
        usage='rose metadata-gen [OPTIONS] [PROPERTY=VALUE ...]',
        description='''
Automatically generate metadata from an application or suite
configuration. An aid for metadata development.

WARNING: May Contain Thorns.
        ''',
        epilog='''
ARGUMENTS
    PROPERTY[=VALUE] ...
       One or more `key=value` pairs of properties to specify for
       every setting e.g. `compulsory=true`. If `=VALUE` is missing,
       the property will be set to a null string in each setting.
        ''',
    )
    opt_parser.add_my_options("auto_type", "conf_dir", "output_dir")
    opt_parser.modify_option(
        'output_dir',
        help=(
            'A directory to output the metadata to.'
            '\nIf not specified, output to the application or suite metadata'
            'directory.'
        )
    )
    opts, args = opt_parser.parse_args()
    metomi.rose.macro.add_meta_paths()
    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    opts.conf_dir = os.path.abspath(opts.conf_dir)
    prop_val_map = {}
    for arg in args:
        if "=" in arg:
            key, val = arg.split("=", 1)
            prop_val_map.update({key: val})
        else:
            prop_val_map.update({arg: ""})
    for filename in [metomi.rose.SUB_CONFIG_NAME, metomi.rose.TOP_CONFIG_NAME]:
        path = os.path.join(opts.conf_dir, filename)
        if os.path.isfile(path):
            break
    else:
        sys.exit(opt_parser.get_usage())
    source_config = metomi.rose.config.load(path)
    meta_dir = os.path.join(opts.conf_dir, metomi.rose.CONFIG_META_DIR)
    metadata_config = metomi.rose.config.ConfigNode()
    try:
        metadata_config = (
            metomi.rose.config_tree.ConfigTreeLoader()
            .load(meta_dir, metomi.rose.META_CONFIG_NAME, list(sys.path))
            .node
        )
    except IOError:
        pass
    metadata_config = metadata_gen(
        source_config,
        metadata_config,
        auto_type=opts.type,
        prop_map=prop_val_map,
    )
    if opts.output_dir is None:
        dest = meta_dir
    else:
        dest = opts.output_dir
    if not os.path.isdir(dest):
        os.mkdir(dest)
    dest_file = os.path.join(dest, metomi.rose.META_CONFIG_NAME)
    metomi.rose.config.dump(metadata_config, dest_file)


if __name__ == "__main__":
    main()
