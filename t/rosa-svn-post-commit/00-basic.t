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
# Test "rosa svn-post-commit": Rosie WS DB update.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! python3 -c 'import sqlalchemy' 2>/dev/null; then
    skip_all '"sqlalchemy" not installed'
fi
tests 71
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
Q_LATEST='SELECT * FROM latest'
Q_MAIN='SELECT idx,branch,revision,owner,project,title,author,status,from_idx FROM main'
Q_META='SELECT * FROM meta'
Q_OPTIONAL='SELECT * FROM optional'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-create"
cat >rose-suite.info <<'__ROSE_SUITE_INFO'
access-list=*
owner=ivy
project=hook
sub-project=post-commit
title=test post commit hook: create
__ROSE_SUITE_INFO
rosie create -q -y --info-file=rose-suite.info --no-checkout
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa000|trunk|1
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
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

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa001'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa001|trunk|2|ivy|hook|test post commit hook: copy empty|$LOGNAME|A |foo-aa000
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa001'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa001|trunk|2
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa001'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa001|trunk|2|access-list|*
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

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|3|ivy|hook|test post commit hook: create|$LOGNAME|M |
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa000|trunk|3
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
foo-aa000|trunk|3|access-list|*
foo-aa000|trunk|3|sub-project|post-commit
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-edit-info"
#rosie checkout -q foo-aa000
sed -i 's/project=hook/project=sticky/' $PWD/roses/foo-aa000/rose-suite.info
sed -i '/^sub-project=/d' $PWD/roses/foo-aa000/rose-suite.info
echo "description=adhesive" >> $PWD/roses/foo-aa000/rose-suite.info
svn commit -q -m 't' $PWD/roses/foo-aa000
svn up -q $PWD/roses/foo-aa000
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|3|ivy|hook|test post commit hook: create|$LOGNAME|M |
foo-aa000|trunk|4|ivy|sticky|test post commit hook: create|$LOGNAME| M|
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa000|trunk|4
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
foo-aa000|trunk|3|access-list|*
foo-aa000|trunk|3|sub-project|post-commit
foo-aa000|trunk|4|access-list|*
foo-aa000|trunk|4|description|adhesive
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

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa002'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa002|trunk|5|ivy|sticky tape|test post commit hook: copy suite with content|$LOGNAME|A |foo-aa000
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa002'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa002|trunk|5
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa002'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa002|trunk|5|access-list|*
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

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-ROSIE'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-ROSIE|trunk|6|rosie|meta|configuration metadata for discovery information|$LOGNAME|A |
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_META" >"$TEST_KEY-meta.out" || exit 1
file_cmp "$TEST_KEY-meta.out" "$TEST_KEY-meta.out" </dev/null
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-ROSIE'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-ROSIE|trunk|6
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-ROSIE'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-ROSIE|trunk|6|access-list|*
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

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-ROSIE'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-ROSIE|trunk|6|rosie|meta|configuration metadata for discovery information|$LOGNAME|A |
foo-ROSIE|trunk|7|rosie|meta|configuration metadata for discovery information|$LOGNAME|M |
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_META" >"$TEST_KEY-meta.out"
file_cmp "$TEST_KEY-meta.out" "$TEST_KEY-meta.out" <<'__OUT__'
known_keys|world galaxy universe
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-ROSIE'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-ROSIE|trunk|7
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-ROSIE'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-ROSIE|trunk|6|access-list|*
foo-ROSIE|trunk|7|access-list|*
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-branch"
svn cp -m t -q $SVN_URL/a/a/0/0/0/trunk $SVN_URL/a/a/0/0/0/hello || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|hello|8|ivy|sticky|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|3|ivy|hook|test post commit hook: create|$LOGNAME|M |
foo-aa000|trunk|4|ivy|sticky|test post commit hook: create|$LOGNAME| M|
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa000|hello|8
foo-aa000|trunk|4
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|hello|8|access-list|*
foo-aa000|hello|8|description|adhesive
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
foo-aa000|trunk|3|access-list|*
foo-aa000|trunk|3|sub-project|post-commit
foo-aa000|trunk|4|access-list|*
foo-aa000|trunk|4|description|adhesive
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-branch-update"
#rosie checkout -q foo-aa000
svn switch -q $SVN_URL/a/a/0/0/0/hello $PWD/roses/foo-aa000 || exit 1
sed -i 's/^title=.*$/title=test post commit hook: branch update/' \
    $PWD/roses/foo-aa000/rose-suite.info || exit 1
sed -i 's/^description=.*$/sub-title=This tests a branch update of the hook/'\
    $PWD/roses/foo-aa000/rose-suite.info || exit 1
