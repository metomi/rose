#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# -----------------------------------------------------------------------------
# Test "rosa svn-pre-commit" with invalid encoded config files.
# -----------------------------------------------------------------------------
. $(dirname $0)/test_header

export ROSE_CONF_PATH=
mkdir conf
cat > conf/rose.conf << '__ROSE_CONF__'
[rosa-svn-pre-commit]
super-users=rosie
__ROSE_CONF__
# -----------------------------------------------------------------------------
tests 3
# -----------------------------------------------------------------------------
mkdir repos
svnadmin create repos/foo
SVN_URL=file://$PWD/repos/foo
ROSE_BIN=$(dirname $(command -v rose))
ROSE_LIB=$(dirname $(python -c "import metomi.rose; print(metomi.rose.__file__)"))
export ROSE_LIB ROSE_BIN
cat > repos/foo/hooks/pre-commit << __PRE_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$PWD/conf
export PATH=$PATH:${ROSE_BIN}
export ROSE_LIB=${ROSE_LIB}
rosa svn-pre-commit "\$@"
__PRE_COMMIT__
chmod +x repos/foo/hooks/pre-commit
export LANG=C

TEST_KEY="${TEST_KEY_BASE}-western"
cat > rose-suite.info << '__INFO__'
owner=ivy
project=euro
title=We should not éñçödê config files in latin-1/western
__INFO__
iconv -f UTF-8 -t LATIN1 rose-suite.info -o rose-suite.info
# -----------------------------------------------------------------------------
run_fail "$TEST_KEY" \
    svn import rose-suite.info -q -m 't' --non-interactive \
    "${SVN_URL}/a/a/0/0/0/trunk/rose-suite.info"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" < /dev/null
sed -i '/^\[FAIL\]/!d' "$TEST_KEY.err"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" << '__ERR__'
[FAIL] Configuration files must be encoded in UTF-8 (or a subset of UTF-8). 'utf-8' codec can't decode byte 0xe9 in position 43: invalid continuation byte
__ERR__
