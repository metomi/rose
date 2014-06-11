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
# Test "rosa svn-post-commit": notification, user-tool=passwd.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
if ! python -c 'import sqlalchemy' 2>/dev/null; then
    skip_all 'python: sqlalchemy not installed'
fi

mock_smtpd_init
if [[ -z ${TEST_SMTPD_HOST:-} ]]; then
    skip_all "cannot start mock SMTP server"
fi

# Sort email recipients
sort_recips() {
    perl -e 'print(join(", ", sort(@ARGV)), "\n")' "$@"
}

mkdir repos
svnadmin create repos/foo
SVN_URL=file://$PWD/repos/foo

mkdir conf
cat >conf/rose.conf <<__CONF__
[rosa-svn]
notification-from=notifications@nowhere.org
smtp-host=$TEST_SMTPD_HOST
user-tool=passwd

[rosie-db]
repos.foo=$PWD/repos/foo
db.foo=sqlite:///$PWD/repos/foo.db

[rosie-id]
local-copy-root=$PWD/roses
prefix-default=foo
prefix-owner-default.foo=fred
prefix-location.foo=$SVN_URL
__CONF__
export ROSE_CONF_PATH=$PWD/conf

cat >repos/foo/hooks/post-commit <<__POST_COMMIT__
#!/bin/bash
export ROSE_CONF_PATH=$ROSE_CONF_PATH
$ROSE_HOME/sbin/rosa svn-post-commit --debug "\$@" \\
    1>$PWD/rosa-svn-post-commit.out 2>$PWD/rosa-svn-post-commit.err
echo \$? >$PWD/rosa-svn-post-commit.rc
__POST_COMMIT__
chmod +x repos/foo/hooks/post-commit
export LANG=C
$ROSE_HOME/sbin/rosa db-create -q

tests 26
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-new"
cat >rose-suite.info <<__ROSE_SUITE_INFO
access-list=*
owner=$USER
project=hook
sub-project=post-commit
title=test post commit hook: create
__ROSE_SUITE_INFO
cat /dev/null >"$TEST_SMTPD_LOG"
rosie create -q -y --info-file=rose-suite.info --no-checkout
file_cmp "$TEST_KEY-smtpd.log" "$TEST_SMTPD_LOG" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-new-access-list"
cat >rose-suite.info <<__ROSE_SUITE_INFO
access-list=root
owner=$USER
project=hook
sub-project=post-commit
title=test post commit hook: create
__ROSE_SUITE_INFO
cat /dev/null >"$TEST_SMTPD_LOG"
rosie create -q -y --info-file=rose-suite.info --no-checkout

file_grep "$TEST_KEY-smtpd.log.sender" "^sender: notifications@nowhere.org" \
    "$TEST_SMTPD_LOG"
RECIPS=$(sort_recips "'$USER'" "'root'")
file_grep "$TEST_KEY-smtpd.log.recips" "^recips: \[$RECIPS\]" "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.subject" \
    "^Data: '.*Subject: \\[foo-aa001/trunk@2\\] owner/access-list change" \
    "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.text" \
    "^Data: '.*+ owner=$USER.*+ access-list=root'$" \
    "$TEST_SMTPD_LOG"
file_cmp "$TEST_KEY-rc" "$PWD/rosa-svn-post-commit.rc" <<<'0'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-mod-owner"
rosie checkout -q foo-aa000
cat >$PWD/roses/foo-aa000/rose-suite.info <<__ROSE_SUITE_INFO
access-list=*
owner=root
project=hook
sub-project=post-commit
title=test post commit hook: create
__ROSE_SUITE_INFO
cat /dev/null >"$TEST_SMTPD_LOG"
svn ci -q -m'foo-aa000: chown' $PWD/roses/foo-aa000/rose-suite.info
rm -fr $PWD/roses/foo-aa000
file_grep "$TEST_KEY-smtpd.log.sender" "^sender: notifications@nowhere.org" \
    "$TEST_SMTPD_LOG"
