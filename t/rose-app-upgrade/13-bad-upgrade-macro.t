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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# Test "rose app-upgrade" for upgrade macro.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3
#------------------------------------------------------------------------------
# Check bad upgrade macro comments.
TEST_KEY=$TEST_KEY_BASE-bad-upgrade-uppercase
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[namelist:characters]
hans_solo=1
luke_skywalker=1
__CONFIG__

setup
init_meta test-app-upgrade 0.1 0.2
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rose.upgrade


class Upgrade01to02(rose.upgrade.MacroUpgrade):
    
    """Test class to upgrade the macro with a bad change and fail on save."""
    
    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def upgrade(self, config, meta_config=None):
        """Perform the upgrade that will fail because of uppercase."""
        self.reports = []
        self.add_setting(config, ["namelist:characters", "Chewie"], "1")
        return config, self.reports
__MACRO__

run_pass "$TEST_KEY" rose app-upgrade -y \
--meta-path=../rose-meta/ -C ../config/ 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade_0.1-0.2: changes: 2
    namelist:characters=Chewie=1
        Added with value '1'
    =meta=test-app-upgrade/0.2
        Upgraded from 0.1 to 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] Error: case mismatch; 
[FAIL]  Chewie does not match chewie, please only use lowercase.
[FAIL] 
__ERROR__

teardown
#-------------------------------------------------------------------------------
exit
