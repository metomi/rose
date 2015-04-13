#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Test "rose config", basic usage.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 27
#-------------------------------------------------------------------------------
init app 1 <<'__APP__'
[env]
# 1 reverse, 5 forward
GEARBOX_GEARS=6
GEARSTICK_DECORATION=golfball
__APP__
init_meta app 1 <<'__META__'
[env=GEARBOX_GEARS]
description=The number of gears available.
title=Gearbox Gears
trigger=env=GEARSTICK_DECORATION: this > 1;

[env=GEARSTICK_DECORATION]
help=1  3  5
    =|  |  |
    =-------
    =|  |  |
    =2  4  R
__META__
init app 2 <<'__APP__'
[env]
GEARSTICK_DECORATION=golfball

[namelist:locking]
air_locking=.false.
__APP__
init_meta app 2 <<'__META__'
[namelist:locking]
description=Different choices of locking methods, if available.

[namelist:locking=air_locking]
title=Air Locking?
__META__
export ROSE_CONF_PATH=$PWD
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
setup
run_fail "$TEST_KEY" rose config-diff $TEST_DIR/app{1,2}/rose-app.conf
sed -i "/rose-app.conf/d" "$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
@@ -1,12 +1,8 @@
 # description=Environment variable configuration
 [env]
-# description=The number of gears available.
-# title=Gearbox Gears
-# 1 reverse, 5 forward
-GEARBOX_GEARS=6
-# help=1  3  5
-#     =|  |  |
-#     =-------
-#     =|  |  |
-#     =2  4  R
 GEARSTICK_DECORATION=golfball
+
+# description=Different choices of locking methods, if available.
+[namelist:locking]
+# title=Air Locking?
+air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-extra-args
run_fail "$TEST_KEY" rose config-diff $TEST_DIR/app{1,2}/rose-app.conf \
    -- --label=app1 --label=app2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
--- app1
+++ app2
@@ -1,12 +1,8 @@
 # description=Environment variable configuration
 [env]
-# description=The number of gears available.
-# title=Gearbox Gears
-# 1 reverse, 5 forward
-GEARBOX_GEARS=6
-# help=1  3  5
-#     =|  |  |
-#     =-------
-#     =|  |  |
-#     =2  4  R
 GEARSTICK_DECORATION=golfball
+
+# description=Different choices of locking methods, if available.
+[namelist:locking]
+# title=Air Locking?
+air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ignore
run_fail "$TEST_KEY" rose config-diff --ignore=env $TEST_DIR/app{1,2}/rose-app.conf
sed -i "/rose-app.conf/d" "$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
@@ -0,0 +1,4 @@
+# description=Different choices of locking methods, if available.
+[namelist:locking]
+# title=Air Locking?
+air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ignore-shorthand
mkdir conf
cat >conf/rose.conf <<__ROSE_CONF__
[rose-config-diff]
ignore{everything}=GEAR,locking
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD/conf
run_pass "$TEST_KEY" rose config-diff --ignore=everything $TEST_DIR/app{1,2}/rose-app.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-custom-properties
echo >conf/rose.conf
run_fail "$TEST_KEY" rose config-diff --properties=title,description \
    $TEST_DIR/app{1,2}/rose-app.conf
sed -i "/rose-app.conf/d" "$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
@@ -1,7 +1,8 @@
 # description=Environment variable configuration
 [env]
-# description=The number of gears available.
-# title=Gearbox Gears
-# 1 reverse, 5 forward
-GEARBOX_GEARS=6
 GEARSTICK_DECORATION=golfball
+
+# description=Different choices of locking methods, if available.
+[namelist:locking]
+# title=Air Locking?
+air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-custom-properties-config
cat >conf/rose.conf <<__ROSE_CONF__
[rose-config-diff]
properties=title,description
__ROSE_CONF__
run_fail "$TEST_KEY" rose config-diff $TEST_DIR/app{1,2}/rose-app.conf
sed -i "/rose-app.conf/d" "$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
@@ -1,7 +1,8 @@
 # description=Environment variable configuration
 [env]
-# description=The number of gears available.
-# title=Gearbox Gears
-# 1 reverse, 5 forward
-GEARBOX_GEARS=6
 GEARSTICK_DECORATION=golfball
+
+# description=Different choices of locking methods, if available.
+[namelist:locking]
+# title=Air Locking?
+air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-custom-diff-tool
echo >conf/rose.conf
run_pass "$TEST_KEY" rose config-diff --diff-tool='cat -n' \
    $TEST_DIR/app{1,2}/rose-app.conf 
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
     1	# description=Environment variable configuration
     2	[env]
     3	# description=The number of gears available.
     4	# title=Gearbox Gears
     5	# 1 reverse, 5 forward
     6	GEARBOX_GEARS=6
     7	# help=1  3  5
     8	#     =|  |  |
     9	#     =-------
    10	#     =|  |  |
    11	#     =2  4  R
    12	GEARSTICK_DECORATION=golfball
    13	# description=Environment variable configuration
    14	[env]
    15	GEARSTICK_DECORATION=golfball
    16	
    17	# description=Different choices of locking methods, if available.
    18	[namelist:locking]
    19	# title=Air Locking?
    20	air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-custom-diff-tool-config
cat >conf/rose.conf <<__ROSE_CONF__
[external]
diff_tool=cat -n
__ROSE_CONF__
run_pass "$TEST_KEY" rose config-diff $TEST_DIR/app{1,2}/rose-app.conf 
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
     1	# description=Environment variable configuration
     2	[env]
     3	# description=The number of gears available.
     4	# title=Gearbox Gears
     5	# 1 reverse, 5 forward
     6	GEARBOX_GEARS=6
     7	# help=1  3  5
     8	#     =|  |  |
     9	#     =-------
    10	#     =|  |  |
    11	#     =2  4  R
    12	GEARSTICK_DECORATION=golfball
    13	# description=Environment variable configuration
    14	[env]
    15	GEARSTICK_DECORATION=golfball
    16	
    17	# description=Different choices of locking methods, if available.
    18	[namelist:locking]
    19	# title=Air Locking?
    20	air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-custom-diff-tool-config-graphical
cat >conf/rose.conf <<__ROSE_CONF__
[external]
gdiff_tool=diff -y
__ROSE_CONF__
run_fail "$TEST_KEY" rose config-diff -g $TEST_DIR/app{1,2}/rose-app.conf
# Note: two column layout assumes 8 space tabs.
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__DIFF__'
# description=Environment variable configuration		# description=Environment variable configuration
[env]								[env]
# description=The number of gears available.		      <
# title=Gearbox Gears					      <
# 1 reverse, 5 forward					      <
GEARBOX_GEARS=6						      <
# help=1  3  5						      <
#     =|  |  |						      <
#     =-------						      <
#     =|  |  |						      <
#     =2  4  R						      <
GEARSTICK_DECORATION=golfball					GEARSTICK_DECORATION=golfball
							      >
							      >	# description=Different choices of locking methods, if availa
							      >	[namelist:locking]
							      >	# title=Air Locking?
							      >	air_locking=.false.
__DIFF__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit 0
