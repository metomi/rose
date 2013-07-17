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
# Test "rose suite-clean", while the suite is running.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
# Install suite, and prove that directories are created
rose suite-run --debug \
    -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME --no-gcontrol 1>/dev/null
ls -ld $HOME/cylc-run/$NAME 1>/dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-running
run_fail "$TEST_KEY" rose suite-clean -y $NAME
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] $NAME: cannot clean, still running on localhost
__ERR__
if [[ ! -d $HOME/cylc-run/$NAME ]]; then
    exit 1
fi
#-------------------------------------------------------------------------------
touch $SUITE_RUN_DIR/flag # let the suite stop
# Wait for the suite to complete
TIMEOUT=$(($(date +%s) + 120)) # wait 2 minutes
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    exit 1
fi
TEST_KEY=$TEST_KEY_BASE-stopped
run_pass "$TEST_KEY" rose suite-clean -y $NAME
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
exit 0
