#!/usr/bin/env bash
#-------------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# Test "rose host-select", detect localhost and equivalent names.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

# Where possible add an extra host to the test command
# This obviously assumes that "job-host-with-share" is not the localhost
MORE_HOST=$(rose config --default= 't' 'job-host-with-share')
export ROSE_CONF_PATH=

LOCAL_HOSTS='localhost 127.0.0.1'
for CMD in 'hostname -s' 'hostname' 'hostname -f' 'hostname -I'; do
    if LOCAL_HOST=$(eval "$CMD"); then
        if ssh -n -q -oBatchMode=yes "${LOCAL_HOST}" true 1>'/dev/null' 2>&1
        then
            LOCAL_HOSTS="${LOCAL_HOSTS} ${LOCAL_HOST}"
        fi
    fi
done
HOSTS="${LOCAL_HOSTS}"
if [[ -n "${MORE_HOST}" ]]; then
    HOSTS="${HOSTS} ${MORE_HOST}"
fi

tests "$(($(wc -w <<<"${HOSTS}") + 2))"

run_pass "${TEST_KEY_BASE}" rose 'host-select' -v -v ${HOSTS}

# 1 bash command
sed 's/[0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0-9]*/YYYY-MM-DDTHHMM/g'\
     "${TEST_KEY_BASE}.out" > stamp-removed.log
grep -F "[INFO] YYYY-MM-DDTHHMM rose" "stamp-removed.log" >"${TEST_KEY_BASE}.out.1"
file_cmp "${TEST_KEY_BASE}.out.1" "${TEST_KEY_BASE}.out.1" <<'__OUT__'
[INFO] YYYY-MM-DDTHHMM rose host-select-client <<'__STDIN__'
__OUT__

# 0 ssh LOCAL_HOST command
for LOCAL_HOST in ${LOCAL_HOSTS}; do
    run_fail "${TEST_KEY_BASE}.out.${LOCAL_HOST}" \
        grep -F "[INFO] ssh -oBatchMode=yes -oConnectTimeout=10 ${LOCAL_HOST}" \
        "${TEST_KEY_BASE}.out"
done

# 1 ssh MORE_HOST command
if [[ -n ${MORE_HOST} ]]; then
    sed 's/[0-9]*-[0-9]*-[0-9]*T[0-9]*:[0-9]*:[0-9]*+[0-9]*/YYYY-MM-DDTHHMM/g'\
        "${TEST_KEY_BASE}.out" > stamp-removed.log
    grep -F "[INFO] YYYY-MM-DDTHHMM ssh -oBatchMode=yes -oConnectTimeout=10 ${MORE_HOST}" \
        "stamp-removed.log" >"${TEST_KEY_BASE}.out.${MORE_HOST}"
    file_cmp "${TEST_KEY_BASE}.out.${MORE_HOST}" \
        "${TEST_KEY_BASE}.out.${MORE_HOST}" <<__OUT__
[INFO] YYYY-MM-DDTHHMM ssh -oBatchMode=yes -oConnectTimeout=10 ${MORE_HOST} bash <<'__STDIN__'
__OUT__
fi

exit
