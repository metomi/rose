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
"""Check a file contains a string."""

OUTPUT_STRING = "%s: File %s %s %s"
PASS = "~~"
FAIL = "!~"


class Mandatory:
    def run(self, task):
        """Perform an exact comparison between the result and the KGO data"""
        if len(task.resultdata) == 0:
            task.set_failure(MandatoryStringResult(task, FAIL))
        else:
            task.set_pass(MandatoryStringResult(task, PASS))
        return task


class MandatoryStringResult:

    """Result of mandatory text examination."""

    def __init__(self, task, status):
        self.resultfile = task.resultfile
        self.extract = task.extract
        self.status = status
        if hasattr(task, "subextract"):
            self.subextract = task.subextract
        else:
            self.subextract = "unknown"

    def __repr__(self):
        return OUTPUT_STRING % (
            self.extract,
            self.resultfile,
            self.status,
            self.subextract,
        )

    __str__ = __repr__
