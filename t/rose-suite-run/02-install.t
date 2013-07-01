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
# Test "rose suite-run", with and without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
N_TESTS=7
tests $N_TESTS
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select $JOB_HOST)
fi
#-------------------------------------------------------------------------------
if [[ $TEST_KEY_BASE == *conf ]]; then
    if ! rose config -q 'rose-suite-run' 'hosts'; then
        skip $N_TESTS '[rose-suite-run]hosts not defined'
        exit 0
    fi
else
    export ROSE_CONF_PATH=
fi
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
OPTION=-i
if [[ $TEST_KEY_BASE == *local* ]]; then
    OPTION=-l
fi
if [[ -n $JOB_HOST ]]; then
    run_pass "$TEST_KEY" rose suite-run --debug \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE $OPTION --name=$NAME --no-gcontrol \
        -S "HOST=\"$JOB_HOST\""
else
    run_pass "$TEST_KEY" rose suite-run --debug \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE $OPTION --name=$NAME --no-gcontrol
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-port-file
run_fail "$TEST_KEY" test -e $HOME/.cylc/ports/$NAME
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-items
run_pass "$TEST_KEY" ls $SUITE_RUN_DIR/{app,etc}
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$SUITE_RUN_DIR/app:
my_task_1

$SUITE_RUN_DIR/etc:
junk
__OUT__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-items-$JOB_HOST
if [[ $TEST_KEY_BASE == *local* ]]; then
    skip 2 "$TEST_KEY: local-install-only"
elif [[ -n $JOB_HOST ]]; then
    run_pass "$TEST_KEY" \
        ssh -oBatchMode=yes $JOB_HOST ls cylc-run/$NAME/{app,etc}
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
cylc-run/$NAME/app:
my_task_1

cylc-run/$NAME/etc:
junk
__OUT__
else
    skip 2 "$TEST_KEY_BASE-items: [t]job-host not defined"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-clean
run_pass "$TEST_KEY" rose suite-clean -y $NAME
rmdir $SUITE_RUN_DIR 2>/dev/null || true
exit 0
