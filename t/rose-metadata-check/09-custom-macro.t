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
# Test "rose metadata-check".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 18
#-------------------------------------------------------------------------------
# Check macro reference checking.
TEST_KEY=$TEST_KEY_BASE-import-simple-ok
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.LogicalTransformer
__META_CONFIG__
init_macro envswitch.py < $TEST_SOURCE_DIR/lib/custom_macro.py
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check macro syntax checking.
TEST_KEY=$TEST_KEY_BASE-import-method-ok
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.LogicalTransformer.transform
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check macro syntax checking.
TEST_KEY=$TEST_KEY_BASE-import-multiple-ok
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.LogicalTransformer, envswitch.LogicalTruthChecker
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check macro syntax checking.
TEST_KEY=$TEST_KEY_BASE-import-multiple-method-ok
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.LogicalTransformer.transform, envswitch.LogicalTruthChecker.validate
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check macro reference checking (fail).
TEST_KEY=$TEST_KEY_BASE-import-fail
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.something.LogicalTransformer

[namelist:macro_nl=my_macro_var2]
macro=LogicalTransformer

[namelist:macro_nl=my_macro_var3]
macro=missing.MissingMacro

[namelist:macro_nl=my_macro_var4]
macro=LogicalTransformer.validate, envswitch.LogicalTransformer.validate

[namelist:macro_nl=my_macro_var5]
macro=envswitch.LogicalTruthChecker.transform
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 5
    namelist:macro_nl=my_macro_var1=macro=envswitch.something.LogicalTransformer
        Not found: envswitch.something.LogicalTransformer
    namelist:macro_nl=my_macro_var2=macro=LogicalTransformer
        Not found: LogicalTransformer
    namelist:macro_nl=my_macro_var3=macro=missing.MissingMacro
        Not found: missing.MissingMacro
    namelist:macro_nl=my_macro_var4=macro=LogicalTransformer.validate, envswitch.LogicalTransformer.validate
        Not found: LogicalTransformer.validate
    namelist:macro_nl=my_macro_var5=macro=envswitch.LogicalTruthChecker.transform
        Not found: transform
__ERROR__
teardown
#-------------------------------------------------------------------------------
# Check bad macro imports (reverse some code in macro to make it fail).
TEST_KEY=$TEST_KEY_BASE-import-fail
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.LogicalTransformer
__META_CONFIG__
init_macro envswitch.py < $TEST_SOURCE_DIR/lib/custom_macro_corrupt.py
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERROR__'
[V] rose.metadata_check.MetadataChecker: issues: 1
    namelist:macro_nl=my_macro_var1=macro=envswitch.LogicalTransformer
        Could not import envswitch.LogicalTransformer: IndentationError: expected an indented block (envswitch.py, line 37)
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
