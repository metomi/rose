#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
#-------------------------------------------------------------------------------
# Test trigger fixing for "rose app-upgrade".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 12

#-------------------------------------------------------------------------------
# Check basic upgrading.
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade 0.1 0.2
init_meta_content test-app-upgrade 0.2 <<'__META__'
[env=A]
trigger=env=Z: 3

[env=Z]
__META__
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade01to02(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.1 to 0.2."""

    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "Z"], "1",
                         info="only one Z")
        return config, self.reports
__MACRO__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-check-version
# Check correct start version
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.1
* 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-add-and-trigger-non-interactive
# Check adding
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade_0.1-0.2: changes: 2
    env=Z=1
        only one Z
    =meta=test-app-upgrade/0.2
        Upgraded from 0.1 to 0.2
[T] UpgradeTriggerFixing: changes: 1
    env=Z=1
        enabled      -> trig-ignored
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.2

[env]
A=4
!!Z=1
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-add-and-trigger
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
# Check adding
run_pass "$TEST_KEY" rose app-upgrade \
 --meta-path=../rose-meta/ -C ../config 0.2 <<'__INPUT__'
y
y
__INPUT__
file_grep "$TEST_KEY.out.grep1" "Upgrade_0.1-0.2: changes: 2" "$TEST_KEY.out"
file_grep "$TEST_KEY.out.grep2" "UpgradeTriggerFixing: changes: 1" \
    "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.2

[env]
A=4
!!Z=1
__CONFIG__
teardown
exit
