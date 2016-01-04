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
# Basic tests for "rosie create".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 49
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
prefix-username.foo=fred
prefix-location.foo=$URL
prefix-location.bar=https://my-host/bar
__ROSE_CONF__
mkdir 'opt'
export ROSE_CONF_PATH=$PWD
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-empty-info-file
touch 'rose-suite.info'
run_fail "$TEST_KEY" rosie create -y --info-file=rose-suite.info
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] rose-suite.info: issues: 3
[FAIL]     =owner=None
[FAIL]         Variable set as compulsory, but not in configuration.
[FAIL]     =project=None
[FAIL]         Variable set as compulsory, but not in configuration.
[FAIL]     =title=None
[FAIL]         Variable set as compulsory, but not in configuration.
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-empty-ans
cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=don't fail
title=this should not fail
__INFO__
run_fail "$TEST_KEY" rosie create --info-file=rose-suite.info </dev/null
echo -n 'Create suite as "foo-?????"? [y or n (default)] ' >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-file
cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=don't fail
title=this should not fail
__INFO__
run_pass "$TEST_KEY" rosie create --info-file=rose-suite.info <<<y
{
    echo -n 'Create suite as "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa000: created at $URL/a/a/0/0/0"
    echo "[INFO] create: $PWD/roses"
    echo "[INFO] foo-aa000: local copy created at $PWD/roses/foo-aa000"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-edit
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=don't fail
title=this should never fail
__INFO__
run_pass "$TEST_KEY" rosie create <<<y
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
owner=fred
project=
title=

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Create suite as "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa001: created at $URL/a/a/0/0/1"
    echo "[INFO] foo-aa001: local copy created at $PWD/roses/foo-aa001"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-edit-with-access-list-default
cat >'opt/rose-access.conf' <<'__CONF__'
[rosie-vc]
access-list-default=holly ivy
__CONF__
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=don't fail
title=this should never fail
__INFO__
run_fail "$TEST_KEY" rosie create <<<n
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
access-list=holly ivy
owner=fred
project=
title=

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Create suite as "foo-?????"? [y or n (default)] '
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
rm -f 'opt/rose-access.conf'
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-edit-with-svn-servers-conf
cat >"$TEST_KEY_BASE-svn-servers-conf" <<'__CONF__'
[groups]
bar=my-host

[bar]
username=barn.owl
__CONF__
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=barn.owl
project=don't fail
title=this should never fail
__INFO__
ROSIE_SUBVERSION_SERVERS_CONF="$PWD/$TEST_KEY_BASE-svn-servers-conf" \
    run_fail "$TEST_KEY" rosie create --prefix=bar <<<n
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
owner=barn.owl
project=
title=

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
echo -n 'Create suite as "bar-?????"? [y or n (default)] ' >"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-info-edit-no-checkout
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=don't fail please
title=this should never ever fail
__INFO__
run_pass "$TEST_KEY" rosie create --no-checkout <<<y
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
owner=fred
project=
title=

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Create suite as "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa002: created at $URL/a/a/0/0/2"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-copy-empty
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=fork
title=divide and conquer 2
__INFO__
run_pass "$TEST_KEY" rosie create foo-aa002 <<<y
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
description=Copy of foo-aa002/trunk@3
owner=fred
project=don't fail please
title=this should never ever fail

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Copy "foo-aa002/trunk@3" to "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa003: created at $URL/a/a/0/0/3"
    echo '[INFO] foo-aa003: copied items from foo-aa002/trunk@3'
    echo "[INFO] foo-aa003: local copy created at $PWD/roses/foo-aa003"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn propget --revprop -r 'HEAD' 'svn:log' "${URL}" >"${TEST_KEY}.log"
file_cmp "${TEST_KEY}.log" "${TEST_KEY}.log" <<'__LOG__'
foo-aa003: new suite, a copy of foo-aa002/trunk@3
__LOG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-copy-empty-trunk-head
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=fork
title=divide and conquer 4
__INFO__
run_pass "$TEST_KEY" rosie create foo-aa002/trunk@HEAD <<<y
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
description=Copy of foo-aa002/trunk@3
owner=fred
project=don't fail please
title=this should never ever fail

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Copy "foo-aa002/trunk@3" to "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa004: created at $URL/a/a/0/0/4"
    echo '[INFO] foo-aa004: copied items from foo-aa002/trunk@3'
    echo "[INFO] foo-aa004: local copy created at $PWD/roses/foo-aa004"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn propget --revprop -r 'HEAD' 'svn:log' "${URL}" >"${TEST_KEY}.log"
file_cmp "${TEST_KEY}.log" "${TEST_KEY}.log" <<'__LOG__'
foo-aa004: new suite, a copy of foo-aa002/trunk@3
__LOG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-copy-not-empty
# Add something to an existing suite working copy
mkdir -p $PWD/roses/foo-aa001/{app/hello,etc}
cat >$PWD/roses/foo-aa001/app/hello/rose-app.conf <<'__ROSE_APP_CONF__'
[command]
default=echo Hello
__ROSE_APP_CONF__
echo $(($RANDOM % 10)) >$PWD/roses/foo-aa001/etc/number
svn add -q $PWD/roses/foo-aa001/{app,etc}
svn ci -q -m 't' $PWD/roses/foo-aa001
svn up -q $PWD/roses/foo-aa001
# Issue the copy command
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=fork
title=divide and conquer
__INFO__
run_pass "$TEST_KEY" rosie create foo-aa001 <<<y
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
description=Copy of foo-aa001/trunk@6
owner=fred
project=don't fail
title=this should never fail

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Copy "foo-aa001/trunk@6" to "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa005: created at $URL/a/a/0/0/5"
    echo '[INFO] foo-aa005: copied items from foo-aa001/trunk@6'
    echo "[INFO] foo-aa005: local copy created at $PWD/roses/foo-aa005"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn propget --revprop -r 'HEAD' 'svn:log' "${URL}" >"${TEST_KEY}.log"
file_cmp "${TEST_KEY}.log" "${TEST_KEY}.log" <<'__LOG__'
foo-aa005: new suite, a copy of foo-aa001/trunk@6
__LOG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-copy-not-empty-trunk-head
# Add something to an existing suite working copy
mkdir -p $PWD/roses/foo-aa001/{app/hello,etc}
cat >$PWD/roses/foo-aa001/app/hello/rose-app.conf <<'__ROSE_APP_CONF__'
[command]
default=echo Hello
__ROSE_APP_CONF__
echo $((10 + $RANDOM % 10)) >$PWD/roses/foo-aa001/etc/number
svn ci -q -m 't' $PWD/roses/foo-aa001
svn up -q $PWD/roses/foo-aa001
# Issue the copy command
cat >"$TEST_KEY_BASE-edit.in" <<__INFO__
access-list=*
owner=$USER
project=fork
title=divide and conquer 3
__INFO__
run_pass "$TEST_KEY" rosie create foo-aa001/trunk@HEAD <<<y
file_cmp "$TEST_KEY.edit.out" "$TEST_KEY_BASE-edit.out" <<__INFO__
description=Copy of foo-aa001/trunk@8
owner=fred
project=don't fail
title=this should never fail

# Make changes ABOVE these lines.
# The "owner", "project" and "title" fields are compulsory.
# Any KEY=VALUE pairs can be added. Known fields include:
# "access-list", "description" and "sub-project".
__INFO__
{
    echo -n 'Copy "foo-aa001/trunk@8" to "foo-?????"? [y or n (default)] '
    echo "[INFO] foo-aa006: created at $URL/a/a/0/0/6"
    echo '[INFO] foo-aa006: copied items from foo-aa001/trunk@8'
    echo "[INFO] foo-aa006: local copy created at $PWD/roses/foo-aa006"
}>"$TEST_KEY.out.1"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" "$TEST_KEY.out.1"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn propget --revprop -r 'HEAD' 'svn:log' "${URL}" >"${TEST_KEY}.log"
file_cmp "${TEST_KEY}.log" "${TEST_KEY}.log" <<'__LOG__'
foo-aa006: new suite, a copy of foo-aa001/trunk@8
__LOG__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-copy-mkdir-parents"
set -e
for I in $(seq 5 9); do
    cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=don't fail
title=this should not fail
__INFO__
    rosie create -q --info-file=rose-suite.info -y --no-checkout
done
set +e
run_pass "$TEST_KEY" rosie create foo-aa001 -y --no-checkout
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] foo-aa012: created at $URL/a/a/0/1/2
[INFO] foo-aa012: copied items from foo-aa001/trunk@8
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svn propget --revprop -r 'HEAD' 'svn:log' "${URL}" >"${TEST_KEY}.log"
file_cmp "${TEST_KEY}.log" "${TEST_KEY}.log" <<'__LOG__'
foo-aa012: new suite, a copy of foo-aa001/trunk@8
__LOG__
#-------------------------------------------------------------------------------
exit 0
