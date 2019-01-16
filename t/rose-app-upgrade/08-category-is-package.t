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
# Test "rose app-upgrade" when the versions.py file is in a package.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
init <<'__CONFIG__'
meta=defence/blaster
__CONFIG__
setup
init_meta defence blaster lightsaber HEAD
init_macro defence <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from jedi import *
__MACRO__
cat >$TEST_DIR/rose-meta/$category/jedi.py <<'__MACRO__'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rose.upgrade


class UpgradeAddLightSaber(rose.upgrade.MacroUpgrade):

    """'An elegant weapon, for a more civilized age.'

    (Star Wars: A New Hope)

    """

    BEFORE_TAG = "blaster"
    AFTER_TAG = "lightsaber"

    def upgrade(self, config, meta_config=None):
        self.add_setting(config, ['env', 'COLOUR'], 'blue')
        return config, self.reports
__MACRO__
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-simple
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config lightsaber
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUTPUT__'
[U] Upgrade_blaster-lightsaber: changes: 3
    env=None=None
        Added
    env=COLOUR=blue
        Added with value 'blue'
    =meta=defence/lightsaber
        Upgraded from blaster to lightsaber
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.file" ../config/rose-app.conf <<'__CONFIG__'
meta=defence/lightsaber

[env]
COLOUR=blue
__CONFIG__
#-----------------------------------------------------------------------------
teardown
