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
# Test "rose suite-scan" with suite localhost or hosts in site/user
# configurations. Assume shared $HOME file system.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
if [[ $TEST_KEY_BASE == *localhost ]]; then
    export ROSE_CONF_PATH=
    HOST=localhost
else
    HOSTS=$(rose config rose-suite-run hosts)
    if [[ -z $HOSTS ]]; then
        skip_all '"[rose-suite-run]hosts" not defined'
    fi
    HOST=$(rose host-select -q $HOSTS)
fi
#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
# Run the suite
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=$HOST
if [[ $HOST == 'localhost' ]]; then
    PORT=$(cat ~/.cylc/ports/$NAME)
else
    PORT=$(ssh -oBatchMode=yes $HOST cat ~/.cylc/ports/$NAME)
fi
#-------------------------------------------------------------------------------
# No argument
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose suite-scan
file_grep "$TEST_KEY.out" "$NAME $USER@$HOST:$PORT" "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Specific host
TEST_KEY=$TEST_KEY_BASE-hostname
run_pass "$TEST_KEY" rose suite-scan $HOST
file_grep "$TEST_KEY.out" "$NAME $USER@$HOST:$PORT" "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Wait for the suite to complete
touch $SUITE_RUN_DIR/flag
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while [[ -e ~/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
rose suite-clean -q -y $NAME || exit 1
#-------------------------------------------------------------------------------
# Left behind port file
TEST_KEY=$TEST_KEY_BASE-port-file
echo 7766 >~/.cylc/ports/$NAME
run_pass "$TEST_KEY" rose suite-scan
file_grep "$TEST_KEY.out" \
    "$NAME $USER@$HOST:~/.cylc/ports/$NAME" "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
rm ~/.cylc/ports/$NAME
#-------------------------------------------------------------------------------
exit 0
