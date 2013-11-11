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
# Test "rose suite-run", modification of the suite run root directory.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
N_TESTS=4
tests $N_TESTS
#-------------------------------------------------------------------------------
if [[ -z $TMPDIR || -z $USER || $TMPDIR/$USER == $HOME ]]; then
    skip $N_TESTS "TMPDIR or USER not defined or TMPDIR/USER is HOME"
    exit 0
fi
#-------------------------------------------------------------------------------
# Start the suite
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
export ROOT_DIR=$TMPDIR/$USER
run_pass "$TEST_KEY" rose suite-run \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -n $NAME \
    -i --no-gcontrol
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-root-symlink"
if [[ -L $HOME/cylc-run/$NAME && \
      $(readlink $HOME/cylc-run/$NAME) == $ROOT_DIR/cylc-run/$NAME ]]
then
    pass "$TEST_KEY"
else
    fail "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-clean"
run_pass "$TEST_KEY" rose suite-clean -y $NAME
if [[ -e $HOME/cylc-run/$NAME || -e $ROOT_DIR/cylc-run/$NAME ]]; then
    fail "$TEST_KEY"
else
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
exit 0
