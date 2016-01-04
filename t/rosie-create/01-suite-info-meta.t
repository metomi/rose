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
# Test "rosie create" with configuration metadata for "rose-suite.info".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 21
#-------------------------------------------------------------------------------
svnadmin create foo
URL=file://$PWD/foo
cat >'rose.conf' <<__ROSE_CONF__
opts=(editor)

[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-username.foo=$USER
prefix-location.foo=$URL
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
run_pass "$TEST_KEY" rosie create -y --info-file='rose-suite.info'
{
    echo "[INFO] foo-aa000: created at $URL/a/a/0/0/0"
    echo "[INFO] create: $PWD/roses"
    echo "[INFO] foo-aa000: local copy created at $PWD/roses/foo-aa000"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
file_cmp "${TEST_KEY}-rose-suite.info" \
    "${PWD}/roses/foo-aa000/rose-suite.info" <<__INFO__
access-list=*
description=not a fail
owner=${USER}
period=Forever
project=dont-fail
sub-project=hello failure is not an option
title=this should never fail
type=success
unknown=I am an unknow field but do include me
__INFO__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-copy-mode
export ROSE_META_PATH=$PWD/rose-meta
run_pass "$TEST_KEY" rosie create -y 'foo-aa000'
{
    echo "[INFO] foo-aa001: created at $URL/a/a/0/0/1"
    echo "[INFO] foo-aa001: copied items from foo-aa000/trunk@1"
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
file_cmp "$TEST_KEY_BASE-info-copy-mode.out" \
    "$TEST_KEY_BASE-info-copy-mode.out" "$TEST_KEY-copy-mode-edit.out" 
file_cmp "${TEST_KEY}-rose-suite.info" \
    "${PWD}/roses/foo-aa001/rose-suite.info" <<__INFO__
description=Copy of foo-aa000/trunk@1
owner=${USER}
period=
project=dont-fail
sub-project=hello failure is not an option
title=this should never fail
unknown=I am an unknow field but do include me
__INFO__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-info-copy-meta-try-0"
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
run_fail "$TEST_KEY" rosie create --info-file='rose-suite.info' <<<'n'
{
    echo -n 'rose-suite.info has invalid settings. Try again? [y or n (default)] '
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] rose-suite.info: issues: 1
[FAIL]     =sub-project=failure is not an option
[FAIL]         failed because: 'hello' not in this
__ERROR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-info-copy-meta-try-2"
export ROSE_META_PATH=$PWD/rose-meta
cat >'opt/rose-editor.conf' <<__ROSE_CONF__
[external]
editor=sed -i -e 's/^sub-project=greet.*$/sub-project=hello/' -e 's/^sub-project=failure.*$/sub-project=greet/'
__ROSE_CONF__
cat >'rose-suite.info' <<__INFO__
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
# "yes" command does not work here, because we cannot use a pipe
for I in $(seq 1 3); do
    echo 'y'
done >'yes-file'
run_pass "$TEST_KEY" rosie create --info-file='rose-suite.info' <'yes-file'
{
    echo -n 'rose-suite.info has invalid settings. Try again? [y or n (default)] '
    echo -n 'rose-suite.info has invalid settings. Try again? [y or n (default)] '
    echo -n 'Create suite as "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa002: created at ${URL}/a/a/0/0/2"
    echo "[INFO] foo-aa002: local copy created at $PWD/roses/foo-aa002"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] rose-suite.info: issues: 1
[FAIL]     =sub-project=failure is not an option
[FAIL]         failed because: 'hello' not in this
[FAIL] rose-suite.info: issues: 1
[FAIL]     =sub-project=greet
[FAIL]         failed because: 'hello' not in this
__ERROR__
rm 'opt/rose-editor.conf'
file_cmp "${TEST_KEY}-rose-suite.info" \
    "${PWD}/roses/foo-aa002/rose-suite.info" <<__INFO__
access-list=*
description=not a fail
owner=${USER}
period=Forever
project=dont-fail
sub-project=hello
title=this should never fail
type=success
__INFO__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-info-copy-meta-try-2-project"
export ROSE_META_PATH=$PWD/rose-meta
cat >'opt/rose-editor.conf' <<__ROSE_CONF__
[external]
editor=sed -i -e 's/^!project=/project=dont-fail/' -e 's/^project=$/!project=/'
__ROSE_CONF__
cat >'rose-suite.info' <<__INFO__
description=not a fail
owner=$USER
period=Forever
project=
sub-project=hello world
title=this should never fail
type=success

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
# "yes" command does not work here, because we cannot use a pipe
for I in $(seq 1 3); do
    echo 'y'
done >'yes-file'
run_pass "$TEST_KEY" rosie create --info-file='rose-suite.info' <'yes-file'
{
    echo -n 'rose-suite.info has invalid settings. Try again? [y or n (default)] '
    echo -n 'rose-suite.info has invalid settings. Try again? [y or n (default)] '
    echo -n 'Create suite as "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa003: created at ${URL}/a/a/0/0/3"
    echo "[INFO] foo-aa003: local copy created at $PWD/roses/foo-aa003"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[FAIL] rose-suite.info: issues: 1
[FAIL]     =project=
[FAIL]         Value  does not contain the pattern: ^.+(?# Must not be empty)
[FAIL] rose-suite.info: issues: 1
[FAIL]     =project=
[FAIL]         Compulsory settings should not be user-ignored.
__ERROR__
rm 'opt/rose-editor.conf'
file_cmp "${TEST_KEY}-rose-suite.info" \
    "${PWD}/roses/foo-aa003/rose-suite.info" <<__INFO__
description=not a fail
owner=${USER}
period=Forever
project=dont-fail
sub-project=hello world
title=this should never fail
type=success
__INFO__
#-------------------------------------------------------------------------------
exit
