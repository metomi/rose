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
# Test "rose prune" removal of logs
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
tests 10
#-------------------------------------------------------------------------------
# Run the suite.
export CYLC_CONF_PATH=
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost \
    -- --debug
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-log
run_fail "$TEST_KEY.1" ls -d $HOME/cylc-run/$NAME/log/job/20100101T0000Z
run_fail "$TEST_KEY.2" ls -d $HOME/cylc-run/$NAME/log/job/20100102T0000Z
run_fail "$TEST_KEY.3" ls -d $HOME/cylc-run/$NAME/log/job/20100103T0000Z
run_fail "$TEST_KEY.4" ls -d $HOME/cylc-run/$NAME/log/job/20100104T0000Z
run_pass "$TEST_KEY.5" ls -d $HOME/cylc-run/$NAME/log/job/20100105T0000Z
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-archived
run_fail "$TEST_KEY.1" ls -d $HOME/cylc-run/$NAME/log/job-20100101T0000Z.tar.gz
run_fail "$TEST_KEY.2" ls -d $HOME/cylc-run/$NAME/log/job-20100102T0000Z.tar.gz
run_fail "$TEST_KEY.3" ls -d $HOME/cylc-run/$NAME/log/job-20100103T0000Z.tar.gz
run_pass "$TEST_KEY.4" ls -d $HOME/cylc-run/$NAME/log/job-20100104T0000Z.tar.gz
#-------------------------------------------------------------------------------
rose suite-clean -q -y --name=$NAME
#-------------------------------------------------------------------------------
exit 0
