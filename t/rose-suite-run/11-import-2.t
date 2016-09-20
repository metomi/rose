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
# Test "rose suite-run", multiple imports.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 5
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
#-------------------------------------------------------------------------------
# Install the "greet_earth" suite
TEST_KEY="$TEST_KEY_BASE-local-install"
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE/greet_earth -n $NAME -l
(cd ~/cylc-run/$NAME; find app bin -type f | LANG=C sort) >"$TEST_KEY.find"
file_cmp "$TEST_KEY.find" "$TEST_KEY.find" <<'__FIND__'
app/hello/rose-app.conf
bin/my-hello
__FIND__
{
    CONF=$HOME/cylc-run/$NAME/log/rose-suite-run.conf
    rose config -f $CONF jinja2:suite.rc hello
    rose config -f $CONF jinja2:suite.rc worlds
} >"$TEST_KEY.conf"
file_cmp "$TEST_KEY.conf" "$TEST_KEY.conf" <<'__FIND__'
"Greet"
["Earth", "Moon"]
__FIND__
#-------------------------------------------------------------------------------
# Start the "greet_earth" suite
TEST_KEY="$TEST_KEY_BASE-suite-run"
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE/greet_earth \
    -n $NAME --no-gcontrol -- --debug
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-suite-run-my-hello.log"
LANG=C sort $SUITE_RUN_DIR/my-hello.log >"$TEST_KEY"
file_cmp "$TEST_KEY" "$TEST_KEY" <<'__LOG__'
[20130101T0000Z] Greet Earth
[20130101T0000Z] Greet Moon
[20130101T1200Z] Greet Earth
[20130101T1200Z] Greet Moon
[20130102T0000Z] Greet Earth
[20130102T0000Z] Greet Moon
__LOG__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
