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
# Test "rose app-upgrade" for real macros.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 57

#-------------------------------------------------------------------------------
# Check basic upgrading.
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
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


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        self.ignore_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade03to04(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.3 to 0.4."""

    BEFORE_TAG = "0.3"
    AFTER_TAG = "0.4"

    def upgrade(self, config, meta_config=None):
        self.enable_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade04to05(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4 to 0.5."""

    BEFORE_TAG = "0.4"
    AFTER_TAG = "0.5"

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade05to10(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.5 to 1.0."""
    
    BEFORE_TAG = "0.5"
    AFTER_TAG = "1.0"
    
    def upgrade(self, config, meta_config=None):
        self.change_setting_value(config, ["env", "Z"], "5")
        return config, self.reports
__MACRO__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-add-start-version
# Check correct start version
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.1
  0.2
  0.3
  0.4
  0.5
* 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-add
# Check adding
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.1-0.2: changes: 2
    env=Z=1
        only one Z
    =meta=test-app-upgrade/0.2
        Upgraded from 0.1 to 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.2

[env]
A=4
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-add-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.2
  0.3
  0.4
  0.5
* 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the upgrade
TEST_KEY=$TEST_KEY_BASE-upgrade-ignore
init <<'__CONFIG__'
meta=test-app-upgrade/0.2

[env]
A=4
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.3
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.2-0.3: changes: 2
    env=A=4
        enabled -> user-ignored
    =meta=test-app-upgrade/0.3
        Upgraded from 0.2 to 0.3
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.3

[env]
!A=4
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-ignore-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.3
  0.4
  0.5
* 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the upgrade
TEST_KEY=$TEST_KEY_BASE-upgrade-enable
init <<'__CONFIG__'
meta=test-app-upgrade/0.3

[env]
!A=4
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.4
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.3-0.4: changes: 2
    env=A=4
        user-ignored -> enabled
    =meta=test-app-upgrade/0.4
        Upgraded from 0.3 to 0.4
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.4

[env]
A=4
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-enable-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.4
  0.5
* 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the upgrade
TEST_KEY=$TEST_KEY_BASE-upgrade-remove
init <<'__CONFIG__'
meta=test-app-upgrade/0.4

[env]
A=4
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.5
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.4-0.5: changes: 2
    env=A=None
        Removed
    =meta=test-app-upgrade/0.5
        Upgraded from 0.4 to 0.5
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.5

[env]
Z=1
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-remove-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 0.5
* 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
# Check the next step in the upgrade
TEST_KEY=$TEST_KEY_BASE-upgrade-change
init <<'__CONFIG__'
meta=test-app-upgrade/0.5

[env]
Z=1
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 1.0
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.5-1.0: changes: 2
    env=Z=5
        Value: '1' -> '5'
    =meta=test-app-upgrade/1.0
        Upgraded from 0.5 to 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/1.0

[env]
Z=5
__CONFIG__

#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade-change-end-version
# Check correct end version
run_pass "$TEST_KEY" rose app-upgrade \
 --meta-path=../rose-meta/ -C ../config/
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
= 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-----------------------------------------------------------------------------
# Upgrade across versions
TEST_KEY=$TEST_KEY_BASE-upgrade-multiple
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 1.0
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.1-1.0: changes: 6
    env=Z=1
        only one Z
    env=A=4
        enabled -> user-ignored
    env=A=4
        user-ignored -> enabled
    env=A=None
        Removed
    env=Z=5
        Value: '1' -> '5'
    =meta=test-app-upgrade/1.0
        Upgraded from 0.1 to 1.0
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/1.0

[env]
Z=5
__CONFIG__

#-------------------------------------------------------------------------------
# Check broken chain upgrading.
TEST_KEY=$TEST_KEY_BASE-upgrade-broken-chain
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
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

run_fail "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.5
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
0.5: invalid version.
__ERROR__
teardown

#-------------------------------------------------------------------------------
# Check broken chain upgrading.
TEST_KEY=$TEST_KEY_BASE-upgrade-broken-chain-before-break
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
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


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        self.ignore_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade04to05(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4 to 0.5."""

    BEFORE_TAG = "0.4"
    AFTER_TAG = "0.5"

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "A"])
        return config, self.reports
__MACRO__

run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.3
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.1-0.3: changes: 3
    env=Z=1
        only one Z
    env=A=4
        enabled -> user-ignored
    =meta=test-app-upgrade/0.3
        Upgraded from 0.1 to 0.3
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.3

[env]
!A=4
Z=1
__CONFIG__
teardown
#-------------------------------------------------------------------------------
# Check broken chain upgrading.
TEST_KEY=$TEST_KEY_BASE-upgrade-broken-chain-after-break
init <<'__CONFIG__'
meta=test-app-upgrade/0.4

[env]
!A=4
B=2
Z=1
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
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


class Upgrade02to03(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.2 to 0.3."""

    BEFORE_TAG = "0.2"
    AFTER_TAG = "0.3"

    def upgrade(self, config, meta_config=None):
        self.ignore_setting(config, ["env", "A"])
        return config, self.reports


class Upgrade04to05(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.4 to 0.5."""

    BEFORE_TAG = "0.4"
    AFTER_TAG = "0.5"

    def upgrade(self, config, meta_config=None):
        self.remove_setting(config, ["env", "A"])
        return config, self.reports
__MACRO__

run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.5
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.4-0.5: changes: 2
    env=A=None
        Removed
    =meta=test-app-upgrade/0.5
        Upgraded from 0.4 to 0.5
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.5

[env]
B=2
Z=1
__CONFIG__
teardown
#-------------------------------------------------------------------------------
# Check file-based upgrading.
TEST_KEY=$TEST_KEY_BASE-upgrade-patch-files
init <<'__CONFIG__'
meta=test-app-upgrade/0.1

[env]
A=4

[namelist:qwerty]
uiop=asdf

[namelist:something]
foo=bar
__CONFIG__
setup
init_meta test-app-upgrade
init_macro test-app-upgrade <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import rose.upgrade


class Upgrade01to02(rose.upgrade.MacroUpgrade):

    """Upgrade from 0.1 to 0.2."""

    BEFORE_TAG = "0.1"
    AFTER_TAG = "0.2"

    def upgrade(self, config, meta_config=None):
        self.act_from_files(config)
        return config, self.reports
__MACRO__

init_resource_file test-app-upgrade 0.1 rose-macro-add.conf <<'__CONFIG__'
[env]
B=5

[namelist:new]
spam=eggs
__CONFIG__
init_resource_file test-app-upgrade 0.1 rose-macro-remove.conf <<'__CONFIG__'
[env]
A=5

[namelist:qwerty]

[namelist:something]
foo=bar
__CONFIG__

run_pass "$TEST_KEY" rose app-upgrade -y \
 --meta-path=../rose-meta/ -C ../config/ 0.2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade0.1-0.2: changes: 8
    env=B=5
        Added with value '5'
    namelist:new=None=None
        Added
    namelist:new=spam=eggs
        Added with value 'eggs'
    env=A=None
        Removed
    namelist:something=foo=None
        Removed
    namelist:qwerty=uiop=None
        Removed
    namelist:qwerty=None=None
        Removed
    =meta=test-app-upgrade/0.2
        Upgraded from 0.1 to 0.2
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=test-app-upgrade/0.2

[env]
B=5

[namelist:new]
spam=eggs

[namelist:something]
__CONFIG__
teardown
#-------------------------------------------------------------------------------
exit
