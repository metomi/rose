# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
"""Tests the data-scraping algorithm used in the rose macro advanced tutorial
is still working."""
import re
import requests
import sys

def main():
    # Get data
    ret = requests.get("http://www.heavens-above.com/planetsummary.aspx")
    assert ret.status_code == 200
    text = '\n'.join(list(ret.iter_lines()))
    planets = re.findall("(\w+)</td>",
                         re.sub(r'(?s)^.*(<thead.*?ascension).*$',
                                r"\1", text))

    # Test code used in the validator macro
    distances = re.findall("([\d.]+)</td>",
                           re.sub('(?s)^.*(Range.*?Brightness).*$',
                                  r"\1", text))
    assert len(planets) == len(distances)
    map(float, distances)

    # Test code used in the reporter macro
    constellations = re.findall("(\w+)</a>",
                           re.sub('(?s)^.*(Constellation.*?Meridian).*$',
                                  r"\1", text))
    assert len(planets) == len(constellations)

if __name__ == '__main__':
    main()
    sys.exit(0)
