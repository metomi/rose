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
# Basic tests for "rosie id".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 45
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

TEST_KEY=$TEST_KEY_BASE-1-to-output.1
run_fail "$TEST_KEY" rosie id --to-output foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] foo-aa000: suite log not found
__ERR__

mkdir -p $HOME/cylc-run/foo-aa000/log/job
rose suite-log -q -U -n foo-aa000
TEST_KEY=$TEST_KEY_BASE-1-to-output.2
run_pass "$TEST_KEY" rosie id --to-output foo-aa000
file_grep "$TEST_KEY.out" '/foo-aa000$' "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
rm -fr "${HOME}/cylc-run/foo-aa000"

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
SUITE_DIR="$(mktemp -d --tmpdir="${HOME}/cylc-run" 'rose-test-battery.XXXXXX')"
SUITE_NAME="$(basename "${SUITE_DIR}")"
svn co -q "${URL}/a/a/0/0/0/trunk" 'foo-aa000'
touch 'foo-aa000/rose-suite.conf'
cat >'foo-aa000/suite.rc' <<'__SUITE_RC__'
[scheduling]
    [[dependencies]]
        graph='t1'
[runtime]
    [[t1]]
__SUITE_RC__
rose suite-run -l -q -C "${PWD}/foo-aa000" --name="${SUITE_NAME}"
run_pass "$TEST_KEY" rosie id "${HOME}/cylc-run/${SUITE_NAME}"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
foo-aa000
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
rose suite-clean -q -y --name="${SUITE_NAME}"
rm -fr 'foo-aa000'
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
exit 0
