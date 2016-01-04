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
# Test --*-log-* options of "rose suite-run".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 31
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
ROSE_SUITE_RUN="rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE"
ROSE_SUITE_RUN="$ROSE_SUITE_RUN --name=$NAME"
ROSE_SUITE_RUN="$ROSE_SUITE_RUN --no-gcontrol"

N_RUNS=6
I_KEEP=$((RANDOM % N_RUNS)) # 0 to N_RUNS - 1
I_NO_LOG_ARCHIVE=$((RANDOM % N_RUNS + 1))
while ((I_KEEP == I_NO_LOG_ARCHIVE)); do
    I_NO_LOG_ARCHIVE=$((RANDOM % N_RUNS + 1))
done
OLD_LOG=
KEPT_LOG=
for I in $(seq 0 $N_RUNS); do
    # Run the suite
    TEST_KEY=$TEST_KEY_BASE-$I
    if ((I == I_KEEP)); then
        run_pass "$TEST_KEY-keep" $ROSE_SUITE_RUN --log-name=keep
    elif ((I == I_NO_LOG_ARCHIVE)); then
        run_pass "$TEST_KEY-no-log-archive" $ROSE_SUITE_RUN --no-log-archive
    else
        run_pass "$TEST_KEY" $ROSE_SUITE_RUN
    fi

    # Wait for the suite to complete
    TEST_KEY=$TEST_KEY_BASE-$I-wait
    TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
    while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
        sleep 1
    done
    if [[ -e $HOME/.cylc/ports/$NAME ]]; then
        fail "$TEST_KEY"
        exit 1
    else
        pass "$TEST_KEY"
    fi
    TEST_KEY=$TEST_KEY_BASE-$I-log
    file_test "$TEST_KEY" $SUITE_RUN_DIR/log -L
    if ((I == I_KEEP)); then
        file_test "$TEST_KEY-keep" $SUITE_RUN_DIR/log.keep -L
        KEPT_LOG=$(readlink $SUITE_RUN_DIR/log.keep)
    fi
    if ((I - 1 == I_KEEP)) || ((I == I_NO_LOG_ARCHIVE)); then
        file_test "$TEST_KEY-old-kept" $SUITE_RUN_DIR/$OLD_LOG
    elif [[ -n $OLD_LOG ]]; then
        file_test "$TEST_KEY-old" $SUITE_RUN_DIR/$OLD_LOG.tar.gz
    fi
    OLD_LOG=$(readlink $SUITE_RUN_DIR/log)
done

TEST_KEY=$TEST_KEY_BASE-log-keep-0
run_pass "$TEST_KEY" $ROSE_SUITE_RUN --log-keep=0

# Wait for the suite to complete
TEST_KEY=$TEST_KEY_BASE-log-keep-0-wait
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    pass "$TEST_KEY"
fi

TEST_KEY=$TEST_KEY_BASE-log-keep-0-ls
ls -d $SUITE_RUN_DIR/log* >$TEST_KEY.out
THIS_LOG=$(readlink $SUITE_RUN_DIR/log)
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
$SUITE_RUN_DIR/log
$SUITE_RUN_DIR/$KEPT_LOG
$SUITE_RUN_DIR/$THIS_LOG
$SUITE_RUN_DIR/log.keep
__OUT__

#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
