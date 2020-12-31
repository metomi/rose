# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
"""Script for extracting PDF documents from a Sphinx LaTeX build.

* Copies PDF documents from the ``latex`` build directory to a ``pdf`` folder.
* Creates an HTML index of these documents.

"""

import errno
import os
import shutil
import sys

import conf


def main():
    try:
        build_dir = sys.argv[1]
    except IndexError:
        sys.exit('usage: extract-pdf-documents build_dir')
    latex_dir = os.path.join(build_dir, 'latex')
    pdf_dir = os.path.join(build_dir, 'pdf')
    os.makedirs(pdf_dir, exist_ok=True)

    # the index html file
    html = (
        '<!DOCTYPE html>'
        '<html>'
        '<head>'
        '<title>Rose Documentation - PDF Documents</title>'
        '</head>'
        '<body>'
        '<h1>Rose Documentation - PDF Documents</h1>'
        '<ul>'
    )

    # loop over PDF documents defined in the Sphinx configuration file
    for file_name, document_name in (x[1:3] for x in conf.latex_documents):
        # move PDF document into the pdf directory
        file_name = file_name.replace('.tex', '.pdf')
        os.rename(
            os.path.join(latex_dir, file_name),
            os.path.join(pdf_dir, file_name)
        )
        # add an index entry for this document
        html += (
            '<li>'
            '<a href="%s">%s</a>'
            '</li>' % (file_name, document_name)
        )

    html += (
        '</ul>'
        '</body>'
        '</html>'
    )

    # write index file
    with open(os.path.join(pdf_dir, 'index.html'), 'w+') as index:
        index.write(html)

    # remove now un-necessary latex directory
    shutil.rmtree(latex_dir)


if __name__ == '__main__':
    main()
