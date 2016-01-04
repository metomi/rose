#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
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
# Test rose_prune built-in application, basic cycle housekeep usage.
# Backward compatibility, with pre- isodatetime syntax.
# Backward compatibility, with pre- prune{anything} syntax.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -z $JOB_HOST ]]; then
    skip 3 '[t]job-host not defined'
else
    JOB_HOST=$(rose host-select -q $JOB_HOST)
fi
#-------------------------------------------------------------------------------
# Run the suite.
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
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
TEST_KEY=$TEST_KEY_BASE-prune-log
sed '/^\[INFO\] \(create\|delete\|update\)/!d;
     /^\[INFO\] delete: \.rose-suite-log.lock/d;
     /\.json/d;
     /[0-9a-h]\{8\}\(-[0-9a-h]\{4\}\)\{3\}-[0-9a-h]\{12\}$/d' \
    $SUITE_RUN_DIR/prune.log >edited-prune.log
if [[ -n $JOB_HOST ]]; then
    sed "s/\\\$JOB_HOST/$JOB_HOST/g" \
        $TEST_SOURCE_DIR/$TEST_KEY_BASE.log >expected-prune.log
else
    sed '/\$JOB_HOST/d; /my_task_2/d' \
        $TEST_SOURCE_DIR/$TEST_KEY_BASE.log >expected-prune.log
fi
file_cmp "$TEST_KEY" expected-prune.log edited-prune.log
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ls
run_pass "$TEST_KEY" \
    ls $SUITE_RUN_DIR/log/job-*.tar.gz $SUITE_RUN_DIR/{log/job,share/cycle,work}
sed "s?\\\$SUITE_RUN_DIR?$SUITE_RUN_DIR?g" \
    $TEST_SOURCE_DIR/$TEST_KEY.out >expected-ls.out
if [[ -z $JOB_HOST ]]; then
    sed -i "/my_task_2/d" expected-ls.out
fi
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" expected-ls.out
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
if [[ -n $JOB_HOST ]]; then
    TEST_KEY=$TEST_KEY_BASE-host-ls
    run_pass "$TEST_KEY" ssh -oBatchMode=yes $JOB_HOST \
        ls cylc-run/$NAME/{log/job,share/cycle,work}
    sed "s/\\\$NAME/$NAME/g" \
        $TEST_SOURCE_DIR/$TEST_KEY.out >expected-host-ls.out
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" expected-host-ls.out
    file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
