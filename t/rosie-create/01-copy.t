#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Copy tests for "rosie create".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 11
#-------------------------------------------------------------------------------
svnadmin create foo
URL=file://$PWD/foo
cat >rose.conf <<__ROSE_CONF__
opts=(access)

[external]
editor=$TEST_SOURCE_DIR/$TEST_KEY_BASE-edit

[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-username.foo=$USER
prefix-location.foo=$URL
prefix-location.bar=https://my-host/bar
__ROSE_CONF__
mkdir 'opt'
export ROSE_CONF_PATH=$PWD

mkdir -p 'rose-meta/dont-fail/HEAD/'
cat >'rose-meta/dont-fail/HEAD/rose-meta.conf' <<__META_CONF__
[=period]
copy-mode=clear

[=sub-project]
fail-if='hello' not in this

[=type]
copy-mode=never
__META_CONF__

#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-copy
cat >"rose-suite.info" <<__INFO__
access-list=*
description=not a fail
owner=$USER
period=Forever
project=dont-fail
sub-project=hello failure is not an option
title=this should never fail
type=success
unknown=I am an unknow field but do include me

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
run_pass "$TEST_KEY" rosie create --info-file=rose-suite.info <<<y
{
    echo -n 'Create suite at "foo"? y/n (default n) '
    echo "[INFO] foo-aa000: created at $URL/a/a/0/0/0"
    echo "[INFO] create: $PWD/roses"
    echo "[INFO] foo-aa000: local copy created at $PWD/roses/foo-aa000"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-copy-mode
export ROSE_META_PATH=$PWD/rose-meta
run_pass "$TEST_KEY" rosie create foo-aa000 <<<y
{
    echo -n 'Copy "foo-aa000/trunk@1"? y/n (default n) '
    echo "[INFO] foo-aa001: created at $URL/a/a/0/0/1"
    echo "[INFO] foo-aa001: copied items from foo-aa000"
    echo "[INFO] foo-aa001: local copy created at $PWD/roses/foo-aa001"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null

run_pass "$TEST_KEY" svn cat $URL/a/a/0/0/1/trunk/rose-suite.info

cat >"$TEST_KEY-copy-mode-edit.out" <<__INFO__
description=Copy of foo-aa000/trunk@1
owner=$USER
period=
project=dont-fail
sub-project=hello failure is not an option
title=this should never fail
unknown=I am an unknow field but do include me
__INFO__
file_cmp "$TEST_KEY_BASE-info-copy-mode.out" "$TEST_KEY_BASE-info-copy-mode.out" "$TEST_KEY-copy-mode-edit.out" 
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-copy-meta-pass
export ROSE_META_PATH=$PWD/rose-meta
cat >"rose-suite.info" <<__INFO__
access-list=*
description=not a fail
owner=$USER
period=Forever
project=dont-fail
sub-project=failure is not an option
title=this should never fail
type=success

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
run_fail "$TEST_KEY" rosie create --info-file=rose-suite.info <<<y
{
    echo -n 'Create suite at "foo"? y/n (default n) Metadata issue, do you want to try again? y/n (default n) '
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
rose.macro.DefaultValidators: issues: 1
    =sub-project=failure is not an option
        failed because: 'hello' not in this
__ERROR__
exit 0
