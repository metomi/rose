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

import sys

from ast import literal_eval

from metomi.rose.loc_handlers.rsync_remote_check import main


def test_check_file(monkeypatch, capsys, tmp_path):
    content = 'blah'
    permission_level = '0o100777'
    filepath = tmp_path / 'stuff'
    filepath.write_text(content)
    filepath.chmod(int(permission_level, base=8))
    monkeypatch.setattr(
        sys, 'argv', ['ignored', str(filepath), 'blob', 'tree']
    )
    main()
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == 'blob'
    mode, mtime, size, path = captured.out.splitlines()[1].split()
    assert path == str(filepath)
    assert mode == permission_level
    assert size == str(filepath.stat().st_size)


def test_check_folder(
    monkeypatch, capsys, tmp_path
):
    folder_permission_level = '0o100777'
    dirpath = tmp_path / 'stuff'
    dirpath.mkdir()
    (dirpath / 'more.stuff').write_text('Hi')
    (dirpath / 'even.more.stuff').write_text('Hi')
    dirpath.chmod(int(folder_permission_level, base=8))
    monkeypatch.setattr(
        sys, 'argv', ['ignored', str(dirpath), 'blob', 'tree']
    )
    main()
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == 'tree'
    mode, _, size, path = literal_eval(captured.out.splitlines()[1])
    assert path == str((dirpath/'more.stuff'))
    assert mode == '0o100644'
    assert size == 2
