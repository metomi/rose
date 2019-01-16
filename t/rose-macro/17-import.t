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
# Test "rose macro" in built-in duplicate checking mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 12
#-------------------------------------------------------------------------------
# Check basic import works.
TEST_KEY=$TEST_KEY_BASE-basic-runs
setup
init <<'__CONFIG__'
meta=baked-alaska/vn1.0

[env]
ICECREAM_FLAVOUR=vanilla
ICECREAM_TEMPERATURE=-1
MERINGUE_NICENESS=0
SPONGE_DENSITY=0.1
__CONFIG__

# Set up main metadata.
init_rose_meta baked-alaska vn1.0 HEAD
init_rose_meta_content baked-alaska vn1.0 <<'__META_CONFIG__'
import=rose-demo-baked-alaska-icecream/vn1.0 rose-demo-baked-alaska-sponge/vn1.0

[env=MERINGUE_NICENESS]
title=Meringue Niceness (version 1)
range=-20:20
type=integer

[env=ICECREAM_FLAVOUR]
values=vanilla
__META_CONFIG__

# Set up imported metadata (1)
init_rose_meta baked-alaska-icecream vn1.0 HEAD
init_rose_meta_content baked-alaska-icecream vn1.0 <<'__META_CONFIG__'
[env=ICECREAM_TEMPERATURE]
range=-20:0
title=Icecream Temperature (celsius) (version 1)
type=integer

[env=ICECREAM_FLAVOUR]
title=Icecream Flavour
values=chocolate,vanilla,strawberry
__META_CONFIG__

# Set up imported metadata (2)
init_rose_meta baked-alaska-sponge vn1.0 HEAD
init_rose_meta_content baked-alaska-sponge vn1.0 <<'__META_CONFIG__'
[env=SPONGE_DENSITY]
range=0:1
title=Sponge Density (g cm^-3) (version 1)
type=real
__META_CONFIG__

# Check that it runs OK.
run_pass "$TEST_KEY" rose macro -M $TEST_DIR/rose-meta --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-basic-correct-metadata
# Check that it gets the correct metadata.
init <<'__CONFIG__'
meta=baked-alaska/vn1.0

[env]
ICECREAM_FLAVOUR=chocolate
ICECREAM_TEMPERATURE=1
MERINGUE_NICENESS=50
SPONGE_DENSITY=20.0
__CONFIG__
run_fail "$TEST_KEY" rose macro -M $TEST_DIR/rose-meta --config=../config rose.macros.DefaultValidators
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 4
    env=ICECREAM_FLAVOUR=chocolate
        Value chocolate should be vanilla
    env=ICECREAM_TEMPERATURE=1
        Value 1 is not in the range criteria: -20:0
    env=MERINGUE_NICENESS=50
        Value 50 is not in the range criteria: -20:20
    env=SPONGE_DENSITY=20.0
        Value 20.0 is not in the range criteria: 0:1
__ERR__
#-------------------------------------------------------------------------------
# Check that it gets the correct custom macros.
TEST_KEY=$TEST_KEY_BASE-basic-custom-macro-list
init_rose_meta_macro baked-alaska-sponge vn1.0 desoggy.py <<'__MACRO__'
# -*- coding: utf-8 -*-

import rose.macro


class SpongeDeSoggifier(rose.macro.MacroBase):

    """De-soggifies the sponge."""

    SOGGY_FIX_TEXT = "de-soggified"

    def transform(self, config, meta_config=None):
        """Reduce the density of the sponge."""
        sponge_density = config.get_value(["env", "SPONGE_DENSITY"])
        if sponge_density is not None and float(sponge_density) > 0.5:
            # 1 g cm^-3 is pure water, so this is pretty soggy.
            config.set(["env", "SPONGE_DENSITY"], "0.3")
            self.add_report(
                "env", "SPONGE_DENSITY", "0.3", self.SOGGY_FIX_TEXT)
        return config, self.reports
__MACRO__
run_pass "$TEST_KEY" rose macro -M $TEST_DIR/rose-meta --config=../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[T] desoggy.SpongeDeSoggifier
    # De-soggifies the sponge.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Run the custom macro.
TEST_KEY=$TEST_KEY_BASE-basic-custom-macro-run
# Check that it gets the correct metadata.
run_pass "$TEST_KEY" rose macro -y -M $TEST_DIR/rose-meta --config=../config desoggy.SpongeDeSoggifier
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[T] desoggy.SpongeDeSoggifier: changes: 1
    env=SPONGE_DENSITY=0.3
        de-soggified
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit
