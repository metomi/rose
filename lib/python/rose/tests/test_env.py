import os
import unittest

from rose.env import env_export


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
