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
# Test "rose suite-run" when port file exists.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/.cylc/ports
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
touch $HOME/.cylc/ports/$NAME
run_fail "$TEST_KEY" \
    rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] Suite "$NAME" may still be running.
[FAIL] Host "localhost" has port-file:
[FAIL]     ~$USER/.cylc/ports/$NAME
[FAIL] Try "rose suite-shutdown --name=$NAME" first?
__ERR__
#-------------------------------------------------------------------------------
rm $HOME/.cylc/ports/$NAME
rose suite-clean -q -y $NAME
exit 0
