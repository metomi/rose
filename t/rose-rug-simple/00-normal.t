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
# Test "rose rug-simple", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=

#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
# Run the suite
TEST_KEY=$TEST_KEY_BASE-suite-run
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" rose suite-run --name=$NAME --no-gcontrol \
    -C $ROSE_HOME/etc/rose-rug-simple -- --debug
#-------------------------------------------------------------------------------
file_cmp "$TEST_KEY_BASE.hello.log" \
    $SUITE_RUN_DIR/share/data/hello.log <<'__LOG__'
[20130101T0000Z] Hello World
[20130101T0600Z] Hello World
[20130101T1200Z] Hello World
[20130101T1800Z] Hello World
[20130102T0000Z] Hello World
__LOG__
sqlite3 $SUITE_RUN_DIR/cylc-suite.db \
    'select cycle,name,status from task_states where status=="succeeded";' \
    | LANG=C sort >"$TEST_KEY_BASE.db"
file_cmp "$TEST_KEY_BASE.db" "$TEST_KEY_BASE.db" <<'__DB__'
20130101T0000Z|hello|succeeded
20130101T0600Z|hello|succeeded
20130101T1200Z|hello|succeeded
20130101T1800Z|hello|succeeded
20130102T0000Z|hello|succeeded
__DB__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
