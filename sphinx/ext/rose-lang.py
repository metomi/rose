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
    ROSE_SETTING_PATTERN = r'^([\s\t]+)?([\w\{\}-]+)(\s+)?(=)(\s+)?'

    # Pattern for a rose (ignored|trigger-ignored|regular) setting.
    ROSE_SETTING_VALUE_PATTERN = ('{0}'  # '', '!', '!!'.
                                  r'[\w{{}}-]+(\s+)?=(\s+)?'
                                  r'[^\n]+((\n[\s\t]+=[^\n]+)+)?')

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
                Text,
                Name.Variable,
                Text,
                Operator,
                Text,
            ), 'value')
        ],

        # Values handled separately so as to colour the equals sign in
        # multi-line values.
        'value': [
            (r'(\n[\s\t]+)(=)', bygroups(
                Text,
                Operator,
            )),
            (r'.', String)
        ],

        # [!foo]bar=baz.
        'setting-in-user-ignored-section': [
            (ROSE_SETTING_VALUE_PATTERN.format(''), ROSE_USER_IGNORED_TOKEN)
        ],

        # [!!foo]bar=baz.
        'setting-in-trigger-ignored-section': [
            include('comment'),
            (ROSE_SETTING_VALUE_PATTERN.format(''), ROSE_TRIGGER_IGNORED_TOKEN)
        ],

        # !bar=baz.
        'user-ignored-setting': [
            (ROSE_SETTING_VALUE_PATTERN.format('\!'), ROSE_USER_IGNORED_TOKEN)
        ],

        # [!!foo]!bar=baz.
        'user-ignored-setting-in-trigger-ignored-section': [
            (ROSE_SETTING_VALUE_PATTERN.format('\!'),
             ROSE_TRIGGER_IGNORED_TOKEN)
        ],

        # !!bar=baz.
        'trigger-ignored-setting': [
            (ROSE_SETTING_VALUE_PATTERN.format('\!\!'),
             ROSE_TRIGGER_IGNORED_TOKEN)
        ],

        # [!foo]!!bar=baz.
        'trigger-ignored-setting-in-user-ignored-section': [
            (ROSE_SETTING_VALUE_PATTERN.format('\!\!'),
             ROSE_USER_IGNORED_TOKEN)
        ],

        # [...].
        'section': [
            (r'\n(?!([\s\t]+)?\[)', Text),
            # A newline that is not followed by a '['.
            include('comment'),
            include('setting'),
            include('user-ignored-setting'),
            include('trigger-ignored-setting'),
            (r'\n', Text, '#pop')
        ],

        # [!...].
        'user-ignored-section': [
            (r'\n(?!([\s\t]+)?\[)', Text),
            # A newline that is not followed by a '['.
            include('comment'),
            include('setting-in-user-ignored-section'),
            include('user-ignored-setting'),
            include('trigger-ignored-setting-in-user-ignored-section'),
            (r'\n', Text, '#pop')
        ],

        # [!!...].
        'trigger-ignored-section': [
            (r'\n(?!([\s\t]+)?\[)', Text),
            # A newline that is not followed by a '['.
            include('comment'),
            include('setting-in-trigger-ignored-section'),
            include('user-ignored-setting-in-trigger-ignored-section'),
            include('trigger-ignored-setting'),
            (r'\n', Text, '#pop')
        ]
    }


def setup(app):
    """Sphinx plugin setup function."""
    app.add_lexer('rose', RoseLexer())
