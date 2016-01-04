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
# Basic tests for "rosie checkout".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 24
#-------------------------------------------------------------------------------
svnadmin create foo
URL=file://$PWD/foo
cat >rose.conf <<__ROSE_CONF__
[external]
editor=$TEST_SOURCE_DIR/$TEST_KEY_BASE-edit

[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-owner-default.foo=fred
prefix-location.foo=$URL
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-empty-ans
cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=world-peace
title=I'll pass...
__INFO__
for I in $(seq 1 6); do
    rosie create -q -y --info-file=rose-suite.info --no-checkout
done
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-prefix
run_fail "$TEST_KEY" rosie checkout -q bo-nd007
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] bo: cannot determine prefix location
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-id
run_fail "$TEST_KEY" rosie checkout foo-tb411
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
SUITE_URL=$URL/t/b/4/1/1/trunk@HEAD
SUITE_WC=$PWD/roses/foo-tb411
file_grep "$TEST_KEY.err" \
    "\\[FAIL\\] svn checkout -q $SUITE_URL $SUITE_WC # return-code=1" \
    "$TEST_KEY.err"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-1
run_pass "$TEST_KEY" rosie checkout foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] foo-aa000: local copy created at $PWD/roses/foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-1-repeat
run_pass "$TEST_KEY" rosie checkout foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[WARN] foo-aa000: skip, local copy already exists at $PWD/roses/foo-aa000
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-multi
run_pass "$TEST_KEY" rosie checkout foo-aa001 foo-aa002 foo-aa003
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] foo-aa001: local copy created at $PWD/roses/foo-aa001
[INFO] foo-aa002: local copy created at $PWD/roses/foo-aa002
[INFO] foo-aa003: local copy created at $PWD/roses/foo-aa003
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
(cd roses/foo-aa003 && touch foo && svn add foo && svn commit -m "")
TEST_KEY=$TEST_KEY_BASE-normal-multi-repeat-1
run_fail "$TEST_KEY" rosie checkout foo-aa003 foo-aa004 foo-aa005
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $PWD/roses/foo-aa003: already exists
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-multi-repeat-force
run_pass "$TEST_KEY" rosie checkout -f foo-aa003 foo-aa004 foo-aa005
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $PWD/roses/foo-aa003/
[INFO] foo-aa003: local copy created at $PWD/roses/foo-aa003
[INFO] foo-aa004: local copy created at $PWD/roses/foo-aa004
[INFO] foo-aa005: local copy created at $PWD/roses/foo-aa005
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-multi-bad-force
rm -rf roses
run_fail "$TEST_KEY" rosie checkout --force foo-aa001 hi-gl055 foo-aa005
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] create: $PWD/roses
[INFO] foo-aa001: local copy created at $PWD/roses/foo-aa001
[INFO] foo-aa005: local copy created at $PWD/roses/foo-aa005
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] hi: cannot determine prefix location
__ERR__
#-------------------------------------------------------------------------------
exit 0
