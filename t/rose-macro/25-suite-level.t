#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
tests 30
#-------------------------------------------------------------------------------
# Setup.
TEST_SUITE=test-suite

# suite
mkdir -p $TEST_DIR/$TEST_SUITE/meta/lib/python/macros
cat >$TEST_DIR/$TEST_SUITE/rose-suite.conf <<'__SUITE_CONF__'
[env]
ANSWER=quarante deux
__SUITE_CONF__
cat >$TEST_DIR/$TEST_SUITE/meta/rose-meta.conf <<'__META_CONF__'
[env=ANSWER]
type=integer
__META_CONF__
touch $TEST_DIR/$TEST_SUITE/meta/lib/python/macros/__init__.py
cat >$TEST_DIR/$TEST_SUITE/meta/lib/python/macros/suite.py <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rose.macro


class SuiteChecker(rose.macro.MacroBase):
    """Suite checker macro."""

    def validate(self, config, meta_config=None):
        node = config.get(['env', 'ANSWER'])
        if node is not None or not node.is_ignored():
            if node.value != 42:
                self.add_report('env', 'ANSWER', node.value, 'Incorrect'
                    'answer')
        return self.reports

    def transform(self, config, meta_config=None):
        return config, self.reports

    def report(self, config, meta_config=None):
        print ('The answer to life, the universe and everything is, is, is ' +
            config.get(['env', 'ANSWER']))
__MACRO__

# app/foo
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
    """Foo checker macro."""

    def validate(self, config, meta_config=None):
        node = config.get(['env', 'FOO'])
        if node is not None or not node.is_ignored():
            if node.value not in ['foo']:
                self.add_report('env', 'FOO', node.value, 'Not foo enough')
        return self.reports

    def transform(self, config, meta_config=None):
        return config, self.reports

    def report(self, config, meta_config=None):
        print 'foo is ' + config.get(['env', 'FOO'])
__MACRO__

# app/bar
mkdir -p $TEST_DIR/$TEST_SUITE/app/bar/meta/lib/python/macros
cat >$TEST_DIR/$TEST_SUITE/app/bar/rose-app.conf <<'__APP_CONF__'
[env]
BAR=|
__APP_CONF__
cat >$TEST_DIR/$TEST_SUITE/app/bar/meta/rose-meta.conf <<'__META_CONF__'
[env=BAR]
macro=bar.BarChecker
type=integer
__META_CONF__
touch $TEST_DIR/$TEST_SUITE/app/bar/meta/lib/python/macros/__init__.py
cat >$TEST_DIR/$TEST_SUITE/app/bar/meta/lib/python/macros/bar.py <<'__MACRO__'
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rose.macro


class BarChecker(rose.macro.MacroBase):
    """Bar checker macro."""

    def validate(self, config, meta_config=None):
        node = config.get(['env', 'BAR'])
        if node is not None or not node.is_ignored():
            if node.value not in ['pub']:
                self.add_report('env', 'BAR', node.value, 'bar < pub')
        return self.reports

    def transform(self, config, meta_config=None):
        return config, self.reports

    def report(self, config, meta_config=None):
        symbol = config.get(['env', 'BAR'])
        print (symbol + ' ') * 6 + 'ram'
__MACRO__
#-------------------------------------------------------------------------------
# List all macros from the suite directory.
TEST_KEY=$TEST_KEY_BASE-list-all-suite
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] app: bar
[V] bar.BarChecker
    # Bar checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] bar.BarChecker
    # Bar checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] bar.BarChecker
    # Bar checker macro.
[INFO] app: foo
[V] foo.FooChecker
    # Foo checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] foo.FooChecker
    # Foo checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] foo.FooChecker
    # Foo checker macro.
[INFO] suite: test-suite
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[V] suite.SuiteChecker
    # Suite checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[T] suite.SuiteChecker
    # Suite checker macro.
[R] suite.SuiteChecker
    # Suite checker macro.
__OUT__
#-------------------------------------------------------------------------------
# List all macros from the suite/app directory.
TEST_KEY=$TEST_KEY_BASE-list-all-app
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] app: bar
[V] bar.BarChecker
    # Bar checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] bar.BarChecker
    # Bar checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] bar.BarChecker
    # Bar checker macro.
[INFO] app: foo
[V] foo.FooChecker
    # Foo checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] foo.FooChecker
    # Foo checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] foo.FooChecker
    # Foo checker macro.
[INFO] suite: test-suite
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[V] suite.SuiteChecker
    # Suite checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[T] suite.SuiteChecker
    # Suite checker macro.
[R] suite.SuiteChecker
    # Suite checker macro.
__OUT__
#-------------------------------------------------------------------------------
# List all macros from the app/foo directory.
TEST_KEY=$TEST_KEY_BASE-list-all-app-foo
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app/foo
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[V] foo.FooChecker
    # Foo checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] foo.FooChecker
    # Foo checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] foo.FooChecker
    # Foo checker macro.
__OUT__
#-------------------------------------------------------------------------------
# List all macros from an app sub-directory.
TEST_KEY=$TEST_KEY_BASE-list-all-app-foo-subdir
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app/foo/meta
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[V] foo.FooChecker
    # Foo checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] foo.FooChecker
    # Foo checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] foo.FooChecker
    # Foo checker macro.
