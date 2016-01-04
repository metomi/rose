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
# Basic tests for "rosa svn-pre-commit".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=
mkdir conf
cat >conf/rose.conf <<'__ROSE_CONF__'
[rosa-svn-pre-commit]
super-users=rosie
__ROSE_CONF__
#-------------------------------------------------------------------------------
tests 114
#-------------------------------------------------------------------------------
mkdir repos
svnadmin create repos/foo
SVN_URL=file://$PWD/repos/foo
cat >repos/foo/hooks/pre-commit <<__PRE_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$PWD/conf
exec $ROSE_HOME/sbin/rosa svn-pre-commit "\$@"
__PRE_COMMIT__
chmod +x repos/foo/hooks/pre-commit
export LANG=C
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-bad-1
run_fail "$TEST_KEY" \
    svn mkdir --parents -q -m 't' --non-interactive $SVN_URL/a/b/c/d/e
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: A   a/b/c/
[FAIL] PERMISSION DENIED: A   a/b/c/d/
[FAIL] PERMISSION DENIED: A   a/b/c/d/e/
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-bad-2
run_fail "$TEST_KEY" \
    svn mkdir --parents -q -m 't' --non-interactive $SVN_URL/1/2/3/4/5
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: A   1/
[FAIL] PERMISSION DENIED: A   1/2/
[FAIL] PERMISSION DENIED: A   1/2/3/
[FAIL] PERMISSION DENIED: A   1/2/3/4/
[FAIL] PERMISSION DENIED: A   1/2/3/4/5/
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-bad-n-levels
run_fail "$TEST_KEY" \
    svn mkdir --parents -q -m 't' --non-interactive $SVN_URL/a/a/0/0/0/0
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE TRUNK: A   a/a/0/0/0/
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-no-info
run_fail "$TEST_KEY" \
    svn mkdir --parents -q -m 't' --non-interactive $SVN_URL/a/a/0/0/0/trunk
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE INFO FILE: A   a/a/0/0/0/
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-empty-info
cat </dev/null >rose-suite.info
run_fail "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE OWNER: A   a/a/0/0/0/trunk/rose-suite.info
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-empty-owner
cat >rose-suite.info <<'__ROSE_SUITE_INFO__'
owner=
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE OWNER: A   a/a/0/0/0/trunk/rose-suite.info
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-good-1
cat >rose-suite.info <<__ROSE_SUITE_INFO__
owner=daisy
project=rose
title=${TEST_KEY}
__ROSE_SUITE_INFO__
run_pass "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/
A   a/a/
A   a/a/0/
A   a/a/0/0/
A   a/a/0/0/0/
A   a/a/0/0/0/trunk/
A   a/a/0/0/0/trunk/rose-suite.info
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-branch
run_pass "$TEST_KEY" \
    svn cp -q -m't' $SVN_URL/a/a/0/0/0/trunk $SVN_URL/a/a/0/0/0/hello
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/a/0/0/0/hello/
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-create-branch-anyone
run_pass "$TEST_KEY" \
    svn cp -q -m't' --username=lily \
    $SVN_URL/a/a/0/0/0/trunk $SVN_URL/a/a/0/0/0/hello2
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/a/0/0/0/hello2/
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-add-to-branch-anyone
mkdir work
svn co -q $SVN_URL/a/a/0/0/0/hello work/aa000
echo 'project=gardening' >work/aa000/rose-suite.conf
svn add -q work/aa000/rose-suite.conf
run_pass "$TEST_KEY" svn ci -q -m't' --username=lily work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/hello/rose-suite.conf >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.conf
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-branch-anyone
echo 'title=gardening is fun' >>work/aa000/rose-suite.conf
run_pass "$TEST_KEY" svn ci -q -m't' --username=lily work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/hello/rose-suite.conf >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.conf
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-delete-branch-anyone
run_pass "$TEST_KEY" svn rm -q -m't' --username=lily $SVN_URL/a/a/0/0/0/hello
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
D   a/a/0/0/0/hello/
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-delete-owner
svn sw -q $SVN_URL/a/a/0/0/0/trunk work/aa000
sed -i '/owner=/d' work/aa000/rose-suite.info
run_fail "$TEST_KEY" svn ci -q -m't' --username=daisy work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE OWNER: U   a/a/0/0/0/trunk/rose-suite.info
__ERR__
svn revert -q -R work/aa000
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-delete-info
svn rm -q work/aa000/rose-suite.info
run_fail "$TEST_KEY" svn ci -q -m't' --username=daisy work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE INFO FILE: D   a/a/0/0/0/trunk/rose-suite.info
__ERR__
svn revert -q -R work/aa000
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-delete-trunk
run_fail "$TEST_KEY" svn rm -q -m't' --username=daisy $SVN_URL/a/a/0/0/0/trunk
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] SUITE MUST HAVE TRUNK: D   a/a/0/0/0/trunk/
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-chown
sed -i 's/daisy/rosemary/' work/aa000/rose-suite.info
run_fail "$TEST_KEY" svn ci --username=rosemary -q -m't' work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info
__ERR__
svn revert -q -R work/aa000
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-chown
sed -i 's/daisy/rosemary/' work/aa000/rose-suite.info
run_pass "$TEST_KEY" svn ci --username=daisy -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/trunk/rose-suite.info >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.info
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-access-add
touch work/aa000/rose-suite.conf
svn add -q work/aa000/rose-suite.conf
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: A   a/a/0/0/0/trunk/rose-suite.conf
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-access-add
run_pass "$TEST_KEY" svn ci --username=rosemary -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
A   a/a/0/0/0/trunk/rose-suite.conf
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-access-modify
cat >work/aa000/rose-suite.conf <<'__ROSE_SUITE_CONF__'
[env]
HELLO=world
__ROSE_SUITE_CONF__
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.conf
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-access-modify
run_pass "$TEST_KEY" svn ci --username=rosemary -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/trunk/rose-suite.conf >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.conf
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-access-delete
svn rm -q work/aa000/rose-suite.conf
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: D   a/a/0/0/0/trunk/rose-suite.conf
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-access-delete
svn rm -q work/aa000/rose-suite.conf
run_pass "$TEST_KEY" svn ci --username=rosemary -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
D   a/a/0/0/0/trunk/rose-suite.conf
__CHANGED__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-access-list-mod
echo 'access-list=*' >>work/aa000/rose-suite.info
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-access-list-mod
run_pass "$TEST_KEY" svn ci --username=rosemary -q -m't' work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/trunk/rose-suite.info >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.info
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-access-list-mod-2
echo 'access-list=fred' >>work/aa000/rose-suite.info
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
svn revert -q -R work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: access-list=fred
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-chown-2
echo 'owner=fred' >>work/aa000/rose-suite.info
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
svn revert -q -R work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.info: owner=fred
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-access-star-mod-anyone
cat >>work/aa000/rose-suite.conf <<'__ROSE_SUITE_CONF__'
[env]
GREET=fred
__ROSE_SUITE_CONF__
svn add -q work/aa000/rose-suite.conf
run_pass "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/trunk/rose-suite.conf >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.conf
#-------------------------------------------------------------------------------
# Make access-list more restrictive
sed -i 's/^\(access-list=\).*$/\1jasmine lily/' work/aa000/rose-suite.info
svn ci --username=rosemary -q -m't' work/aa000 || exit 1
svn up -q work/aa000
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-modify-with-access-list
cat >>work/aa000/rose-suite.conf <<'__ROSE_SUITE_CONF__'
[env]
GREET=fred's friend
__ROSE_SUITE_CONF__
run_fail "$TEST_KEY" svn ci --username=fred -q -m't' work/aa000
svn revert -q -R work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: U   a/a/0/0/0/trunk/rose-suite.conf
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-with-access-list
sed -i 's/^\(GREET=\).*$/\1plant kingdom/' work/aa000/rose-suite.conf
run_pass "$TEST_KEY" svn ci --username=lily -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/trunk/rose-suite.conf >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.conf
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-owner-by-super-user
sed -i 's/^\(owner=\).*$/\1jasmine/' work/aa000/rose-suite.info
run_pass "$TEST_KEY" svn ci --username=rosie -q -m't' work/aa000
svn up -q work/aa000
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook cat repos/foo a/a/0/0/0/trunk/rose-suite.info >"$TEST_KEY.cat"
file_cmp "$TEST_KEY.cat" "$TEST_KEY.cat" work/aa000/rose-suite.info
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-delete-suite-by-non-owner
run_fail "$TEST_KEY" svn rm --username=rosemary -q -m't' $SVN_URL/a/a/0/0/0
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] PERMISSION DENIED: D   a/a/0/0/0/
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-delete-suite
run_pass "$TEST_KEY" svn rm --username=jasmine -q -m't' $SVN_URL/a/a/0/0/0
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
svnlook changed repos/foo >"$TEST_KEY.changed"
file_cmp "$TEST_KEY.changed" "$TEST_KEY.changed" <<'__CHANGED__'
D   a/a/0/0/0/
__CHANGED__
#-------------------------------------------------------------------------------
exit 0
