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

import json
from pathlib import Path
from typing import Optional
import pytest

from metomi.rosie.suite_id import SuiteId


@pytest.mark.parametrize(
    'vcs_info, expected',
    [
        pytest.param(
            {
                'version control system': 'svn',
                'url': '/a/b/c',
                'revision': '4242'
            },
            '/a/b/c@4242',
            id="Valid SVN info"
        ),
        pytest.param(
            {'version control system': 'git'},
            None,
            id="Non-SVN VCS info"
        )
    ]
)
def test_parse_cylc_vc_file(
    vcs_info: dict, expected: Optional[str], tmp_path: Path
):
    vcs_file = tmp_path / 'gimli.json'
    vcs_file.write_text(json.dumps(vcs_info))
    assert SuiteId._parse_cylc_vc_file(str(vcs_file)) == expected
