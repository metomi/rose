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
from argparse import ArgumentParser
import re
from subprocess import DEVNULL, PIPE, Popen
import sys
from textwrap import dedent, indent

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList

import sphinx
from sphinx.util.nodes import nested_parse_with_titles


# RE_CMD = re.compile(r'^={5,}$\n^(.*)$\n^={5,}$')
RE_CMD = re.compile(r'={5,}\n')
RE_USAGE = re.compile(r'Usage: (.*)')
RE_SECTION = re.compile(r'^([A-Z][A-Z: ]+)$')

RST_HEADINGS = ['=', '-', '^', '"']

RE_LITERAL = re.compile(r'(?<!\`)\`(?!\`)([^\`]+)(?<!\`)\`(?!\`)')


def format_literals(text, references_to_match=None, ref_template='%s'):
    r"""Replace single back-quotes with double ones.

    Optionally replace certain strings with references to other sections in
    this document.

    Args:
        text (str): The text to format literals in.
        references_to_match (list): List of strings which will be replaced
            by rst document references using the ref_template.
        ref_template (str): Template string for the document reference.

    Examples:
        >>> format_literals('a`x`a b`x` `x`c `x`')
        'a\\ ``x``\\ a b\\ ``x`` ``x``\\ c ``x``\\ '
        >>> format_literals('here-`bar`', ['bar'], 'foo%sbaz')
        'here-:ref:`foobarbaz`\\ '

    Returns: str

    """
    if not references_to_match:
        references_to_match = []
    ref_template = ':ref:`{0}`'.format(ref_template)

    for match in reversed([x for x in RE_LITERAL.finditer(text)]):
        repl = ''
        start, end = match.span()

        if start > 0:
            pre_char = text[start - 1]
        else:
            pre_char = '\n'
        if pre_char != ' ' and pre_char != '\n':
            repl += '\\ '

        body = match.group()[1:-1]
        if body in references_to_match:
            repl = ref_template % body.replace(' ', '-')
        else:
            repl += '``%s``' % body

        if end < len(text) - 2:
            post_char = text[end]
        else:
            post_char = ''
        if post_char not in [' ', '\n']:
            repl += '\\ '

        text = text[:start] + repl + text[end:]

    return text


def list_strip(lst):
    """

    Examples:
        >>> list_strip(['', '', 'foo', '', ''])
        ['foo']
        >>> list_strip(['foo', '', 'bar'])
        ['foo', '', 'bar']

    """
    for item in list(lst):
        if not item:
            lst.pop(0)
        else:
            break
    for item in reversed(lst):
        if not item:
            lst.pop(-1)
        else:
            break
    return lst


def split(text):
    parts = RE_CMD.split(text)

    return {
        cmd.strip(): parse(content.strip())
        for cmd, content in zip(parts[1::2], parts[2::2])
    }


def parse(text):
    if not text:
        return
    lines = text.splitlines()
    ret = {}

    try:
        ret['USAGE'] = RE_USAGE.search(lines[0]).group()
    except AttributeError:
        pass
    except IndexError:
        breakpoint()

    section = 'DESCRIPTION'
    buffer = []
    for line in lines[1:]:
        if RE_SECTION.search(line):
            ret[section] = '\n'.join(list_strip(buffer))
            buffer = []
            section = RE_SECTION.search(line).groups()[0].replace(':', '')
        else:
            buffer.append(line)
    else:
        ret[section] = '\n'.join(list_strip(buffer))

    if 'USAGE' not in ret:
        try:
            ret['USAGE'] = ret.pop('SYNOPSIS')
        except KeyError:
            ret['USAGE'] = ''

    if 'NAME' in ret:
        ret.pop('NAME')

    return ret


def rst_heading(text, level=0):
    return f'\n{text}\n{RST_HEADINGS[level] * len(text)}\n'


def rst_code_block(code, lang=None):
    return (
        '\n'
        f'.. code-block:: {lang or ""}'
        '\n\n'
        + indent(dedent(code), ' ' * 3)
        + '\n'
    )
    return dedent(f'''
        .. code-block:: {lang}

           {indent(dedent(code), ' ' * 0)}\n
    ''')


def rst_anchor(text):
    return f'\n.. _{text}:\n'


def rst_body(text):
    return f'\n{format_literals(dedent(text))}\n'


def write(ns, cmds, _write):
    for cmd, content in cmds.items():
        if 'USAGE' not in content:
            breakpoint()
        _write(
            rst_anchor(f'command-{cmd.replace(" ", "-")}')
        )
        _write(
            rst_heading(cmd, 1)
        )
        _write(
            rst_code_block(content['USAGE'], 'bash')
        )
        _write(
            rst_body(content['DESCRIPTION'])
        )
        for key, text in content.items():
            if key in {'USAGE', 'DESCRIPTION'}:
                continue
            _write(
                rst_heading(key.capitalize(), 2)
            )
            if key in {'OPTIONS'}:
                _write(
                    rst_code_block(text)
                )
            elif key in {'EXAMPLE', 'EXAMPLES'}:
                _write(
                    rst_code_block(text, 'bash')
                )
            else:
                _write(
                    rst_body(text)
                )


def load_from_file(filename):
    with open(filename, 'r') as doc_file:
        return doc_file.read().strip()


def load_from_cli(ns):
    return Popen(
        [f'{ns}', 'doc'],
        stdin=DEVNULL,
        stdout=PIPE,
        text=True
    ).communicate()[0].strip()


def get_parser():
    parser = ArgumentParser()

    parser.add_argument(
        'ns',
        default=None,
        help='Rose namespace i.e. rose, rosie, rosa'
    )

    parser.add_argument(
        'doc_file',
        nargs='?',
        default=None,
        help='read `rose doc` output from a file (for testing).'
    )

    return parser


def test():
    parser = get_parser()
    args = parser.parse_args()

    if args.doc_file:
        text = load_from_file(args.doc_file)
    else:
        text = load_from_cli(args.ns)

    main(args.ns, text, sys.stdout.write)


def make(ns):
    text = load_from_cli(ns)
    lines = []

    def _write(text):
        nonlocal lines
        lines.extend(text.splitlines())

    main(ns, text, _write)
    return lines


def main(ns, text, _write):
    cmds = split(text)
    write(ns, cmds, _write)


class AutoCLIDoc(Directive):
    """A custom ReStructured Text directive for auto-documenting CLIs.

    Directive Args:
        cli_help_format (str): The type of command line help to generate help
            for (only option "rose").
        command (str): The command to document.

    """
    option_spec = {}
    required_arguments = 2

    def run(self):
        # The rose command to document (i.e. rose / rosie)
        _, ns = self.arguments[0:2]

        lines = make(ns)

        # Parse these lines into a docutills node.
        node = nodes.section()
        node.document = self.state.document
        nested_parse_with_titles(self.state, ViewList(lines), node)

        # Return the children of this node (the generated nodes).
        return node.children


def setup(app):
    """Sphinx setup function."""
    app.add_directive('auto-cli-doc', AutoCLIDoc)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}


if __name__ == '__main__':
    test()
