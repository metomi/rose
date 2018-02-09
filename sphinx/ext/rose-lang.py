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
"""An extension providing a pygments lexer for rose configuration files."""

from pygments.lexer import RegexLexer, bygroups, include, words
from pygments.token import (Comment, Name, Text, Operator, String)


class RoseLexer(RegexLexer):
    """Pygments lexer for the rose rose-app.conf language."""

    # Pattern for a rose setting with capture groups.
    ROSE_SETTING_PATTERN = (
        r'([\w\{\}\[\]\:\-]+'  # setting-name{}[]
        r'(?:\(.*\))?)'        # Brackets for namelists.
        r'(\s+)?(=)(\s+)?')    # Optional spaces around = operator, value.

    # Patter for the value to a rose setting.
    ROSE_VALUE_PATTERN = (
        r'.*\n'        # Match anything after the = to the end of the line.
        r'(?:'         # Optionally match additional lines.
        r'(?:'         # Repeating line matching group.
        r'(?: +.*\n)'  # Lines must be prefixed with a space (do not use \s).
        r'\n?'         # Blank lines are permitted (e.g. foo\n\n bar).
        r')+'          # End repeating multiline group.
        r')?')         # End optional group.

    # Pygments tokens for rose config elements which have no direct
    # translation.
    ROSE_USER_IGNORED_TOKEN = Comment
    ROSE_TRIGGER_IGNORED_TOKEN = Comment.Preproc

    # Pygments values.
    name = 'Rose'
    aliases = ['rose']
    filenames = ['rose-app.conf', 'rose-suite.conf']
    # mimetypes = ['text/x-ini', 'text/inf']

    # Patterns, rules and tokens.
    tokens = {
        'root': [
            # foo=bar.
            include('setting'),

            # !foo=bar.
            include('user-ignored-setting'),

            # !!foo=bar.
            include('trigger-ignored-setting'),

            # # ...
            include('comment'),

            # [!!...]
            (r'\[\!\!.*\]', ROSE_TRIGGER_IGNORED_TOKEN,
             'trigger-ignored-section'),

            # [!...]
            (r'\[\!.*\]', ROSE_USER_IGNORED_TOKEN,
             'user-ignored-section'),

            # [...], []
            (r'\[.*\]', Name.Tag, 'section'),
        ],

        # Rose comments - w/ or w/o/ leading whitespace.
        'comment': [
            (r'^([\s\t]+)?(#[^\n]+)$', Comment.Single)
        ],

        # Rose settings broken down by constituent parts, values handled
        # separately.
        'setting': [
            (ROSE_SETTING_PATTERN, bygroups(
                Name.Variable,
                Text,
                Operator,
                Text,
            ), 'value')
        ],

        # Values handled separately so as to colour the equals sign in
        # multi-line values.
        'value': [
            (r'(\n[\s\t]+)(=)?', bygroups(
                Text,
                Operator,
            )),
            (r'.', String)
        ],

        # !bar=baz.
        'user-ignored-setting': [
            (r'\!' + ROSE_SETTING_PATTERN + ROSE_VALUE_PATTERN,
             ROSE_USER_IGNORED_TOKEN),
        ],

        # !!bar=baz.
        'trigger-ignored-setting': [
            (r'\!\!' + ROSE_SETTING_PATTERN + ROSE_VALUE_PATTERN,
             ROSE_TRIGGER_IGNORED_TOKEN)
        ],

        # [...].
        'section': [
            (r'\n(?!([\s\t]+)?\[)', Text),
            # A newline that is not followed by a '['.
            include('comment'),
            include('setting'),
            include('user-ignored-setting'),
            include('trigger-ignored-setting'),
            # Escape section without swallowing any characters if no matches.
            (r'(?=.)', Text, '#pop')
        ],

        # [!...].
        'user-ignored-section': [
            (r'\n(?!([\s\t]+)?\[)', Text),
            # A newline that is not followed by a '['.
            include('comment'),
            # Match any regular, ignored or trigger ignored setting.
            (r'([\!]+)?' + ROSE_SETTING_PATTERN + ROSE_VALUE_PATTERN,
             ROSE_USER_IGNORED_TOKEN),
            # Escape section without swallowing any characters if no matches.
            (r'(?=.)', Text, '#pop')
        ],

        # [!!...].
        'trigger-ignored-section': [
            (r'\n(?!([\s\t]+)?\[)', Text),
            # A newline that is not followed by a '['.
            include('comment'),
            # Match any regular, ignored or trigger ignored setting.
            (r'([\!]+)?' + ROSE_SETTING_PATTERN + ROSE_VALUE_PATTERN,
             ROSE_TRIGGER_IGNORED_TOKEN),
            # Escape section without swallowing any characters if no matches.
            (r'(?=.)', Text, '#pop')
        ]
    }


def setup(app):
    """Sphinx plugin setup function."""
    app.add_lexer('rose', RoseLexer())
