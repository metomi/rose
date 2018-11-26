# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2012-2018 British Crown (Met Office) & Contributors.
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
"""Sphinx directive for including the output of external commands into RST."""

import os
from shlex import split as sh_split
from subprocess import Popen, PIPE

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList

import sphinx
from sphinx.util.nodes import nested_parse_with_titles


class ScriptInclude(Directive):
    """Insert parsed RST node from command output."""
    option_spec = {}
    required_arguments = 1
    optional_arguments = 1000

    def run(self):
        command = sh_split(' '.join(self.arguments[0:]))
        stdout = Popen(command, stdout=PIPE, stdin=open(os.devnull)
                       ).communicate()[0]
        node = nodes.section()
        node.document = self.state.document
        nested_parse_with_titles(self.state, ViewList(stdout.splitlines()),
                                 node)
        return node.children


def setup(app):
    """Sphinx setup function."""
    app.add_directive('script-include', ScriptInclude)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
