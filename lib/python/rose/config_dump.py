# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
"""Re-dump all Rose configuration files in a directory."""


import filecmp
import fnmatch
import os

from rose import META_CONFIG_NAME
from rose.config import ConfigDumper, ConfigLoader
from rose.fs_util import FileSystemUtil
from rose.macro import pretty_format_config
from rose.opt_parse import RoseOptionParser
from rose.reporter import Event, Reporter
from tempfile import NamedTemporaryFile


class ConfigDumpEvent(Event):
    """Event raised on dumping to a config file."""
    def __str__(self):
        return "M %s" % self.args[0]


def main():
    """Implement the "rose config-dump" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("conf_dir", "files", "no_pretty_mode")
    opts, args = opt_parser.parse_args()
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    fs_util = FileSystemUtil(report)
    if opts.conf_dir:
        fs_util.chdir(opts.conf_dir)
    file_names = []
    if opts.files:
        file_names = opts.files
    else:
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in fnmatch.filter(filenames, "rose-*.conf"):
                p = os.path.join(dirpath, filename)[2:]  # remove leading ./
                file_names.append(p)
    for file_name in file_names:
        t = NamedTemporaryFile()
        node = ConfigLoader()(file_name)
        if (not opts.no_pretty_mode and
                os.path.basename(file_name) != META_CONFIG_NAME):
            pretty_format_config(node, ignore_error=True)
        ConfigDumper()(node, t)
        t.seek(0)
        if not filecmp.cmp(t.name, file_name, shallow=False):
            report(ConfigDumpEvent(file_name))
            ConfigDumper()(node, file_name)


if __name__ == "__main__":
    main()
