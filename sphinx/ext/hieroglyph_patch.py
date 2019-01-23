"""Monkey patch hieroglyph to work with Sphinx 1.8.0+.

This extension serves as a temporary workaround, for more information see
`https://github.com/nyergler/hieroglyph/issues/148`_.

If an extension provides its own visit or depart methods, patch them into the
``HTMLTranslator`` class below.

It would be possible to patch the ``add_node`` method of the Sphinx application
to patch extensions automatically but in the interests of keeping the hack to a
minimum this hard-coded extension should suffice.

"""

import sphinx

from sphinx.writers.html import HTMLTranslator

from sphinx.ext.graphviz import html_visit_graphviz
from sphinx.ext.autosummary import (autosummary_toc_visit_html,
                                    autosummary_table_visit_html)
from minicylc import MiniCylc


def none(*args, **kwargs):
    pass


def setup(app):
    if tuple(int(x) for x in sphinx.__version__.split('.')) > (1, 7, 9):
        # sphinx.ext.graphviz
        HTMLTranslator.visit_graphviz = html_visit_graphviz

        # sphinx.ext.autosummary
        HTMLTranslator.visit_autosummary_toc = autosummary_toc_visit_html
        HTMLTranslator.depart_autosummary_toc = none
        HTMLTranslator.visit_autosummary_table = autosummary_table_visit_html
        HTMLTranslator.depart_autosummary_table = none

        # ext.minicylc
        HTMLTranslator.visit_MiniCylc = MiniCylc.visit_html
