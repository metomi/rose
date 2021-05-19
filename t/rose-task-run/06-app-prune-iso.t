#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# Test rose_prune built-in application, basic cycle housekeep usage.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
JOB_HOST=$(rose config --default= 't' 'job-host')
tests 9
if [[ -z $JOB_HOST ]]; then
    JOB_HOST=localhost
fi
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
#-------------------------------------------------------------------------------
get_reg
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        -C "$TEST_SOURCE_DIR/$TEST_KEY_BASE" \
        --flow-name="$FLOW" \
        --no-run-name \
        -S "HOST='${JOB_HOST}'"
run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "$FLOW" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-prune-log
sed '/^\[INFO\] \(create\|delete\|update\)/!d;
     /^\[INFO\] create.*share\/\(cycle\|data\)/d;
     /^\[INFO\] delete: \.rose-suite-log.lock/d;
     /\.json/d;
     /[0-9a-h]\{8\}\(-[0-9a-h]\{4\}\)\{3\}-[0-9a-h]\{12\}$/d' \
    $FLOW_RUN_DIR/prune.log >edited-prune.log
if [[ $JOB_HOST != localhost ]]; then
    sed "s/\\\$JOB_HOST/$JOB_HOST/g" \
        $TEST_SOURCE_DIR/$TEST_KEY_BASE.log >expected-prune.log
else
    sed '/\$JOB_HOST/d; /my_task_2/d' \
        $TEST_SOURCE_DIR/$TEST_KEY_BASE.log >expected-prune.log
fi

sort expected-prune.log > expected-prune.log.sorted
sort edited-prune.log > edited-prune.log.sorted

cp "expected-prune.log.sorted" ~/
cp "edited-prune.log.sorted" ~/

file_cmp "$TEST_KEY" expected-prune.log.sorted edited-prune.log.sorted
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-ls
run_pass "$TEST_KEY" \
    ls $FLOW_RUN_DIR/log/job-*.tar.gz $FLOW_RUN_DIR/{log/job,share/cycle,work}
sed "s?\\\$SUITE_RUN_DIR?$FLOW_RUN_DIR?g" \
    $TEST_SOURCE_DIR/$TEST_KEY.out >expected-ls.out
if [[ $JOB_HOST != localhost ]]; then
    sed -i "/my_task_2/d" expected-ls.out
fi
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" expected-ls.out
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
if [[ $JOB_HOST != localhost ]]; then
    TEST_KEY=$TEST_KEY_BASE-host-ls
    run_pass "$TEST_KEY" ssh -oBatchMode=yes -q "${JOB_HOST}" \
        ls "cylc-run/${FLOW}/{log/job,share/cycle,work}"
    sed "s@\\\$FLOW@$FLOW@g" \
        "${TEST_KEY}.out" >expected-host-ls.out
    file_cmp "$TEST_KEY.out" "$TEST_KEY.out" expected-host-ls.out
    file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
else
    skip 3 '[t]job-host not defined'
fi
#-------------------------------------------------------------------------------
purge
exit 0
