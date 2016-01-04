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
# Test "rose config", optional keys for optional configuration.
# N.B. More usages tested by "rose-app-run/07-opt.t".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

conf_bus() {
    cat >'opt/rose-t-bus.conf' <<'__CONF__'

# London bus
[bus]
decks=2
colour=red
name=Routemaster
__CONF__
}

conf_taxi() {
    cat >'opt/rose-t-taxi.conf' <<'__CONF__'

# London taxi
[taxi]
colour=black
name=Hackney Carriage
__CONF__
}

conf_root() {
    rm -f 'opt/rose-t-bus.conf' 'opt/rose-t-taxi.conf'
    FILE="${PWD}/rose-t.conf"
    cat >"${FILE}" <<__CONF__
# Location
#
# London
location=London
greeting=Hello
my-home=\$HOME
opts=${@}
__CONF__
}

ok_root() {
    run_pass "$TEST_KEY" rose config -f "${FILE}"
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
# Location
#
# London

greeting=Hello
location=London
my-home=$HOME
__OUT__
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
}

ok_root_bus() {
    run_pass "$TEST_KEY" rose config -f "${FILE}"
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
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
__OUT__
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
}

ok_root_taxi() {
    run_pass "$TEST_KEY" rose config -f "${FILE}"
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
# Location
#
# London

greeting=Hello
location=London
my-home=$HOME

# London taxi
[taxi]
colour=black
name=Hackney Carriage
__OUT__
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
}

ok_root_bus_taxi() {
    run_pass "$TEST_KEY" rose config -f "${FILE}"
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__OUT__'
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
    file_cmp "${TEST_KEY}.err" "${TEST_KEY}.err" </dev/null
}

not_ok_opt() {
    local KEY="${1}"
    run_fail "$TEST_KEY" rose config -f "${FILE}"
    file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" </dev/null
    file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERR__
[FAIL] [Errno 2] No such file or directory: '${PWD}/opt/rose-t-${KEY}.conf'
__ERR__
}

mkdir 'opt/'

#-------------------------------------------------------------------------------
tests 48
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-0-0-0"
conf_root '(bus)' '(taxi)'
ok_root
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-0-0-1"
conf_root '(bus)' '(taxi)'
conf_taxi
ok_root_taxi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-0-1-0"
conf_root '(bus)' 'taxi'
not_ok_opt 'taxi'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-0-1-1"
conf_root '(bus)' 'taxi'
conf_taxi
ok_root_taxi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-1-0-0"
conf_root '(bus)' '(taxi)'
conf_bus
ok_root_bus
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-1-0-1"
conf_root '(bus)' '(taxi)'
conf_bus
conf_taxi
ok_root_bus_taxi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-1-1-0"
conf_root '(bus)' 'taxi'
conf_bus
not_ok_opt 'taxi'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-0-1-1-1"
conf_root '(bus)' 'taxi'
conf_bus
conf_taxi
ok_root_bus_taxi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-0-0-0"
conf_root 'bus' '(taxi)'
not_ok_opt 'bus'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-0-0-1"
conf_root 'bus' '(taxi)'
conf_taxi
not_ok_opt 'bus'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-0-1-0"
conf_root 'bus' 'taxi'
not_ok_opt 'bus'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-0-1-1"
conf_root 'bus' 'taxi'
conf_taxi
not_ok_opt 'bus'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-1-0-0"
conf_root 'bus' '(taxi)'
conf_bus
ok_root_bus
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-1-0-1"
conf_root 'bus' '(taxi)'
conf_bus
conf_taxi
ok_root_bus_taxi
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-1-1-0"
conf_root 'bus' 'taxi'
conf_bus
not_ok_opt 'taxi'
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-1-1-1-1"
conf_root 'bus' 'taxi'
conf_bus
conf_taxi
ok_root_bus_taxi
#-------------------------------------------------------------------------------
exit 0
