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
# Test "rose suite-run -O KEY".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 9
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
cat </dev/null >tests
mkdir -p $HOME/cylc-run
for OPT_KEY in world earth neutron-star; do
    SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
    echo "$OPT_KEY $SUITE_RUN_DIR" >>tests
done
# Run the suites
while read OPT_KEY SUITE_RUN_DIR; do
    NAME=$(basename $SUITE_RUN_DIR)
    ROSE_SUITE_RUN="rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE"
    ROSE_SUITE_RUN="$ROSE_SUITE_RUN --name=$NAME --no-gcontrol"
    if [[ $OPT_KEY != 'world' ]]; then
        ROSE_SUITE_RUN="$ROSE_SUITE_RUN -O $OPT_KEY"
    fi
    TEST_KEY=$TEST_KEY_BASE-$OPT_KEY
    run_pass "$TEST_KEY" $ROSE_SUITE_RUN
done <tests

# Wait for the suites to complete
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while read OPT_KEY SUITE_RUN_DIR; do
    TEST_KEY=$TEST_KEY_BASE-$OPT_KEY
    NAME=$(basename $SUITE_RUN_DIR)
    while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
        sleep 1
    done
    if [[ -e $HOME/.cylc/ports/$NAME ]]; then
        fail "$TEST_KEY"
        fail "$TEST_KEY_BASE-$OPT_KEY-txt"
    else
        pass "$TEST_KEY"
        if [[ $OPT_KEY == 'world' ]]; then
            CONF=$TEST_SOURCE_DIR/$TEST_KEY_BASE/rose-suite.conf
        else
            CONF=$TEST_SOURCE_DIR/$TEST_KEY_BASE/opt/rose-suite-$OPT_KEY.conf
        fi
        VALUE=$(rose config -f $CONF 'jinja2:suite.rc' 'WORLD')
        TEST_KEY=$TEST_KEY_BASE-$OPT_KEY-txt
        file_cmp "$TEST_KEY" $SUITE_RUN_DIR/log/job/1/my_task_1/01/job.txt <<__OUT__
Hello $VALUE
__OUT__
    fi
done <tests

#-------------------------------------------------------------------------------
# Tidy up
while read OPT_KEY SUITE_RUN_DIR; do
    NAME=$(basename $SUITE_RUN_DIR)
    rose suite-clean -q -y $NAME
done <tests
#-------------------------------------------------------------------------------
exit 0
