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
# Tests for "rosa svn-pre-commit", Unix passwd user check.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=
mkdir conf
cat >conf/rose.conf <<'__ROSE_CONF__'
[rosa-svn]
super-users=rosie
user-tool=passwd
__ROSE_CONF__
#-------------------------------------------------------------------------------
tests 13
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
TEST_KEY=$TEST_KEY_BASE-bad-owner
cat >rose-suite.info <<'__ROSE_SUITE_INFO__'
project=rose
title=${TEST_KEY}
owner=no-such-user-550
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] NO SUCH USER: A   a/a/0/0/0/trunk/rose-suite.info: owner=no-such-user-550
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-bad-access-list
cat >rose-suite.info <<__ROSE_SUITE_INFO__
project=rose
title=${TEST_KEY}
owner=$USER
access-list=no-such-user-550
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] NO SUCH USER: A   a/a/0/0/0/trunk/rose-suite.info: access-list=no-such-user-550
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-good-owner
cat >rose-suite.info <<__ROSE_SUITE_INFO__
project=rose
title=${TEST_KEY}
owner=$USER
access-list=*
__ROSE_SUITE_INFO__
run_pass "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    $SVN_URL/a/a/0/0/0/trunk/rose-suite.info
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-bad-owner
svn co -q $SVN_URL/a/a/0/0/0/trunk aa000
cat >aa000/rose-suite.info <<'__ROSE_SUITE_INFO__'
project=rose
title=${TEST_KEY}
owner=no-such-user-550
access-list=*
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" svn commit -q -m 't' --non-interactive aa000
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] NO SUCH USER: U   a/a/0/0/0/trunk/rose-suite.info: owner=no-such-user-550
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-bad-owner
#svn co -q $SVN_URL/a/a/0/0/0/trunk aa000
cat >aa000/rose-suite.info <<__ROSE_SUITE_INFO__
project=rose
title=${TEST_KEY}
owner=$USER
access-list=no-such-user-550
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" svn commit -q -m 't' --non-interactive aa000
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] NO SUCH USER: U   a/a/0/0/0/trunk/rose-suite.info: access-list=no-such-user-550
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-modify-bad-owner-2
#svn co -q $SVN_URL/a/a/0/0/0/trunk aa000
cat >aa000/rose-suite.info <<__ROSE_SUITE_INFO__
project=rose
title=${TEST_KEY}
owner=$USER
access-list=no-such-user-550 root no-such-user-551
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" svn commit -q -m 't' --non-interactive aa000
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] NO SUCH USER: U   a/a/0/0/0/trunk/rose-suite.info: access-list=no-such-user-550
[FAIL] NO SUCH USER: U   a/a/0/0/0/trunk/rose-suite.info: access-list=no-such-user-551
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-copy-with-bad-owner"
svn co -q "${SVN_URL}/a/a/0/0/" 'aa00'
svn mkdir -q 'aa00/1'
svn cp -q 'aa00/0/trunk' 'aa00/1/'
cat >'aa00/1/trunk/rose-suite.info' <<'__ROSE_SUITE_INFO__'
project=rose
title=${TEST_KEY}
owner=no-such-user-550
access-list=*
__ROSE_SUITE_INFO__
run_fail "$TEST_KEY" svn commit -q -m 't' --non-interactive 'aa00/1'
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] NO SUCH USER: U   a/a/0/0/1/trunk/rose-suite.info: owner=no-such-user-550
__ERR__
#-------------------------------------------------------------------------------
exit 0
