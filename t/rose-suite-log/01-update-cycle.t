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
# Test "rose suite-log --update CYCLE", without site/user configurations.
# Test "rose suite-log --archive CYCLE", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_IGNORE=true

#-------------------------------------------------------------------------------
tests 23
#-------------------------------------------------------------------------------
# Run the suite.
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C ${0%.t} --name=$NAME --no-gcontrol --host=localhost
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
# Test --archive.
CYCLE=2013010100
TEST_KEY="$TEST_KEY_BASE-$CYCLE"
run_pass "$TEST_KEY-before" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log-$CYCLE.json" \
    'my_task_2' <<'__PYTHON__'
import json, sys
file_name, task_name = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(task_name in d["tasks"])
__PYTHON__
run_pass "$TEST_KEY-main-before" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log.json" $CYCLE <<'__PYTHON__'
import json, sys
file_name, cycle = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(cycle not in d["cycle_times_current"]
         or cycle in d["cycle_times_archived"])
__PYTHON__
run_pass "$TEST_KEY-list-job-logs-before" ls $SUITE_RUN_DIR/log/job/*$CYCLE*
N_JOB_LOGS=$(wc -l "$TEST_KEY-list-job-logs-before.out" | cut -d' ' -f1)
run_pass "$TEST_KEY-command" rose suite-log -n $NAME --archive $CYCLE --debug
run_fail "$TEST_KEY-list-job-logs-after" ls $SUITE_RUN_DIR/log/job/*$CYCLE*
file_test "$TEST_KEY-tar-exist" $SUITE_RUN_DIR/log/job-$CYCLE.tar.gz
N_JOB_LOGS_ARCH=$(tar -tzf $SUITE_RUN_DIR/log/job-$CYCLE.tar.gz | wc -l \
    | cut -d' ' -f1)
if ((N_JOB_LOGS == N_JOB_LOGS_ARCH)); then
    pass "$TEST_KEY-n-arch"
else
    fail "$TEST_KEY-n-arch"
fi
file_grep "$TEST_KEY-command.out" \
    "\\[INFO\\] update: rose-suite-log-$CYCLE.json" \
    "$TEST_KEY-command.out"
file_cmp "$TEST_KEY-command.err" "$TEST_KEY-command.err" </dev/null
run_pass "$TEST_KEY-after" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log-$CYCLE.json" \
    'my_task_2' <<'__PYTHON__'
import json, sys
file_name, task_name = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(task_name not in d["tasks"])
__PYTHON__
run_pass "$TEST_KEY-main-after" python - \
    "$HOME/cylc-run/$NAME/log/rose-suite-log.json" $CYCLE <<'__PYTHON__'
import json, sys
file_name, cycle = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(cycle in d["cycle_times_current"]
         or cycle not in d["cycle_times_archived"])
__PYTHON__
#-------------------------------------------------------------------------------
# Test --update.
for CYCLE in 2013010112 2013010200; do
    TEST_KEY="$TEST_KEY_BASE-$CYCLE"
    run_pass "$TEST_KEY-before" python - \
        "$HOME/cylc-run/$NAME/log/rose-suite-log-$CYCLE.json" \
        'my_task_2' <<'__PYTHON__'
import json, sys
file_name, task_name = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(task_name in d["tasks"])
__PYTHON__
    run_pass "$TEST_KEY-command" rose suite-log -n $NAME --update $CYCLE --debug
    file_grep "$TEST_KEY-command.out" \
        "\\[INFO\\] update: rose-suite-log-$CYCLE.json" \
        "$TEST_KEY-command.out"
    file_cmp "$TEST_KEY-command.err" "$TEST_KEY-command.err" </dev/null
    run_pass "$TEST_KEY-after" python - \
        "$HOME/cylc-run/$NAME/log/rose-suite-log-$CYCLE.json" \
        'my_task_2' <<'__PYTHON__'
import json, sys
file_name, task_name = sys.argv[1:]
d = json.load(open(file_name))
sys.exit(task_name not in d["tasks"])
__PYTHON__
done
#-------------------------------------------------------------------------------
if $OK; then
    rm -r $SUITE_RUN_DIR
fi
exit 0
