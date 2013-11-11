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
# Test "rose rug-brief-tour", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=

#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
# Run rose rug-brief-tour command
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose rug-brief-tour
#-------------------------------------------------------------------------------
# Run the suite
TEST_KEY=$TEST_KEY_BASE-suite-run
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
# N.B. SLEEP=\":\" means run the ":" command instead of "sleep $((RANDOM % 10))"
run_pass "$TEST_KEY" rose suite-run --name=$NAME --no-gcontrol -S SLEEP=\":\"
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
TIMEOUT=$(($(date +%s) + 300)) # wait 5 minutes
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
# Check that the suite runs to success
TEST_KEY=$TEST_KEY_BASE-db
sqlite3 $SUITE_RUN_DIR/cylc-suite.db \
    'SELECT cycle,name FROM task_events
     WHERE event=="succeeded" ORDER BY cycle,name ASC;' \
    >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
2013010100|fcm_make
2013010100|fred_hello_world
2013010100|locate_fred
2013010100|my_hello_mars
2013010100|my_hello_world
2013010106|fred_hello_world
2013010106|locate_fred
2013010106|my_hello_world
2013010112|fred_hello_world
2013010112|locate_fred
2013010112|my_hello_mars
2013010112|my_hello_world
2013010118|fred_hello_world
2013010118|locate_fred
2013010118|my_hello_world
2013010200|fred_hello_world
2013010200|locate_fred
2013010200|my_hello_mars
2013010200|my_hello_world
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
cylc unregister $NAME 1>/dev/null 2>&1
exit 0
