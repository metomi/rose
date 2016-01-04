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
# Test "rose config", optional configuration.
# N.B. More usages tested by "rose-app-run/07-opt.t".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
FILE=$PWD/rose-t.conf
cat >$FILE <<'__CONF__'
# Location
#
# London
location=London
greeting=Hello
my-home=$HOME

opts=bus taxi
__CONF__
mkdir opt/
cat >opt/rose-t-bus.conf <<'__CONF__'

# London bus
[bus]
decks=2
colour=red
name=Routemaster
__CONF__
cat >opt/rose-t-taxi.conf <<'__CONF__'

# London taxi
[taxi]
colour=black
name=Hackney Carriage
__CONF__

#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
# Dump file.
TEST_KEY=$TEST_KEY_BASE-dump
setup
run_pass "$TEST_KEY" rose config -f $FILE
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" <<'__OUT__'
# Location
#
# London

greeting=Hello
location=London
my-home=$HOME

# London bus
[bus]
colour=red
decks=2
name=Routemaster

# London taxi
[taxi]
colour=black
name=Hackney Carriage
__OUT__
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
exit 0
