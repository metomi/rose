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
# Test "rose suite-run", import.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
tests 6
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
#-------------------------------------------------------------------------------
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
#-------------------------------------------------------------------------------
# Install the "hello_earth" suite
TEST_KEY="$TEST_KEY_BASE-local-install"
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE/hello_earth -n $NAME -l
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
"Hello"
["Earth", "Moon"]
__FIND__
#-------------------------------------------------------------------------------
# Start the "hello_earth" suite
TEST_KEY="$TEST_KEY_BASE-suite-run"
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE/hello_earth \
    -n $NAME --no-gcontrol
#-------------------------------------------------------------------------------
# Wait for the "hello_earth" suite to complete
TEST_KEY="$TEST_KEY_BASE-suite-run-wait"
TIMEOUT=$(($(date +%s) + 120)) # wait 2 minutes
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
    exit 1
else
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-suite-run-my-hello.log"
LANG=C sort $SUITE_RUN_DIR/my-hello.log >"$TEST_KEY"
file_cmp "$TEST_KEY" "$TEST_KEY" <<'__LOG__'
[2013010100] Hello Earth
[2013010100] Hello Moon
[2013010112] Hello Earth
[2013010112] Hello Moon
[2013010200] Hello Earth
[2013010200] Hello Moon
__LOG__
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
