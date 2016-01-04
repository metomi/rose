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
# Test "rose suite-run --restart" does not re-initialise run directory.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 3

export ROSE_CONF_PATH=
cp -r $TEST_SOURCE_DIR/$TEST_KEY_BASE src
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -n $NAME --no-gcontrol -C src -- --debug
cat >'src/rose-suite.conf' <<__CONF__
root-dir=*=$PWD
__CONF__
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-restart"
run_pass "$TEST_KEY" \
    rose suite-run -q -n $NAME --no-gcontrol -C src --restart -- --debug
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-dir"
run_pass "$TEST_KEY" test -d "$SUITE_RUN_DIR" 
TEST_KEY="$TEST_KEY_BASE-symlink"
run_fail "$TEST_KEY" test -L "$SUITE_RUN_DIR" 
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit
