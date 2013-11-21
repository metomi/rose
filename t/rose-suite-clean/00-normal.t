#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
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

#-------------------------------------------------------------------------------
N_TESTS=3
tests $N_TESTS
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select $JOB_HOST)
fi
#-------------------------------------------------------------------------------
set -e
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
# Install suite, and prove that directories are created
if [[ -n $JOB_HOST ]]; then
    rose suite-run --debug \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -i --name=$NAME --no-gcontrol \
        -S "HOST=\"$JOB_HOST\"" 1>/dev/null
    ssh $JOB_HOST "ls -d cylc-run/$NAME 1>/dev/null"
else
    rose suite-run --debug \
        -C $TEST_SOURCE_DIR/$TEST_KEY_BASE -i --name=$NAME --no-gcontrol 1>/dev/null
fi
ls -d $HOME/cylc-run/$NAME 1>/dev/null
ls -d $HOME/.cylc/$NAME 1>/dev/null
ls -d $HOME/.cylc/REGDB/$NAME 1>/dev/null
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ans-empty
run_fail "$TEST_KEY" rose suite-clean $NAME <<<''
ls -d $HOME/cylc-run/$NAME 1>/dev/null
if [[ -n $JOB_HOST ]]; then
    ssh $JOB_HOST "ls -d cylc-run/$NAME 1>/dev/null"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ans-n
run_fail "$TEST_KEY" rose suite-clean $NAME <<<'n'
ls -d $HOME/cylc-run/$NAME 1>/dev/null
if [[ -n $JOB_HOST ]]; then
    ssh $JOB_HOST "ls -d cylc-run/$NAME 1>/dev/null"
fi
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ans-y
ls -l $HOME/cylc-run/$NAME/log
run_pass "$TEST_KEY" rose suite-clean -v -v $NAME <<<'y'
! ls -d $HOME/cylc-run/$NAME 1>/dev/null 2>&1
! ls -d $HOME/.cylc/$NAME 1>/dev/null 2>&1
! ls -d $HOME/.cylc/REGDB/$NAME 1>/dev/null 2>&1
if [[ -n $JOB_HOST ]]; then
    ssh $JOB_HOST "! ls -d cylc-run/$NAME 1>/dev/null 2>&1"
fi
#-------------------------------------------------------------------------------
exit 0