RECIPS=$(sort_recips "'$USER'" "'root'")
file_grep "$TEST_KEY-smtpd.log.recips" "^recips: \[$RECIPS\]" "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.subject" \
    "^Data: '.*Subject: \\[foo-aa000/trunk@3\\] owner/access-list change" \
    "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.text" \
    "^Data: '.*- owner=$USER.*+ owner=root'$" \
    "$TEST_SMTPD_LOG"
file_cmp "$TEST_KEY-rc" "$PWD/rosa-svn-post-commit.rc" <<<'0'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-mod-access-list"
rosie checkout -q foo-aa001
cat >$PWD/roses/foo-aa001/rose-suite.info <<__ROSE_SUITE_INFO
access-list=*
owner=$USER
project=hook
sub-project=post-commit
title=test post commit hook: create
__ROSE_SUITE_INFO
cat /dev/null >"$TEST_SMTPD_LOG"
svn ci -q -m'foo-aa001: chown' $PWD/roses/foo-aa001/rose-suite.info
rm -fr $PWD/roses/foo-aa001
file_grep "$TEST_KEY-smtpd.log.sender" "^sender: notifications@nowhere.org" \
    "$TEST_SMTPD_LOG"
RECIPS=$(sort_recips "'$USER'" "'root'")
file_grep "$TEST_KEY-smtpd.log.recips" "^recips: \[$RECIPS\]" "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.subject" \
    "^Data: '.*Subject: \\[foo-aa001/trunk@4\\] owner/access-list change" \
    "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.text" \
    "^Data: '.*- access-list=root.*+ access-list=\\*'$" \
    "$TEST_SMTPD_LOG"
file_cmp "$TEST_KEY-rc" "$PWD/rosa-svn-post-commit.rc" <<<'0'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-mod-access-list-2"
rosie checkout -q foo-aa001
cat >$PWD/roses/foo-aa001/rose-suite.info <<__ROSE_SUITE_INFO
access-list=root bin
owner=$USER
project=hook
sub-project=post-commit
title=test post commit hook: create
__ROSE_SUITE_INFO
cat /dev/null >"$TEST_SMTPD_LOG"
svn ci -q -m'foo-aa001: chown' $PWD/roses/foo-aa001/rose-suite.info
rm -fr $PWD/roses/foo-aa001
file_grep "$TEST_KEY-smtpd.log.sender" "^sender: notifications@nowhere.org" \
    "$TEST_SMTPD_LOG"
RECIPS=$(sort_recips "'bin'" "'$USER'" "'root'")
file_grep "$TEST_KEY-smtpd.log.recips" "^recips: \[$RECIPS\]" "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.subject" \
    "^Data: '.*Subject: \\[foo-aa001/trunk@5\\] owner/access-list change" \
    "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.text" \
    "^Data: '.*- access-list=\\*.*+ access-list=root bin'$" \
    "$TEST_SMTPD_LOG"
file_cmp "$TEST_KEY-rc" "$PWD/rosa-svn-post-commit.rc" <<<'0'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-del"
cat /dev/null >"$TEST_SMTPD_LOG"
rosie delete -y -q foo-aa001
file_grep "$TEST_KEY-smtpd.log.sender" "^sender: notifications@nowhere.org" \
    "$TEST_SMTPD_LOG"
RECIPS=$(sort_recips "'bin'" "'$USER'" "'root'")
file_grep "$TEST_KEY-smtpd.log.recips" "^recips: \[$RECIPS\]" "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.subject" \
    "^Data: '.*Subject: \\[foo-aa001/trunk@6\\] owner/access-list change" \
    "$TEST_SMTPD_LOG"
file_grep "$TEST_KEY-smtpd.log.text" \
    "^Data: '.*- owner=$USER.*- access-list=root bin'$" \
    "$TEST_SMTPD_LOG"
file_cmp "$TEST_KEY-rc" "$PWD/rosa-svn-post-commit.rc" <<<'0'
#-------------------------------------------------------------------------------
mock_smtpd_kill
exit 0
