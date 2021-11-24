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
# -----------------------------------------------------------------------------
import os
import sys

import metomi.rose
from metomi.rose.popen import RosePopener

# rose-documentation build configuration file, initial version created by
# sphinx-quickstart.


# Add local sphinx extensions directory to extensions path.
sys.path.append(os.path.abspath('ext'))

# Register extensions.
extensions = [
    # sphinx built-in extensions
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.graphviz',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    # sphinx user community extensions
    'hieroglyph',
    'sphinxcontrib.httpdomain',
    # custom project extensions (located in ext/)
    'auto_cli_doc',
    'rose_lang',
    'rose_domain',
    'script_include',
    # cylc.sphinx_ext extensions (from cylc.sphinx_ext-extensions library)
    'cylc.sphinx_ext.cylc_lang',
    'cylc.sphinx_ext.diff_selection',
    'cylc.sphinx_ext.grid_table',
    'cylc.sphinx_ext.hieroglyph_addons',
    'cylc.sphinx_ext.minicylc',
    'cylc.sphinx_ext.practical',
    'cylc.sphinx_ext.rtd_theme_addons',
    'cylc.sphinx_ext.sub_lang',
]

# Select best available SVG image converter.
for svg_converter, extension in [
    ('rsvg', 'sphinxcontrib.rsvgconverter'),
    ('inkscape', 'sphinxcontrib.inkscapeconverter'),
]:
    try:
        assert RosePopener.which(svg_converter)
        __import__(extension)
    except (AssertionError, ImportError):
        # converter or extension not available
        pass
    else:
        extensions.append(extension)
        break
else:
    # no extensions or converters available, fall-back to default
    # vector graphics will be converted to bitmaps in all documents
    extensions.append('sphinx.ext.imgconverter')

# mapping to other Sphinx projects
# (allows us to reference objects from other projects)
cylc_version = '8.0b2'
intersphinx_mapping = {
    'cylc': (f'https://cylc.github.io/cylc-doc/{cylc_version}/html/', None),
    'python': ('https://docs.python.org/', None),
}

# Slide (hieroglyph) settings.
slide_theme = 'single-level'
slide_link_to_html = True
slide_theme_options = {'custom_css': 'css/slides-custom.css'}

# Use SVG for all graphviz (and by extension minicylc) blocks (alt png).
graphviz_output_format = 'svg'

# Global configuration for graphviz diagrams.
graphviz_dot_args = ['-Gfontname=sans', '-Gbgcolor=none', '-Nfontname=sans']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Rose Documentation'
copyright = (
    ': Copyright (C) British Crown (Met Office) & Contributors. '
    'See Terms of Use. '
    'This document is released under the Open Government Licence'
)

# The full version for the project you're documenting, acts as replacement for
# |version|.
release = metomi.rose.__version__
# The short X.Y version, acts as replacement for |release|.
version = release

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'autumn'


# -- Options for HTML output ----------------------------------------------

html_theme = 'sphinx_rtd_theme'
# rtd_theme only handles 4 levels for the sidebar navigation.
html_theme_options = {'navigation_depth': 4}

html_js_files = ['js/versioning.js']

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False
# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True
# Output file base name for HTML help builder.
htmlhelp_basename = 'rose-doc'

# Basic styling: add a favicon & replace sidebar heading title with Rose logo.
html_theme_options = {
    'logo_only': True,
}
html_logo = 'img/rose-logo-crop.png'
html_favicon = 'img/rose-favicon.png'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
    'maxlistdepth': 10,  # Prevent "Too Deeply Nested" errors.
}

# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        'index',
        'rose-documentation.tex',
        'Rose Documentation',
        'Metomi',
        'manual',
    ),
    (
        'tutorial/cylc/index',
        'cylc-tutorial.tex',
        'Cylc Tutorial',
        'Metomi',
        'manual',
    ),
    (
        'tutorial/rose/index',
        'rose-tutorial.tex',
        'Rose Tutorial',
        'Metomi',
        'manual',
    ),
]
latex_logo = 'img/rose-logo.png'
# If true, show page references after internal links.
latex_show_pagerefs = True
# If true, show URL addresses after external links.
latex_show_urls = 'inline'
# Don't link RST source page.
html_show_sourcelink = False
# Add a custom css file to make tables wrap correctly.
html_css_files = ['custom.css']

# -- Options for manual page output ---------------------------------------

# (source start file, name, description, authors, manual section).
man_pages = [('index', 'rose-doc', 'rose-doc Documentation', ['Metomi'], 1)]


# -- Options for Texinfo output -------------------------------------------

# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        'index',
        'rose-doc',
        'Rose Documentation',
        'Metomi',
        'rose-doc',
        'Documentation For The Rose Configuration System.',
        'Miscellaneous',
    ),
]
# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'


def setup(app):
    # set the html_static_path in an extension so as not to conflict with
    # cylc.sphinx_ext extensions
    app.config.html_static_path.append('_static')
