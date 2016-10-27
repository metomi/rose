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
# Test "rose macro" in the absence of a rose configuration.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
init </dev/null
rm config/rose-app.conf
#-------------------------------------------------------------------------------
tests 7
#-------------------------------------------------------------------------------
# run from suite directory
TEST_KEY=$TEST_KEY_BASE-suite
TEST_SUITE=test-suite
mkdir -p $TEST_DIR/$TEST_SUITE/meta
cat >$TEST_DIR/$TEST_SUITE/rose-suite.conf <<'__SUITE_CONF__'
[env]
SUITE=sweet
__SUITE_CONF__
cat >$TEST_DIR/$TEST_SUITE/meta/rose-meta.conf <<'__META_CONF__'
[env=SUITE]
type=integer
__META_CONF__
run_fail "$TEST_KEY" rose macro -V -C $TEST_DIR/$TEST_SUITE
#echo `rose macro -V -C $TEST_DIR/$TEST_SUITE`
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 1
    env=SUITE=sweet
        Not an integer: 'sweet'
__ERR__
#-------------------------------------------------------------------------------
# run from suite/app directory
TEST_KEY=$TEST_KEY_BASE-suite-app-dir
mkdir -p $TEST_DIR/$TEST_SUITE/app/foo/meta/lib/python/macros
cat >$TEST_DIR/$TEST_SUITE/app/foo/rose-app.conf <<'__APP_CONF__'
[env]
FOO=baz
__APP_CONF__
cat >$TEST_DIR/$TEST_SUITE/app/foo/meta/rose-meta.conf <<'__META_CONF__'
[env=FOO]
macro=foo.FooChecker
__META_CONF__
touch $TEST_DIR/$TEST_SUITE/app/foo/meta/lib/python/macros/__init__.py
cat >$TEST_DIR/$TEST_SUITE/app/foo/meta/lib/python/macros/foo.py <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rose.macro


class FooChecker(rose.macro.MacroBase):
    """Checks weather suite is sweet enough."""

    def validate(self, config, meta_config=None):
        node = config.get(['env', 'FOO'])
        if node is not None or not node.is_ignored():
            if node.value not in ['foo']:
                self.add_report('env', 'FOO', node.value, 'Not foo enough')
        return self.reports

    def transform(self, config, meta_config=None):
        # This is here to ensure transform macros are not run with the -V
        # option.
        return config, self.reports
__MACRO__
run_fail "$TEST_KEY" rose macro -V -C $TEST_DIR/$TEST_SUITE/app
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] app: foo
[INFO] suite: test-suite
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[V] foo.FooChecker: issues: 1
    env=FOO=baz
        Not foo enough
[V] rose.macros.DefaultValidators: issues: 1
    env=SUITE=sweet
        Not an integer: 'sweet'
__ERR__
#-------------------------------------------------------------------------------
# run with --suite-only option
TEST_KEY=$TEST_KEY_BASE-suite-only
run_pass "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE/app --suite-only
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] suite: test-suite
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
__OUT__
#-------------------------------------------------------------------------------

rm -r $TEST_DIR/$TEST_SUITE
exit
