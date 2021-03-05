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

from pathlib import Path

from metomi.rose.loc_handlers.rsync_remote_check import main


def test_check_file(capsys, tmp_path):
    content = 'blah'
    permission_level = 33188
    filepath = tmp_path / 'stuff'
    filepath.write_text(content)
    filepath.chmod(permission_level)
    main(str(filepath), 'blob', 'tree')
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == 'blob'
    mode, mtime, size, path = captured.out.splitlines()[1].split()
    assert path == str(filepath)
    assert int(mode) == permission_level
    assert size == str(filepath.stat().st_size)


def test_check_folder(capsys, tmp_path):
    # create a file and chmod it
    (tmp_path / 'more.stuff').write_text('Hi')
    (tmp_path / 'more.stuff').chmod(int('0o100633', base=8))

    # create another file
    (tmp_path / 'even.more.stuff').write_text('Hi')

    # run the remote check on the dir
    main(str(tmp_path), 'blob', 'tree')
    lines = capsys.readouterr().out.splitlines()

    # the first line should be the dir
    assert lines[0] == 'tree'

    # the following lines should be the files
    files = {
        # filename: [mode, mod_time, size]
        str(Path(line.split()[-1]).relative_to(tmp_path)): line.split()[:-1]
        for line in lines[1:]
    }
    assert list(sorted(files)) == ['even.more.stuff', 'more.stuff']
    mode, _, size = files['more.stuff']
    assert mode == '33179'
    assert size == '2'
