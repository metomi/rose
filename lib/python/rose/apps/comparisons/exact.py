# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
"""Compare two lists of numbers exactly."""

from rose.apps.rose_ana import DataLengthError

OUTPUT_STRING = "%s %s: %s%%: File %s %s %s"
PASS = "=="
FAIL = "!="

class Exact(object):
    def run(self, task): 
        """Perform an exact comparison between the result and the KGO data"""
        failures = 0
        if len(task.resultdata) != len(task.kgo1data):
            raise DataLengthError(task)
        location = 0
        for val1, val2 in zip(task.resultdata, task.kgo1data):
            location += 1
            if val1 != val2:
                task.set_failure(ExactComparisonFailure(task, val1, val2, 
                                   location))
                return task
            task.set_pass(ExactComparisonSuccess(task))
        return task


class ExactComparisonFailure(object):

    """Class used if results do not match the KGO"""

    def __init__(self, task, val1, val2, location):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        if hasattr(task, "subextract"):
            self.extract = self.extract + ":" + task.subextract
        try:
            self.val1 = float(val1)
            self.val2 = float(val2)
            self.percentage = abs((self.val1 - self.val2) / self.val2 * 100.0)
        except ValueError:
            self.val1 = val1
            self.val2 = val2
            self.percentage = "XX"
        except ZeroDivisionError:
            self.val1 = val1
            self.val2 = val2
            self.percentage = "XX"
        self.location = location

    def __repr__(self):
        return OUTPUT_STRING % ( self.extract, self.location, self.percentage,
                                 self.resultfile, FAIL, self.kgo1file,)

    __str__ = __repr__


class ExactComparisonSuccess(object):

    """Class used if results match the KGO"""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        if hasattr(task, "subextract"):
            self.extract = self.extract + ":" + task.subextract

    def __repr__(self):
        return OUTPUT_STRING % ( self.extract, "all", 0,
                                 self.resultfile, PASS, self.kgo1file, )

    __str__ = __repr__
