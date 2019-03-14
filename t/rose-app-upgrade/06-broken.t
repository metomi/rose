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
# Test "rose app-upgrade" for broken macros.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 11

#-------------------------------------------------------------------------------
# Check complex upgrading
init <<'__CONFIG__'
meta=test-app-upgrade/HEAD

__CONFIG__
setup
init_meta test-app-upgrade apple fig HEAD
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class UpgradeWhatevertoOtherWhatever(rose.upgrade.MacroUpgrade):

    """Upgrade from Whatever to Other Whatever."""

    BEFORE_TAG = "whatever"
    AFTER_TAG = "other whatever"

    def upgrade(self, config, meta_config=None):
        return config, self.reports


class UpgradeDunnoToOtherDunno(rose.upgrade.MacroUpgrade):

    """Upgrade from Dunno to Other Dunno."""

    BEFORE_TAG = "dunno"
    AFTER_TAG = "other dunno"

    def upgrade(self, config, meta_config=None):
        return config, self.reports
__MACRO__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-HEAD
# Check a broken upgrade pathway from HEAD
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= HEAD
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-random
# Check a broken upgrade pathway from an arbitrary made-up version.
init <<'__CONFIG__'
meta=test-app-upgrade/not-sure
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= not-sure
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-after-tag
# Check a broken upgrade pathway from an arbitrary made-up version.
init <<'__CONFIG__'
meta=test-app-upgrade/other whatever
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= other whatever
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-----------------------------------------------------------------------------
# Check that an error is reported if there is a broken import in versions.py
TEST_KEY=$TEST_KEY_BASE-broken-import
# Overwrite versions.py with something with a broken import
rm "../rose-meta/test-app-upgrade/versions.pyc"
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3

import rose.upgrade
import some_broken_import
__MACRO__

run_fail "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_grep "$TEST_KEY.out.grep" "ModuleNotFoundError" "$TEST_KEY.err"
teardown
