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
# Test "rose suite-scan" with suite hosts in site/user configurations.
# Assume shared $HOME file system.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
HOSTS=$(rose config rose-suite-run hosts)
if [[ -z $HOSTS ]]; then
    skip 6 '[rose-suite-run]hosts not defined'
fi
HOST=$(rose host-select $HOSTS)
#-------------------------------------------------------------------------------
tests 6
#-------------------------------------------------------------------------------
# Run the suite.
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=$HOST
#-------------------------------------------------------------------------------
# No argument
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose suite-scan
file_grep "$TEST_KEY.out" "$NAME $USER@$HOST" "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Specific host
TEST_KEY=$TEST_KEY_BASE-hostname
run_pass "$TEST_KEY" rose suite-scan -v -v --debug $HOST
file_grep "$TEST_KEY.out" "$NAME $USER@$HOST" "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Wait for the suite to complete
touch $SUITE_RUN_DIR/flag
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
while ! rose suite-clean -q -y $NAME 2>/dev/null && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
#-------------------------------------------------------------------------------
exit 0
