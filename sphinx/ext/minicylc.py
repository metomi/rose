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
"""Provides the minicylc directive and its associated node as sphinx
extensions."""

import re
import types

import sphinx
from sphinx.directives.code import CodeBlock
from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.ext.graphviz import (
    graphviz, GraphvizSimple, html_visit_graphviz, latex_visit_graphviz,
    texinfo_visit_graphviz, text_visit_graphviz, man_visit_graphviz)


class MiniCylc(graphviz):
    """Node to represent an animated Cylc graph.

    Works by extending the built-in ``sphinx.ext.graphviz`` code.

    """

    @staticmethod
    def promote_graphviz(graphviz_node):
        """Promote a sphinx.ext.graphviz node to a MiniCylc node.

        Returns a new MiniCylc node with attributes set to the values of the
        provided graphviz node.

        """
        # Duplicate provided node
        new_node = MiniCylc()
        for item in dir(graphviz_node):
            if item.startswith('__'):
                # Skip builtins.
                continue
            attr = getattr(graphviz_node, item)
            if isinstance(attr, types.MethodType):
                # Skip methods.
                continue
            setattr(new_node, item, attr)

        # Use the digraph graphviz layout.
        new_node['code'] = new_node['code'].replace('minicylc', 'digraph')
        return new_node

    @staticmethod
    def visit_html(builder, node):
        """Wrap the standard graphviz output to provide alignment for svg.

        At present the ``align`` option for ``sphinx.ext.graphviz`` directives
        does nothing for html output when ``graphviz_output_format`` is set to
        ``svg``. This method wraps the html output to provide alignment
        capability.

        """
        # Alignment.
        try:
            align = node['align']
        except KeyError:
            align = 'center'
        style = 'text-align: %s;' % align

        # Theme.
        theme = node.get('theme', 'default')

        # Graphing.
        data = '//'.join(node['graph_lines'])

        # Construct <div> element.
        builder.body.append(
            ('<div class="minicylc" style="{0}" data-dependencies="{1}" '
             'data-theme="{2}" >').format(style, data, theme))

        # Call graphviz html builder.
        try:
            # This method raises nodes.SkipNode in the success and fail case!
            html_visit_graphviz(builder, node)
        except nodes.SkipNode:
            # Close <div> element (we are not using an exit_html function.
            builder.body.append('</div>')
            raise


class MiniCylcDirective(GraphvizSimple):
    """Implement the ``mini-cylc`` directive for animating Cylc graphs.

    Works by extending the built-in ``sphinx.ext.graphviz`` code.

    """
    option_spec = dict(GraphvizSimple.option_spec)
    option_spec['snippet'] = directives.flag
    option_spec['theme'] = directives.unchanged
    option_spec['size'] = directives.unchanged
    required_arguments = 0  # Arg will be provided in run().

    CONDITIONAL_CHARS = ['&', '|', '(', ')']
    CONDITIONAL_REGEX = re.compile(r'([\(\)\|\&])')

    @staticmethod
    def extract_or_deps(dep):
        """Return a list of tasks which have an OR dependency in a string."""
        ors = set([])
        ind = 0
        while ind < len(dep):
            if dep[ind] == '|':
                # Scan backwards.
                lvl = 0
                tmp_ind = ind
                while lvl >= 0 and tmp_ind > 0:
                    if dep[tmp_ind] == '(':
                        lvl -= 1
                    elif dep[tmp_ind] == ')':
                        lvl += 1
                    else:
                        if dep[tmp_ind] not in ['&', '|']:
                            ors.add(dep[tmp_ind])
                    tmp_ind -= 1
                # Scan forwards.
                lvl = 0
                tmp_ind = ind
                while lvl >= 0 and tmp_ind < len(dep):
                    if dep[tmp_ind] == '(':
                        lvl += 1
                    elif dep[tmp_ind] == ')':
                        lvl -= 1
                    else:
                        if dep[tmp_ind] not in ['&', '|']:
                            ors.add(dep[tmp_ind])
                    tmp_ind += 1
            ind += 1
        return ors

    @classmethod
    def get_triggers(cls, graph_lines):
        """Return a set of triggers for the provided graph code.

        Returned set of the form (left, right, conditional?).

        """
        trigs = set()

        for line in graph_lines:
            deps = [[y.strip() for y in cls.CONDITIONAL_REGEX.split(x)]
                    for x in line.split('=>')]
            for itt, dep in enumerate(deps):
                if itt < len(deps) - 1:
                    ors = cls.extract_or_deps(dep)
                    # There is a RHS to this dep.
                    for left in (i for i in dep if i not in
                                 cls.CONDITIONAL_CHARS):
                        for right in (i for i in deps[itt + 1] if i not in
                                      cls.CONDITIONAL_CHARS):
                            trigs.add((left, right, left in ors))
                elif len(dep) == 1:
                    # No depedent task.
                    for left in (i for i in dep if i not in
                                 cls.CONDITIONAL_CHARS):
                        trigs.add((None, left, False))
        return trigs

    def rationalise_graphing(self):
        """Reduces a graph string to a list of individual dependency
        strings."""
        lines = []
        buff = []
        for line in self.content:
            if not line:
                continue
            temp = line.strip()
            if temp[-1] in ['|', '&'] or temp[-2:] == '=>':
                buff.append(line)
            elif buff:
                lines.append(' '.join(buff))
                buff = []
            else:
                lines.append(line)
        self.content = lines

    def run(self):
        ret = []

        # Provide a dummy argument to match the spec of GraphvizSimple.
        self.arguments = ['Mini_Cylc']

        # Generate Cylc code snippet if requested.
        if 'snippet' in self.options:
            ret.extend(CodeBlock(self.name,
                                 ['cylc-graph'],
                                 {},  # Opts.
                                 self.content,
                                 self.lineno,
                                 self.content_offset,
                                 self.block_text,
                                 self.state,
                                 self.state_machine).run())

        # Clean up graphing.
        self.rationalise_graphing()
        clean_graphing = self.content

        # Generate dotcode for graphviz.
        # dotcode = ['bgcolor=none'] now set in conf.py:graphviz_dot_args
        dotcode = []
        if 'size' in self.options:
            dotcode.append('size="%s"' % self.options['size'])
        for left, right, conditional in self.get_triggers(self.content):
            if left:
                dotcode.append('%s -> %s%s' % (
                    left, right, ' [arrowhead=o]' if conditional else ''))
            else:
                dotcode.append(right)
        self.content = dotcode

        # Get MiniCylc node.
        node = MiniCylc.promote_graphviz(GraphvizSimple.run(self)[0])
        node['graph_lines'] = clean_graphing
        if 'theme' in self.options:
            node['theme'] = self.options['theme']
        ret.append(node)

        return ret


def setup(app):
    app.add_node(MiniCylc,
                 html=(MiniCylc.visit_html, None),
                 latex=(latex_visit_graphviz, None),
                 texinfo=(texinfo_visit_graphviz, None),
                 text=(text_visit_graphviz, None),
                 man=(man_visit_graphviz, None))
    app.add_directive('minicylc', MiniCylcDirective)
    app.add_javascript('js/minicylc.js')
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
