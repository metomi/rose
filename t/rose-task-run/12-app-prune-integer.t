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
# Test "rose prune" with integer cycling
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select -q $JOB_HOST)
    tests 15
else
    tests 12
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
        -D "[jinja2:suite.rc]HOST=\"$JOB_HOST\"" \
        -- --debug
else
    run_pass "$TEST_KEY" \
        rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
        --no-gcontrol --host=localhost \
        -- --debug
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-work
run_fail "$TEST_KEY.1" ls -d $HOME/cylc-run/$NAME/work/1
run_fail "$TEST_KEY.2" ls -d $HOME/cylc-run/$NAME/work/2
run_pass "$TEST_KEY.3" ls -d $HOME/cylc-run/$NAME/work/3
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-share
run_fail "$TEST_KEY.1" ls -d $HOME/cylc-run/$NAME/share/cycle/1
run_fail "$TEST_KEY.2" ls -d $HOME/cylc-run/$NAME/share/cycle/2
run_pass "$TEST_KEY.3" ls -d $HOME/cylc-run/$NAME/share/cycle/3
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-archive
TEST_KEY=$TEST_KEY_BASE-share
run_fail "$TEST_KEY.1" ls -d $HOME/cylc-run/$NAME/log/job/1
run_pass "$TEST_KEY.1-tar" ls -d $HOME/cylc-run/$NAME/log/job-1.tar.gz
run_fail "$TEST_KEY.2" ls -d $HOME/cylc-run/$NAME/log/job/2
run_pass "$TEST_KEY.2-tar" ls -d $HOME/cylc-run/$NAME/log/job-2.tar.gz
run_pass "$TEST_KEY.3" ls -d $HOME/cylc-run/$NAME/log/job/3
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-remote
if [[ -n "$JOB_HOST" ]]; then
    run_fail "$TEST_KEY.1" ssh "$JOB_HOST" "ls -d ~/cylc-run/$NAME/log/job/1"
    run_fail "$TEST_KEY.2" ssh "$JOB_HOST" "ls -d ~/cylc-run/$NAME/log/job/2"
    run_pass "$TEST_KEY.3" ssh "$JOB_HOST" "ls -d ~/cylc-run/$NAME/log/job/3"
fi
#-------------------------------------------------------------------------------
rose suite-clean -y --name=$NAME
#-------------------------------------------------------------------------------
exit 0
