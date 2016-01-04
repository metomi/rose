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
# Test "rose suite-run", null reloads.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 7
export ROSE_CONF_PATH=
cp -r $TEST_SOURCE_DIR/$TEST_KEY_BASE src
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -n $NAME --no-gcontrol -C src
poll ! test -e "$SUITE_RUN_DIR/log/job/2013010100/t1/01/job.status"
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0"
run_pass "$TEST_KEY" rose suite-run --run=reload -n $NAME --no-gcontrol -C src
sed '1,/export ROSE_VERSION=/d; /^\[INFO\] delete: .*\/.cylc\//d' \
    "$TEST_KEY.out" >"$TEST_KEY.out.tail"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out.tail" <<__OUT__
[INFO] $NAME: reload complete. "suite.rc" unchanged
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" /dev/null
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1"
# Add file that allows the jobs to proceed
cat >"src/hello.txt" <<'__TXT__'
hello world
hello earth
__TXT__
run_pass "$TEST_KEY" rose suite-run --run=reload -n $NAME --no-gcontrol -C src
sed '1,/export ROSE_VERSION=/d; /\/.cylc\//d' "$TEST_KEY.out" \
    >"$TEST_KEY.out.tail"
file_cmp "$TEST_KEY.out" "$TEST_KEY.out.tail" <<__OUT__
[INFO] install: hello.txt
[INFO]     source: $PWD/src/hello.txt
[INFO] $NAME: reload complete. "suite.rc" unchanged
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" /dev/null
# Wait for the suite to complete
poll test -e "$HOME/.cylc/ports/$NAME"
grep '^hello ' $SUITE_RUN_DIR/log/job/*/t1/01/job.out >"$TEST_KEY.job.out"
file_cmp "$TEST_KEY.job.out" "$TEST_KEY.job.out" <<__OUT__
$SUITE_RUN_DIR/log/job/2013010100/t1/01/job.out:hello world
$SUITE_RUN_DIR/log/job/2013010112/t1/01/job.out:hello world
__OUT__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit
