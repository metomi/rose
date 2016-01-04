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
# Test "rose suite-clean", normal mode.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

install_suite() {
    set -e
    if [[ -n "$JOB_HOST" ]]; then
        rose suite-run --new -q \
            -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -i --name=$NAME --no-gcontrol \
            -S "HOST=\"$JOB_HOST\""
        ssh "$JOB_HOST" "ls -d cylc-run/$NAME 1>/dev/null"
    else
        rose suite-run --new -q \
            -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -i --name=$NAME --no-gcontrol
    fi
    ls -d $HOME/cylc-run/$NAME $HOME/.cylc/{$NAME,REGDB/$NAME} 1>/dev/null
    set +e
}
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select -q $JOB_HOST)
    tests 15
else
    tests 10
fi
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
install_suite
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ans-empty
run_fail "$TEST_KEY" rose suite-clean $NAME <<<''
run_pass "$TEST_KEY.locahost.ls" ls -d $HOME/cylc-run/$NAME
if [[ -n "$JOB_HOST" ]]; then
    run_pass "$TEST_KEY.job-host.ls" ssh "$JOB_HOST" "ls -d cylc-run/$NAME"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ans-n
run_fail "$TEST_KEY" rose suite-clean $NAME <<<'n'
run_pass "$TEST_KEY.locahost.ls" ls -d $HOME/cylc-run/$NAME
if [[ -n "$JOB_HOST" ]]; then
    run_pass "$TEST_KEY.job-host.ls" ssh "$JOB_HOST" "ls -d cylc-run/$NAME"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE--name-ans-n
run_fail "$TEST_KEY" rose suite-clean --name=$NAME <<<'n'
run_pass "$TEST_KEY.locahost.ls" ls -d $HOME/cylc-run/$NAME
if [[ -n "$JOB_HOST" ]]; then
    run_pass "$TEST_KEY.job-host.ls" ssh "$JOB_HOST" "ls -d cylc-run/$NAME"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ans-y
run_pass "$TEST_KEY" rose suite-clean -v -v $NAME <<<'y'
run_fail "$TEST_KEY.locahost.ls" \
    ls -d $HOME/cylc-run/$NAME $HOME/.cylc/{$NAME,REGDB/$NAME}
if [[ -n "$JOB_HOST" ]]; then
    run_fail "$TEST_KEY.job-host.ls" ssh "$JOB_HOST" "ls -d cylc-run/$NAME"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE--name-ans-y
install_suite
run_pass "$TEST_KEY" rose suite-clean -v -v -n $NAME <<<'y'
run_fail "$TEST_KEY.locahost.ls" \
    ls -d $HOME/cylc-run/$NAME $HOME/.cylc/{$NAME,REGDB/$NAME}
if [[ -n "$JOB_HOST" ]]; then
    run_fail "$TEST_KEY.job-host.ls" ssh "$JOB_HOST" "ls -d cylc-run/$NAME"
fi
#-------------------------------------------------------------------------------
exit 0
