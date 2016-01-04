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
# Test "rose suite-run", reload with !CYLC_VERSION.
# See issue metomi/rose#1143.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 1
export ROSE_CONF_PATH=
cp -r $TEST_SOURCE_DIR/$TEST_KEY_BASE/* .
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -n $NAME --no-gcontrol
# Wait for the only task to fail, before reload
ST_FILE=$SUITE_RUN_DIR/log/job/1/t1/01/job.status
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while (($(date +%s) < TIMEOUT)) \
    && ! grep -q 'CYLC_JOB_EXIT_TIME=' $ST_FILE 2>/dev/null
do
    sleep 1
done
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose suite-run --reload -q -n $NAME --no-gcontrol
#-------------------------------------------------------------------------------
rose suite-stop -q -y -n $NAME -- --max-polls=12 --interval=5
rose suite-clean -q -y $NAME
exit
