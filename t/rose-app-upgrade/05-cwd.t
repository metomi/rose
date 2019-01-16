#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# Test "rose app-upgrade" for complex macros.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3

#-------------------------------------------------------------------------------
# Check current working directory is app directory while upgrading
init <<'__CONFIG__'
meta=test-app-upgrade/apple
__CONFIG__
setup
init_meta test-app-upgrade apple fig
init_macro test-app-upgrade < $TEST_SOURCE_DIR/lib/versions_cwd.py
#-----------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-upgrade
# Check a complex upgrade
CONFIG_DIR=$(cd ../config && pwd -P)
run_pass "$TEST_KEY" rose app-upgrade --non-interactive \
 --meta-path=../rose-meta/ -C ../config fig
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUTPUT__
[U] Upgrade_apple-fig: changes: 2
    namelist:add_sect_only=None=None
        Added
    =meta=test-app-upgrade/fig
        Upgraded from apple to fig
Current directory: $CONFIG_DIR
__OUTPUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
