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
"""
This module contains:
 * the class Section, which acts as a data structure for section attributes.
"""

import copy


class Section:

    """This class stores the data and metadata of an input section.

    The section is ignored if any ignored_reason keys exist,
    and contains errors if the error attribute is not empty.

    """

    def __init__(
        self,
        name,
        options=None,
        metadata=None,
        ignored_reason=None,
        error=None,
        warning=None,
        flags=None,
        comments=None,
    ):
        self.name = name
        if options is None:
            options = []
        self.options = list(options)
        if metadata is None:
            metadata = {}
        if ignored_reason is None:
            ignored_reason = {}
        if error is None:
            error = {}
        if warning is None:
            warning = {}
        if flags is None:
            flags = {}
        if comments is None:
            comments = []
        self.metadata = dict(metadata.items())
        self.flags = dict(flags.items())
        self.ignored_reason = dict(ignored_reason.items())
        self.error = error
        self.warning = warning
        self.comments = comments

    def to_hashable(self):
        """Return a hashable summary of the current state."""
        return (
            self.name,
            tuple(sorted(self.ignored_reason.keys())),
            tuple(self.comments),
        )

    def process_metadata(self, metadata):
        """Update metadata."""
        self.metadata.update(metadata)

    def copy(self):
        new_section = Section(
            self.name,
            copy.deepcopy(self.options),
            copy.deepcopy(self.metadata),
            copy.deepcopy(self.ignored_reason),
            copy.deepcopy(self.error),
            copy.deepcopy(self.warning),
            copy.deepcopy(self.flags),
            copy.deepcopy(self.comments),
        )
        return new_section

    def __repr__(self):
        text = '<rose.section :- name: ' + self.name + ': '
        if self.options:
            text += "options: "
            for option in sorted(self.options):
                text += option + ", "
        else:
            text += "(empty), "
        text += 'metadata: ' + str(self.metadata)
        text += ', ignored: ' + ['yes', 'no'][self.ignored_reason == {}]
        text += ', error: ' + str(self.error)
        text += ', warning: ' + str(self.warning)
        if self.flags:
            text += ', flags: ' + str(self.flags)
        text += ">"
        return text
