#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
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
#-------------------------------------------------------------------------------
# Test "rose app-upgrade" for complex macros.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 8

#-------------------------------------------------------------------------------
# Check complex upgrading
init <<'__CONFIG__'
meta=test-app-upgrade/apple

[namelist:standard_sect]
standard_opt=.true.

[namelist:add_sect]

[namelist:add_opt_override]
opt_override=.true.

[namelist:add_force_opt_override]
opt_has_changed=.false.

[namelist:enable_sect_enabled]

[namelist:enable_opt_enabled]
already_enabled=.true.

[!namelist:enable_sect_ignored]

[namelist:enable_opt_ignored]
!starts_off_ignored=.true.

[!!namelist:enable_sect_trig_ignored]

[namelist:enable_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!!namelist:ignore_sect_trig_ignored]

[namelist:ignore_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!namelist:ignore_sect_ignored]

[namelist:ignore_opt_ignored]
!already_ignored=.true.

[namelist:ignore_sect_enabled]

[namelist:ignore_opt_enabled]
starts_off_enabled=.true.

[!!namelist:trig_ignore_sect_trig_ignored]

[namelist:trig_ignore_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!namelist:trig_ignore_sect_ignored]

[namelist:trig_ignore_opt_ignored]
!already_ignored=.true.

[namelist:trig_ignore_sect_enabled]

[namelist:trig_ignore_opt_enabled]
starts_off_enabled=.true.

[namelist:change_opt]
opt_has_changed=.false.
!ignore_opt_has_changed=.false.
!!trig_ignore_opt_has_changed=.false.

[namelist:remove_sect_full]
opt_with_content=.true.

[namelist:remove_sect_empty]

[namelist:remove_opt]
remove_this_opt=.true.

[!namelist:remove_ignore_sect_full]
opt_with_content=.true.

[!namelist:remove_ignore_sect_empty]

[namelist:remove_ignore_opt]
!remove_this_ignore_opt=.true.

[!!namelist:remove_trig_ignore_sect_full]
!opt_with_content=.true.

[!!namelist:remove_trig_ignore_sect_empty]

[namelist:remove_trig_ignore_opt]
!!remove_this_trig_ignore_opt=.true.

[namelist:change_opt_if_value]
change_opt_if_true=.true.

[namelist:change_ign_opt_if_value]
!change_opt_if_true=.true.

[namelist:not_change_ign_opt_if_value]
!change_opt_if_true=.true.
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import rose.upgrade


