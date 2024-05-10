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
# Compatibility Mode Test
# Ensure that when Cylc Rose gets workflow config that
# compatibility run mode isn't changed.
# https://github.com/cylc/cylc-rose/issues/319
#-------------------------------------------------------------------------------
. "$(dirname "$0")/test_header"

if ! fcm help make 1>/dev/null 2>&1; then
    skip_all '"fcm make" unavailable'
fi
if ! gfortran --version 1>/dev/null 2>&1; then
    skip_all '"gfortran" unavailable'
fi
JOB_HOST="$(rose config --default= 't' 'job-host')"
if [[ -n "${JOB_HOST}" ]]; then
    JOB_HOST="$(rose host-select -q "${JOB_HOST}")"
fi
if [[ -z "${JOB_HOST}" ]]; then
    skip_all '"[t]job-host" not defined or not available'
fi

tests 2
export ROSE_CONF_PATH=
get_reg

run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        --workflow-name="${FLOW}" \
        --no-run-name \
        -S "HOST='${JOB_HOST}'" \
        "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}"

run_pass "${TEST_KEY_BASE}-play" \
    timeout 120 \
        cylc play \
            "${FLOW}" \
            --abort-if-any-task-fails \
            --host='localhost' \
            --no-detach \
            --debug

purge
exit 0
