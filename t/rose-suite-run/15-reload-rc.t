#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
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
# Test "rose suite-run", reload "suite.rc".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 3
export ROSE_CONF_PATH=
mkdir -p src
cp -r $TEST_SOURCE_DIR/$TEST_KEY_BASE/* src
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -n $NAME --no-gcontrol -C src
poll ! test -e "$SUITE_RUN_DIR/log/job/20130101T0000Z/t1/01/job.status"
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE"
cat >src/rose-suite.conf <<'__CONF__'
[jinja2:suite.rc]
ROSE_TASK_RUN_ARGS="-O earth"
__CONF__
run_pass "$TEST_KEY" rose suite-run --run=reload -n $NAME --no-gcontrol -C src
sed -n '/\(delete\|install\): suite\.rc/p; /will reload on localhost/p' \
    "$TEST_KEY.out" >"$TEST_KEY.out.tail"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out.tail" <<__OUT__
[INFO] delete: suite.rc
[INFO] install: suite.rc
[INFO] $NAME: will reload on localhost
__OUT__
poll ! grep -q \
    -e 'RELOADING.TASK.DEFINITION.FOR.t1\.20130101T0000Z' \
    -e 'RELOADING.TASK.DEFINITION.FOR.t1\.20130101T1200Z' \
    "$SUITE_RUN_DIR/log/suite/log"
# Add file that allows the jobs to proceed
cat >"$SUITE_RUN_DIR/hello.txt" <<'__TXT__'
hello world
hello earth
__TXT__
# Wait for the suite to complete
poll test -e "$HOME/cylc-run/$NAME/.service/contact"
grep '^hello ' $SUITE_RUN_DIR/log/job/*/t1/01/job.out >"$TEST_KEY.job.out"
file_cmp "$TEST_KEY.job.out" "$TEST_KEY.job.out" <<__OUT__
$SUITE_RUN_DIR/log/job/20130101T0000Z/t1/01/job.out:hello world
$SUITE_RUN_DIR/log/job/20130101T1200Z/t1/01/job.out:hello earth
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit
