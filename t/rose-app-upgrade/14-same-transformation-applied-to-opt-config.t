#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# Test to ensure that the state of parent nodes is not lost during the
# generation of optional configs.
# See https://github.com/metomi/rose/issues/2853
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 4
rsync -vr "$TEST_SOURCE_DIR/$TEST_KEY_BASE/" .
run_pass "${TEST_KEY_BASE}-init" git init '.'; git add '.'; git commit -m '.'
run_pass "${TEST_KEY_BASE}-upgrade" \
  rose app-upgrade \
    -a -y --debug --verbose \
    -M rose-meta/ \
    -C app/example_app/ \
    vn1.0_t999
run_pass "${TEST_KEY_BASE}-diff" git diff

file_cmp "${TEST_KEY_BASE}-kgo" "${TEST_KEY_BASE}-diff.out" <<__HERE__
diff --git a/app/example_app/opt/rose-app-demo.conf b/app/example_app/opt/rose-app-demo.conf
index ec076f4..087a01d 100644
--- a/app/example_app/opt/rose-app-demo.conf
+++ b/app/example_app/opt/rose-app-demo.conf
@@ -1,2 +1,5 @@
+[!!namelist:namelist_2]
+!!new_value=10.0
+
 [namelist:namelist_3]
 existing_value=10.0
diff --git a/app/example_app/rose-app.conf b/app/example_app/rose-app.conf
index 4a4a5c6..7f34d78 100644
--- a/app/example_app/rose-app.conf
+++ b/app/example_app/rose-app.conf
@@ -1,4 +1,4 @@
-meta=example_meta/vn1.0
+meta=example_meta/vn1.0_t999
 
 [command]
 default=true
@@ -7,6 +7,7 @@ default=true
 use_namelist_2=.false.
 
 [!!namelist:namelist_2]
+!!new_value=5.0
 !!other_value=1.0
 
 [namelist:namelist_3]
__HERE__

exit 0
