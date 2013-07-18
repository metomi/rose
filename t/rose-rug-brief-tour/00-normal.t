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
tests 9
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
# See if rose suite-hook has dumped out the event data
TEST_KEY=$TEST_KEY_BASE-hook
run_pass "$TEST_KEY-cycle_times_current" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log.json" <<'__PYTHON__'
import json, sys
sys.exit(json.load(open(sys.argv[1]))["cycle_times_current"] !=
         ["2013010200", "2013010118", "2013010112", "2013010106", "2013010100"])
__PYTHON__
EXPECTED='
2013010100 fcm_make,fred_hello_world,locate_fred,my_hello_mars,my_hello_world
2013010106 fred_hello_world,locate_fred,my_hello_world
2013010112 fred_hello_world,locate_fred,my_hello_mars,my_hello_world
2013010118 fred_hello_world,locate_fred,my_hello_world
2013010200 fred_hello_world,locate_fred,my_hello_mars,my_hello_world
'
for CYCLE in 2013010200 2013010118 2013010112 2013010106 2013010100; do
    run_pass "$TEST_KEY-cycle_time-$CYCLE" python - \
        "$HOME/cylc-run/$NAME/log/rose-suite-log-$CYCLE.json" \
        $(awk "/$CYCLE/" <<<"$EXPECTED") <<'__PYTHON__'
import json, sys
file_name, cycle, tasks_str = sys.argv[1:]
tasks = tasks_str.split(",")
d = json.load(open(file_name))
sys.exit(d["cycle_time"] != cycle or len(d["tasks"]) != len(tasks) or
         any([t not in d["tasks"] for t in tasks]) or
         any([len(d["tasks"][t]) != 1 for t in tasks]) or
         any([d["tasks"][t][0]["status"] != "pass" for t in tasks]))
__PYTHON__
done
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
