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
# Basic tests for "rosie delete".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 42
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
for I in $(seq 1 7); do
    rosie create -q -y --info-file=rose-suite.info --no-checkout
done
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-prefix
run_fail "$TEST_KEY" rosie delete -y bo-nd007
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] bo: cannot determine prefix location
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-id
run_fail "$TEST_KEY" rosie delete -y foo-tb411
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" \
    "\\[FAIL\\] svn delete -q.*$URL/t/b/4/1/1 # return-code=1" \
    "$TEST_KEY.err"
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-y-url-only
run_pass "$TEST_KEY" rosie delete -y foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $URL/a/a/0/0/0
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-y-local-only
rosie checkout -q foo-aa001
run_pass "$TEST_KEY" rosie delete -y --local-only foo-aa001
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $PWD/roses/foo-aa001/
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-y-both
rosie checkout -q foo-aa001
run_pass "$TEST_KEY" rosie delete -y foo-aa001
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $PWD/roses/foo-aa001/
[INFO] delete: $URL/a/a/0/0/1
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-empty-ans
run_fail "$TEST_KEY" rosie delete foo-aa002 </dev/null
{
    echo -n 'foo-aa002: delete local+repository copies?'
    echo -n ' [y or n (default) or a (yes to all)] '
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-ans-n
run_fail "$TEST_KEY" rosie delete foo-aa002 <<<n
{
    echo -n 'foo-aa002: delete local+repository copies?'
    echo -n ' [y or n (default) or a (yes to all)] '
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-ans-y
rosie checkout -q foo-aa002
run_pass "$TEST_KEY" rosie delete foo-aa002 <<<y
{
    echo -n 'foo-aa002: delete local+repository copies?'
    echo -n ' [y or n (default) or a (yes to all)] '
    echo "[INFO] delete: $PWD/roses/foo-aa002/"
    echo "[INFO] delete: $URL/a/a/0/0/2"
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-status
rosie checkout -q foo-aa003
touch $PWD/roses/foo-aa003/file
run_fail "$TEST_KEY" rosie delete foo-aa003 <<<y
{
    echo -n 'foo-aa003: delete local+repository copies?'
    echo -n ' [y or n (default) or a (yes to all)] '
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] foo-aa003: $PWD/roses/foo-aa003: local copy has uncommitted changes:
[FAIL] ?       $PWD/roses/foo-aa003/file
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal-status-force
#rosie checkout -q foo-aa003 # done above
#touch $PWD/roses/foo-aa003/file # done above
run_pass "$TEST_KEY" rosie delete -f --local-only foo-aa003 <<<y
{
    echo -n 'foo-aa003: delete local copy?'
    echo -n ' [y or n (default) or a (yes to all)] '
    echo "[INFO] delete: $PWD/roses/foo-aa003/"
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-multiple-local-only
rosie checkout -q foo-aa003
rosie checkout -q foo-aa004
rosie checkout -q foo-aa005
run_pass "$TEST_KEY" \
    rosie delete -f --local-only foo-aa003 foo-aa004 foo-aa005 <<__IN__
y
y
y
__IN__
{
    echo -n 'foo-aa003: delete local copy?'
    echo -n ' [y or n (default) or a (yes to all)] '
    echo "[INFO] delete: $PWD/roses/foo-aa003/"
    echo -n 'foo-aa004: delete local copy?'
    echo -n ' [y or n (default) or a (yes to all)] '
    echo "[INFO] delete: $PWD/roses/foo-aa004/"
    echo -n 'foo-aa005: delete local copy?'
    echo -n ' [y or n (default) or a (yes to all)] '
    echo "[INFO] delete: $PWD/roses/foo-aa005/"
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-multiple-ans-a
rosie checkout -q foo-aa003
rosie checkout -q foo-aa004
rosie checkout -q foo-aa005
run_pass "$TEST_KEY" \
    rosie delete -f foo-aa003 foo-aa004 foo-aa005 <<<a
{
    echo -n 'foo-aa003: delete local+repository copies?'
    echo -n ' [y or n (default) or a (yes to all)] '
    echo "[INFO] delete: $PWD/roses/foo-aa003/"
    echo "[INFO] delete: $URL/a/a/0/0/3"
    echo "[INFO] delete: $PWD/roses/foo-aa004/"
    echo "[INFO] delete: $URL/a/a/0/0/4"
    echo "[INFO] delete: $PWD/roses/foo-aa005/"
    echo "[INFO] delete: $URL/a/a/0/0/5"
} >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-multiple-bad-id
run_fail "$TEST_KEY" rosie delete -y bo-nd007 foo-aa006
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] bo: cannot determine prefix location
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-multiple-bad-id-force
run_fail "$TEST_KEY" rosie delete --force -y bo-nd007 foo-aa006
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $URL/a/a/0/0/6
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] bo: cannot determine prefix location
__ERR__
#-------------------------------------------------------------------------------
exit 0
