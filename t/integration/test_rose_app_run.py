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
"""Integration tests for Rose app-run"""

import pytest

from metomi.rose.app_run import AppRunner as rose_app_run
from metomi.rose.popen import RosePopenError
from metomi.rose.opt_parse import RoseOptionParser
from metomi.rose.reporter import Reporter


def test_adds_shadow_pythonpath(monkeypatch, tmp_path, capsys):
    """If _PYTHONPATH is set rose app uses this as PYTHONPATH.

    This allows Cylc and Rose to operate in some other environment
    but this app to go to the users preferred env.
    """
    # Sets up a rose-app:
    (tmp_path / 'rose-app.conf').write_text(
        '[command]\n'
        'default = echo "${PYTHONPATH}" && exit 0'
    )

    monkeypatch.setenv('_PYTHONPATH', '/foo:/bar')

    # Fake the rose options:
    opt_parser = RoseOptionParser()
    option_keys = rose_app_run.OPTIONS
    opt_parser.add_my_options(*option_keys)
    opts, args = opt_parser.parse_args()
    opts.conf_dir = str(tmp_path)
    event_handler = Reporter(opts.verbosity - opts.quietness)
    runner = rose_app_run(event_handler)

    # Run our app.
    # Rose Popen doesn't like Pytests fake stdin and fails
    # we want to ensure that it's _that_ failure:
    with pytest.raises(RosePopenError) as exc:
        runner(opts, [str(tmp_path)])
    assert exc.value.stderr.split(' ')[-1] == f"'{str(tmp_path)}'"

    # Finally we test what we came here for:
    readouterr = capsys.readouterr()
    assert 'export PYTHONPATH=/foo:/bar' in readouterr.out
