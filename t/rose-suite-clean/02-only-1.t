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
# Test "rose suite-clean", simple --only= modes.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

run_suite() {
    set -e
    if [[ -n "$JOB_HOST" ]]; then
        rose suite-run --new -q \
            -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" -i --name="$NAME" \
            --no-gcontrol -S "HOST=\"$JOB_HOST\"" -- --debug
        ssh "$JOB_HOST" "ls -d cylc-run/$NAME 1>/dev/null"
    else
        rose suite-run --new -q \
            -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" -i --name=$NAME \
            --no-gcontrol -- --debug
    fi
    ls -d $HOME/cylc-run/$NAME $HOME/.cylc/{$NAME,REGDB/$NAME} 1>/dev/null
    set +e
}

#-------------------------------------------------------------------------------
N_TESTS=6
tests "$N_TESTS"
#-------------------------------------------------------------------------------
JOB_HOST=$(rose config --default= 't' 'job-host')
if [[ -n $JOB_HOST ]]; then
    JOB_HOST=$(rose host-select -q $JOB_HOST)
fi
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
SUITE_RUN_DIR=$(readlink -f "$SUITE_RUN_DIR")
NAME=$(basename $SUITE_RUN_DIR)
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-share"
run_suite
run_pass "$TEST_KEY" rose suite-clean -y -n "$NAME" --only=share
sed -i '/\/\.cylc\//d' "$TEST_KEY.out"
if [[ -n "$JOB_HOST" ]]; then
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/share/
[INFO] delete: $JOB_HOST:cylc-run/$NAME/share
__OUT__
else
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/share/
__OUT__
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-work"
run_suite
run_pass "$TEST_KEY" rose suite-clean -y -n "$NAME" --only=work
sed -i '/\/\.cylc\//d' "$TEST_KEY.out"
if [[ -n "$JOB_HOST" ]]; then
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/work/
[INFO] delete: $JOB_HOST:cylc-run/$NAME/work
__OUT__
else
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/work/
__OUT__
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-both"
run_suite
run_pass "$TEST_KEY" rose suite-clean -y -n "$NAME" --only=share --only=work
sed -i '/\/\.cylc\//d' "$TEST_KEY.out"
if [[ -n "$JOB_HOST" ]]; then
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/share/
[INFO] delete: $SUITE_RUN_DIR/work/
[INFO] delete: $JOB_HOST:cylc-run/$NAME/share
[INFO] delete: $JOB_HOST:cylc-run/$NAME/work
__OUT__
else
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<__OUT__
[INFO] delete: $SUITE_RUN_DIR/share/
[INFO] delete: $SUITE_RUN_DIR/work/
__OUT__
fi
#-------------------------------------------------------------------------------
rose suite-clean -q -y --name="$NAME"
exit 0
