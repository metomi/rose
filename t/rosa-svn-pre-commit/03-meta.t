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
# Tests for "rosa svn-pre-commit", validate against configuration metadata.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
export ROSE_CONF_PATH=
mkdir -p 'conf' 'rose-meta/foolish/HEAD'
cat >'conf/rose.conf' <<__ROSE_CONF__
meta-path=${PWD}/rose-meta

[rosa-svn]
user-tool=passwd
__ROSE_CONF__
cat >'rose-meta/foolish/HEAD/rose-meta.conf' <<__ROSE_META_CONF__
[=bin]
compulsory=true
values=executable, garbage
__ROSE_META_CONF__
#-------------------------------------------------------------------------------
tests 10
#-------------------------------------------------------------------------------
mkdir 'repos'
svnadmin create 'repos/foo'
SVN_URL="file://${PWD}/repos/foo"
cat >'repos/foo/hooks/pre-commit' <<__PRE_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=${PWD}/conf
exec ${ROSE_HOME}/sbin/rosa svn-pre-commit "\$@"
__PRE_COMMIT__
chmod +x 'repos/foo/hooks/pre-commit'
export LANG='C'
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-basic-no-title"
cat >'rose-suite.info' <<__ROSE_SUITE_INFO__
project=whatever
owner=${USER}
__ROSE_SUITE_INFO__
run_fail "${TEST_KEY}" \
    svn import 'rose-suite.info' -q -m 't' --non-interactive \
    "${SVN_URL}/a/a/0/0/0/trunk/rose-suite.info"
sed -i '/^\[FAIL\]/!d' "${TEST_KEY}.err"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<'__ERR__'
[FAIL] BAD VALUE IN FILE: A   a/a/0/0/0/trunk/rose-suite.info:
[FAIL] a/a/0/0/0/trunk/rose-suite.info: issues: 1
[FAIL]     =title=None
[FAIL]         Variable set as compulsory, but not in configuration.
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-basic-good"
cat >'rose-suite.info' <<__ROSE_SUITE_INFO__
project=whatever
owner=${USER}
title=${TEST_KEY}
__ROSE_SUITE_INFO__
run_pass "${TEST_KEY}" \
    svn import 'rose-suite.info' -q -m 't' --non-interactive \
    "${SVN_URL}/a/a/0/0/0/trunk/rose-suite.info"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-foolish-no-bin"
cat >'rose-suite.info' <<__ROSE_SUITE_INFO__
project=foolish
owner=${USER}
title=${TEST_KEY}
__ROSE_SUITE_INFO__
run_fail "${TEST_KEY}" \
    svn import 'rose-suite.info' -q -m 't' --non-interactive \
    "${SVN_URL}/a/a/0/0/1/trunk/rose-suite.info"
sed -i '/^\[FAIL\]/!d' "${TEST_KEY}.err"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<'__ERR__'
[FAIL] BAD VALUE IN FILE: A   a/a/0/0/1/trunk/rose-suite.info:
[FAIL] a/a/0/0/1/trunk/rose-suite.info: issues: 1
[FAIL]     =bin=None
[FAIL]         Variable set as compulsory, but not in configuration.
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-foolish-bad-items-in-bin"
cat >'rose-suite.info' <<__ROSE_SUITE_INFO__
project=foolish
owner=${USER}
title=${TEST_KEY}
bin=cat
__ROSE_SUITE_INFO__
run_fail "${TEST_KEY}" \
    svn import 'rose-suite.info' -q -m 't' --non-interactive \
    "${SVN_URL}/a/a/0/0/1/trunk/rose-suite.info"
sed -i '/^\[FAIL\]/!d' "${TEST_KEY}.err"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <<'__ERR__'
[FAIL] BAD VALUE IN FILE: A   a/a/0/0/1/trunk/rose-suite.info:
[FAIL] a/a/0/0/1/trunk/rose-suite.info: issues: 1
[FAIL]     =bin=cat
[FAIL]         Value cat not in allowed values ['executable', 'garbage']
__ERR__
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-foolish-good"
cat >'rose-suite.info' <<__ROSE_SUITE_INFO__
project=foolish
owner=${USER}
title=${TEST_KEY}
bin=executable
__ROSE_SUITE_INFO__
run_pass "${TEST_KEY}" \
    svn import 'rose-suite.info' -q -m 't' --non-interactive \
    "${SVN_URL}/a/a/0/0/1/trunk/rose-suite.info"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
#-------------------------------------------------------------------------------
exit 0
