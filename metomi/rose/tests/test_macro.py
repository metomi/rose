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

import pytest

from metomi.rose.config import ConfigNode
from metomi.rose.macro import pretty_format_config


def test_pretty_format_config(capsys):
    """It should exit 1 on config format issue.

    See https://github.com/metomi/rose/pull/3022
    """
    # NOTE: there's a rule that namelist keys should be lowercase
    node = ConfigNode()
    node.set(['namelist:a', 'Foo'], 'bar')

    _out, err = capsys.readouterr()
    assert (_out, err) == None

    # which should cause this call to exit 1
    with pytest.raises(SystemExit) as exc_ctx:
        pretty_format_config(node)

    assert exc_ctx.value.code == 1

    # and output a message to stderr
    _out, err = capsys.readouterr()
    assert 'Foo does not match foo' in err
