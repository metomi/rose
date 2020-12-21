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
import os
import unittest

from metomi.rose.env import env_export


class _TestEnvExport(unittest.TestCase):
    """Test "env_export" function."""

    def test_report_new(self):
        """Ensure that env_export only reports 1st time or on change."""
        events = []
        env_export("FOO", "foo", events.append)
        env_export("FOO", "foo", events.append)
        env_export("FOO", "food", events.append)
        env_export("FOO", "foot", events.append)
        env_export("FOO", "foot", events.append)
        event_args = [event.args[1] for event in events]
        self.assertEqual(event_args, ["foo", "food", "foot"], "events")

    def test_report_old(self):
        """Ensure that env_export only reports 1st time or on change."""
        events = []
        os.environ["BAR"] = "bar"
        env_export("BAR", "bar", events.append)
        env_export("BAR", "bar", events.append)
        env_export("BAR", "bar", events.append)
        env_export("BAR", "barley", events.append)
        env_export("BAR", "barley", events.append)
        env_export("BAR", "barber", events.append)
        event_args = [event.args[1] for event in events]
        self.assertEqual(event_args, ["bar", "barley", "barber"], "events")


if __name__ == "__main__":
    unittest.main()
