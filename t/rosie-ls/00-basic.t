#!/bin/bash
#-------------------------------------------------------------------------------
# Copyright (C) 2012-2018 British Crown (Met Office) & Contributors.
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
# Basic tests for "rosie ls", with 2 repositories.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
if ! python2 -c 'import cherrypy, sqlalchemy' 2>/dev/null; then
    skip_all '"cherrypy" or "sqlalchemy" not installed'
fi
tests 15
#-------------------------------------------------------------------------------
# Setup Rose site/user configuration for the tests.
export TZ='UTC'

set -e

# Create repositories
mkdir 'repos'
svnadmin create 'repos/foo'
SVN_URL_FOO="file://${PWD}/repos/foo"
svnadmin create 'repos/bar'
SVN_URL_BAR="file://${PWD}/repos/bar"

# Setup configuration file.
mkdir conf
cat >conf/rose.conf <<__ROSE_CONF__
opts=port

[rosie-db]
repos.bar=$PWD/repos/bar
repos.foo=$PWD/repos/foo
db.bar=sqlite:///$PWD/repos/bar.db
db.foo=sqlite:///$PWD/repos/foo.db

[rosie-id]
local-copy-root=$PWD/roses
prefix-location.foo=$SVN_URL_FOO
prefix-location.bar=$SVN_URL_BAR
__ROSE_CONF__
export ROSE_CONF_PATH="${PWD}/conf"

mkdir 'conf/opt'
touch 'conf/opt/rose-port.conf'

# Add some suites
cat >'rose-suite.info' <<'__ROSE_SUITE_INFO'
access-list=*
description=Strawberry, raspberry, blueberry, blackberry
owner=daisy
project=smoothie
title=Berry berry
__ROSE_SUITE_INFO
rosie create -q -y --prefix=foo --info-file=rose-suite.info

cat >'rose-suite.info' <<'__ROSE_SUITE_INFO'
access-list=*
description=Hit or stand?
owner=betty
project=game
title=Blackjack
__ROSE_SUITE_INFO
rosie create -q -y --prefix=foo --info-file=rose-suite.info

cat >'rose-suite.info' <<'__ROSE_SUITE_INFO'
access-list=*
description=Banana, mango, pineapple, passion fruit
owner=holly
project=smoothie
title=Tropical parasite
__ROSE_SUITE_INFO
rosie create -q -y --prefix=bar --info-file=rose-suite.info
svn cp -q -m 'branch create' --non-interactive --no-auth-cache \
    "$SVN_URL_BAR/a/a/0/0/0/trunk" "$SVN_URL_BAR/a/a/0/0/0/fix-typo"
svn sw -q "$SVN_URL_BAR/a/a/0/0/0/fix-typo" "$PWD/roses/bar-aa000"
cat >"$PWD/roses/bar-aa000/rose-suite.info" <<'__ROSE_SUITE_INFO'
access-list=*
description=Banana, mango, pineapple, passion fruit
owner=holly
project=smoothie
title=Tropical paradise
__ROSE_SUITE_INFO
svn ci -q -m 'fix typo' --non-interactive --no-auth-cache \
    "$PWD/roses/bar-aa000"
svn sw -q "$SVN_URL_BAR/a/a/0/0/0/trunk" "$PWD/roses/bar-aa000"
svn merge --force '^/a/a/0/0/0/fix-typo' "$PWD/roses/bar-aa000"
svn ci -q -m 'merge typo fix' --non-interactive --no-auth-cache \
    "$PWD/roses/bar-aa000"

cat >'rose-suite.info' <<'__ROSE_SUITE_INFO'
access-list=*
description=1, 2, 3, 4, 5, or 6?
owner=penny
project=game
title=Dice
__ROSE_SUITE_INFO
rosie create -q -y --prefix=bar --info-file=rose-suite.info

# Setup DB
$ROSE_HOME/sbin/rosa db-create -q

#-------------------------------------------------------------------------------
# Run WS
PORT="$((RANDOM + 10000))"
while port_is_busy "${PORT}"; do
    PORT="$((RANDOM + 10000))"
done
cat >'conf/opt/rose-port.conf' <<__ROSE_CONF__
[rosie-id]
prefix-ws.bar=http://${HOSTNAME}:${PORT}/bar
prefix-ws.foo=http://${HOSTNAME}:${PORT}/foo
__ROSE_CONF__
rosie disco 'start' "${PORT}" \
    0<'/dev/null' 1>'rosie-disco.out' 2>'rosie-disco.err' &
ROSA_WS_PID="${!}"
T_INIT="$(date +%s)"
while ! port_is_busy "${PORT}" && (($(date +%s) < T_INIT + 60)); do
    sleep 1
done
if ! port_is_busy "${PORT}"; then
    exit 1
fi

#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}"
run_pass "${TEST_KEY}" rosie ls
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<__OUT__
local suite             owner project  title
=     foo-aa000/trunk@1 daisy smoothie Berry berry
=     foo-aa001/trunk@2 betty game     Blackjack
=     bar-aa000/trunk@4 holly smoothie Tropical paradise
=     bar-aa001/trunk@5 penny game     Dice
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-prefix"
run_pass "${TEST_KEY}" rosie ls --prefix=foo
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<__OUT__
local suite             owner project  title
=     foo-aa000/trunk@1 daisy smoothie Berry berry
=     foo-aa001/trunk@2 betty game     Blackjack
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-no-headers"
run_pass "${TEST_KEY}" rosie ls --no-headers
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<__OUT__
= foo-aa000/trunk@1 daisy smoothie Berry berry
= foo-aa001/trunk@2 betty game     Blackjack
= bar-aa000/trunk@4 holly smoothie Tropical paradise
= bar-aa001/trunk@5 penny game     Dice
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-switch"
svn sw -q "$SVN_URL_BAR/a/a/0/0/0/fix-typo" "$PWD/roses/bar-aa000"
run_pass "${TEST_KEY}" rosie ls --prefix=bar
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<__OUT__
local suite                owner project  title
=     bar-aa000/fix-typo@3 holly smoothie Tropical paradise
=     bar-aa001/trunk@5    penny game     Dice
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
svn sw -q "$SVN_URL_BAR/a/a/0/0/0/trunk" "$PWD/roses/bar-aa000"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-old"
svn up -q -r 1 "$PWD/roses/bar-aa000"
run_pass "${TEST_KEY}" rosie ls --prefix=bar
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<__OUT__
local suite             owner project  title
<     bar-aa000/trunk@4 holly smoothie Tropical paradise
=     bar-aa001/trunk@5 penny game     Dice
__OUT__
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
svn up -q "$PWD/roses/bar-aa000"
#-------------------------------------------------------------------------------
kill "${ROSA_WS_PID}"
wait 2>'/dev/null'
rm -f ~/.metomi/rosie-disco-0.0.0.0-${PORT}*
exit
