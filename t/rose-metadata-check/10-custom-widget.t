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
# Test "rose metadata-check".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 15
#-------------------------------------------------------------------------------
# Check widget reference checking.
TEST_KEY=$TEST_KEY_BASE-simple-ok
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spin.SpinnerValueWidget
__META_CONFIG__
init_widget spin.py < $(dirname $0)/lib/custom_widget.py
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check widget reference checking with arguments.
TEST_KEY=$TEST_KEY_BASE-args-ok
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spin.SpinnerValueWidget something1 something2
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check widget reference checking with arguments.
TEST_KEY=$TEST_KEY_BASE-import-builtin-ok
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=rose.config_editor.valuewidget.intspin.IntSpinButtonValueWidget
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check widget not found checking.
TEST_KEY=$TEST_KEY_BASE-import-find-fail
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spinner.SpinnerValueWidget

[namelist:widget_nl=my_widget_var2]
widget[rose-config-edit]=spin.SpinnerSpinValueWidget
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 2
    namelist:widget_nl=my_widget_var1=widget[rose-config-edit]=spinner.SpinnerValueWidget
        Not found: spinner.SpinnerValueWidget
    namelist:widget_nl=my_widget_var2=widget[rose-config-edit]=spin.SpinnerSpinValueWidget
        Not found: spin.SpinnerSpinValueWidget
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check widget broken Python code checking.
TEST_KEY=$TEST_KEY_BASE-import-code-fail
setup
init <<__META_CONFIG__
[namelist:widget_nl=my_widget_var1]
widget[rose-config-edit]=spin.SpinnerValueWidget
__META_CONFIG__
init_widget spin.py < $(dirname $0)/lib/custom_widget_corrupt.py
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:widget_nl=my_widget_var1=widget[rose-config-edit]=spin.SpinnerValueWidget
        Could not import spin.SpinnerValueWidget: SyntaxError: invalid syntax (spin.py, line 28)
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
