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
# Test "rosa svn-post-commit": Discovery Service database update with unicode.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
if ! python3 -c 'import sqlalchemy' 2>'/dev/null'; then
    skip_all '"sqlalchemy" not installed'
fi
tests 10
#-------------------------------------------------------------------------------
set -e
mkdir 'repos'
svnadmin create 'repos/foo'
SVN_URL="file://${PWD}/repos/foo"
mkdir 'conf'
cat >'conf/rose.conf' <<__ROSE_CONF__
[rosie-db]
repos.foo=${PWD}/repos/foo
db.foo=sqlite:///${PWD}/repos/foo.db
[rosie-id]
local-copy-root=${PWD}/roses
prefix-default=foo
prefix-owner-default.foo=fred
prefix-location.foo=${SVN_URL}
__ROSE_CONF__
export ROSE_CONF_PATH="${PWD}/conf"
cat >'repos/foo/hooks/post-commit' <<__POST_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH="${ROSE_CONF_PATH}"
'${ROSE_HOME}/sbin/rosa' 'svn-post-commit' --debug "\$@" \\
    1>'${PWD}/rosa-svn-post-commit.out' 2>'${PWD}/rosa-svn-post-commit.err'
echo "\$?" >'${PWD}/rosa-svn-post-commit.rc'
__POST_COMMIT__
chmod +x 'repos/foo/hooks/post-commit'
export LANG='C'
"${ROSE_HOME}/sbin/rosa" 'db-create' -q
set +e

Q_MAIN='SELECT idx,branch,revision,owner,project,title,author,status,from_idx FROM main'
Q_OPTIONAL='SELECT * FROM optional'
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-create"
cat >'rose-suite.info' <<'__ROSE_SUITE_INFO'
access-list=*
owner=ivy
project=euro
title=The euro symbol € requires unicode
more-title=We may lose € if we can't handle unicode
!whatever=
__ROSE_SUITE_INFO
rosie create -q -y --info-file='rose-suite.info'
file_cmp "${TEST_KEY}-hook.out" "${PWD}/rosa-svn-post-commit.out" <'/dev/null'
file_cmp "${TEST_KEY}-hook.err" "${PWD}/rosa-svn-post-commit.err" <'/dev/null'
file_cmp "${TEST_KEY}-hook.rc" "${PWD}/rosa-svn-post-commit.rc" <<<'0'

TEST_KEY="${TEST_KEY}-db-select"
sqlite3 "${PWD}/repos/foo.db" "${Q_MAIN} WHERE idx=='foo-aa000'" \
    >"${TEST_KEY}-main.out"
file_cmp "${TEST_KEY}-main.out" "${TEST_KEY}-main.out" <<__OUT__
foo-aa000|trunk|1|ivy|euro|The euro symbol € requires unicode|${USER}|A |
__OUT__
sqlite3 "${PWD}/repos/foo.db" "${Q_OPTIONAL} WHERE idx=='foo-aa000'" \
    >"${TEST_KEY}-optional.out"
file_cmp "${TEST_KEY}-optional.out" "${TEST_KEY}-optional.out" <<'__OUT__'
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|more-title|We may lose € if we can't handle unicode
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-modify"
cat >"${PWD}/roses/foo-aa000/rose-suite.info" <<'__ROSE_SUITE_INFO'
access-list=*
owner=ivy
project=euro
title=Euro symbol € requires unicode
more-title=We will lose € if we can't handle unicode
!whatever=
__ROSE_SUITE_INFO
set -e
svn commit -q -m 't' "${PWD}/roses/foo-aa000"
svn update -q "${PWD}/roses/foo-aa000"
set +e
file_cmp "${TEST_KEY}-hook.out" "${PWD}/rosa-svn-post-commit.out" <'/dev/null'
file_cmp "${TEST_KEY}-hook.err" "${PWD}/rosa-svn-post-commit.err" <'/dev/null'
file_cmp "${TEST_KEY}-hook.rc" "${PWD}/rosa-svn-post-commit.rc" <<<'0'

TEST_KEY="${TEST_KEY}-db-select"
sqlite3 "${PWD}/repos/foo.db" "${Q_MAIN} WHERE idx=='foo-aa000'" \
    >"${TEST_KEY}-main.out"
file_cmp "${TEST_KEY}-main.out" "${TEST_KEY}-main.out" <<__OUT__
foo-aa000|trunk|1|ivy|euro|The euro symbol € requires unicode|${USER}|A |
foo-aa000|trunk|2|ivy|euro|Euro symbol € requires unicode|${USER}| M|
__OUT__
sqlite3 "${PWD}/repos/foo.db" "${Q_OPTIONAL} WHERE idx=='foo-aa000'" \
    >"${TEST_KEY}-optional.out"
file_cmp "${TEST_KEY}-optional.out" "${TEST_KEY}-optional.out" <<'__OUT__'
foo-aa000|trunk|1|access-list|*
foo-aa000|trunk|1|more-title|We may lose € if we can't handle unicode
foo-aa000|trunk|2|access-list|*
foo-aa000|trunk|2|more-title|We will lose € if we can't handle unicode
__OUT__
#-------------------------------------------------------------------------------
exit 0
