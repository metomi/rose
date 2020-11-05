#!/usr/ bin/env python3
# coding=utf-8

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

import codecs

from glob import glob
from os.path import join, abspath, dirname
import re


from setuptools import setup, find_namespace_packages

here = abspath(dirname(__file__))


def read(*parts):
    with codecs.open(join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r") as fh:
    long_description = fh.read()


INSTALL_REQUIRES = [
    "jinja2>=2.10.1",
    "aiofiles",
    "tornado",
    "sqlalchemy",
    "metomi-isodatetime",
    "requests",
    "ldap3",
]
EXTRAS_REQUIRE = {
    'docs': [
        'sphinx',
        'sphinx_rtd_theme',
        'sphinxcontrib-httpdomain',
        'hieroglyph',
        'sphinxcontrib-svg2pdfconverter',
        'cylc-sphinx-extensions[all]'
    ]
}
EXTRAS_REQUIRE['all'] = list({y for x in EXTRAS_REQUIRE.values() for y in x})


setup(
    # Metadata
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=find_version("metomi", "rose", "__init__.py"),

    # Options
    scripts=glob(join("bin", "*"))
    + glob(join("sbin", "*"))
    + glob(join("lib", "bash", "*")),
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    package_data={
        "metomi.rose": ["etc/.*"],
        "metomi.rosie": ["lib/*"]
    },
    packages=find_namespace_packages(include=["metomi.*"]),
)
