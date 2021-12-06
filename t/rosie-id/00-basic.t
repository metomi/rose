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
# Basic tests for "rosie id".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 39
#-------------------------------------------------------------------------------
svnadmin create foo
URL=file://$PWD/foo
cat >rose.conf <<__ROSE_CONF__
[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-location.foo=$URL
prefix-web.foo=http://trac-host/foo/intertrac/source:
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD
#-------------------------------------------------------------------------------
# Tests on empty repository.
TEST_KEY=$TEST_KEY_BASE-empty-latest
run_pass "$TEST_KEY" rosie id --latest
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
TEST_KEY=$TEST_KEY_BASE-empty-next
run_pass "$TEST_KEY" rosie id --next
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Tests on an ID.
INFO_FILE=rosie-create.info
cat >$INFO_FILE <<__INFO__
access-list=*
owner=$USER
project=rose tea
title=Identify the best rose tea in the world
__INFO__
rosie create -q -y --info-file=$INFO_FILE || exit 1

TEST_KEY=$TEST_KEY_BASE-1-latest
run_pass "$TEST_KEY" rosie id --latest
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY=$TEST_KEY_BASE-1-next
run_pass "$TEST_KEY" rosie id --next
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
foo-aa001
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY=$TEST_KEY_BASE-1-to-origin
run_pass "$TEST_KEY" rosie id --to-origin foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$URL/a/a/0/0/0
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY=$TEST_KEY_BASE-1-to-local-copy
run_pass "$TEST_KEY" rosie id --to-local-copy foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$PWD/roses/foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY=$TEST_KEY_BASE-1-to-web
run_pass "$TEST_KEY" rosie id --to-web foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
http://trac-host/foo/intertrac/source:/a/a/0/0/0/trunk@HEAD
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY=$TEST_KEY_BASE-1-full-wc-id
run_pass "$TEST_KEY" rosie id roses/foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

cd roses/foo-aa000
TEST_KEY=$TEST_KEY_BASE-1-wc-id
run_pass "$TEST_KEY" rosie id
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
cd $OLDPWD

TEST_KEY=$TEST_KEY_BASE-1-url-id
run_pass "$TEST_KEY" rosie id $URL/a/a/0/0/0
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY="${TEST_KEY_BASE}-run"
get_reg
svn co -q "${URL}/a/a/0/0/0/trunk" 'foo-aa000'
touch 'foo-aa000/rose-suite.conf'
cat >'foo-aa000/flow.cylc' <<'__SUITE_RC__'
[scheduling]
   [[dependencies]]
       graph='t1'
[runtime]
   [[t1]]
__SUITE_RC__
cylc install \
   -C "${PWD}/foo-aa000" \
   --flow-name="${FLOW}" \
   --no-run-name
run_pass "$TEST_KEY" rosie id "${HOME}/cylc-run/${FLOW}"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Latest and next should still be correct if latest suite removed from HEAD
TEST_KEY=$TEST_KEY_BASE-latest-not-at-head
rosie delete -f -q -y foo-aa000 || exit 1
run_pass "$TEST_KEY" rosie id --latest
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
TEST_KEY=$TEST_KEY_BASE-next-with-latest-not-at-head
run_pass "$TEST_KEY" rosie id --next
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
foo-aa001
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
purge
rm -fr 'foo-aa000'
exit 0
