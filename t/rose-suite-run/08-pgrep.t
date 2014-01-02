#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose suite-run" when a running suite's port file is removed,
# so will rely on pgrep to detect whether it is still running or not.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
set -eu
#-------------------------------------------------------------------------------
N_TESTS=4
tests $N_TESTS
#-------------------------------------------------------------------------------
HOST=
OPT_HOST=
if [[ $TEST_KEY_BASE == *conf ]]; then
    HOST_GROUP=$(rose config --default= 'rose-suite-run' 'hosts')
    if [[ -z $HOST_GROUP ]]; then
        skip $N_TESTS '[rose-suite-run]hosts not defined'
        exit 0
    fi
    HOST=$(rose 'host-select' -q $HOST_GROUP)
    OPT_HOST="--host=$HOST"
fi
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME $OPT_HOST \
    --no-gcontrol
TIME_OUT=$(($(date +%s) + 120))
GREP="grep -q CYLC_JOB_EXIT= ~/cylc-run/$NAME/log/job/my_task_1.1.1.status"
if [[ -n $HOST ]]; then
    CMD_PREFIX="ssh -oBatchMode=yes $HOST"
else
    CMD_PREFIX=eval
fi
while ! $CMD_PREFIX "$GREP" 2>/dev/null; do
    if (($(date +%s) > $TIME_OUT)); then
        break
    fi
    sleep 1
done
$CMD_PREFIX "mv ~/.cylc/ports/$NAME $NAME.port"
ERR_HOST=${HOST:-localhost}
run_fail "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    $OPT_HOST --no-gcontrol
file_grep "$TEST_KEY.err" \
    '\[FAIL\] '$NAME': is still running (detected '$ERR_HOST \
    "$TEST_KEY.err"
run_pass "$TEST_KEY.NAME1" \
    rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=${NAME}1 \
    $OPT_HOST --no-gcontrol
run_pass "$TEST_KEY.SHORTNAME" \
    rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=${NAME%?} \
    $OPT_HOST --no-gcontrol
#-------------------------------------------------------------------------------
set +e
sleep 1
$CMD_PREFIX "mv $NAME.port ~/.cylc/ports/$NAME"
SHUTDOWN_OPTS='--kill --max-polls=24 --interval=5'
for N in $NAME ${NAME}1 ${NAME%?}; do
    if $CMD_PREFIX test -f ~/.cylc/ports/$N; then
        rose suite-shutdown --debug -q -y -n $N -- $SHUTDOWN_OPTS 2>/dev/null
    fi
done
rose suite-clean --debug -q -y $NAME ${NAME}1 ${NAME%?}
exit 0
