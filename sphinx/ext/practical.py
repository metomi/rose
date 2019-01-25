# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
    NAME = 'Practical'
    CLASSES = ['note']

    def run(self):
        self.options.update({'class': self.CLASSES})  # Affects the display.
        self.arguments = [self.NAME]  # Sets the title of the admonition.
        return super(Practical, self).run()


class PracticalExtension(Practical):
    """Directive for practical extension exercises."""
    NAME = 'Practical Extension'
    CLASSES = ['note', 'spoiler']


class Spoiler(BaseAdmonition):
    """Directive for auto-hiden "spoiler" sections.

    When rendered in HTML the section will be collapsed and a "Show" button put
    in its place.

    Otherwise the content will be displayed normally.

    """
    node_class = nodes.admonition
    required_arguments = 1

    def run(self):
        classes = ['spoiler']
        args = self.arguments[0].split(' ')
        if len(args) > 1:
            classes.append(args[1])
        self.arguments = args[:1]
        self.options.update({'class': classes})
        return super(Spoiler, self).run()


def setup(app):
    """Sphinx setup function."""
    app.add_directive('practical', Practical)
    app.add_directive('practical-extension', PracticalExtension)
    app.add_directive('spoiler', Spoiler)
    app.add_javascript('js/spoiler.js')  # self-hiding node.
