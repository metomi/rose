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
# Test "rose host-select".
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
HOST_GROUPS=$(rose config 't' "host-groups")
if [[ -n $HOST_GROUPS ]]; then
    N_HOST_GROUPS=0
    for HOST_GROUP in $HOST_GROUPS; do
        ((++N_HOST_GROUPS))
    done
else
    N_HOST_GROUPS=1
fi
tests $((N_HOST_GROUPS * 2 + 4))
#-------------------------------------------------------------------------------
# Host groups that can be tested.
if [[ -n $HOST_GROUPS ]]; then
    for HOST_GROUP in $HOST_GROUPS; do
        TEST_KEY=$TEST_KEY_BASE-group-$HOST_GROUP
        run_pass "$TEST_KEY" rose 'host-select' $HOST_GROUP
        file_test "$TEST_KEY.out" "$TEST_KEY.out" -s
    done
else
    skip 2 '[t:rose-host-select]groups not defined'
fi
#-------------------------------------------------------------------------------
# Default host group.
TEST_KEY=$TEST_KEY_BASE-default
if [[ -n $(rose config 'rose-host-select' 'default') ]]; then
    run_pass "$TEST_KEY" rose 'host-select'
    file_test "$TEST_KEY.out" "$TEST_KEY.out" -s
else
    skip 2 'rose-host-select default not set'
fi
#-------------------------------------------------------------------------------
# Default host group using memory rank method
TEST_KEY=$TEST_KEY_BASE-default-mem
if [[ -n $(rose config 'rose-host-select' 'default') ]]; then
    run_pass "$TEST_KEY" rose 'host-select' --rank-method=mem
    file_test "$TEST_KEY.out" "$TEST_KEY.out" -s
else
    skip 2 'rose-host-select default not set'
fi
#-------------------------------------------------------------------------------
exit 0
