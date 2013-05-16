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
export ROSE_CONF_IGNORE=true

#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
# Run rose rug-brief-tour command
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose rug-brief-tour
#-------------------------------------------------------------------------------
# Run the suite
TEST_KEY=$TEST_KEY_BASE-suite-run
NAME="rose-test-suite-$TEST_KEY_BASE"
run_pass "$TEST_KEY" rose suite-run --name=$NAME --no-gcontrol
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
TIMEOUT=$(($(date +%s) + 36000)) # wait 10 minutes
OK=false
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
else
    OK=true
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
# See if all tasks are OK
TEST_KEY=$TEST_KEY_BASE-tasks
run_pass "$TEST_KEY" sqlite3 "$HOME/cylc-run/$NAME/cylc-suite.db" \
    'SELECT name,cycle,submit_num FROM task_events
         WHERE event=="execution succeeded"
         ORDER BY name,cycle,submit_num;'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
fcm_make|2013010100|1
fred_hello_world|2013010100|1
fred_hello_world|2013010106|1
fred_hello_world|2013010112|1
fred_hello_world|2013010118|1
fred_hello_world|2013010200|1
locate_fred|2013010100|1
locate_fred|2013010106|1
locate_fred|2013010112|1
locate_fred|2013010118|1
locate_fred|2013010200|1
my_hello_mars|2013010100|1
my_hello_mars|2013010112|1
my_hello_mars|2013010200|1
my_hello_world|2013010100|1
my_hello_world|2013010106|1
my_hello_world|2013010112|1
my_hello_world|2013010118|1
my_hello_world|2013010200|1
__OUT__
#-------------------------------------------------------------------------------
if $OK; then
    rm -r $HOME/cylc-run/$NAME
fi
exit 0
