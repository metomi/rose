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
# Test for "rosie ls", ensure healthy on large number of checked out suites.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"
if ! python2 -c 'import cherrypy, sqlalchemy' 2>'/dev/null'; then
    skip_all '"cherrypy" or "sqlalchemy" not installed'
fi
tests 3
#-------------------------------------------------------------------------------
# Setup Rose site/user configuration for the tests.
export TZ='UTC'

set -e

# Create repositories
mkdir 'repos'
svnadmin create 'repos/foo'
SVN_URL_FOO="file://${PWD}/repos/foo"

# Setup configuration file.
mkdir 'conf'
cat >'conf/rose.conf' <<__ROSE_CONF__
opts=port

[rosie-db]
repos.foo=${PWD}/repos/foo
db.foo=sqlite:///${PWD}/repos/foo.db

[rosie-id]
local-copy-root=${PWD}/roses
prefix-location.foo=$SVN_URL_FOO
__ROSE_CONF__
export ROSE_CONF_PATH="${PWD}/conf"

mkdir 'conf/opt'
touch 'conf/opt/rose-port.conf'

#-------------------------------------------------------------------------------
# Add some suites
N_SUITES=256
for I in $(seq 1 "${N_SUITES}"); do
    cat >'rose-suite.info' <<__ROSE_SUITE_INFO
description=Number of berries is ${I}
owner=daisy
project=smoothie
title=Berry Berry
__ROSE_SUITE_INFO
    rosie create -q -y --prefix=foo --info-file='rose-suite.info'
done

# Setup DB
"${ROSE_HOME}/sbin/rosa" db-create -q

#-------------------------------------------------------------------------------
# Run WS
PORT="$((RANDOM + 10000))"
while port_is_busy "${PORT}"; do
    PORT="$((RANDOM + 10000))"
done
cat >'conf/opt/rose-port.conf' <<__ROSE_CONF__
[rosie-id]
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
{
    echo 'local suite               owner project  title'
    for I in $(seq 1 "${N_SUITES}"); do
        IDN="$(printf "%03d" $((${I} - 1)))"
        REV="$((${I} - 1))"
        PAD="$(printf "%0.s " $(seq $(wc -c <<<"${I}") 4))"
        echo "=     foo-aa${IDN}/trunk@${I}${PAD}daisy smoothie Berry Berry"
    done
} >"${TEST_KEY}.out.expected"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <"${TEST_KEY}.out.expected"
file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" <'/dev/null'
#-------------------------------------------------------------------------------
kill "${ROSA_WS_PID}"
wait 2>'/dev/null'
rm -f ~/.metomi/rosie-disco-0.0.0.0-${PORT}*
exit
