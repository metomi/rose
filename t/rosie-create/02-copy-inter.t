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
# Test for "rosie create", inter-repository copies.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
#-------------------------------------------------------------------------------
tests 16
#-------------------------------------------------------------------------------
svnadmin create 'bar'
svnadmin create 'foo'
URL_BAR="file://${PWD}/bar"
URL_FOO="file://${PWD}/foo"
cat >'rose.conf' <<__ROSE_CONF__
[rosie-id]
local-copy-root=${PWD}/roses
prefix-default=foo
prefix-username.bar=bob
prefix-location.bar=${URL_BAR}
prefix-username.foo=fred
prefix-location.foo=${URL_FOO}
__ROSE_CONF__
export ROSE_CONF_PATH=$PWD
#-------------------------------------------------------------------------------
# Create some suites, add some contents
cat >'rose-suite.info' <<__INFO__
owner=$USER
project=bar
title=barley
__INFO__
rosie create -q --prefix='bar' --info-file='rose-suite.info' -y
mkdir -p "${PWD}/roses/bar-aa000/app/barley"
cat >"${PWD}/roses/bar-aa000/app/barley/rose-app.conf" <<'__CONF__'
[command]
default=printenv BARLEY
__CONF__
cat >"${PWD}/roses/bar-aa000/rose-suite.conf" <<'__CONF__'
[env]
BARLEY=an important grain
__CONF__
svn add --parents -q "${PWD}/roses/bar-aa000/app/barley/rose-app.conf"
svn commit -q -m 'whatever' "${PWD}/roses/bar-aa000"

cat >'rose-suite.info' <<__INFO__
owner=$USER
project=foo
title=football
__INFO__
rosie create -q --prefix='foo' --info-file='rose-suite.info' -y
mkdir -p "${PWD}/roses/foo-aa000/app/football"
cat >"${PWD}/roses/foo-aa000/app/football/rose-app.conf" <<'__CONF__'
[command]
default=printenv FOOTBALL
__CONF__
cat >"${PWD}/roses/foo-aa000/rose-suite.conf" <<'__CONF__'
[env]
FOOTBALL=a good game
__CONF__
svn add --parents -q "${PWD}/roses/foo-aa000/app/football/rose-app.conf"
svn commit -q -m 'whatever' "${PWD}/roses/foo-aa000"
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-foo-foo"
run_pass "${TEST_KEY}" rosie copy -y 'foo-aa000'
{
    echo "[INFO] foo-aa001: created at ${URL_FOO}/a/a/0/0/1"
    echo "[INFO] foo-aa001: copied items from foo-aa000/trunk@2"
    echo "[INFO] foo-aa001: local copy created at ${PWD}/roses/foo-aa001"
}>"${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" "${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
file_cmp "${TEST_KEY}-rose-suite.conf" \
    "${PWD}/roses/foo-aa000/rose-suite.conf" \
    "${PWD}/roses/foo-aa001/rose-suite.conf" \
file_cmp "${TEST_KEY}-rose-app.conf" \
    "${PWD}/roses/foo-aa000/app/football/rose-app.conf" \
    "${PWD}/roses/foo-aa001/app/football/rose-app.conf" \
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-bar-bar"
run_pass "${TEST_KEY}" rosie copy -y 'bar-aa000'
{
    echo "[INFO] bar-aa001: created at ${URL_BAR}/a/a/0/0/1"
    echo "[INFO] bar-aa001: copied items from bar-aa000/trunk@2"
    echo "[INFO] bar-aa001: local copy created at ${PWD}/roses/bar-aa001"
}>"${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" "${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
file_cmp "${TEST_KEY}-rose-suite.conf" \
    "${PWD}/roses/bar-aa000/rose-suite.conf" \
    "${PWD}/roses/bar-aa001/rose-suite.conf" \
file_cmp "${TEST_KEY}-rose-app.conf" \
    "${PWD}/roses/bar-aa000/app/barley/rose-app.conf" \
    "${PWD}/roses/bar-aa001/app/barley/rose-app.conf" \
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-foo-bar"
run_pass "${TEST_KEY}" rosie copy --prefix='bar' -y 'foo-aa000'
{
    echo "[INFO] bar-aa002: created at ${URL_BAR}/a/a/0/0/2"
    echo "[INFO] bar-aa002: copied items from foo-aa000/trunk@2"
    echo "[INFO] bar-aa002: local copy created at ${PWD}/roses/bar-aa002"
}>"${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" "${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
file_cmp "${TEST_KEY}-rose-suite.conf" \
    "${PWD}/roses/foo-aa000/rose-suite.conf" \
    "${PWD}/roses/bar-aa002/rose-suite.conf" \
file_cmp "${TEST_KEY}-rose-app.conf" \
    "${PWD}/roses/foo-aa000/app/football/rose-app.conf" \
    "${PWD}/roses/bar-aa002/app/football/rose-app.conf" \
#-------------------------------------------------------------------------------
TEST_KEY="${TEST_KEY_BASE}-bar-foo"
run_pass "${TEST_KEY}" rosie copy --prefix='foo' -y 'bar-aa000'
{
    echo "[INFO] foo-aa002: created at ${URL_FOO}/a/a/0/0/2"
    echo "[INFO] foo-aa002: copied items from bar-aa000/trunk@2"
    echo "[INFO] foo-aa002: local copy created at ${PWD}/roses/foo-aa002"
}>"${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" "${TEST_KEY}.out.1"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
file_cmp "${TEST_KEY}-rose-suite.conf" \
    "${PWD}/roses/bar-aa000/rose-suite.conf" \
    "${PWD}/roses/foo-aa002/rose-suite.conf" \
file_cmp "${TEST_KEY}-rose-app.conf" \
    "${PWD}/roses/bar-aa000/app/barley/rose-app.conf" \
    "${PWD}/roses/foo-aa002/app/barley/rose-app.conf" \
#-------------------------------------------------------------------------------
exit 0
