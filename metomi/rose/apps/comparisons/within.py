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
"""Compare one list of numbers is within a tolerance of a second."""

import re

from metomi.rose.apps.rose_ana_v1 import DataLengthError

OUTPUT_STRING = (
    "%(extract)s %(percent)s%% %(sign)s %(tolerance)s: "
    + "File %(file1)s c.f. %(file2)s (%(numvals)s values)"
)
OUTPUT_STRING_WITH_POSN = (
    "%(extract)s %(percent)s%% %(sign)s "
    + "%(tolerance)s: File %(file1)s c.f. "
    + "%(file2)s (value %(valnum)s of %(numvals)s)"
)
OUTPUT_STRING_WITH_VALS = (
    "%(extract)s %(percent)s%% %(sign)s "
    + "%(tolerance)s: File %(file1)s "
    + "(%(val1)s) c.f. %(file2)s (%(val2)s)"
)
PASS = "<="
FAIL = ">"


class Within:
    def run(self, task):
        """Check that the results are within a specified tolerance."""
        if len(task.resultdata) != len(task.kgo1data):
            raise DataLengthError(task)
        val_num = 0
        for val1, val2 in zip(task.resultdata, task.kgo1data):
            val_num = val_num + 1
            val1 = float(val1)
            val2 = float(val2)
            lwr = 0
            upr = 0
            result = re.search(r"%", task.tolerance)  # Percentage or absolute
            if result:
                tol = float(re.sub(r"%", r"", task.tolerance))
                lwr = val2 * (1.0 - 0.01 * tol)
                upr = val2 * (1.0 + 0.01 * tol)
            else:
                lwr = val2 - float(task.tolerance)
                upr = val2 + float(task.tolerance)
            if not lwr <= val1 <= upr:
                task.set_failure(
                    WithinComparisonFailure(task, val1, val2, val_num)
                )
                return task
            task.set_pass(WithinComparisonSuccess(task))
        return task


class WithinComparisonFailure:

    """Class used if results are not within a certain amount of the KGO"""

    def __init__(self, task, val1, val2, val_num):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.valnum = val_num
        self.numvals = len(task.resultdata)
        if hasattr(task, "subextract"):
            self.extract = self.extract + ":" + task.subextract
        self.tolerance = task.tolerance
        try:
            self.val1 = float(val1)
            self.val2 = float(val2)
            self.percentage = abs((self.val1 - self.val2) / self.val2 * 100.0)
        except ValueError:
            self.val1 = 'Unknown'
            self.val2 = 'Unknown'
            self.percentage = "XX"

    def __repr__(self):
        if self.numvals == 1:
            return OUTPUT_STRING_WITH_VALS % {
                'extract': self.extract,
                'percent': self.percentage,
                'sign': FAIL,
                'tolerance': self.tolerance,
                'file1': self.resultfile,
                'val1': self.val1,
                'file2': self.kgo1file,
                'val2': self.val2,
            }
        else:
            return OUTPUT_STRING_WITH_POSN % {
                'extract': self.extract,
                'percent': self.percentage,
                'sign': FAIL,
                'tolerance': self.tolerance,
                'file1': self.resultfile,
                'file2': self.kgo1file,
                'valnum': self.valnum,
                'numvals': self.numvals,
            }

    __str__ = __repr__


class WithinComparisonSuccess:

    """Class used if results are within a certain amount of the KGO"""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.numvals = len(task.resultdata)
        if hasattr(task, "subextract"):
            self.extract = self.extract + ":" + task.subextract
        self.tolerance = task.tolerance

    def __repr__(self):
        return OUTPUT_STRING % {
            'extract': self.extract,
            'percent': 'all',
            'sign': PASS,
            'tolerance': self.tolerance,
            'file1': self.resultfile,
            'file2': self.kgo1file,
            'numvals': self.numvals,
        }

    __str__ = __repr__
