#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2019 British Crown (Met Office) & Contributors.
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
# Basic tests for "rosa db-create".
# Imports of information from a non-empty repository is really done via "rosa
# svn-post-commit", which is tested quite thoroughly in its own test suite.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! python3 -c 'import sqlalchemy' 2>/dev/null; then
    skip_all '"sqlalchemy" not installed'
fi
tests 16
#-------------------------------------------------------------------------------
mkdir repos
svnadmin create repos/foo || exit 1
SVN_URL=file://$PWD/repos/foo
mkdir conf
cat >conf/rose.conf <<__ROSE_CONF__
[rosie-db]
repos.foo=$PWD/repos/foo
db.foo=sqlite:///$PWD/repos/foo.db
[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-owner-default.foo=fred
prefix-location.foo=$SVN_URL
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD/conf
cat >repos/foo/hooks/post-commit <<__POST_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$ROSE_CONF_PATH
$ROSE_HOME/sbin/rosa svn-post-commit --debug "\$@" \\
    1>$PWD/rosa-svn-post-commit.out 2>$PWD/rosa-svn-post-commit.err
echo \$? >$PWD/rosa-svn-post-commit.rc
__POST_COMMIT__
chmod +x repos/foo/hooks/post-commit
export LANG=C
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0"
run_pass "$TEST_KEY" $ROSE_HOME/sbin/rosa db-create
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] sqlite:///$PWD/repos/foo.db: DB created.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
sqlite3 $PWD/repos/foo.db '.dump' >"$TEST_KEY.dump"
file_cmp "$TEST_KEY.dump" "$TEST_KEY.dump" "$TEST_SOURCE_DIR/$TEST_KEY.dump"
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1"
rm $PWD/repos/foo.db
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=iris
project=eye pad
title=Should have gone to ...
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout || exit 1
echo "2009-02-13T23:31:30.000000Z" >foo-date-1.txt
svnadmin setrevprop $PWD/repos/foo -r 1 svn:date foo-date-1.txt
run_pass "$TEST_KEY" $ROSE_HOME/sbin/rosa db-create
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] sqlite:///$PWD/repos/foo.db: DB created.
[INFO] $PWD/repos/foo: DB loaded, r1 of 1.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
sqlite3 $PWD/repos/foo.db '.dump' >"$TEST_KEY.dump"
sed "s/\\\$USER/$USER/" "$TEST_SOURCE_DIR/$TEST_KEY.dump" >"$TEST_KEY.dump.expected"
file_cmp "$TEST_KEY.dump" "$TEST_KEY.dump" "$TEST_KEY.dump.expected"
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-2"
rm $PWD/repos/foo.db
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=roses
project=poetry
title=Roses are Red,...
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info || exit 1
echo "2009-02-13T23:31:31.000000Z" >foo-date-2.txt
svnadmin setrevprop $PWD/repos/foo -r 2 svn:date foo-date-2.txt
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=roses
project=poetry
title=Roses are Red, Violets are Blue,...
__ROSE_SUITE_INFO
cp rose-suite.info $PWD/roses/foo-aa001/
(cd $PWD/roses/foo-aa001 && svn commit -q -m "update" && \
     svn update -q) || exit 1
echo "2009-02-13T23:31:32.000000Z" >foo-date-3.txt
svnadmin setrevprop $PWD/repos/foo -r 3 svn:date foo-date-3.txt
run_pass "$TEST_KEY" $ROSE_HOME/sbin/rosa db-create
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] sqlite:///$PWD/repos/foo.db: DB created.
[INFO] $PWD/repos/foo: DB loaded, r3 of 3.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
sqlite3 $PWD/repos/foo.db '.dump' >"$TEST_KEY.dump"
sed "s/\\\$USER/$USER/" "$TEST_SOURCE_DIR/$TEST_KEY.dump" >"$TEST_KEY.dump.expected"
file_cmp "$TEST_KEY.dump" "$TEST_KEY.dump" "$TEST_KEY.dump.expected"
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-3"
rm $PWD/repos/foo.db
rosie delete -q -y foo-aa000 || exit 1
echo "2009-02-13T23:31:33.000000Z" >foo-date-4.txt
svnadmin setrevprop $PWD/repos/foo -r 4 svn:date foo-date-4.txt
run_pass "$TEST_KEY" $ROSE_HOME/sbin/rosa db-create
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] sqlite:///$PWD/repos/foo.db: DB created.
[INFO] $PWD/repos/foo: DB loaded, r4 of 4.
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
sqlite3 $PWD/repos/foo.db '.dump' >"$TEST_KEY.dump"
sed "s/\\\$USER/$USER/" "$TEST_SOURCE_DIR/$TEST_KEY.dump" >"$TEST_KEY.dump.expected"
file_cmp "$TEST_KEY.dump" "$TEST_KEY.dump" "$TEST_KEY.dump.expected"
#-------------------------------------------------------------------------------
