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
"""Compress archive sources using xz."""


import os


class RoseArchXz:

    """Compress archive sources in xz."""

    SCHEMES = ["xz"]

    def __init__(self, app_runner, *args, **kwargs):
        self.app_runner = app_runner

    def compress_sources(self, target, work_dir, threads="1"):
        """xz each source in target.

        Use work_dir to dump results.

        """
        for source in target.sources.values():
            if source.path.endswith("." + target.compress_scheme):
                continue  # assume already done
            name_xz = source.name + "." + target.compress_scheme
            work_path_xz = os.path.join(work_dir, name_xz)
            self.app_runner.fs_util.makedirs(
                self.app_runner.fs_util.dirname(work_path_xz)
            )

            command = "xz -c '%s' >'%s'" % (source.path, work_path_xz)
            self.app_runner.popen.run_simple(command, shell=True)
            source.path = work_path_xz
