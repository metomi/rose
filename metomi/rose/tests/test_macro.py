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

from pathlib import Path

import pytest

from metomi.rose.config import ConfigNode
from metomi.rose.macro import (
    load_meta_macro_modules,
    pretty_format_config,
)


def test_load_meta_macro_modules(tmp_path: Path):
    """It should execute metadata macro modules."""
    (macro_dir := tmp_path / 'lib' / 'python' / 'macros').mkdir(parents=True)
    macro_path = macro_dir / 'custom_macro.py'
    macro_path.write_text('VALUE = "loaded"\n')

    modules = load_meta_macro_modules([str(macro_path)], module_prefix='test_')

    assert len(modules) == 1
    assert modules[0].__name__ == 'test_custom_macro'
    assert modules[0].VALUE == 'loaded'


def test_pretty_format_config(capsys):
    """It should exit 1 on config format issue.

    See https://github.com/metomi/rose/pull/3022
    """
    # NOTE: there's a rule that namelist keys should be lowercase
    node = ConfigNode()
    node.set(['namelist:a', 'Foo'], 'bar')

    # which should cause this call to exit 1
    with pytest.raises(SystemExit) as exc_ctx:
        pretty_format_config(node)

    assert exc_ctx.value.code == 1

    # and output a message to stderr
    _out, err = capsys.readouterr()
    assert 'Foo does not match foo' in err
