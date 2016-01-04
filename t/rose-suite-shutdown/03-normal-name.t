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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
set -e
#-------------------------------------------------------------------------------
tests 1
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol
HOST=$(<$SUITE_RUN_DIR/log/rose-suite-run.host)
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
mkdir -p "$TEST_KEY/$NAME"
ln -s $TEST_SOURCE_DIR/$TEST_KEY_BASE/rose-suite.conf $TEST_KEY/$NAME/
cd "$TEST_KEY/$NAME"
run_pass "$TEST_KEY" rose suite-stop -y -- --max-polls=12 --interval=5
cd $OLDPWD
#-------------------------------------------------------------------------------
sleep 1
rose suite-clean -q -y $NAME
exit 0
