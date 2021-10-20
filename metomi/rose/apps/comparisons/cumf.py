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
"""Compare two UM output files using cumf."""

import os
import re

DIFF_INDEX = {"#": 10, "X": 1, "O": 0.1, "o": 0.01, ":": 0, ".": -1}
MISSING_DATA = "~"
OUTPUT_STRING = "Files %s: %s c.f. %s \n    (%s) %s"
PASS = "compare"
FAIL = "differ"
HEADER = "differ, however the data fields are identical"


class Cumf:

    """Analyse the output from the UM small exec cumf"""

    def run(self, task):
        """Analyse the output from the UM small exec cumf"""
        for line in task.resultdata:
            result = re.search(r"Summary in:\s*(\S*)", line)
            if result:
                task.cumfsummaryfile = result.group(1)
        if not hasattr(task, "cumfsummaryfile"):
            task.set_failure(CumfSummaryNotFoundFailure(task))
            return task
        if task.cumfsummaryfile:
            for line in open(task.cumfsummaryfile):
                if "files compare" in line:
                    task.set_pass(CumfComparisonSuccess(task))
            if not task.good:
                task.set_failure(CumfComparisonFailure(task))
        else:
            task.set_failure(CumfSummaryNotFoundFailure(task))
        return task


class CumfWarnHeader:

    """As cumf, but issue a warning if only the header has changed"""

    RE_NUM_FIELDS = re.compile(
        r"Number\s*of\s*fields\s*with\s*differences\s*=\s*0\D"
    )

    def __init__(self):
        self.cumf = Cumf()

    def run(self, task):
        """As Cumf.run, but issue a warning if only the header has changed"""
        self.cumf.run(task)
        if task.numericstatus and task.cumfsummaryfile:
            for line in open(task.cumfsummaryfile):
                if self.RE_NUM_FIELDS.search(line):
                    task.set_warning(CumfComparisonHeaderWarning(task))
        return task


class CumfComparisonFailure:

    """Class used if a cumf comparison fails."""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        task = analyse_cumf_diff(task)
        self.errors = task.errors
        self.cumfdir = os.path.dirname(task.cumfsummaryfile)

    def __repr__(self):
        errors = ""
        if self.errors:
            for error in self.errors:
                errors += "\n         %s: >%s%%" % (error, self.errors[error])
        return OUTPUT_STRING % (
            FAIL,
            self.resultfile,
            self.kgo1file,
            self.cumfdir,
            errors,
        )

    __str__ = __repr__


class CumfComparisonSuccess:

    """Class used if a cumf comparison succeeds"""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.cumfdir = os.path.dirname(task.cumfsummaryfile)

    def __repr__(self):
        return OUTPUT_STRING % (
            PASS,
            self.resultfile,
            self.kgo1file,
            self.cumfdir,
            "",
        )

    __str__ = __repr__


class CumfComparisonHeaderWarning:

    """Class used if cumf reports just the header of a file is different"""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.cumfdir = os.path.dirname(task.cumfsummaryfile)

    def __repr__(self):
        return OUTPUT_STRING % (
            HEADER,
            self.resultfile,
            self.kgo1file,
            self.cumfdir,
            "",
        )

    __str__ = __repr__


class CumfSummaryNotFoundFailure:

    """Class used if there is a problem finding a cumf summary file"""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.resultdata = task.resultdata

    def __repr__(self):
        return "Cannot ascertain cumf summary file from:\n%s" % (
            self.resultdata
        )

    __str__ = __repr__


class CumfDiffNotFoundFailure:

    """Class used if there is a problem finding a cumf diff file"""

    def __init__(self, task):
        self.resultfile = task.resultfile
        self.kgo1file = task.kgo1file
        self.extract = task.extract
        self.resultdata = task.resultdata

    def __repr__(self):
        return "Cannot ascertain cumf diff file from:\n%s" % (self.resultdata)

    __str__ = __repr__


class DiffNotUnderstoodException(Exception):

    """Exception for unexpected characters in the cumf diff map"""

    def __init__(self, task, character):
        Exception.__init__(self, task, character)
        self.character = character
        self.file1 = task.resultfile
        self.file2 = task.kgo1file

    def __repr__(self):
        return "Invalid character '%s' in cumf diff between %s and %s" % (
            self.character,
            self.file1,
            self.file2,
        )

    __str__ = __repr__


def analyse_cumf_diff(task):
    """Find percentage difference for each field from cumf diff."""
    task.errors = {}
    for line in task.resultdata:
        result = re.search(r"Difference maps.*:\s*(\S*)", line)
        if result:
            task.cumfdifffile = result.group(1)
    if not hasattr(task, "cumfdifffile"):
        task.set_failure(CumfDiffNotFoundFailure(task))
        return task
    if task.cumfdifffile:
        task.cumfdiffoutput = open(task.cumfdifffile).read()
        fields = task.cumfdiffoutput.split("Field")
        for field in fields:
            name = ""
            result = re.search(r":.*:\s*(.*)", field)
            if result:
                name = result.group(1)
            if not name or "OK" in field:
                continue
            diffmap = get_diff_map(field)
            max_error = DIFF_INDEX["."]
            for character in diffmap:
                if character == MISSING_DATA:
                    continue
                if character not in DIFF_INDEX:
                    raise DiffNotUnderstoodException(task, character)
                if DIFF_INDEX[character] > max_error:
                    max_error = DIFF_INDEX[character]
            if name not in task.errors or task.errors[name] < max_error:
                task.errors[name] = max_error
    return task


def get_diff_map(field):
    """Return a list of diff map characters for a field."""
    lines = field.split("\n")
    diffmap = []
    inmap = False
    for line in lines:
        if "1234567890" in line or re.search(r"^\s*\d+\s*$", line):
            inmap = True
        if r"->" in line and inmap:
            mapline = re.sub(r".*->", r"", line)
            diffmap += list(mapline)
    return diffmap
