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
