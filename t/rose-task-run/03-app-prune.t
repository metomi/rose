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
# Test rose_prune built-in application, basic cycle housekeep usage.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -z $JOB_HOST ]]; then
    skip 3 '[t]job-host not defined'
    :
else
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
# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-suite-run-wait
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
TEST_KEY=$TEST_KEY_BASE-ls
run_pass "$TEST_KEY" \
    ls $SUITE_RUN_DIR/log/job-*.tar.gz $SUITE_RUN_DIR/{log/job,share/data,work}
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$SUITE_RUN_DIR/log/job-2013010100.tar.gz
$SUITE_RUN_DIR/log/job-2013010112.tar.gz

$SUITE_RUN_DIR/log/job:
my_task_1.2013010200.1
my_task_1.2013010200.1.err
my_task_1.2013010200.1.out
my_task_1.2013010200.1.status
my_task_2.2013010200.1
my_task_2.2013010200.1.err
my_task_2.2013010200.1.out
my_task_2.2013010200.1.status
rose_prune.2013010200.1
rose_prune.2013010200.1.err
rose_prune.2013010200.1.out
rose_prune.2013010200.1.status

$SUITE_RUN_DIR/share/data:
2013010200

$SUITE_RUN_DIR/work:
my_task_1.2013010200
rose_prune.2013010200
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
if [[ -n $JOB_HOST ]]; then
    TEST_KEY=$TEST_KEY_BASE-host-ls
    run_pass "$TEST_KEY" ssh -oBatchMode=yes $JOB_HOST \
        ls cylc-run/$NAME/{log/job,share/data,work}
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
cylc-run/$NAME/log/job:
my_task_2.2013010200.1
my_task_2.2013010200.1.err
my_task_2.2013010200.1.out
my_task_2.2013010200.1.status

cylc-run/$NAME/share/data:
2013010200

cylc-run/$NAME/work:
my_task_2.2013010200
__OUT__
    file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-clean
run_pass "$TEST_KEY" rose suite-clean -y $NAME
rmdir $SUITE_RUN_DIR 2>/dev/null || true
exit 0