__OUT__
#-------------------------------------------------------------------------------
# List all macros from a suite sub-directory
TEST_KEY=$TEST_KEY_BASE-list-all-suite-subdir
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/meta
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] app: bar
[V] bar.BarChecker
    # Bar checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] bar.BarChecker
    # Bar checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] bar.BarChecker
    # Bar checker macro.
[INFO] app: foo
[V] foo.FooChecker
    # Foo checker macro.
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[T] foo.FooChecker
    # Foo checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[R] foo.FooChecker
    # Foo checker macro.
[INFO] suite: test-suite
[V] rose.macros.DefaultValidators
    # Runs all the default checks, such as compulsory checking.
[V] suite.SuiteChecker
    # Suite checker macro.
[T] rose.macros.DefaultTransforms
    # Runs all the default fixers, such as trigger fixing.
[T] suite.SuiteChecker
    # Suite checker macro.
[R] suite.SuiteChecker
    # Suite checker macro.
__OUT__
#-------------------------------------------------------------------------------
# Run all validator macros from the suite directory.
TEST_KEY=$TEST_KEY_BASE-validate-all-suite
run_fail $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE -V
file_cmp $TEST_KEY.err $TEST_KEY.err <<'__ERR__'
[V] bar.BarChecker: issues: 1
    env=BAR=|
        bar < pub
[V] rose.macros.DefaultValidators: issues: 1
    env=BAR=|
        Not an integer: '|'
[V] foo.FooChecker: issues: 1
    env=FOO=baz
        Not foo enough
[V] rose.macros.DefaultValidators: issues: 1
    env=FOO=baz
        Not an integer: 'baz'
[V] rose.macros.DefaultValidators: issues: 1
    env=ANSWER=quarante deux
        Not an integer: 'quarante deux'
[V] suite.SuiteChecker: issues: 1
    env=ANSWER=quarante deux
        Incorrectanswer
__ERR__
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] app: bar
[INFO] app: foo
[INFO] suite: test-suite
__OUT__
#-------------------------------------------------------------------------------
# Run all transformer macros from the suite directory.
TEST_KEY=$TEST_KEY_BASE-transform-all-suite
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE -T
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] app: bar
[T] bar.BarChecker: changes: 0
[T] rose.macros.DefaultTransforms: changes: 0
[INFO] app: foo
[T] foo.FooChecker: changes: 0
[T] rose.macros.DefaultTransforms: changes: 0
[INFO] suite: test-suite
[T] rose.macros.DefaultTransforms: changes: 0
[T] suite.SuiteChecker: changes: 0
__OUT__
#-------------------------------------------------------------------------------
# Run all fixer macros from the suite directory.
TEST_KEY=$TEST_KEY_BASE-fix-all-suite
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE -F
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] app: bar
[T] rose.macros.DefaultTransforms: changes: 0
[INFO] app: foo
[T] rose.macros.DefaultTransforms: changes: 0
[INFO] suite: test-suite
[T] rose.macros.DefaultTransforms: changes: 0
__OUT__
#-------------------------------------------------------------------------------
# Run all validator macros for the suite only.
TEST_KEY=$TEST_KEY_BASE-validate-all-suite-only-suite
run_fail $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE -V --suite-only
file_cmp $TEST_KEY.err $TEST_KEY.err <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 1
    env=ANSWER=quarante deux
        Not an integer: 'quarante deux'
[V] suite.SuiteChecker: issues: 1
    env=ANSWER=quarante deux
        Incorrectanswer
__ERR__
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] suite: test-suite
__OUT__
#-------------------------------------------------------------------------------
# Run all validator macros for the suite only from an app directory.
TEST_KEY=$TEST_KEY_BASE-validate-all-suite-only-app-foo
run_fail $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app/foo -V --suite-only
file_cmp $TEST_KEY.err $TEST_KEY.err <<'__ERR__'
[V] rose.macros.DefaultValidators: issues: 1
    env=ANSWER=quarante deux
        Not an integer: 'quarante deux'
[V] suite.SuiteChecker: issues: 1
    env=ANSWER=quarante deux
        Incorrectanswer
__ERR__
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[INFO] suite: test-suite
__OUT__
#-------------------------------------------------------------------------------
# Run all validator macros from an app directory.
TEST_KEY=$TEST_KEY_BASE-validate-all-suite
run_fail $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app/foo -V
file_cmp $TEST_KEY.err $TEST_KEY.err <<'__ERR__'
[V] foo.FooChecker: issues: 1
    env=FOO=baz
        Not foo enough
[V] rose.macros.DefaultValidators: issues: 1
    env=FOO=baz
        Not an integer: 'baz'
__ERR__
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
__OUT__
#-------------------------------------------------------------------------------
# Run all transformer macros from an app directory.
TEST_KEY=$TEST_KEY_BASE-transform-all-suite
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app/foo -T
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[T] foo.FooChecker: changes: 0
[T] rose.macros.DefaultTransforms: changes: 0
__OUT__
#-------------------------------------------------------------------------------
# Run all fixer macros from an app directory.
TEST_KEY=$TEST_KEY_BASE-fix-all-suite
run_pass $TEST_KEY rose macro -C $TEST_DIR/$TEST_SUITE/app/foo -F
file_cmp $TEST_KEY.out $TEST_KEY.out <<'__OUT__'
[T] rose.macros.DefaultTransforms: changes: 0
__OUT__

#-------------------------------------------------------------------------------
rm -r $TEST_DIR/$TEST_SUITE
exit
