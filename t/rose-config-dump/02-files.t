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
# Test "rose config-dump".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------
# Specific file, current directory.
TEST_KEY=$TEST_KEY_BASE-f
setup
cat >rose-foo.conf <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
cat >rose-bar.conf <<'__CONTENT__'
duck=quack
cat=meow
__CONTENT__
run_pass "$TEST_KEY" rose config-dump -f rose-bar.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] M rose-bar.conf
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.foo" 'rose-foo.conf' <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
file_cmp "$TEST_KEY.bar" 'rose-bar.conf' <<'__CONTENT__'
cat=meow
duck=quack
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Specific file, other directory.
TEST_KEY=$TEST_KEY_BASE-mktemp-f
setup
cat >rose-foo.conf <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
FILE=$(mktemp)
cat >$FILE <<'__CONTENT__'
duck=quack
cat=meow
__CONTENT__
run_pass "$TEST_KEY" rose config-dump -f $FILE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] M $FILE
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.foo" 'rose-foo.conf' <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
file_cmp "$TEST_KEY.file" $FILE <<'__CONTENT__'
cat=meow
duck=quack
__CONTENT__
rm -f $FILE
teardown
#-------------------------------------------------------------------------------
# Change directory.
TEST_KEY=$TEST_KEY_BASE-C
setup
cat >rose-foo.conf <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
mkdir d
cat >d/rose-foo.conf <<'__CONTENT__'
C=silly
B=billy
__CONTENT__
run_pass "$TEST_KEY" rose config-dump -C d
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] chdir: d/
[INFO] M rose-foo.conf
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.foo" 'rose-foo.conf' <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
file_cmp "$TEST_KEY.d/foo" 'd/rose-foo.conf' <<'__CONTENT__'
B=billy
C=silly
__CONTENT__
teardown
#-------------------------------------------------------------------------------
# Change directory, specific file.
TEST_KEY=$TEST_KEY_BASE-C-f
setup
cat >rose-foo.conf <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
mkdir d
cat >d/rose-foo.conf <<'__CONTENT__'
C=silly
B=billy
__CONTENT__
cat >d/rose-bar.conf <<'__CONTENT__'
duck=quack
cat=meow
__CONTENT__
run_pass "$TEST_KEY" rose config-dump -C d -f rose-bar.conf
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
[INFO] chdir: d/
[INFO] M rose-bar.conf
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "$TEST_KEY.foo" 'rose-foo.conf' <<'__CONTENT__'
foo=FOO
bar=BAR
__CONTENT__
file_cmp "$TEST_KEY.d/foo" 'd/rose-foo.conf' <<'__CONTENT__'
C=silly
B=billy
__CONTENT__
file_cmp "$TEST_KEY.d/bar" 'd/rose-bar.conf' <<'__CONTENT__'
cat=meow
duck=quack
__CONTENT__
teardown
#-------------------------------------------------------------------------------
exit 0
