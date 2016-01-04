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
# Test "rose suite-hook --mail --shutdown" when email does not work.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
# Run the suite.
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -q
#-------------------------------------------------------------------------------
# Start and stop the mail server.
bad_smtpd_init
if [[ -z ${TEST_SMTPD_HOST:-} ]]; then
    skip_all "cannot start bad SMTP server"
fi
mkdir conf
cat >conf/rose.conf <<__CONF__
[rose-suite-hook]
smtp-host=$TEST_SMTPD_HOST
__CONF__
export ROSE_CONF_PATH=$PWD/conf
#-------------------------------------------------------------------------------
tests 4
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_fail "$TEST_KEY" rose suite-hook --mail --shutdown \
    some-event "$NAME" some-msg
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_grep "$TEST_KEY.err" "^smtplib.SMTPServerDisconnected: " "$TEST_KEY.err"
TIMEOUT=$(($(date +%s) + 30)) # Wait a maximum of 30 seconds
while [[ -e $HOME/.cylc/ports/$NAME ]] && (($(date +%s) < TIMEOUT)); do
    sleep 1
done
if [[ -e $HOME/.cylc/ports/$NAME ]]; then
    fail "$TEST_KEY"
else
    pass "$TEST_KEY"
fi
#-------------------------------------------------------------------------------
bad_smtpd_kill
rose suite-clean -q -y $NAME
exit 0
