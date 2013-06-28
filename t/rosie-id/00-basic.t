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
# Basic tests for "rosie id".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 36
#-------------------------------------------------------------------------------
svnadmin create foo
URL=file://$PWD/foo
cat >rose.conf <<__ROSE_CONF__
[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-location.foo=$URL
prefix-web.foo=http://trac-host/foo
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
rosie create -q -y --info-file=$INFO_FILE

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
http://trac-host/foo/browser/a/a/0/0/0/trunk?rev=HEAD
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

TEST_KEY=$TEST_KEY_BASE-1-to-output.1
run_pass "$TEST_KEY" rosie id --to-output foo-aa000
# FIXME: "None" is not a nice output for a shell command.
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
None
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

mkdir -p $HOME/cylc-run/foo-aa000/log
rose suite-log -q -u -n foo-aa000
TEST_KEY=$TEST_KEY_BASE-1-to-output.2
ROSE_CONF_IGNORE=true run_pass "$TEST_KEY" rosie id --to-output foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
file://$HOME/cylc-run/foo-aa000/log/index.html
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
rm -rf  $HOME/cylc-run/foo-aa000

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
#-------------------------------------------------------------------------------
exit 0
