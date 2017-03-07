#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
# Test "rose rug-brief-tour", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=

#-------------------------------------------------------------------------------
tests 3
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
run_pass "$TEST_KEY" \
    rose suite-run --name=$NAME --no-gcontrol -S SLEEP=\":\" -- --debug
#-------------------------------------------------------------------------------
# Check that the suite runs to success
TEST_KEY=$TEST_KEY_BASE-db
sqlite3 $SUITE_RUN_DIR/log/db \
    'SELECT cycle,name FROM task_jobs
     WHERE run_status==0 ORDER BY cycle,name ASC;' \
    >"$TEST_KEY.out"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
20130101T0000Z|fcm_make
20130101T0000Z|fred_hello_world
20130101T0000Z|locate_fred
20130101T0000Z|my_hello_mars
20130101T0000Z|my_hello_saturn
20130101T0000Z|my_hello_world
20130101T0600Z|fred_hello_world
20130101T0600Z|locate_fred
20130101T0600Z|my_hello_world
20130101T1200Z|fred_hello_world
20130101T1200Z|locate_fred
20130101T1200Z|my_hello_mars
20130101T1200Z|my_hello_world
20130101T1800Z|fred_hello_world
20130101T1800Z|locate_fred
20130101T1800Z|my_hello_world
20130102T0000Z|fred_hello_world
20130102T0000Z|locate_fred
20130102T0000Z|my_hello_mars
20130102T0000Z|my_hello_world
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
