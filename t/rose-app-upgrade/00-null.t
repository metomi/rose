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
# Test "rose app-upgrade" in the absence of proper macros
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
rm config/rose-app.conf
#-------------------------------------------------------------------------------
tests 36
#-------------------------------------------------------------------------------
# Normal mode.
TEST_KEY=$TEST_KEY_BASE-base
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[FAIL] $PWD: not an application or suite directory.
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Normal mode, -C.
TEST_KEY=$TEST_KEY_BASE-C
setup
CONFIG_DIR=$(cd .. && pwd -P)/config
run_fail "$TEST_KEY" rose app-upgrade --non-interactive -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__CONTENT__
[FAIL] $CONFIG_DIR: not an application or suite directory.
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown option.
TEST_KEY=$TEST_KEY_BASE-unknown-option
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive --unknown-option -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
Usage: rose app-upgrade [OPTIONS] [VERSION]

rose app-upgrade: error: no such option: --unknown-option
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# No meta flag.
init </dev/null
TEST_KEY=$TEST_KEY_BASE-no-metadata
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown metadata flag, I
init << '__CONFIG__'
meta=unknown-flag
__CONFIG__
init_meta different_flag
TEST_KEY=$TEST_KEY_BASE-unknown-flag-i
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Unknown metadata flag, II
init << '__CONFIG__'
meta=unknown-flag/10.0
__CONFIG__
init_meta different_flag
TEST_KEY=$TEST_KEY_BASE-unknown-flag-ii
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Malformed metadata flag, I
init << '__CONFIG__'
meta=
__CONFIG__
init_meta different_flag
TEST_KEY=$TEST_KEY_BASE-malformed-flag-i
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Malformed metadata flag, II
init << '__CONFIG__'
meta=flag/
 /45/
 flag'456
__CONFIG__
init_meta different_flag
TEST_KEY=$TEST_KEY_BASE-malformed-flag-ii
setup
run_fail "$TEST_KEY" rose app-upgrade --non-interactive -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__CONTENT__'
[FAIL] Error: could not find meta flag
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Check upgrading to a bad version (i).
TEST_KEY=$TEST_KEY_BASE-upgrade-bad-version-i
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade 0.1 0.2 0.3
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        return config, self.reports
__MACRO__
run_fail "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] 0.2: invalid version.
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check upgrading to a bad version.
TEST_KEY=$TEST_KEY_BASE-upgrade-bad-version-ii
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade 0.1 0.2 0.3
init_macro test-app-upgrade << '__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        return config, self.reports
__MACRO__
run_fail "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.3
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] 0.3: invalid version.
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check upgrading to a bad version (iii).
TEST_KEY=$TEST_KEY_BASE-upgrade-bad-version-iii
init <<'__CONFIG__'
meta=test-app-upgrade/0.3

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade 0.1 0.2 0.3
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        return config, self.reports
__MACRO__
run_fail "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.4
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] 0.4: invalid version.
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check upgrading to a bad version (iv).
TEST_KEY=$TEST_KEY_BASE-upgrade-bad-version-iv
init <<'__CONFIG__'
meta=test-app-upgrade/0.3

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade 0.1 0.2 0.3
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade
__MACRO__
run_fail "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] 0.1: invalid version.
__ERROR__
teardown
exit
#-------------------------------------------------------------------------------
# Check upgrading to a bad version (v).
TEST_KEY=$TEST_KEY_BASE-upgrade-bad-version-v
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
# No named metadata version for 0.3.
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
        return config, self.reports


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        return config, self.reports
__MACRO__
run_fail "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.3
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] 0.3: invalid version.
__ERROR__
teardown
exit
