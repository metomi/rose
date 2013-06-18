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
# Test "rose suite-hook", remote jobs, file system not shared.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 5
HOST=$(rose config 't:rose-suite-hook' 'host{01-remote}')
if [[ -z $HOST ]]; then
    skip 5 '[t:rose-suite-hook]01-remote{host} not defined'
    exit 0
fi
export ROSE_CONF_IGNORE=true
#-------------------------------------------------------------------------------
# Run the suite.
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C ${0%.t} --name=$NAME --no-gcontrol --host=localhost \
    "--define=[jinja2:suite.rc]HOST=\"$HOST\""
cat "$TEST_KEY.err"
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-ok
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
# Test for local copy of remote job logs.
TEST_KEY=$TEST_KEY_BASE-log
(
    cd $SUITE_RUN_DIR/log/job
    file_test "$TEST_KEY-my_task_1.out" "my_task_1.1.1.out"
    file_test "$TEST_KEY-my_task_1.err" "my_task_1.1.1.txt"
    file_cmp "$TEST_KEY-my_task_1.txt" "my_task_1.1.1.txt" <<'__CONTENT__'
Hello World
__CONTENT__
)

#-------------------------------------------------------------------------------
if $OK; then
    rm -r $SUITE_RUN_DIR
fi
exit 0
