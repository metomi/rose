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
# Test "rose suite-hook", remote jobs.
# 01 - Test with a remote host without a shared $HOME.
# 02 - Test with a remote host with a shared $HOME.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 6
KEY=${TEST_KEY_BASE#0?-}
HOST=$(rose config 't' $KEY)
if [[ -z $HOST ]]; then
    skip 6 "[t]$KEY not defined"
    exit 0
fi
HOST=$(rose host-select $HOST)
export ROSE_CONF_IGNORE=true
#-------------------------------------------------------------------------------
# Run the suite.
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost \
    "--define=[jinja2:suite.rc]HOST=\"$HOST\""
#-------------------------------------------------------------------------------
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-ok
TIMEOUT=$(($(date +%s) + 300)) # wait 5 minutes
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
cd $SUITE_RUN_DIR/log/job
file_test "$TEST_KEY-my_task_1.out" "my_task_1.1.1.out"
file_test "$TEST_KEY-my_task_1.err" "my_task_1.1.1.txt"
file_cmp "$TEST_KEY-my_task_1.txt" "my_task_1.1.1.txt" <<'__CONTENT__'
Hello World
__CONTENT__
cd $OLDPWD

#-------------------------------------------------------------------------------
run_pass "$TEST_KEY_BASE-clean" rose suite-clean -y $NAME
rmdir $SUITE_RUN_DIR 2</dev/null || true
exit 0
