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
# Test "rose app-upgrade" for real macros.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
# Check upgrading with optional configurations.
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
init_opt foo<<'__CONFIG__'
[env]
A=1
D=2
__CONFIG__
setup
init_meta test-app-upgrade 0.1 0.2
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
        if config.get(["env", "D"]) is not None:
            self.change_setting_value(
                config, ["env", "D"], "56")
        self.remove_setting(config, ["env", "A"])
        return config, self.reports
__MACRO__
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-add
# Check adding
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade_0.1-0.2: changes: 5
    env=Z=1
        only one Z
    env=A=4
        Removed
    =meta=test-app-upgrade/0.2
        Upgraded from 0.1 to 0.2
    (opts=foo)env=D=56
        Value: '2' -> '56'
    (opts=foo)env=A=1
        Removed
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.2

[env]
Z=1
__CONFIG__
file_cmp "$TEST_KEY.opt-config" ../config/opt/rose-app-foo.conf <<'__CONFIG__'
[env]
D=56
__CONFIG__
teardown
#-------------------------------------------------------------------------------
exit
