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
# Test "rose suite-hook --mail", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

python -m smtpd -c DebuggingServer -d -n 1>smtpd.out 2>&1 &
SMTPD_PID=$!
while ! grep -q 'DebuggingServer started' smtpd.out; do
    if ps $SMTPD_PID 1>/dev/null 2>&1; then
        sleep 1
    else
        echo "$TEST_KEY_BASE: cannot start SMTP server" >&2
        exit 1
    fi
done
mkdir conf
cat >conf/rose.conf <<'__CONF__'
[rose-suite-hook]
smtp-host=localhost:8025
__CONF__
export ROSE_CONF_PATH=$PWD/conf

#-------------------------------------------------------------------------------
tests 1
#-------------------------------------------------------------------------------
# Run the suite.
TEST_KEY=$TEST_KEY_BASE
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug -q
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-mail"
run_pass "$TEST_KEY" rose suite-hook --mail succeeded $NAME t1.1 ''
cat "$TEST_KEY.out"
cat "$TEST_KEY.err" >&2
cat smtpd.out
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
kill $SMTPD_PID
wait $SMTPD_PID
exit 0