svn ci -q -m t $PWD/roses/foo-aa000
svn switch -q $SVN_URL/a/a/0/0/0/trunk $PWD/roses/foo-aa000 || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|hello|8|ivy|sticky|test post commit hook: create|$LOGNAME|A |
foo-aa000|hello|9|ivy|sticky|test post commit hook: branch update|$LOGNAME| M|
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|3|ivy|hook|test post commit hook: create|$LOGNAME|M |
foo-aa000|trunk|4|ivy|sticky|test post commit hook: create|$LOGNAME| M|
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa000|hello|9
foo-aa000|trunk|4
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|hello|8|access-list|*
foo-aa000|hello|8|description|adhesive
foo-aa000|hello|9|access-list|*
foo-aa000|hello|9|sub-title|This tests a branch update of the hook
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
foo-aa000|trunk|3|access-list|*
foo-aa000|trunk|3|sub-project|post-commit
foo-aa000|trunk|4|access-list|*
foo-aa000|trunk|4|description|adhesive
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-branch-delete"
svn rm -q -m t $SVN_URL/a/a/0/0/0/hello || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|hello|8|ivy|sticky|test post commit hook: create|$LOGNAME|A |
foo-aa000|hello|9|ivy|sticky|test post commit hook: branch update|$LOGNAME| M|
foo-aa000|hello|10|ivy|sticky|test post commit hook: branch update|$LOGNAME|D |
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|3|ivy|hook|test post commit hook: create|$LOGNAME|M |
foo-aa000|trunk|4|ivy|sticky|test post commit hook: create|$LOGNAME| M|
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" <<'__OUT__'
foo-aa000|trunk|4
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|hello|8|access-list|*
foo-aa000|hello|8|description|adhesive
foo-aa000|hello|9|access-list|*
foo-aa000|hello|9|sub-title|This tests a branch update of the hook
foo-aa000|hello|10|access-list|*
foo-aa000|hello|10|sub-title|This tests a branch update of the hook
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
foo-aa000|trunk|3|access-list|*
foo-aa000|trunk|3|sub-project|post-commit
foo-aa000|trunk|4|access-list|*
foo-aa000|trunk|4|description|adhesive
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-suite-delete"
svn rm -q -m t $SVN_URL/a/a/0/0/0 || exit 1
file_cmp "$TEST_KEY-hook.out" $PWD/rosa-svn-post-commit.out </dev/null
file_cmp "$TEST_KEY-hook.err" $PWD/rosa-svn-post-commit.err </dev/null
file_cmp "$TEST_KEY-hook.rc" $PWD/rosa-svn-post-commit.rc <<<0

TEST_KEY="$TEST_KEY-db-select"
sqlite3 $PWD/repos/foo.db "$Q_MAIN WHERE idx=='foo-aa000'" >"$TEST_KEY-main.out"
file_cmp "$TEST_KEY-main.out" "$TEST_KEY-main.out" <<__OUT__
foo-aa000|hello|8|ivy|sticky|test post commit hook: create|$LOGNAME|A |
foo-aa000|hello|9|ivy|sticky|test post commit hook: branch update|$LOGNAME| M|
foo-aa000|hello|10|ivy|sticky|test post commit hook: branch update|$LOGNAME|D |
foo-aa000|trunk|1|ivy|hook|test post commit hook: create|$LOGNAME|A |
foo-aa000|trunk|3|ivy|hook|test post commit hook: create|$LOGNAME|M |
foo-aa000|trunk|4|ivy|sticky|test post commit hook: create|$LOGNAME| M|
foo-aa000|trunk|11|ivy|sticky|test post commit hook: create|$LOGNAME|D |
__OUT__
sqlite3 $PWD/repos/foo.db "$Q_LATEST WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-latest.out"
file_cmp "$TEST_KEY-latest.out" "$TEST_KEY-latest.out" </dev/null
sqlite3 $PWD/repos/foo.db "$Q_OPTIONAL WHERE idx=='foo-aa000'" \
    >"$TEST_KEY-optional.out"
file_cmp "$TEST_KEY-optional.out" "$TEST_KEY-optional.out" <<'__OUT__'
foo-aa000|hello|8|access-list|*
foo-aa000|hello|8|description|adhesive
foo-aa000|hello|9|access-list|*
foo-aa000|hello|9|sub-title|This tests a branch update of the hook
foo-aa000|hello|10|access-list|*
foo-aa000|hello|10|sub-title|This tests a branch update of the hook
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|sub-project|post-commit
foo-aa000|trunk|3|access-list|*
foo-aa000|trunk|3|sub-project|post-commit
foo-aa000|trunk|4|access-list|*
foo-aa000|trunk|4|description|adhesive
foo-aa000|trunk|11|access-list|*
foo-aa000|trunk|11|description|adhesive
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-suite-add-file-at-branch-level"
echo 'Not much stuff' >'null'
svn import -q -m t 'null' "${SVN_URL}/a/a/0/0/1/null" || exit 1
file_cmp "${TEST_KEY}-hook.out" "${PWD}/rosa-svn-post-commit.out" <'/dev/null'
file_cmp "${TEST_KEY}-hook.err" "${PWD}/rosa-svn-post-commit.err" <'/dev/null'
file_cmp "${TEST_KEY}-hook.rc" "${PWD}/rosa-svn-post-commit.rc" <<<0
#-------------------------------------------------------------------------------
exit 0
