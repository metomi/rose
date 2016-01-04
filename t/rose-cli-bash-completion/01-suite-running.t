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
# Test the rose CLI bash completion script for running suites.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
export ROSE_CONF_PATH=
tests 20
#-------------------------------------------------------------------------------
# Source the script.
. $ROSE_HOME/etc/rose-bash-completion || exit 1
#-------------------------------------------------------------------------------
# Run the suite.
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -q -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost
#-------------------------------------------------------------------------------
# rose suite-gcontrol --name=
TEST_KEY=$TEST_KEY_BASE
TEST_KEY=$TEST_KEY_BASE-gcontrol-name
COMP_WORDS=( rose suite-gcontrol --name = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply" '^'"$NAME"'$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# rose suite-log -n
TEST_KEY=$TEST_KEY_BASE
TEST_KEY=$TEST_KEY_BASE-log-n
COMP_WORDS=( rose suite-log -n "" )
COMP_CWORD=3
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply" '^'"$NAME"'$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# rose suite-log --name
TEST_KEY=$TEST_KEY_BASE
TEST_KEY=$TEST_KEY_BASE-log-name
COMP_WORDS=( rose suite-log --name = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply" '^'"$NAME"'$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# rose suite-shutdown --name
TEST_KEY=$TEST_KEY_BASE
TEST_KEY=$TEST_KEY_BASE-shutdown-name
COMP_WORDS=( rose suite-shutdown --name = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply" '^'"$NAME"'$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# rose suite-stop --name
TEST_KEY=$TEST_KEY_BASE
TEST_KEY=$TEST_KEY_BASE-stop-name
COMP_WORDS=( rose suite-stop --name = "" )
COMP_CWORD=4
COMPREPLY=
run_pass "$TEST_KEY" _rose
compreply_grep "$TEST_KEY.reply" '^'"$NAME"'$'
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
#-------------------------------------------------------------------------------
# Wait for the suite to complete
touch $SUITE_RUN_DIR/flag
TIMEOUT=$(($(date +%s) + 60)) # wait 1 minute
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
rose suite-clean -q -y $NAME || exit 1
#-------------------------------------------------------------------------------
exit 0
