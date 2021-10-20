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
"""Re-dump all Rose configuration files in a directory."""


import filecmp
import fnmatch
import os
from tempfile import NamedTemporaryFile

from metomi.rose import META_CONFIG_NAME
from metomi.rose.config import ConfigDumper, ConfigLoader
from metomi.rose.fs_util import FileSystemUtil
from metomi.rose.macro import pretty_format_config
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Event, Reporter


class ConfigDumpEvent(Event):
    """Event raised on dumping to a config file."""

    def __str__(self):
        return "M %s" % self.args[0]


def main():
    """Implement the "rose config-dump" command."""
    opt_parser = RoseOptionParser(
        description='''
Re-dump Rose configuration files in the common format.

Load and dump `"rose-*.conf"` files in place. Apply format-specific
pretty-printing.

By default, it recursively loads and dumps all `rose-*.conf` files in the
current working directory.

EXAMPLES
    rose config-dump
    rose config-dump -C /path/to/conf/dir
    rose config-dump -f /path/to/file1 -f /path/to/file2
        '''
    )
    opt_parser.add_my_options("conf_dir", "files", "no_pretty_mode")
    opts = opt_parser.parse_args()[0]
    verbosity = opts.verbosity - opts.quietness
    report = Reporter(verbosity)
    fs_util = FileSystemUtil(report)
    if opts.conf_dir:
        fs_util.chdir(opts.conf_dir)
    file_names = []
    if opts.files:
        file_names = opts.files
    else:
        for dirpath, _, filenames in os.walk("."):
            for filename in fnmatch.filter(filenames, "rose-*.conf"):
                path = os.path.join(dirpath, filename)[2:]  # remove leading ./
                file_names.append(path)
    for file_name in file_names:
        handle = NamedTemporaryFile()
        node = ConfigLoader()(file_name)
        if (
            not opts.no_pretty_mode
            and os.path.basename(file_name) != META_CONFIG_NAME
        ):
            pretty_format_config(node, ignore_error=True)
        ConfigDumper()(node, handle)
        handle.seek(0)
        if not filecmp.cmp(handle.name, file_name, shallow=False):
            report(ConfigDumpEvent(file_name))
            ConfigDumper()(node, file_name)


if __name__ == "__main__":
    main()
