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
# Tests for "rosa svn-pre-commit" with "rosie create".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 16
#-------------------------------------------------------------------------------
mkdir repos
svnadmin create repos/foo
SVN_URL=file://$PWD/repos/foo
mkdir conf
cat >conf/rose.conf <<__ROSE_CONF__
[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-owner-default.foo=fred
prefix-location.foo=$SVN_URL
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD/conf
cat >repos/foo/hooks/pre-commit <<__PRE_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$ROSE_CONF_PATH
exec $ROSE_HOME/sbin/rosa svn-pre-commit --debug "\$@"
__PRE_COMMIT__
chmod +x repos/foo/hooks/pre-commit
export LANG=C
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-normal
cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=hello
title=greeting to this world
__INFO__
run_pass "$TEST_KEY" rosie create -y --info-file=rose-suite.info --no-checkout
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] foo-aa000: created at $SVN_URL/a/a/0/0/0
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/
A   a/a/
A   a/a/0/
A   a/a/0/0/
A   a/a/0/0/0/
A   a/a/0/0/0/trunk/
A   a/a/0/0/0/trunk/rose-suite.conf
A   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-copy
# Add something to foo-aa000
rosie checkout -q foo-aa000
mkdir -p $PWD/roses/foo-aa000/{app/hello,etc}
cat >$PWD/roses/foo-aa000/app/hello/rose-app.conf <<'__ROSE_APP_CONF__'
[command]
default=cat

[file:STDIN]
source=$HOME/etc/hello.list
__ROSE_APP_CONF__
echo $(($RANDOM % 10)) >$PWD/roses/foo-aa000/etc/random
svn add -q $PWD/roses/foo-aa000/{app,etc}
svn ci -m 't' -q $PWD/roses/foo-aa000
# Copy
cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=hello
title=greeting to a list of people
__INFO__
run_pass "$TEST_KEY" \
    rosie create -y --info-file=rose-suite.info --no-checkout foo-aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] foo-aa001: created at $SVN_URL/a/a/0/0/1
[INFO] foo-aa001: copied items from foo-aa000/trunk@2
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
# Changeset test
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed.1" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/a/0/0/1/
A   a/a/0/0/1/trunk/
U   a/a/0/0/1/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-meta-empty
cat >rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=meta
title=configuration metadata for discovery information
__INFO__
run_pass "$TEST_KEY" \
    rosie create -y --meta-suite --info-file=rose-suite.info --no-checkout
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] foo-ROSIE: created at $SVN_URL/R/O/S/I/E
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   R/
A   R/O/
A   R/O/S/
A   R/O/S/I/
A   R/O/S/I/E/
A   R/O/S/I/E/trunk/
A   R/O/S/I/E/trunk/rose-suite.conf
A   R/O/S/I/E/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-meta-keys-file
rosie checkout -q foo-ROSIE
cat >$PWD/roses/foo-ROSIE/rosie-keys <<__KEYS__
world galaxy universe
__KEYS__
svn add -q $PWD/roses/foo-ROSIE/rosie-keys
run_pass "$TEST_KEY" svn commit -q -m 't' $PWD/roses/foo-ROSIE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   R/O/S/I/E/trunk/rosie-keys
__CHANGED__
#-------------------------------------------------------------------------------
exit 0
