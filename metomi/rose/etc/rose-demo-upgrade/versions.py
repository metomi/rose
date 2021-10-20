#!/usr/bin/env python3
# Copyright (C) British Crown (Met Office) & Contributors.
# -----------------------------------------------------------------------------
"""Module containing example macros for using rose app-upgrade.

Quotes are copyright Python (Monty) Pictures Ltd, Freeway Cam (UK) Ltd.

"""

import metomi.rose.upgrade


class UpgradeGarden01(metomi.rose.upgrade.MacroUpgrade):

    """'We want... a shrubbery!'"""

    BEFORE_TAG = "garden0.1"
    AFTER_TAG = "garden0.2"

    def downgrade(self, config, meta_config=None):
        self.remove_setting(config, ["namelist:features", "shrubberies"])
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:features", "shrubberies"], "1")
        return config, self.reports


class UpgradeGarden02(metomi.rose.upgrade.MacroUpgrade):

    """'...there is one small problem...'"""

    BEFORE_TAG = "garden0.2"
    AFTER_TAG = "garden0.3"

    def downgrade(self, config, meta_config=None):
        self.remove_setting(config, ["namelist:features", "shrubbery_laurels"])
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.add_setting(
            config,
            ["namelist:features", "shrubbery_laurels"],
            "'particularly nice'",
        )
        shrub_num = self.get_setting_value(
            config, ["namelist:features", "shrubberies"]
        )
        if shrub_num in ["0", "1"]:
            self.add_report(
                "namelist:features",
                "shrubberies",
                shrub_num,
                info="More than one shrubbery is desirable",
                is_warning=True,
            )
        return config, self.reports


class UpgradeGarden03(metomi.rose.upgrade.MacroUpgrade):

    """'You must find... another shrubbery!'"""

    BEFORE_TAG = "garden0.3"
    AFTER_TAG = "garden0.4"

    def downgrade(self, config, meta_config=None):
        if self._get_shrub_num(config) == 2:
            self.change_setting_value(
                config, ["namelist:features", "shrubberies"], "1"
            )
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        if self._get_shrub_num(config) == 1:
            self.change_setting_value(
                config,
                ["namelist:features", "shrubberies"],
                "2",
                info="Fetched another shrubbery",
            )
        return config, self.reports

    def _get_shrub_num(self, config):
        shrub_num = self.get_setting_value(
            config, ["namelist:features", "shrubberies"]
        )
        try:
            shrub_num = float(shrub_num)
        except (TypeError, ValueError):
            return None
        return shrub_num


class UpgradeGarden041(metomi.rose.upgrade.MacroUpgrade):

    """'...the two-level effect with a little path running down the middle'"""

    BEFORE_TAG = "garden0.4"
    AFTER_TAG = "garden0.4.1"

    def downgrade(self, config, meta_config=None):
        self.act_from_files(config, downgrade=True)
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.act_from_files(config, downgrade=False)
        return config, self.reports


class UpgradeGarden09(metomi.rose.upgrade.MacroUpgrade):

    """'cut down the mightiest tree in the forest... with... a herring!'"""

    BEFORE_TAG = "garden0.4.1"
    AFTER_TAG = "garden0.9"

    def downgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "AXE"])
        self.remove_setting(config, ["namelist:trees"])
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:trees", "mighty_tree"], "1")
        self.add_setting(config, ["env", "AXE"], "herring")
        return config, self.reports
