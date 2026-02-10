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

import pytest
from gi.repository.Gtk import MessageType

from metomi.rose.gtk.dialog import run_dialog

import metomi.rose.config_editor #NOQA: F401 lazily loaded.


@pytest.mark.parametrize(
    'args, kwargs',
    (
        (
            ('OK', 'test'),
            {
                'extra_text': 'Antidisestablismentarianism is a long word!',
                # Make and destroy the dialog box:
                'modal': False,
            }
        ),
        (
            (MessageType.INFO, 'test'),
            {
                'extra_text': 'Antidisestablismentarianism is a long word!',
                # Make and destroy the dialog box:
                'modal': False,
            }
        )
    )
)
def test_dialog_ok(args, kwargs):
    """Create (but only show very, very briefly) a dialog box.

    Tests that we've got the pack_start args correct:
    https://github.com/metomi/rose/issues/2993
    """
    run_dialog(*args, **kwargs)
