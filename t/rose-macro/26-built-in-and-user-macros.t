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
tests 12
#-------------------------------------------------------------------------------
# Setup.
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
mkdir -p $TEST_DIR/$TEST_SUITE/app/foo/meta/lib/python/macros
cat >$TEST_DIR/$TEST_SUITE/app/foo/rose-app.conf <<'__APP_CONF__'
[env]
FOO=baz
__APP_CONF__
cat >$TEST_DIR/$TEST_SUITE/app/foo/meta/rose-meta.conf <<'__META_CONF__'
[env=FOO]
macro=foo.FooChecker
type=integer
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
#-------------------------------------------------------------------------------
# List all macros.
TEST_KEY=$TEST_KEY_BASE-all
run_pass "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] app: foo
[V] foo.FooChecker
    # Checks weather suite is sweet enough.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] foo.FooChecker
    # Checks weather suite is sweet enough.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[INFO] suite: test-suite
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
__OUT__
#-------------------------------------------------------------------------------
# List only default macros.
TEST_KEY=$TEST_KEY_BASE-default-only
run_pass "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE --default-only
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] app: foo
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[INFO] suite: test-suite
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
__OUT__
#-------------------------------------------------------------------------------
# Run all validate macros.
TEST_KEY=$TEST_KEY_BASE-validate
run_fail "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE -V
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__OUT__'
[V] foo.FooChecker: issues: 1
    env=FOO=baz
        Not foo enough
[V] rose.macros.DefaultValidators: issues: 1
    env=FOO=baz
        Not an integer: 'baz'
[V] rose.macros.DefaultValidators: issues: 1
    env=SUITE=sweet
        Not an integer: 'sweet'
__OUT__
#-------------------------------------------------------------------------------
# Run only default validate macros.
TEST_KEY=$TEST_KEY_BASE-validate-default-only
run_fail "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE -V --default-only
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__OUT__'
[V] rose.macros.DefaultValidators: issues: 1
    env=FOO=baz
        Not an integer: 'baz'
[V] rose.macros.DefaultValidators: issues: 1
    env=SUITE=sweet
        Not an integer: 'sweet'
__OUT__
#-------------------------------------------------------------------------------
# Run all fixer macros.
TEST_KEY=$TEST_KEY_BASE-fixer
run_pass "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE -F
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] app: foo
[T] foo.FooChecker: changes: 0
[T] rose.macros.DefaultTransforms: changes: 0
[INFO] suite: test-suite
[T] rose.macros.DefaultTransforms: changes: 0
__OUT__
#-------------------------------------------------------------------------------
# Run only default fixer macros.
TEST_KEY=$TEST_KEY_BASE-fixer-default-only
run_pass "$TEST_KEY" rose macro -C $TEST_DIR/$TEST_SUITE -F --default-only
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] app: foo
[T] rose.macros.DefaultTransforms: changes: 0
[INFO] suite: test-suite
[T] rose.macros.DefaultTransforms: changes: 0
__OUT__
#-------------------------------------------------------------------------------
rm -r $TEST_DIR/$TEST_SUITE
exit
