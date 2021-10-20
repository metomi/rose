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
"""Return a list of values matching a regular expression."""

from metomi.rose.apps.rose_ana_v1 import data_from_regexp

REGEXPS = {
    'um_wallclock': r"Maximum Elapsed Wallclock Time:\s*(\S+)",
    'um_initial_norms': r"initial\s*Absolute\s*Norm\s*:\s*(\S+)",
    'um_final_norms': r"Final\s*Absolute\s*Norm\s*:\s*(\S+)",
}


class OutputGrepper:
    def run(self, task, variable):
        """Return a list of values matching a regular expression."""
        filevar = variable + "file"
        filename = getattr(task, filevar)
        if task.subextract in REGEXPS:
            regexp = REGEXPS[task.subextract]
        else:
            if task.subextract.startswith("'") and task.subextract.endswith(
                "'"
            ):
                regexp = task.subextract[1:-1]
        numbers = data_from_regexp(regexp, filename)
        datavar = variable + "data"
        setattr(task, datavar, numbers)
        return task
