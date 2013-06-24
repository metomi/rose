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
# Test "rose suite-log --update TASK", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 10
#-------------------------------------------------------------------------------
if [[ $TEST_KEY_BASE == *-remote* ]]; then
    JOB_HOST=$(rose config 't:rose-suite-log' "job-host")
    if [[ -z $JOB_HOST ]]; then
        skip 10 "[t:rose-suite-log]job-host not defined"
        exit 0
    fi
    JOB_HOST=$(rose host-select $JOB_HOST)
fi
#-------------------------------------------------------------------------------
# Run the suite.
export ROSE_CONF_IGNORE=true
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
if [[ -n ${JOB_HOST:-} ]]; then
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost \
        -D "[jinja2:suite.rc]HOST=\"$JOB_HOST\""
else
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost
fi
#-------------------------------------------------------------------------------
# Wait for the suite to complete, test shutdown on fail
TEST_KEY="$TEST_KEY_BASE-complete"
TIMEOUT=$(($(date +%s) + 36000)) # wait 10 minutes
OK=false
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    OK=true
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
run_pass "$TEST_KEY_BASE-before" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log-1.json" 'my_task_2' <<'__PYTHON__'
import json, sys
file_name, task_name = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(task_name in d["tasks"])
__PYTHON__
TEST_KEY=$TEST_KEY_BASE-before-log.out
if [[ -n ${JOB_HOST:-} ]]; then
    run_fail "$TEST_KEY-log.out" \
        test -f $SUITE_RUN_DIR/log/job/my_task_2.1.1.out
else
    pass "$TEST_KEY-log.out"
fi
TEST_KEY=$TEST_KEY_BASE-command
run_pass "$TEST_KEY" rose suite-log -n $NAME -u 'my_task_2' --debug
file_grep "$TEST_KEY.out" '\[INFO\] update: rose-suite-log-1.json' \
    "$TEST_KEY.out"
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
TEST_KEY=$TEST_KEY_BASE-after
run_pass "$TEST_KEY" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log-1.json" 'my_task_2' <<'__PYTHON__'
import json, sys
file_name, task_name = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(task_name not in d["tasks"])
__PYTHON__
file_test "$TEST_KEY-log.out" $SUITE_RUN_DIR/log/job/my_task_2.1.1.out
#-------------------------------------------------------------------------------
run_pass "$TEST_KEY_BASE-clean" rose suite-clean -y --debug $NAME
rmdir $SUITE_RUN_DIR 2</dev/null || true
exit 0
