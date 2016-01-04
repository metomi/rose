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
# Test "rose suite-run", file install targets overlap.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 3
export ROSE_CONF_PATH=

mkdir -p src
echo 'yummie' >src/bacon.txt

mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
export TEST_DIR
run_pass "$TEST_KEY-1" rose suite-run \
    -n $NAME --no-gcontrol -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -i
run_pass "$TEST_KEY-2" rose suite-run \
    -n $NAME --no-gcontrol -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -i
(cd $SUITE_RUN_DIR/etc; find -type f) | LANG=C sort >"$TEST_KEY.find"
file_cmp "$TEST_KEY.find" "$TEST_KEY.find" <<'__FIND__'
./foo/bar/baz/bacon.txt
./foo/bar/egg/humpty.txt
__FIND__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit
