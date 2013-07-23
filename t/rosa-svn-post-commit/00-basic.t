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
# Basic tests for "rosa svn-post-commit".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 45
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
$ROSE_HOME/sbin/rosa db-create -q || exit 1
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-create"
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=ivy
project=hook
title=test post commit hook: create
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|hook|test post commit hook: create
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-copy-empty"
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=ivy
project=hook
title=test post commit hook: copy empty
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout foo-aa000
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|hook|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-edit"
rosie checkout -q foo-aa000
cat >$PWD/roses/foo-aa000/rose-suite.conf <<'__ROSE_SUITE_CONF__'
[env]
HELLO=world
__ROSE_SUITE_CONF__
mkdir -p $PWD/roses/foo-aa000/app/hello
cat >$PWD/roses/foo-aa000/app/hello/rose-app.conf <<'__ROSE_APP_CONF__'
[command]
echo $HELLO

[env]
HELLO=earth
__ROSE_APP_CONF__
svn add -q $PWD/roses/foo-aa000/app
svn commit -q -m 't' $PWD/roses/foo-aa000
svn up -q $PWD/roses/foo-aa000
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|hook|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-edit-info"
#rosie checkout -q foo-aa000
sed -i 's/project=hook/project=sticky/' $PWD/roses/foo-aa000/rose-suite.info
svn commit -q -m 't' $PWD/roses/foo-aa000
svn up -q $PWD/roses/foo-aa000
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|sticky|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-copy-suite-with-content"
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=ivy
project=sticky tape
title=test post commit hook: copy suite with content
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout foo-aa000
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|sticky|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
foo-aa002|trunk|ivy|sticky tape|test post commit hook: copy suite with content
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-meta"
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=rosie
project=meta
title=configuration metadata for discovery information
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout --meta-suite
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|sticky|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
foo-aa002|trunk|ivy|sticky tape|test post commit hook: copy suite with content
foo-ROSIE|trunk|rosie|meta|configuration metadata for discovery information
__OUT__
sqlite3 $PWD/repos/foo.db 'SELECT * FROM meta' >"$TEST_KEY-db-select.out" \
    || exit 1
file_cmp "$TEST_KEY-db-select-meta.out" "$TEST_KEY-db-select.out" <<'__OUT__'
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-meta-edit"
rosie checkout -q foo-ROSIE || exit 1
echo 'world galaxy universe' >$PWD/roses/foo-ROSIE/rosie-keys
svn add -q $PWD/roses/foo-ROSIE/rosie-keys || exit 1
svn ci -q -m t $PWD/roses/foo-ROSIE || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM meta' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select.out" "$TEST_KEY-db-select.out" <<'__OUT__'
known_keys|world galaxy universe
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-branch"
svn cp -m t -q $SVN_URL/a/a/0/0/0/trunk $SVN_URL/a/a/0/0/0/hello || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|sticky|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
foo-aa002|trunk|ivy|sticky tape|test post commit hook: copy suite with content
foo-ROSIE|trunk|rosie|meta|configuration metadata for discovery information
foo-aa000|hello|ivy|sticky|test post commit hook: create
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-branch-update"
#rosie checkout -q foo-aa000
svn switch -q $SVN_URL/a/a/0/0/0/hello $PWD/roses/foo-aa000 || exit 1
sed -i 's/^title=.*$/title=test post commit hook: branch update/' \
    $PWD/roses/foo-aa000/rose-suite.info || exit 1
svn ci -q -m t $PWD/roses/foo-aa000
svn switch -q $SVN_URL/a/a/0/0/0/trunk $PWD/roses/foo-aa000 || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db 'SELECT * FROM main' >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-main.out" "$TEST_KEY-db-select.out" <<'__OUT__'
foo-aa000|trunk|ivy|sticky|test post commit hook: create
foo-aa001|trunk|ivy|hook|test post commit hook: copy empty
foo-aa002|trunk|ivy|sticky tape|test post commit hook: copy suite with content
foo-ROSIE|trunk|rosie|meta|configuration metadata for discovery information
foo-aa000|hello|ivy|sticky|test post commit hook: branch update
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-branch-delete"
svn rm -q -m t $SVN_URL/a/a/0/0/0/hello || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db \
    'SELECT status,idx,branch FROM changeset
         WHERE idx=="foo-aa000" AND status=="D "' \
    >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-changeset.out" "$TEST_KEY-db-select.out" <<'__OUT__'
D |foo-aa000|hello
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-suite-delete"
svn rm -q -m t $SVN_URL/a/a/0/0/0 || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0
sqlite3 $PWD/repos/foo.db \
    'SELECT status,idx,branch FROM changeset
        WHERE idx=="foo-aa000" AND status=="D "' \
    >"$TEST_KEY-db-select.out"
file_cmp "$TEST_KEY-db-select-changeset.out" "$TEST_KEY-db-select.out" <<'__OUT__'
D |foo-aa000|hello
D |foo-aa000|trunk
__OUT__
#-------------------------------------------------------------------------------
exit 0
