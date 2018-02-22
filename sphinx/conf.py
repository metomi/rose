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
import sys
import os

from rose.resource import ResourceLocator

# rose-documentation build configuration file, initial version created by
# sphinx-quickstart.


# Add local sphinx extensions directory to extensions path.
sys.path.append(os.path.abspath('ext'))

# Register extensions.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.graphviz',
    'sphinx.ext.mathjax',
    'minicylc',
    'cylc_lang',
    'rose_lang',
    'rose_domain',
    'sub_lang',
    'practical',
    'auto_cli_doc',
    'script_include',
    'sphinxcontrib.httpdomain'
]

# Use SVG for all graphviz (and by extension minicylc) blocks (alt png).
graphviz_output_format = 'svg'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Rose Documentation'
copyright = (': British Crown Copyright 2012-8 Met Office. See Terms of Use. '
             'This document is released under the Open Government Licence')

# The full version for the project you're documenting, acts as replacement for
# |version|.
release = ResourceLocator().get_version()
# The short X.Y version, acts as replacement for |release|.
version = release.split('-')[0]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'autumn'


# -- Options for HTML output ----------------------------------------------

html_theme = 'sphinx_rtd_theme'
# rtd_theme only handles 4 levels for the sidebar navigation.
html_theme_options = {'navigation_depth': 4}
html_static_path = ['_static']
# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False
# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True
# Output file base name for HTML help builder.
htmlhelp_basename = 'rose-doc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    'papersize': 'a4paper'
    # 'preamble': '',  # Additional stuff for the LaTeX preamble.
}

# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    ('index', 'rose-documentation.tex', 'Rose Documentation',
     'Metomi', 'manual'),
]
# latex_logo = None
# If true, show page references after internal links.
latex_show_pagerefs = True
# If true, show URL addresses after external links.
latex_show_urls = 'inline'
# Don't link RST source page.
html_show_sourcelink = False


# -- Options for manual page output ---------------------------------------

# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'rose-doc', 'rose-doc Documentation',
     ['Metomi'], 1)
]


# -- Options for Texinfo output -------------------------------------------

# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    ('index', 'rose-doc', 'Rose Documentation', 'Metomi', 'rose-doc',
     'Documentation For The Rose Configuration System.', 'Miscellaneous'),
]
# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'
