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
"""Tests for functions in the cylc suite engine proc.
"""

import pytest
from pytest import param

try:
    import cylc.rose.platform_utils
except ImportError:
    pytestmark = pytest.mark.skip(reason="cylc-rose not found")

from metomi.rose.suite_engine_procs.cylc import CylcProcessor


@pytest.mark.parametrize(
    'platform, expect',
    [
        param({'hosts': ['localhost']}, None, id='platform is local'),
        param(
            {
                'hosts': ['my_host'],
                'selection': {'method': 'definition order'},
            },
            'my_host',
            id='platform is remote',
        ),
        param(None, None, id='Task not in config'),
    ],
)
def test_get_task_auth(monkeypatch, platform, expect):
    def fake_get_platform(*_):
        if platform is None:
            raise KeyError
        else:
            return platform

    monkeypatch.setattr(
        cylc.rose.platform_utils,
        'get_platform_from_task_def',
        fake_get_platform,
    )
    result = CylcProcessor().get_task_auth('foo', 'bar')
    assert result is expect


@pytest.mark.parametrize(
    'cycle_name_tuples, job_platform_map, expect',
    [
        param(
            [('1', None)],
            {
                '1': {
                    'task_1': {
                        'hosts': ['hello'],
                        'selection': {'method': 'definition order'},
                    }
                }
            },
            ['hello'],
            id='1 cycle:1 host',
        ),
        param(
            [('1', None)],
            {
                '1': {
                    'task_1': {
                        'hosts': ['hey', 'hi', 'howdy'],
                        'selection': {'method': 'definition order'},
                    }
                }
            },
            ['hey', 'hi', 'howdy'],
            id='1 cycle:3 hosts',
        ),
        param(
            [('1', None), ('2', None)],
            {
                '1': {
                    'task_1': {
                        'hosts': ['hello'],
                        'selection': {'method': 'definition order'},
                    }
                },
                '2': {
                    'task_1': {
                        'hosts': ['hello'],
                        'selection': {'method': 'definition order'},
                    }
                },
            },
            ['hello'],
            id='2 cycles:1 platform',
        ),
        param(
            [('1', None), ('2', None)],
            {
                '1': {
                    'task_1': {
                        'hosts': ['hello'],
                        'selection': {'method': 'definition order'},
                    }
                },
                '2': {
                    'task_1': {
                        'hosts': ['goodbye'],
                        'selection': {'method': 'definition order'},
                    }
                },
            },
            ['hello', 'goodbye'],
            id='2 cycles:2 platforms',
        ),
    ],
)
def test_get_suite_jobs_auths(
    monkeypatch, cycle_name_tuples, job_platform_map, expect
):
    monkeypatch.setattr(
        cylc.rose.platform_utils,
        'get_platforms_from_task_jobs',
        lambda _, cycle: job_platform_map[cycle],
    )
    for item in CylcProcessor().get_suite_jobs_auths(
        'suite_name', cycle_name_tuples
    ):
        assert item in expect
