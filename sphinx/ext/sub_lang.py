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
"""An extension providing a lexer which highlights text <substitutions>."""

from pygments.lexer import RegexLexer
from pygments.token import Text, String, Comment


class SubstitutionLexer(RegexLexer):
    """Pygments lexer for highlighting <subsitutions> in code e.g. paths."""
    name = 'Substitution'
    aliases = []
    filenames = []

    tokens = {
        'root': [
            (r'\<[^\>]+\>', String),
            ('#.*', Comment),
            ('.', Text)
        ]
    }


def setup(app):
    """Sphinx plugin setup function."""
    app.add_lexer('sub', SubstitutionLexer())
