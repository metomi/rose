# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
"""An extension providing a directive for writing pratical sections."""

from docutils import nodes
from docutils.parsers.rst.directives.admonitions import BaseAdmonition


class Practical(BaseAdmonition):
    """Directive for practical sections in documentation.

    This class serves as a standin for maintainability purposes. It is
    equivalient to:

        .. admonition:: Practical
           :class: note

    """
    node_class = nodes.admonition

    def run(self):
        self.options.update({'class': ['note']})  # Affects the display.
        self.arguments = ['Practical']  # Sets the title of the admonition.
        return super(Practical, self).run()


def setup(app):
    """Sphinx setup function."""
    app.add_directive('practical', Practical)