class UpgradeAppletoFig(rose.upgrade.MacroUpgrade):

    """Upgrade from Apple to Fig."""

    BEFORE_TAG = "apple"
    AFTER_TAG = "fig"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:add_sect", "new_opt"],
                         ".true.")
        self.add_setting(config, ["namelist:add_sect_only"])
        self.add_setting(config, ["namelist:add_implied_sect",
                                  "opt_forces_section"], ".true.")
        self.add_setting(config, ["namelist:add_opt_override",
                                  "opt_override"], ".false.")
        self.add_setting(config, ["namelist:add_force_opt_override",
                                  "opt_has_changed"], ".true.")
        self.enable_setting(config, ["namelist:missing_sect"])
        self.enable_setting(config, ["namelist:standard_sect",
                                     "missing_option"])
        self.enable_setting(config, ["namelist:enable_sect_enabled"])
        self.enable_setting(config, ["namelist:enable_opt_enabled",
                                     "already_enabled"])
        self.enable_setting(config, ["namelist:enable_sect_trig_ignored"])
        self.enable_setting(config, ["namelist:enable_opt_trig_ignored",
                                     "starts_off_trig_ignored"])
        self.enable_setting(config, ["namelist:enable_sect_ignored"])
        self.enable_setting(config, ["namelist:enable_opt_ignored",
                                     "already_ignored"])
        self.ignore_setting(config, ["namelist:missing_sect"])
        self.ignore_setting(config, ["namelist:standard_sect",
                                     "missing_option"])
        self.ignore_setting(config, ["namelist:ignore_sect_enabled"])
        self.ignore_setting(config, ["namelist:ignore_opt_enabled",
                                     "starts_off_enabled"])
        self.ignore_setting(config, ["namelist:ignore_sect_trig_ignored"])
        self.ignore_setting(config, ["namelist:ignore_opt_trig_ignored",
                                     "starts_off_trig_ignored"])
        self.ignore_setting(config, ["namelist:ignore_sect_ignored"])
        self.ignore_setting(config, ["namelist:ignore_opt_ignored",
                                     "already_ignored"])
        self.ignore_setting(config, ["namelist:missing_sect"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config, ["namelist:standard_sect",
                                     "missing_option"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config, ["namelist:trig_ignore_sect_enabled"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config, ["namelist:trig_ignore_opt_enabled",
                                     "starts_off_enabled"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config,
                            ["namelist:trig_ignore_sect_trig_ignored"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config, ["namelist:trig_ignore_opt_trig_ignored",
                                     "starts_off_trig_ignored"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config, ["namelist:trig_ignore_sect_ignored"],
                            state=config.STATE_SYST_IGNORED)
        self.ignore_setting(config, ["namelist:trig_ignore_opt_ignored",
                                     "already_ignored"],
                            state=config.STATE_SYST_IGNORED)
        self.change_setting_value(config, ["namelist:standard_sect",
                                           "missing_opt"], "5")
        self.change_setting_value(config, ["namelist:change_opt", 
                                           "opt_has_changed"],
                                  ".true.")
        self.change_setting_value(config, ["namelist:change_opt", 
                                           "ignore_opt_has_changed"],
                                  ".true.")
        self.change_setting_value(config, ["namelist:change_opt", 
                                           "trig_ignore_opt_has_changed"],
                                  ".true.")
        self.remove_setting(config, ["namelist:missing_sect"])
        self.remove_setting(config, ["namelist:missing_sect", "missing_opt"])
        self.remove_setting(config, ["namelist:standard_sect", "missing_opt"])
        self.remove_setting(config, ["namelist:remove_sect_empty"])
        self.remove_setting(config, ["namelist:remove_sect_full"])
        self.remove_setting(config, ["namelist:remove_opt",
                                     "remove_this_opt"])
        self.remove_setting(config, ["namelist:remove_ignore_sect_empty"])
        self.remove_setting(config, ["namelist:remove_ignore_sect_full"])
        self.remove_setting(config, ["namelist:remove_ignore_opt",
                                     "remove_this_ignore_opt"])
        self.remove_setting(config,
                            ["namelist:remove_trig_ignore_sect_empty"])
        self.remove_setting(config,
                            ["namelist:remove_trig_ignore_sect_full"])
        self.remove_setting(config,
                            ["namelist:remove_trig_ignore_opt",
                             "remove_this_trig_ignore_opt"])
        if self.get_setting_value(config,
                                  ["namelist:change_opt_if_value",
                                   "change_opt_if_true"]) == ".true.":
            self.change_setting_value(
                        config, ["namelist:change_opt_if_value",
                                 "change_opt_if_true"], ".false.")
        if self.get_setting_value(config,
                                  ["namelist:change_ign_opt_if_value",
                                   "change_opt_if_true"],
                                  no_ignore=False) == ".true.":
            self.change_setting_value(
                        config, ["namelist:change_ign_opt_if_value",
                                 "change_opt_if_true"], ".false.")
        if self.get_setting_value(config,
                                  ["namelist:not_change_ign_opt_if_value",
                                   "change_opt_if_true"],
                                  no_ignore=True) == ".true.":
            self.change_setting_value(
                        config, ["namelist:not_change_ign_opt_if_value",
                                 "change_opt_if_true"], ".false.")
        return config, self.reports
__MACRO__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade
# Check a complex upgrade
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config fig
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgradeapple-fig: changes: 33
    namelist:add_sect=new_opt=.true.
        Added with value '.true.'
    namelist:add_sect_only=None=None
        Added
    namelist:add_implied_sect=None=None
        Added
    namelist:add_implied_sect=opt_forces_section=.true.
        Added with value '.true.'
    namelist:enable_sect_trig_ignored=None=None
        trig-ignored -> enabled
    namelist:enable_opt_trig_ignored=starts_off_trig_ignored=.true.
        trig-ignored -> enabled
    namelist:enable_sect_ignored=None=None
        user-ignored -> enabled
    namelist:ignore_sect_enabled=None=None
        enabled -> user-ignored
    namelist:ignore_opt_enabled=starts_off_enabled=.true.
        enabled -> user-ignored
    namelist:ignore_sect_trig_ignored=None=None
        trig-ignored -> user-ignored
    namelist:ignore_opt_trig_ignored=starts_off_trig_ignored=.true.
        trig-ignored -> user-ignored
    namelist:trig_ignore_sect_enabled=None=None
        enabled -> trig-ignored
    namelist:trig_ignore_opt_enabled=starts_off_enabled=.true.
        enabled -> trig-ignored
    namelist:trig_ignore_sect_ignored=None=None
        user-ignored -> trig-ignored
    namelist:trig_ignore_opt_ignored=already_ignored=.true.
        user-ignored -> trig-ignored
    namelist:change_opt=opt_has_changed=.true.
        Value: '.false.' -> '.true.'
    namelist:change_opt=ignore_opt_has_changed=.true.
        Value: '.false.' -> '.true.'
    namelist:change_opt=trig_ignore_opt_has_changed=.true.
        Value: '.false.' -> '.true.'
    namelist:remove_sect_empty=None=None
        Removed
    namelist:remove_sect_full=opt_with_content=None
        Removed
    namelist:remove_sect_full=None=None
        Removed
    namelist:remove_opt=remove_this_opt=None
        Removed
    namelist:remove_ignore_sect_empty=None=None
        Removed
    namelist:remove_ignore_sect_full=opt_with_content=None
        Removed
    namelist:remove_ignore_sect_full=None=None
        Removed
    namelist:remove_ignore_opt=remove_this_ignore_opt=None
        Removed
    namelist:remove_trig_ignore_sect_empty=None=None
        Removed
    namelist:remove_trig_ignore_sect_full=opt_with_content=None
        Removed
    namelist:remove_trig_ignore_sect_full=None=None
        Removed
    namelist:remove_trig_ignore_opt=remove_this_trig_ignore_opt=None
        Removed
    namelist:change_opt_if_value=change_opt_if_true=.false.
        Value: '.true.' -> '.false.'
    namelist:change_ign_opt_if_value=change_opt_if_true=.false.
        Value: '.true.' -> '.false.'
    =meta=test-app-upgrade/fig
        Upgraded from apple to fig
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/fig

[namelist:add_force_opt_override]
opt_has_changed=.false.

[namelist:add_implied_sect]
opt_forces_section=.true.

[namelist:add_opt_override]
opt_override=.true.

[namelist:add_sect]
new_opt=.true.

[namelist:add_sect_only]

[namelist:change_ign_opt_if_value]
!change_opt_if_true=.false.

[namelist:change_opt]
!ignore_opt_has_changed=.true.
opt_has_changed=.true.
!!trig_ignore_opt_has_changed=.true.

[namelist:change_opt_if_value]
change_opt_if_true=.false.

[namelist:enable_opt_enabled]
already_enabled=.true.

[namelist:enable_opt_ignored]
!starts_off_ignored=.true.

[namelist:enable_opt_trig_ignored]
starts_off_trig_ignored=.true.

[namelist:enable_sect_enabled]

[namelist:enable_sect_ignored]

[namelist:enable_sect_trig_ignored]

[namelist:ignore_opt_enabled]
!starts_off_enabled=.true.

[namelist:ignore_opt_ignored]
!already_ignored=.true.

[namelist:ignore_opt_trig_ignored]
!starts_off_trig_ignored=.true.

[!namelist:ignore_sect_enabled]

[!namelist:ignore_sect_ignored]

[!namelist:ignore_sect_trig_ignored]

[namelist:not_change_ign_opt_if_value]
!change_opt_if_true=.true.

[namelist:remove_ignore_opt]

[namelist:remove_opt]

[namelist:remove_trig_ignore_opt]

[namelist:standard_sect]
standard_opt=.true.

[namelist:trig_ignore_opt_enabled]
!!starts_off_enabled=.true.

[namelist:trig_ignore_opt_ignored]
!!already_ignored=.true.

[namelist:trig_ignore_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!!namelist:trig_ignore_sect_enabled]

[!!namelist:trig_ignore_sect_ignored]

[!!namelist:trig_ignore_sect_trig_ignored]
__CONFIG__
teardown

#-------------------------------------------------------------------------------
# Check complex upgrading with info
init <<'__CONFIG__'
meta=test-app-upgrade/apple

[namelist:standard_sect]
standard_opt=.true.

[namelist:add_sect]

[namelist:add_opt_override]
opt_override=.true.

[namelist:add_force_opt_override]
opt_has_changed=.false.

[namelist:enable_sect_enabled]

[namelist:enable_opt_enabled]
already_enabled=.true.

[!namelist:enable_sect_ignored]

[namelist:enable_opt_ignored]
!starts_off_ignored=.true.

[!!namelist:enable_sect_trig_ignored]

[namelist:enable_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!!namelist:ignore_sect_trig_ignored]

[namelist:ignore_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!namelist:ignore_sect_ignored]

[namelist:ignore_opt_ignored]
!already_ignored=.true.

[namelist:ignore_sect_enabled]

[namelist:ignore_opt_enabled]
starts_off_enabled=.true.

[!!namelist:trig_ignore_sect_trig_ignored]

[namelist:trig_ignore_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!namelist:trig_ignore_sect_ignored]

[namelist:trig_ignore_opt_ignored]
!already_ignored=.true.

[namelist:trig_ignore_sect_enabled]

[namelist:trig_ignore_opt_enabled]
starts_off_enabled=.true.

[namelist:change_opt]
opt_has_changed=.false.
!ignore_opt_has_changed=.false.
!!trig_ignore_opt_has_changed=.false.

[namelist:remove_sect_full]
opt_with_content=.true.

[namelist:remove_sect_empty]

[namelist:remove_opt]
remove_this_opt=.true.

[!namelist:remove_ignore_sect_full]
opt_with_content=.true.

[!namelist:remove_ignore_sect_empty]

[namelist:remove_ignore_opt]
!remove_this_ignore_opt=.true.

[!!namelist:remove_trig_ignore_sect_full]
!opt_with_content=.true.

[!!namelist:remove_trig_ignore_sect_empty]

[namelist:remove_trig_ignore_opt]
!!remove_this_trig_ignore_opt=.true.

[namelist:change_opt_if_value]
change_opt_if_true=.true.

[namelist:change_ign_opt_if_value]
!change_opt_if_true=.true.

[namelist:not_change_ign_opt_if_value]
!change_opt_if_true=.true.
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import rose.upgrade


class UpgradeAppletoFig(rose.upgrade.MacroUpgrade):

    """Upgrade from Apple to Fig."""

    BEFORE_TAG = "apple"
    AFTER_TAG = "fig"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["namelist:add_sect", "new_opt"],
                         ".true.", info="good")
        self.add_setting(config, ["namelist:add_sect_only"],
                         info="good")
        self.add_setting(config, ["namelist:add_implied_sect",
                                  "opt_forces_section"], ".true.",
                         info="good")
        self.add_setting(config, ["namelist:add_opt_override",
                                  "opt_override"], ".false.",
                         info="bad")
        self.add_setting(config, ["namelist:add_force_opt_override",
                                  "opt_has_changed"], ".true.",
                         info="good")
        self.enable_setting(config, ["namelist:missing_sect"],
                            info="bad")
        self.enable_setting(config, ["namelist:standard_sect",
                                     "missing_option"],
                            info="bad")
        self.enable_setting(config, ["namelist:enable_sect_enabled"],
                            info="bad")
        self.enable_setting(config, ["namelist:enable_opt_enabled",
                                     "already_enabled"],
                            info="bad")
        self.enable_setting(config, ["namelist:enable_sect_trig_ignored"],
                            info="good")
        self.enable_setting(config, ["namelist:enable_opt_trig_ignored",
                                     "starts_off_trig_ignored"],
                            info="good")
        self.enable_setting(config, ["namelist:enable_sect_ignored"],
                            info="good")
        self.enable_setting(config, ["namelist:enable_opt_ignored",
                                     "already_ignored"],
                            info="good")
        self.ignore_setting(config, ["namelist:missing_sect"],
                            info="bad")
        self.ignore_setting(config, ["namelist:standard_sect",
                                     "missing_option"],
                            info="bad")
        self.ignore_setting(config, ["namelist:ignore_sect_enabled"],
                            info="good")
        self.ignore_setting(config, ["namelist:ignore_opt_enabled",
                                     "starts_off_enabled"],
                            info="good")
        self.ignore_setting(config, ["namelist:ignore_sect_trig_ignored"],
                            info="good")
        self.ignore_setting(config, ["namelist:ignore_opt_trig_ignored",
                                     "starts_off_trig_ignored"],
                            info="good")
        self.ignore_setting(config, ["namelist:ignore_sect_ignored"],
                            info="bad")
        self.ignore_setting(config, ["namelist:ignore_opt_ignored",
                                     "already_ignored"],
                            info="bad")
        self.ignore_setting(config, ["namelist:missing_sect"],
                            state=config.STATE_SYST_IGNORED,
                            info="bad")
        self.ignore_setting(config, ["namelist:standard_sect",
                                     "missing_option"],
                            state=config.STATE_SYST_IGNORED,
                            info="bad")
        self.ignore_setting(config, ["namelist:trig_ignore_sect_enabled"],
                            state=config.STATE_SYST_IGNORED,
                            info="good")
        self.ignore_setting(config, ["namelist:trig_ignore_opt_enabled",
                                     "starts_off_enabled"],
                            state=config.STATE_SYST_IGNORED,
                            info="good")
        self.ignore_setting(config,
                            ["namelist:trig_ignore_sect_trig_ignored"],
                            state=config.STATE_SYST_IGNORED,
                            info="bad")
        self.ignore_setting(config, ["namelist:trig_ignore_opt_trig_ignored",
                                     "starts_off_trig_ignored"],
                            state=config.STATE_SYST_IGNORED,
                            info="bad")
        self.ignore_setting(config, ["namelist:trig_ignore_sect_ignored"],
                            state=config.STATE_SYST_IGNORED,
                            info="good")
        self.ignore_setting(config, ["namelist:trig_ignore_opt_ignored",
                                     "already_ignored"],
                            state=config.STATE_SYST_IGNORED,
                            info="good")
        self.change_setting_value(config, ["namelist:standard_sect",
                                           "missing_opt"], "5",
                                  info="good")
        self.change_setting_value(config, ["namelist:change_opt", 
                                           "opt_has_changed"],
                                  ".true.", info="good")
        self.change_setting_value(config, ["namelist:change_opt", 
                                           "ignore_opt_has_changed"],
                                  ".true.", info="good")
        self.change_setting_value(config, ["namelist:change_opt", 
                                           "trig_ignore_opt_has_changed"],
                                  ".true.", info="good")
        self.remove_setting(config, ["namelist:missing_sect"], info="bad")
        self.remove_setting(config, ["namelist:missing_sect", "missing_opt"],
                            info="bad")
        self.remove_setting(config, ["namelist:standard_sect", "missing_opt"],
                            info="bad")
        self.remove_setting(config, ["namelist:remove_sect_empty"],
                            info="good")
        self.remove_setting(config, ["namelist:remove_sect_full"],
                            info="good")
        self.remove_setting(config, ["namelist:remove_opt",
                                     "remove_this_opt"],
                            info="good")
        self.remove_setting(config, ["namelist:remove_ignore_sect_empty"],
                            info="good")
        self.remove_setting(config, ["namelist:remove_ignore_sect_full"],
                            info="good")
        self.remove_setting(config, ["namelist:remove_ignore_opt",
                                     "remove_this_ignore_opt"],
                            info="good")
        self.remove_setting(config,
                            ["namelist:remove_trig_ignore_sect_empty"],
                            info="good")
        self.remove_setting(config,
                            ["namelist:remove_trig_ignore_sect_full"],
                            info="good")
        self.remove_setting(config,
                            ["namelist:remove_trig_ignore_opt",
                             "remove_this_trig_ignore_opt"],
                            info="good")
        if self.get_setting_value(config,
                                  ["namelist:change_opt_if_value",
                                   "change_opt_if_true"]) == ".true.":
            self.change_setting_value(
                        config, ["namelist:change_opt_if_value",
                                 "change_opt_if_true"], ".false.",
                        info="good")
        if self.get_setting_value(config,
                                  ["namelist:change_ign_opt_if_value",
                                   "change_opt_if_true"],
                                  no_ignore=False) == ".true.":
            self.change_setting_value(
                        config, ["namelist:change_ign_opt_if_value",
                                 "change_opt_if_true"], ".false.",
                        info="good")
        if self.get_setting_value(config,
                                  ["namelist:not_change_ign_opt_if_value",
                                   "change_opt_if_true"],
                                  no_ignore=True) == ".true.":
            self.change_setting_value(
                        config, ["namelist:not_change_ign_opt_if_value",
                                 "change_opt_if_true"], ".false.",
                        info="bad")
        return config, self.reports
__MACRO__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-info
# Check a complex upgrade with info messages.
# meta-test: no 'bad' allowed, must match above number of 'good'.
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config fig
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgradeapple-fig: changes: 33
    namelist:add_sect=new_opt=.true.
        good
    namelist:add_sect_only=None=None
        good
    namelist:add_implied_sect=None=None
        Added
    namelist:add_implied_sect=opt_forces_section=.true.
        good
    namelist:enable_sect_trig_ignored=None=None
        good
    namelist:enable_opt_trig_ignored=starts_off_trig_ignored=.true.
        good
    namelist:enable_sect_ignored=None=None
        good
    namelist:ignore_sect_enabled=None=None
        good
    namelist:ignore_opt_enabled=starts_off_enabled=.true.
        good
    namelist:ignore_sect_trig_ignored=None=None
        good
    namelist:ignore_opt_trig_ignored=starts_off_trig_ignored=.true.
        good
    namelist:trig_ignore_sect_enabled=None=None
        good
    namelist:trig_ignore_opt_enabled=starts_off_enabled=.true.
        good
    namelist:trig_ignore_sect_ignored=None=None
        good
    namelist:trig_ignore_opt_ignored=already_ignored=.true.
        good
    namelist:change_opt=opt_has_changed=.true.
        good
    namelist:change_opt=ignore_opt_has_changed=.true.
        good
    namelist:change_opt=trig_ignore_opt_has_changed=.true.
        good
    namelist:remove_sect_empty=None=None
        good
    namelist:remove_sect_full=opt_with_content=None
        good
    namelist:remove_sect_full=None=None
        good
    namelist:remove_opt=remove_this_opt=None
        good
    namelist:remove_ignore_sect_empty=None=None
        good
    namelist:remove_ignore_sect_full=opt_with_content=None
        good
    namelist:remove_ignore_sect_full=None=None
        good
    namelist:remove_ignore_opt=remove_this_ignore_opt=None
        good
    namelist:remove_trig_ignore_sect_empty=None=None
        good
    namelist:remove_trig_ignore_sect_full=opt_with_content=None
        good
    namelist:remove_trig_ignore_sect_full=None=None
        good
    namelist:remove_trig_ignore_opt=remove_this_trig_ignore_opt=None
        good
    namelist:change_opt_if_value=change_opt_if_true=.false.
        good
    namelist:change_ign_opt_if_value=change_opt_if_true=.false.
        good
    =meta=test-app-upgrade/fig
        Upgraded from apple to fig
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/fig

[namelist:add_force_opt_override]
opt_has_changed=.false.

[namelist:add_implied_sect]
opt_forces_section=.true.

[namelist:add_opt_override]
opt_override=.true.

[namelist:add_sect]
new_opt=.true.

[namelist:add_sect_only]

[namelist:change_ign_opt_if_value]
!change_opt_if_true=.false.

[namelist:change_opt]
!ignore_opt_has_changed=.true.
opt_has_changed=.true.
!!trig_ignore_opt_has_changed=.true.

[namelist:change_opt_if_value]
change_opt_if_true=.false.

[namelist:enable_opt_enabled]
already_enabled=.true.

[namelist:enable_opt_ignored]
!starts_off_ignored=.true.

[namelist:enable_opt_trig_ignored]
starts_off_trig_ignored=.true.

[namelist:enable_sect_enabled]

[namelist:enable_sect_ignored]

[namelist:enable_sect_trig_ignored]

[namelist:ignore_opt_enabled]
!starts_off_enabled=.true.

[namelist:ignore_opt_ignored]
!already_ignored=.true.

[namelist:ignore_opt_trig_ignored]
!starts_off_trig_ignored=.true.

[!namelist:ignore_sect_enabled]

[!namelist:ignore_sect_ignored]

[!namelist:ignore_sect_trig_ignored]

[namelist:not_change_ign_opt_if_value]
!change_opt_if_true=.true.

[namelist:remove_ignore_opt]

[namelist:remove_opt]

[namelist:remove_trig_ignore_opt]

[namelist:standard_sect]
standard_opt=.true.

[namelist:trig_ignore_opt_enabled]
!!starts_off_enabled=.true.

[namelist:trig_ignore_opt_ignored]
!!already_ignored=.true.

[namelist:trig_ignore_opt_trig_ignored]
!!starts_off_trig_ignored=.true.

[!!namelist:trig_ignore_sect_enabled]

[!!namelist:trig_ignore_sect_ignored]

[!!namelist:trig_ignore_sect_trig_ignored]
__CONFIG__
teardown
