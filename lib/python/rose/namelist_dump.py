# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------
"""
Module to convert from a Fortran namelist file to a Rose configuration.

This contains wrapper functions for the namelist parser and the dumper
(rose.config).

"""

import os
import re
import sys
import rose.config
import rose.formats.namelist
from rose.opt_parse import RoseOptionParser


RE_NAME_INDEX = re.compile("^(.*)\((\d+)\)$")
STD_FILE_ARG = "-"


def tr_case(string, case_mode=None):
    """Return the string with its case translated to upper, lower or unchanged
    depending on the value of "case_mode", which can be "upper", "lower" or None.
    """
    if case_mode == "lower":
        return string.lower()
    elif case_mode == "upper":
        return string.upper()
    else:
        return string


def _sort_config_key(key_1, key_2):
    match_1 = RE_NAME_INDEX.match(key_1)
    match_2 = RE_NAME_INDEX.match(key_2)
    if match_1 and match_2:
        name_1, index_1 = match_1.groups()
        name_2, index_2 = match_2.groups()
        if name_1.lower() == name_2.lower():
            return cmp(int(index_1), int(index_2))
    return cmp(key_1.lower(), key_2.lower())


def namelist_dump(args=None, output_file=None, case_mode=None):
    # Input and output options
    if not args:
        args = [STD_FILE_ARG]
    if output_file is None or output_file == STD_FILE_ARG:
        output_file = sys.stdout
    else:
        output_file = open(output_file, "w")

    # Config: file: sections
    config = rose.config.ConfigNode()
    files = []
    for arg in args:
        if arg == STD_FILE_ARG:
            files.append(sys.stdin)
            config.set(["file:STDIN"], {})
        else:
            files.append(open(arg, "r"))
            config.set(["file:" + arg], {})

    # Parse files into a list of NamelistGroup objects
    groups = rose.formats.namelist.parse(files)

    # Count group in files and group
    groups_in_file = {}
    groups_by_name = {}
    index_of_group = {}
    for group in groups:
        name = group.name.lower()
        if not groups_by_name.has_key(name):
            groups_by_name[name] = []
        groups_by_name[name].append(group)
        index_of_group[group] = len(groups_by_name[name])
        if not groups_in_file.has_key(group.file):
            groups_in_file[group.file] = []
        groups_in_file[group.file].append(group)

    # Add contents to relevant file: sections
    for file, groups in groups_in_file.items():
        section = "file:" + file
        if file == sys.stdin.name:
            section = "file:STDIN"
        group_sections = []
        for group in groups:
            group_section = "namelist:" + tr_case(group.name, case_mode)
            if len(groups_by_name[group.name.lower()]) > 1:
                group_section += "(" + str(index_of_group[group]) + ")"
            group_sections.append(group_section)
        config.set([section, "source"], " ".join(group_sections))

    # Add namelist: sections
    for name, groups in groups_by_name.items():
        for group in groups:
            section = "namelist:" + tr_case(group.name, case_mode)
            if len(groups) > 1:
                section += "(" + str(index_of_group[group]) + ")"
            config.set([section], {})
            for object in group.objects:
                lhs = tr_case(object.lhs, case_mode)
                config.set([section, lhs], object.get_rhs_as_string())

    # Config: write results
    rose.config.dump(config, output_file,
                     sort_sections=_sort_config_key,
                     sort_option_items=_sort_config_key,
                     env_escape_ok=True)
    output_file.close()


def main():
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("case_mode", "lower", "output_file", "upper")
    opts, args = opt_parser.parse_args()
    return namelist_dump(args, opts.output_file, opts.case_mode)


if __name__ == "__main__":
    main()
