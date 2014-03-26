# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
#-----------------------------------------------------------------------------
"""Compare one list of numbers is within a tolerance of a second."""

import re
from rose.apps.rose_ana import DataLengthError

OUTPUT_STRING = "%s %s%% %s %s: File %s c.f. %s (%s values)"
PASS = "<="
FAIL = ">"

class Within(object):
    def run(self, task):
        """Check that the results are within a specified tolerance."""
        failures = 0
        if len(task.resultdata) != len(task.kgo1data):
            raise DataLengthError(task)
        for val1, val2 in zip(task.resultdata, task.kgo1data):
            val1 = float(val1)
            val2 = float(val2)
            lwr = 0
            upr = 0
            result = re.search(r"%",task.tolerance) # Percentage or absolute
                                                    # difference?
            if result:
                tol = float(re.sub(r"%", r"", task.tolerance))
                lwr = val2 * (1.0 - 0.01 * tol)
                upr = val2 * (1.0 + 0.01 * tol)
            else:
                lwr = val2 - float(task.tolerance)
                upr = val2 + float(task.tolerance)
            if  not lwr <= val1 <= upr:
                task.set_failure(WithinComparisonFailure(task, val1, val2))
                return task
            task.set_pass(WithinComparisonSuccess(task))
        return task


class WithinComparisonFailure(object):

    """Class used if results are not within a certain amount of the KGO"""

    def __init__(self, task, val1, val2):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.numvals = len(task.resultdata)
        if hasattr(task, "subextract"):
            self.extract = self.extract + ":" + task.subextract
        self.tolerance = task.tolerance
        try:
          self.val1 = float(val1)
          self.val2 = float(val2)
          self.percentage = abs((self.val1 - self.val2) / self.val2 * 100.0)
        except ValueError:
          self.val1 = val1
          self.val2 = val2
          self.percentage = "XX"

    def __repr__(self):
        return OUTPUT_STRING % ( self.extract, self.percentage, FAIL,
                                 self.tolerance, self.resultfile,
                                 self.kgo1file,  self.numvals )

    __str__ = __repr__


class WithinComparisonSuccess(object):

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
        return OUTPUT_STRING % ( self.extract, "all", PASS, self.tolerance,
                                 self.resultfile, self.kgo1file,
                                 self.numvals )

    __str__ = __repr__

