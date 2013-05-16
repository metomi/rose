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
tests 18
#-------------------------------------------------------------------------------
# Check macro reference checking.
TEST_KEY=$TEST_KEY_BASE-import-simple-ok
setup
init <<__META_CONFIG__
[namelist:macro_nl=my_macro_var1]
macro=envswitch.LogicalTransformer
__META_CONFIG__
init_macro envswitch.py <<__MACRO__
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------

import rose.macro


class LogicalTransformer(rose.macro.MacroBase):

    """Test class to change the value of a boolean environment variable."""

    WARNING_CHANGED_VALUE = "{0} -> {1}"

    def transform(self, config, meta_config=None):
        """Perform the transform operation on the env switch."""
        self.reports = []
        if config.get(["env", "TRANSFORM_SWITCH"]) is not None:
            value = config.get(["env", "TRANSFORM_SWITCH"]).value
            if value == rose.TYPE_BOOLEAN_VALUE_FALSE:
                new_value = rose.TYPE_BOOLEAN_VALUE_TRUE
            else:
                new_value = rose.TYPE_BOOLEAN_VALUE_FALSE
            config.set(["env", "TRANSFORM_SWITCH"], new_value)
            info = self.WARNING_CHANGED_VALUE.format(value, new_value)
            self.add_report("env", "TRANSFORM_SWITCH", value, info)
        return config, self.reports


class LogicalTruthChecker(rose.macro.MacroBase):

    """Test class to check the value of a boolean environment variable."""

    ERROR_NOT_TRUE = "Should be true: {0}"

    def validate(self, config, meta_config=None):
        """Check the env switch."""
        self.reports = []
        node = config.get(["env", "TRANSFORM_SWITCH"], no_ignore=True)
        if node is not None and node.value != rose.TYPE_BOOLEAN_VALUE_FALSE:
            info = self.ERROR_NOT_TRUE.format(node.value)
            self.add_report("env", "TRANSFORM_SWITCH", value, info)
        return self.reports
__MACRO__
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
        Invalid method: envswitch.LogicalTruthChecker.transform
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
init_macro envswitch.py << '__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------

import rose.macro


class LogicalTransformer(rose.macro.MacroBase):

    """Test class to change the value of a boolean environment variable."""

    WARNING_CHANGED_VALUE = "{0} -> {1}"

    def transform(self, config, meta_config=None):
        """Perform the transform operation on the env switch."""
        self.reports = []
        if config.get(["env", "TRANSFORM_SWITCH"]) is not None:
            value = config.get(["env", "TRANSFORM_SWITCH"]).value
            if value == rose.TYPE_BOOLEAN_VALUE_FALSE:
        node = config.get(["env", "TRANSFORM_SWITCH"], no_ignore=True)
        self.reports = []
        """Check the env switch."""
    def validate(self, config, meta_config=None):

    ERROR_NOT_TRUE = "Should be true: {0}"

    """Test class to check the value of a boolean environment variable."""

class LogicalTruthChecker(rose.macro.MacroBase):


        return config, self.reports
            self.add_report("env", "TRANSFORM_SWITCH", value, info)
            info = self.WARNING_CHANGED_VALUE.format(value, new_value)
            config.set(["env", "TRANSFORM_SWITCH"], new_value)
                new_value = rose.TYPE_BOOLEAN_VALUE_FALSE
            else:
                new_value = rose.TYPE_BOOLEAN_VALUE_TRUE
        node = config.get(["env", "TRANSFORM_SWITCH"], no_ignore=True)
        if node is not None and node.value != rose.TYPE_BOOLEAN_VALUE_FALSE:
            info = self.ERROR_NOT_TRUE.format(node.value)
            self.add_report("env", "TRANSFORM_SWITCH", value, info)
        return self.reports
__MACRO__
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
