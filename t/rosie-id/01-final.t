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
# "rosie id --next" on the final ID in a repository.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
svnadmin create foo
URL=file://$PWD/foo
cat >rose.conf <<__ROSE_CONF__
[rosie-id]
prefix-default=foo
prefix-location.foo=$URL
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD
#-------------------------------------------------------------------------------
mkdir src
touch src/rose-suite.conf
cat >src/rose-suite.info <<__INFO__
access-list=*
owner=$USER
project=rose tea
title=Identify the final ultimate rose tea in the world
__INFO__
svn import -q -m 'zz999: import' src $URL/z/z/9/9/9/trunk
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_fail "$TEST_KEY" rosie id --next
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] foo-zz999: cannot increment ID
__ERR__
#-------------------------------------------------------------------------------
exit 0
