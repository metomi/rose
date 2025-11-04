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

import hashlib
from pathlib import Path
import pytest

from metomi.rose.checksum import get_checksum

HELLO_WORLD = hashlib.md5(b'Hello World').hexdigest()
HELLO_JUPITER = hashlib.md5(b'Hello Jupiter').hexdigest()


@pytest.fixture(scope='module')
def checksums_setup(tmp_path_factory):
    """provide some exemplars for checksum to work on."""
    tmp_path = tmp_path_factory.getbasetemp()
    (tmp_path / 'foo').write_text('Hello World')
    (tmp_path / 'bar').mkdir()
    (tmp_path / 'bar/baz').write_text('Hello Jupiter')
    (tmp_path / 'goodlink').symlink_to('foo')
    (tmp_path / 'badlink').symlink_to('bad')
    yield tmp_path


@pytest.fixture(scope='module')
def checksums_dir(checksums_setup):
    yield (
        {a: (b, c) for a, b, c in get_checksum(str(checksums_setup))},
        checksums_setup
    )


def test_checksum_single_file(checksums_setup):
    res = get_checksum(str(checksums_setup / 'foo'))[0][1]
    assert res == HELLO_WORLD


def test_checksum_custom_checksum_function(checksums_setup):
    res = get_checksum(
        str(checksums_setup / 'foo'),
        # Last 3 letters of the reversed filename:
        checksum_func=lambda x, _: x[-1:-4:-1]
    )[0][1]
    assert res == 'oof'


def test_get_checksum_for_all_files(checksums_dir):
    assert len(checksums_dir[0]) == 7


def test_get_checksum_for_goodlink(checksums_dir):
    assert checksums_dir[0]['goodlink'][0] == HELLO_WORLD


def test_get_checksum_for_badlink(checksums_dir):
    assert checksums_dir[0]['badlink'][0] == str(checksums_dir[1] / 'bad')


def test_get_checksum_for_subdir_file(checksums_dir):
    assert checksums_dir[0]['bar/baz'][0] == HELLO_JUPITER


def test_get_checksum_for_non_path():
    unlikely = '/var/tmp/ariuaibvnoijunhoiujoiuj'
    assert not Path(unlikely).exists()
    with pytest.raises(FileNotFoundError, match=unlikely):
        get_checksum(unlikely)
