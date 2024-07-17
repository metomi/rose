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

"""Tests for rose macros rule module.
"""

import pytest
from metomi.rose.macros.rule import RuleEvaluator


param = pytest.param
rule_evaluator = RuleEvaluator()


@pytest.mark.parametrize(
    'section',
    (('template variables'), ('namelist'), ('empy:suite.rc')))
@pytest.mark.parametrize(
    'rule_in, id_in, rule_out, this, this_out', [
        param(
            '{section}=FOO == 42',
            '{section}=FOO',
            '{% if this == 42 %}True{% else %}False{% endif %}',
            '42',
            {'this': '42'},
            id='basic_rule'
        ),
        param(
            'all({section}=FOO == "42")',
            '{section}=FOO',
            '{% if (this == _value0 and this == _value0 and'
            ' this == _value0) %}True{% else %}False{% endif %}',
            '42,43,44',
            {'this': '42,43,44', '_value0': '42'},
            id='all_rule'
        ),
        param(
            'len({section}=FOO) < 4',
            '{section}=FOO',
            '{% if 3 < 4 %}True{% else %}False{% endif %}',
            '42,43,44',
            {'this': '42,43,44'},
            id='len_rule'
        )
    ]
)
def test__process_rule(rule_in, id_in, rule_out, this, this_out, section):
    """Test processing of rules into jinja2.

    Also provides tests for
    https://github.com/metomi/rose/issues/2737
    """
    rule_in = rule_in.format(section=section)
    id_in = id_in.format(section=section)
    rule_evaluator._get_value_from_id = lambda *_: this
    rule, map_ = rule_evaluator._process_rule(
        rule_in, id_in, 'patchme', 'patchme')
    assert rule == rule_out
    assert map_ == this_out


def test__process_rule_scientific_numbers():
    """A string which looks like a scientific number comes out as
    a scientific number.
    """
    this = "99"
    rule = 'template variables=FOO=="9e9"'

    rule_evaluator._get_value_from_id = lambda *_: this

    _, map_ = rule_evaluator._process_rule(
        rule, 'template variables=FOO', 'patchme', 'patchme')
    assert map_ == {
        'this': '99',
        '_scinum0': 9000000000.0,
        '_value0': '_scinum0'
    }
