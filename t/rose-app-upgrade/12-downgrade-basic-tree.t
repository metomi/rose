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
# Test "rose app-upgrade --downgrade" for real macros.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 63

#-------------------------------------------------------------------------------
# Check basic downgrading.
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/1.0

[env]
Z=5
__CONFIG__
setup
init_meta test_tree/test-app-upgrade 0.1 0.2 0.3 0.4 0.5
init_macro test_tree/test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade01to02(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.1 to 0.2."""

    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def downgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "Z"],
                            info="removed Z")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "Z"], "1",
                         info="only one Z")
        return config, self.reports


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def downgrade(self, config, meta_config=None):
        self.enable_setting(config, ["env", "A"])
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.ignore_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade03to04(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.3 to 0.4."""

    BEFORE_TAG = "0.3"
    AFTER_TAG = "0.4"

    def downgrade(self, config, meta_config=None):
        self.ignore_setting(config, ["env", "A"])
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.enable_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade04to041(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4 to 0.4.1."""

    BEFORE_TAG = "0.4"
    AFTER_TAG = "0.4.1"

    def downgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "A"], "4")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade041to10(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4.1 to 1.0."""

    BEFORE_TAG = "0.4.1"
    AFTER_TAG = "1.0"

    def downgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "Z"], "1")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "Z"], "5")
        return config, self.reports
__MACRO__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-change-start-version
# Check correct start version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
  0.2
  0.3
  0.4
= 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-change-start-version-all
# Check correct start version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --meta-path=../rose-meta/ -C ../config --all-versions
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
  0.2
  0.3
  0.4
  0.4.1
= 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-change
# Check changing within a downgrade
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --non-interactive --meta-path=../rose-meta/ -C ../config -a 0.4.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_1.0-0.4.1: changes: 2
    env=Z=1
        Value: '5' -> '1'
    =meta=test_tree/test-app-upgrade/0.4.1
        Downgraded from 1.0 to 0.4.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.4.1

[env]
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-change-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --non-interactive --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
  0.2
  0.3
  0.4
= 0.4.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the downgrade
TEST_KEY=$TEST_KEY_BASE-downgrade-add
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.4.1

[env]
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.4
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.4.1-0.4: changes: 2
    env=A=4
        Added with value '4'
    =meta=test_tree/test-app-upgrade/0.4
        Downgraded from 0.4.1 to 0.4
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.4

[env]
A=4
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-add-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
  0.2
  0.3
= 0.4
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the downgrade
TEST_KEY=$TEST_KEY_BASE-downgrade-ignore
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.4

[env]
A=4
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.3
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.4-0.3: changes: 2
    env=A=4
        enabled -> user-ignored
    =meta=test_tree/test-app-upgrade/0.3
        Downgraded from 0.4 to 0.3
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.3

[env]
!A=4
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-ignore-enable-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
  0.2
= 0.3
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the downgrade
TEST_KEY=$TEST_KEY_BASE-downgrade-enable
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.3

[env]
!A=4
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.3-0.2: changes: 2
    env=A=4
        user-ignored -> enabled
    =meta=test_tree/test-app-upgrade/0.2
        Downgraded from 0.3 to 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.2

[env]
A=4
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-enable-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
= 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the upgrade
TEST_KEY=$TEST_KEY_BASE-downgrade-remove
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.2

[env]
A=4
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.2-0.1: changes: 2
    env=Z=1
        removed Z
    =meta=test_tree/test-app-upgrade/0.1
        Downgraded from 0.2 to 0.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.1

[env]
A=4
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-downgrade-remove-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-----------------------------------------------------------------------------
# Downgrade across versions
TEST_KEY=$TEST_KEY_BASE-downgrade-multiple
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/1.0

[env]
Z=5
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_1.0-0.1: changes: 6
    env=Z=1
        Value: '5' -> '1'
    env=A=4
        Added with value '4'
    env=A=4
        enabled -> user-ignored
    env=A=4
        user-ignored -> enabled
    env=Z=1
        removed Z
    =meta=test_tree/test-app-upgrade/0.1
        Downgraded from 1.0 to 0.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.1

[env]
A=4
__CONFIG__

#-------------------------------------------------------------------------------
# Check broken chain downgrading.
TEST_KEY=$TEST_KEY_BASE-downgrade-broken-chain
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.5

