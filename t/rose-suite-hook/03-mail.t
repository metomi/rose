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
# Test "rose suite-hook --mail", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
mock_smtpd_init
if [[ -z ${TEST_SMTPD_HOST:-} ]]; then
    skip_all "cannot start mock SMTP server"
fi
mkdir conf
cat >conf/rose.conf <<__CONF__
[rose-suite-hook]
smtp-host=$TEST_SMTPD_HOST
__CONF__
export ROSE_CONF_PATH=$PWD/conf

#-------------------------------------------------------------------------------
tests 31
#-------------------------------------------------------------------------------
# Run the suite.
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -q -- --debug
N_QUIT=0
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose suite-hook --mail succeeded $NAME t1.1 ''
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
((++N_QUIT))
TIMEOUT=$(($(date +%s) + 10))
while (($(date +%s) <= $TIMEOUT)) \
    && (($(grep -c "Data: 'quit'" "$TEST_SMTPD_LOG") < $N_QUIT))
do
    sleep 1
done
tail -2 "$TEST_SMTPD_LOG" >smtpd-tail.out
file_grep "$TEST_KEY.smtp.from" "From: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" "To: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.subject" \
    "Subject: \\[succeeded\\] $NAME" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.1" "Task: t1.1" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.2" "See: .*/$NAME\\>" smtpd-tail.out
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-cc
run_pass "$TEST_KEY" \
    rose suite-hook --mail --mail-cc=holly,ivy succeeded $NAME t1.1 ''
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
((++N_QUIT))
TIMEOUT=$(($(date +%s) + 10))
while (($(date +%s) <= $TIMEOUT)) \
    && (($(grep -c "Data: 'quit'" "$TEST_SMTPD_LOG") < $N_QUIT))
do
    sleep 1
done
tail -2 "$TEST_SMTPD_LOG" >smtpd-tail.out
file_grep "$TEST_KEY.smtp.from" "From: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" "To: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" \
    "Cc: holly@localhost, ivy@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.subject" \
    "Subject: \\[succeeded\\] $NAME" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.1" "Task: t1.1" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.2" "See: .*/$NAME\\>" smtpd-tail.out
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-at-host
cat >conf/rose.conf <<__CONF__
[rose-suite-hook]
smtp-host=$TEST_SMTPD_HOST
email-host=hms.beagle
__CONF__
run_pass "$TEST_KEY" rose suite-hook \
    --mail --mail-cc=robert.fitzroy,charles.darwin,nobody@home \
    succeeded $NAME t1.1 ''
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
((++N_QUIT))
TIMEOUT=$(($(date +%s) + 10))
while (($(date +%s) <= $TIMEOUT)) \
    && (($(grep -c "Data: 'quit'" "$TEST_SMTPD_LOG") < $N_QUIT))
do
    sleep 1
done
tail -2 "$TEST_SMTPD_LOG" >smtpd-tail.out
file_grep "$TEST_KEY.smtp.from" "From: $USER@hms.beagle" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" "To: $USER@hms.beagle" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" \
    "Cc: robert.fitzroy@hms.beagle, charles.darwin@hms.beagle, nobody@home" \
    smtpd-tail.out
file_grep "$TEST_KEY.smtp.subject" \
    "Subject: \\[succeeded\\] $NAME" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.1" "Task: t1.1" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.2" "See: .*/$NAME\\>" smtpd-tail.out
tail -20 "$TEST_SMTPD_LOG" >smtpd-tail.out
file_grep "$TEST_KEY.smtp.mail.from" \
    "^===> MAIL FROM:<$USER@hms.beagle>" smtpd-tail.out
file_grep "$TEST_KEY.smtp.rcpt.to.1" \
    "^===> RCPT TO:<$USER@hms.beagle>" smtpd-tail.out
file_grep "$TEST_KEY.smtp.rcpt.to.2" \
    "^===> RCPT TO:<robert.fitzroy@hms.beagle>" smtpd-tail.out
file_grep "$TEST_KEY.smtp.rcpt.to.3" \
    "^===> RCPT TO:<charles.darwin@hms.beagle>" smtpd-tail.out
file_grep "$TEST_KEY.smtp.rcpt.to.4" \
    "^===> RCPT TO:<nobody@home>" smtpd-tail.out
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
mock_smtpd_kill
exit 0
