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
# Test fcm_make built-in application:
# * new mode, orig make only
#
# N.B. Test requires compatible versions of "rose" and "fcm make", as well as
#      "gfortran" being installed and available.
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

if ! fcm help make 1>/dev/null 2>&1; then
    skip_all '"fcm make" unavailable'
fi
if ! gfortran --version 1>/dev/null 2>&1; then
    skip_all '"gfortran" unavailable'
fi
if [[ "${TEST_KEY_BASE}" == *-with-share ]]; then
    JOB_HOST="$(rose config --default= 't' 'job-host-with-share')"
else
    JOB_HOST="$(rose config --default= 't' 'job-host')"
fi
if [[ -n "${JOB_HOST}" ]]; then
    JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
fi
if [[ -z "${JOB_HOST}" ]]; then
    skip_all '"[t]job-host" not defined or not available'
fi
#-------------------------------------------------------------------------------
tests 4
export ROSE_CONF_PATH=
get_reg

run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        --workflow-name="${FLOW}" \
        --no-run-name \
        -C "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        -S "HOST='${JOB_HOST}'"

# Add some garbage before running the suite
ssh -n -oBatchMode=yes "${JOB_HOST}" \
    "mkdir -p 'cylc-run/${FLOW}/share/hello-make/junk2'"
ssh -n -oBatchMode=yes "${JOB_HOST}" \
    "touch 'cylc-run/${FLOW}/share/hello-make/junk1'"

run_pass "${TEST_KEY_BASE}-play" \
    timeout 120 \
        cylc play \
            "${FLOW}" \
            --abort-if-any-task-fails \
            --host='localhost' \
            --no-detach \
            --debug
#-------------------------------------------------------------------------------
ssh -n -oBatchMode=yes "${JOB_HOST}" \
    cat "cylc-run/${FLOW}/share/hello.txt" >'hello.txt'
file_cmp "${TEST_KEY_BASE}" 'hello.txt' <<<'Hello World!'
run_fail "${TEST_KEY_BASE}" \
    ssh -n -oBatchMode=yes "${JOB_HOST}" \
    "ls 'cylc-run/${FLOW}/share/hello-make/junk'*"
#-------------------------------------------------------------------------------
purge
exit 0
