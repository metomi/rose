from shlex import split as sh_split
from subprocess import Popen, PIPE

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList

import sphinx
from sphinx.util.nodes import nested_parse_with_titles


class ScriptInclude(Directive):
    option_spec = {}
    required_arguments = 1
    optional_arguments = 1000

    def run(self):
        command = sh_split(' '.join(self.arguments[0:]))
        stdout = Popen(command, stdout=PIPE).communicate()[0]
        node = nodes.section()
        node.document = self.state.document
        nested_parse_with_titles(self.state, ViewList(stdout.split('\n')), node)
        return node.children


def setup(app):
    """Sphinx setup function."""
    app.add_directive('script-include', ScriptInclude)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
