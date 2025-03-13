import sys

from metomi.rose.upgrade import MacroUpgrade


class UpgradeError(Exception):
    """Exception created when an upgrade fails."""

    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        sys.tracebacklimit = 0
        return self.msg

    __str__ = __repr__


class vn10_t999(MacroUpgrade):

    BEFORE_TAG = "vn1.0"
    AFTER_TAG = "vn1.0_t999"

    def upgrade(self, config, meta_config=None):
        existing_value = self.get_setting_value(
            config,
            ["namelist:namelist_3", "existing_value"]
        )
        self.add_setting(
            config,
            ["namelist:namelist_2", "new_value"],
            existing_value
        )
        return config, self.reports