[env]
A=4
__CONFIG__
setup
init_meta test_tree/test-app-upgrade 0.1 0.2 0.3 0.4 0.5
init_macro test_tree/test-app-upgrade <<'__MACRO__'
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


class Upgrade04to05(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4 to 0.5."""

    BEFORE_TAG = "0.4"
    AFTER_TAG = "0.5"

    def upgrade(self, config, meta_config=None):
        return config, self.reports
__MACRO__

run_fail "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[FAIL] 0.1: invalid version.
__ERROR__
teardown

#-------------------------------------------------------------------------------
# Check broken chain downgrading.
TEST_KEY=$TEST_KEY_BASE-downgrade-broken-chain-before-break
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.3

[env]
!A=4
Z=1
__CONFIG__
setup
init_meta test_tree/test-app-upgrade 0.1 0.2 0.3 0.4 0.5
init_macro test_tree/test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade01to02(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.1 to 0.2."""

    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def downgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "Z"],
                            info="no more Zs")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "Z"], "1",
                         info="only one Z")
        return config, self.reports


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def downgrade(self, config, meta_config=None):
        self.enable_setting(config, ["env", "A"])
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.ignore_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade04to05(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4 to 0.5."""

    BEFORE_TAG = "0.4"
    AFTER_TAG = "0.5"

    def downgrade(self, config, meta_config=None):
        self.add_setting(config, ["env", "A"], "4")
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "A"])
        return config, self.reports
__MACRO__

run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.3-0.1: changes: 3
    env=A=4
        user-ignored -> enabled
    env=Z=1
        no more Zs
    =meta=test_tree/test-app-upgrade/0.1
        Downgraded from 0.3 to 0.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.1

[env]
A=4
__CONFIG__
#-------------------------------------------------------------------------------
# Check broken chain upgrading.
TEST_KEY=$TEST_KEY_BASE-downgrade-broken-chain-after-break
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.5

[env]
B=2
Z=1
__CONFIG__

run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.4
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.5-0.4: changes: 2
    env=A=4
        Added with value '4'
    =meta=test_tree/test-app-upgrade/0.4
        Downgraded from 0.5 to 0.4
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.4

[env]
A=4
B=2
Z=1
__CONFIG__
teardown
#-------------------------------------------------------------------------------
init <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.2

[env]
B=5

[namelist:new]
spam=eggs

[namelist:something]
__CONFIG__
setup
init_meta test_tree/test-app-upgrade 0.1 0.2
init_macro test_tree/test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade01to02(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.1 to 0.2."""

    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def downgrade(self, config, meta_config=None):
        self.act_from_files(config, downgrade=True)
        return config, self.reports

    def upgrade(self, config, meta_config=None):
        self.act_from_files(config)
        return config, self.reports
__MACRO__

init_resource_file test_tree/test-app-upgrade 0.1 rose-macro-add.conf <<'__CONFIG__'
[env]
B=5

[namelist:new]
spam=eggs
__CONFIG__
init_resource_file test_tree/test-app-upgrade 0.1 rose-macro-remove.conf <<'__CONFIG__'
[env]
A=5

[namelist:qwerty]

[namelist:something]
foo=bar
__CONFIG__

#-----------------------------------------------------------------------------
# Check correct start version
TEST_KEY=$TEST_KEY_BASE-downgrade-patch-files-start-version
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
* 0.1
= 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-----------------------------------------------------------------------------
# Check file-based upgrading.
TEST_KEY=$TEST_KEY_BASE-downgrade-patch-files
run_pass "$TEST_KEY" rose app-upgrade --downgrade \
 -y --meta-path=../rose-meta/ -C ../config/ 0.1
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[D] Downgrade_0.2-0.1: changes: 6
    namelist:something=foo=bar
        Added with value 'bar'
    namelist:qwerty=None=None
        Added
    env=A=5
        Added with value '5'
    namelist:new=spam=eggs
        Removed
    env=B=5
        Removed
    =meta=test_tree/test-app-upgrade/0.1
        Downgraded from 0.2 to 0.1
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test_tree/test-app-upgrade/0.1

[env]
A=5

[namelist:new]

[namelist:qwerty]

[namelist:something]
foo=bar
__CONFIG__
teardown
#-------------------------------------------------------------------------------
exit
