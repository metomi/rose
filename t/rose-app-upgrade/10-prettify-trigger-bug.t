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
# Test "rose app-upgrade" triggering when a value can be prettified post-upgrade.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
init <<'__CONFIG__'
meta=tulip/red

[namelist:flower_props]
completeness_bonus=12
has_petals_and_sepals=6*.true.
__CONFIG__
setup
init_meta tulip red blue
init_meta_content tulip red <<'__META__'
[namelist:flower_props=completeness_bonus]
type=integer

[namelist:flower_props=has_petals_and_sepals]
length=:
trigger=namelist:flower_props=completeness_bonus: all(this == '.true.');
type=logical
__META__
init_meta_content tulip blue <<'__META__'
[namelist:flower_props=completeness_bonus]
type=integer

[namelist:flower_props=has_petals_and_sepals]
length=:
trigger=namelist:flower_props=completeness_bonus: all(this == '.true.');
type=logical
__META__
init_macro tulip <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rose.upgrade

class UpgradeTulipToBlue(rose.upgrade.MacroUpgrade):

    """Blue tulips are prettier (?)."""

    BEFORE_TAG="red"
    AFTER_TAG="blue"

    def upgrade(self, config, meta_config=None):
        """Don't do anything..."""
        return config, self.reports
__MACRO__
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config blue
# We don't want any spurious triggering from '6*.true.' being used literally.
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade_red-blue: changes: 1
    =meta=tulip/blue
        Upgraded from red to blue
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=tulip/blue

[namelist:flower_props]
completeness_bonus=12
has_petals_and_sepals=6*.true.
__CONFIG__
#-----------------------------------------------------------------------------
teardown
