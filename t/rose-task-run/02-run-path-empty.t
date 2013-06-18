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
# Test "rose task-run --path=", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_IGNORE=true

#-------------------------------------------------------------------------------
tests 5
#-------------------------------------------------------------------------------
# Run the suite.
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C ${0%.t} --name=$NAME --no-gcontrol --host=localhost
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
    exit 1
else
    OK=true
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
MY_PATH="$SUITE_RUN_DIR/etc/your-path"
PREV_CYCLE=
for CYCLE in 2013010100 2013010112 2013010200; do
    TEST_KEY=$TEST_KEY_BASE-file-$CYCLE
    TASK=my_task_1
    FILE=$HOME/cylc-run/$NAME/log/job/$TASK.$CYCLE.1.txt
    file_grep "$TEST_KEY-PATH" "PATH=$SUITE_RUN_DIR/app/$TASK/bin:$SUITE_RUN_DIR/etc/your-path" $FILE
    PREV_CYCLE=$CYCLE
done
#-------------------------------------------------------------------------------
if $OK; then
    rm -r $SUITE_RUN_DIR
fi
exit 0
