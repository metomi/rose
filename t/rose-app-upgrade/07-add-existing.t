#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# Test "rose app-upgrade" when trying to add existing options.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
init <<'__CONFIG__'
meta=park/no-dinosaurs

[env]
DINOSAURS(1)=velociraptor
SOFTWARE_QA=bad

[food(1)]
humans=4
__CONFIG__
setup
init_meta park no-dinosaurs dinosaurs HEAD
init_macro park <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import rose.upgrade


class UpgradeAddDinosaurs(rose.upgrade.MacroUpgrade):

    """Install dinosaurs in our super-secure facility."""

    BEFORE_TAG = "no-dinosaurs"
    AFTER_TAG = "dinosaurs"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ['env', 'DINOSAURS'], 'compy,t-rex')
        self.add_setting(config, ['env', 'FENCES'], 'electric,electric')
        self.add_setting(config, ['env', 'SOFTWARE_QA'], 'ok')
        self.add_setting(config, ['food(1)'])
        return config, self.reports
__MACRO__
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-simple
# Check a broken upgrade pathway from an arbitrary made-up version.
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config dinosaurs
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade_no-dinosaurs-dinosaurs: changes: 2
    env=FENCES=electric,electric
        Added with value 'electric,electric'
    =meta=park/dinosaurs
        Upgraded from no-dinosaurs to dinosaurs
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=park/dinosaurs

[env]
DINOSAURS(1)=velociraptor
FENCES=electric,electric
SOFTWARE_QA=bad

[food(1)]
humans=4
__CONFIG__
#-----------------------------------------------------------------------------
teardown
